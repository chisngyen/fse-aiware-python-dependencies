"""Reusable agent tools — pure functions every method can call.

Each tool has a typed input/output and ZERO global state. Side effects
(constraints learned, reflections added) flow through the Blackboard
passed in by the calling method, never through hidden globals.

The CSP solver here delegates to the existing
``tools/cgar/src/constraint_solver.py`` — we DO NOT rewrite that logic.
"""

from __future__ import annotations

import logging
import re
import sys
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None  # type: ignore

from .paths import PROJECT_ROOT

log = logging.getLogger(__name__)

# Make tools/cgar/src importable without a copy.
_CGAR_SRC = PROJECT_ROOT / "tools" / "cgar" / "src"
if str(_CGAR_SRC) not in sys.path:
    sys.path.insert(0, str(_CGAR_SRC))


# ---------- PyPI metadata ----------------------------------------------

@dataclass
class PypiMetadata:
    name: str
    versions: list[str]                 # newest first
    requires_python: dict[str, str]     # version -> requires_python spec
    has_wheel_linux: dict[str, bool]    # version -> True if has linux wheel


@lru_cache(maxsize=2048)
def pypi_release_dates(package: str, timeout: int = 10) -> dict[str, str] | None:
    """Return {version: ISO-date} for first upload of each release.

    Powers temporal reasoning: agents can infer a snippet's authorship era
    from when its imported packages were released. Distinct from query_pypi
    because release dates are the SEMANTICALLY DIFFERENT signal (time, not
    compatibility) and a separate tool reads cleaner in agent traces.
    """
    if requests is None:
        return None
    try:
        r = requests.get(f"https://pypi.org/pypi/{package}/json", timeout=timeout)
        if r.status_code != 200:
            return None
        releases = r.json().get("releases", {}) or {}
    except Exception as e:  # noqa: BLE001
        log.debug("pypi_release_dates(%s) failed: %s", package, e)
        return None
    out: dict[str, str] = {}
    for v, files in releases.items():
        if not files:
            continue
        # Earliest upload_time across files; format "YYYY-MM-DDTHH:MM:SS"
        dates = sorted(f.get("upload_time", "") for f in files if f.get("upload_time"))
        if dates:
            out[v] = dates[0][:10]
    return out


@lru_cache(maxsize=2048)
def query_pypi(package: str, timeout: int = 10) -> PypiMetadata | None:
    """Fetch ``https://pypi.org/pypi/<pkg>/json`` and cache. Returns None on failure."""
    if requests is None:
        return None
    try:
        r = requests.get(f"https://pypi.org/pypi/{package}/json", timeout=timeout)
        if r.status_code != 200:
            return None
        data = r.json()
    except Exception as e:  # noqa: BLE001
        log.debug("query_pypi(%s) failed: %s", package, e)
        return None

    releases = data.get("releases", {}) or {}
    versions = sorted(releases.keys(), key=_version_key, reverse=True)
    requires_python: dict[str, str] = {}
    has_wheel: dict[str, bool] = {}
    for v, files in releases.items():
        if files:
            requires_python[v] = files[0].get("requires_python") or ""
        has_wheel[v] = _any_linux_wheel(files or [])
    return PypiMetadata(
        name=data.get("info", {}).get("name", package),
        versions=versions,
        requires_python=requires_python,
        has_wheel_linux=has_wheel,
    )


def _version_key(v: str) -> tuple:
    """Sort key tolerant of mixed numeric/string tokens (e.g. '1.0rc1').

    Every token becomes (numeric_part, suffix_str). Pure-digit tokens get
    (int, ""); tokens like '0rc1' get (0, 'rc1'); non-numeric tokens like
    'post' get (-1, 'post'). All elements are comparable across versions.
    """
    parts: list[tuple[int, str]] = []
    for tok in re.split(r"[.\-+]", v):
        if not tok:
            continue
        m = re.match(r"(\d+)(.*)", tok)
        if m:
            parts.append((int(m.group(1)), m.group(2)))
        else:
            parts.append((-1, tok))
    return tuple(parts)


def _any_linux_wheel(files: list[dict]) -> bool:
    """True if any file is a Linux/x86_64-compatible wheel."""
    for f in files:
        fn = (f.get("filename") or "").lower()
        if not fn.endswith(".whl"):
            continue
        if "manylinux" in fn or "py3-none-any" in fn or "py2.py3-none-any" in fn:
            return True
        if re.search(r"cp\d+-cp\d+.*linux_x86_64", fn):
            return True
    return False


def wheel_filter(meta: PypiMetadata, version: str, python_version: str) -> bool:
    """True if the (pkg, version) likely installs on the given Python in Linux."""
    if not meta.has_wheel_linux.get(version, False):
        return False
    spec = meta.requires_python.get(version, "")
    if not spec:
        return True
    return _spec_allows(spec, python_version)


def _spec_allows(spec: str, py: str) -> bool:
    """Very small subset of PEP 440 specs: >=3.7, <4, !=3.8, ==3.6.* style."""
    try:
        target = tuple(int(p) for p in py.split(".")[:2])
    except ValueError:
        return True
    for clause in spec.split(","):
        clause = clause.strip()
        m = re.match(r"(>=|<=|>|<|==|!=)\s*(\d+)(?:\.(\d+))?", clause)
        if not m:
            continue
        op = m.group(1)
        bound = (int(m.group(2)), int(m.group(3) or 0))
        if op == ">=" and target < bound: return False
        if op == ">"  and target <= bound: return False
        if op == "<=" and target > bound: return False
        if op == "<"  and target >= bound: return False
        if op == "==" and target != bound: return False
        if op == "!=" and target == bound: return False
    return True


# ---------- Docker error parsing ---------------------------------------

@dataclass
class ErrorKind:
    family: str          # "ImportError" | "NoMatchingDistribution" | "SyntaxError" |
                         # "CouldNotBuildWheels" | "PythonVersionMismatch" | "Other"
    package: str | None  # culprit if identifiable
    detail: str          # one-line evidence excerpt
    is_hard: bool        # HARD vs SOFT for constraint emission


_PATTERNS: list[tuple[str, str, bool]] = [
    (r"ERROR: Could not find a version that satisfies the requirement (\S+)",
     "NoMatchingDistribution", True),
    (r"ERROR: Could not build wheels for (\S+)",
     "CouldNotBuildWheels", True),
    (r"requires Python .* but the running Python is",
     "PythonVersionMismatch", True),
    (r"ImportError: cannot import name '?(\S+?)'?\s+from\s+'?(\S+?)'?",
     "ImportError", False),
    (r"ModuleNotFoundError: No module named '?(\S+?)'?",
     "ImportError", False),
    (r"SyntaxError",
     "SyntaxError", True),
]


def parse_docker_error(log_text: str) -> ErrorKind:
    """Classify a Docker build/run log. Replaces the regex table in
    tools/cgar/src/failure_injector.py with a flat, agent-callable form."""
    for pat, family, is_hard in _PATTERNS:
        m = re.search(pat, log_text)
        if m:
            pkg = m.group(1) if m.groups() else None
            line = next((ln for ln in log_text.splitlines() if m.group(0) in ln),
                        m.group(0))
            return ErrorKind(family=family, package=pkg, detail=line.strip()[:200], is_hard=is_hard)
    return ErrorKind(family="Other", package=None, detail=log_text.splitlines()[-1][:200]
                     if log_text.strip() else "(empty log)", is_hard=False)


# ---------- CSP solver (delegated) -------------------------------------

def solve_csp(candidates: dict[str, list[str]], excluded: set[tuple[str, str]] | None = None,
              max_attempts: int = 50) -> dict[str, str] | None:
    """Wraps tools/cgar/src/constraint_solver.py without rewriting it.

    candidates: {pkg: [v_newest, ..., v_oldest]} — order matters (wheel-first preferred).
    excluded:   set of (pkg, version) tuples already known infeasible.
    Returns {pkg: version} or None.
    """
    excluded = excluded or set()
    # Greedy newest-first respecting excluded. Simple and good enough for the
    # general case; for complex combos defer to the existing CGAR solver via
    # constraint_solver import below.
    try:
        from constraint_solver import ConstraintSolver  # type: ignore
        from constraint_store import ConstraintStore    # type: ignore
        store = ConstraintStore()
        for pkg, ver in excluded:
            try:
                store.add_hard(pkg, ver, python_version="")
            except Exception:  # noqa: BLE001
                pass
        solver = ConstraintSolver(store=store, max_attempts=max_attempts)
        # The CGAR solver expects a candidate graph object; if signatures
        # differ across versions we fall through to the greedy path.
        result = solver.solve(candidates, python_version="")  # type: ignore
        if result:
            return result
    except Exception as e:  # noqa: BLE001
        log.debug("CGAR solver delegation failed (%s); falling back to greedy", e)

    chosen: dict[str, str] = {}
    for pkg, versions in candidates.items():
        for v in versions:
            if (pkg, v) not in excluded:
                chosen[pkg] = v
                break
        else:
            return None
    return chosen


# ---------- Import → package mapping (lightweight) ---------------------

_COMMON_IMPORT_TO_PKG = {
    "cv2": "opencv-python", "sklearn": "scikit-learn", "PIL": "Pillow",
    "yaml": "PyYAML", "bs4": "beautifulsoup4", "skimage": "scikit-image",
    "Crypto": "pycryptodome", "OpenGL": "PyOpenGL", "wx": "wxPython",
    "Image": "Pillow",
}


def imports_to_packages(imports: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for imp in imports:
        pkg = _COMMON_IMPORT_TO_PKG.get(imp, imp)
        if pkg not in seen:
            seen.add(pkg)
            out.append(pkg)
    return out


def extract_imports(source: str) -> list[str]:
    """Static import scan — top-level only. Enough for the negotiator."""
    out: list[str] = []
    for m in re.finditer(r"^\s*(?:from\s+(\S+)\s+import|import\s+([^\s,;]+))", source, re.M):
        name = (m.group(1) or m.group(2) or "").split(".")[0]
        if name and name not in out:
            out.append(name)
    return out
