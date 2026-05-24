"""Single canonical Docker build+run for every method.

Method files MUST go through ``build_and_run`` to execute a snippet —
they may not shell out to docker themselves. This guarantees every
method runs under identical conditions.

G3 baseline parity with MEMRES (FSE'26)
---------------------------------------
This harness is intentionally aligned with MEMRES's `_build_and_test`
(see ``tools/memres/src/enhanced_resolver.py:1456+``) so that m11-m14's
Docker rescue attempts run under conditions equivalent to MEMRES's
own pipeline. Specifically matched:
- Base image: ``python:<X.Y>`` (full image, not -slim) per MEMRES's
  DOCKER_PYTHON_IMAGES map. Slim was a deviation; reverted.
- SYSTEM_APT_DEPS injection (DockerizeMe ICSE 2019 pattern) for
  C-extension packages.
- Debian archive sed-fix for Py2.7 stretch images (sources archived).
- ``RUN pip install --upgrade pip`` before package install.
- ``--trusted-host pypi.python.org --default-timeout=100`` pip flags.
- ``docker run --rm`` (no ``--network=none``; runtime network ON).
- Build/run timeouts default 180s / 60s.

Differences explicitly NOT matched (with rationale):
- ``--privileged`` for DinD: not needed since we orchestrate on host.
- MEMRES's PY27_VERSION_CASCADE: that's a *resolver* feature; we
  consume pin specs from method file.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from .tools_lib import ErrorKind, parse_docker_error

log = logging.getLogger(__name__)


# ---- MEMRES SYSTEM_APT_DEPS (verbatim from enhanced_resolver.py:65) ---------

SYSTEM_APT_DEPS: dict[str, list[str]] = {
    # Data/science
    "lxml": ["libxml2-dev", "libxslt1-dev"],
    "gdal": ["libgdal-dev", "gdal-bin"],
    "fiona": ["libgdal-dev", "gdal-bin"],
    "rasterio": ["libgdal-dev", "gdal-bin"],
    "pyproj": ["libproj-dev", "proj-data"],
    "shapely": ["libgeos-dev"],
    "cartopy": ["libgeos-dev", "libproj-dev"],
    # Image
    "pillow": ["libjpeg-dev", "zlib1g-dev", "libfreetype6-dev"],
    "opencv-python": ["libgl1-mesa-glx", "libglib2.0-0"],
    "opencv-contrib-python": ["libgl1-mesa-glx", "libglib2.0-0"],
    # Audio
    "pyaudio": ["portaudio19-dev"],
    "soundfile": ["libsndfile1"],
    "pydub": ["ffmpeg"],
    # Scientific (C-ext)
    "scipy": ["gfortran", "libopenblas-dev", "liblapack-dev"],
    "numpy": ["gfortran", "libopenblas-dev"],
    "scikit-learn": ["gfortran", "libopenblas-dev"],
    # Build essentials
    "dlib": ["cmake", "build-essential"],
    "cmake": ["cmake"],
    "cython": ["build-essential"],
    # Crypto
    "cryptography": ["libffi-dev", "libssl-dev"],
    "pynacl": ["libffi-dev", "libsodium-dev"],
    "m2crypto": ["libssl-dev", "swig"],
    # DB
    "psycopg2": ["libpq-dev"],
    "psycopg2-binary": ["libpq-dev"],
    "mysqlclient": ["default-libmysqlclient-dev", "build-essential"],
    "mysql-python": ["default-libmysqlclient-dev", "build-essential"],
    # XML/HTML
    "xmlsec": ["libxmlsec1-dev", "libxmlsec1-openssl"],
    # Compression
    "python-snappy": ["libsnappy-dev"],
    # Network
    "pycurl": ["libcurl4-openssl-dev"],
    # System interface
    "python-prctl": ["libcap-dev"],
    # Graphics
    "pygraphviz": ["graphviz", "libgraphviz-dev"],
    "cairosvg": ["libcairo2-dev"],
    "cairocffi": ["libcairo2-dev"],
    # Video
    "av": ["libavformat-dev", "libavcodec-dev", "libavutil-dev", "libswscale-dev"],
    # HDF5
    "h5py": ["libhdf5-dev"],
    "tables": ["libhdf5-dev"],
    # ZMQ
    "pyzmq": ["libzmq3-dev"],
    # Build-essential bundle (added for Py2 C-ext builds)
    "_build_essential": ["build-essential", "gcc", "g++"],
}

DOCKER_PYTHON_IMAGES = {
    "2.7": "python:2.7",
    "3.4": "python:3.4",
    "3.5": "python:3.5",
    "3.6": "python:3.6",
    "3.7": "python:3.7",
    "3.8": "python:3.8",
    "3.9": "python:3.9",
    "3.10": "python:3.10",
    "3.11": "python:3.11",
}


@dataclass
class BuildResult:
    passed: bool
    python_version: str
    packages: list[str]
    error_kind: ErrorKind
    log_text: str
    duration_sec: float
    image_tag: str = ""


def _parse_pkg(spec: str) -> tuple[str, str]:
    """Return (name, version) from 'pkg==1.2.3' or just 'pkg' (version='')."""
    if "==" in spec:
        name, ver = spec.split("==", 1)
        return name.strip(), ver.strip()
    # Strip range operators
    name = spec.split("<")[0].split(">")[0].split("~")[0].strip()
    return name, ""


def _gen_dockerfile(python_version: str, packages: list[str],
                    apt_packages: list[str] | None = None) -> str:
    """Match MEMRES `_build_and_test` Dockerfile generation."""
    image = DOCKER_PYTHON_IMAGES.get(python_version, f"python:{python_version}")
    lines = [f"FROM {image}", "WORKDIR /app"]

    # === SYSTEM_APT_DEPS auto-injection (DockerizeMe ICSE 2019 pattern) ===
    auto_apt: set[str] = set()
    pkg_lowers = [_parse_pkg(p)[0].lower() for p in packages]
    for name in pkg_lowers:
        if name in SYSTEM_APT_DEPS:
            auto_apt.update(SYSTEM_APT_DEPS[name])
    # For Py2.7 with any C-extension package, always add build-essential
    if python_version.startswith("2") and any(n in SYSTEM_APT_DEPS for n in pkg_lowers):
        auto_apt.update(SYSTEM_APT_DEPS["_build_essential"])
    # Merge with caller-provided apt_packages
    if apt_packages:
        auto_apt.update(apt_packages)

    if auto_apt:
        apt_list = " ".join(sorted(auto_apt))
        # Debian archive sed-fix for old (stretch/jessie) images
        lines.append(
            'RUN sed -i -e "s|deb.debian.org|archive.debian.org|g" '
            '-e "s|security.debian.org|archive.debian.org|g" '
            '-e "/stretch-updates/d" '
            "/etc/apt/sources.list 2>/dev/null || true"
        )
        lines.append(
            f"RUN apt-get update && apt-get install -y --no-install-recommends "
            f"{apt_list} && rm -rf /var/lib/apt/lists/* || true"
        )

    # === pip upgrade first (MEMRES does this) ===
    lines.append('RUN ["pip","install","--upgrade","pip"]')

    # === Batch pip install (single command, lets pip resolve transitives) ===
    if packages:
        pip_cmd = ["pip", "install", "--trusted-host", "pypi.python.org",
                   "--default-timeout=100", "--no-cache-dir"]
        has_torch_cpu = False
        for spec in packages:
            name, ver = _parse_pkg(spec)
            if not name:
                continue
            # Pass spec through (supports pkg==ver, pkg<ver, pkg, etc.)
            pip_cmd.append(spec if (ver or any(c in spec for c in "<>~!=")) else name)
            if name.lower() in ("torch", "torchvision", "torchaudio") and "+cpu" in ver:
                has_torch_cpu = True
        if has_torch_cpu:
            pip_cmd.extend(["--extra-index-url", "https://download.pytorch.org/whl/cpu"])
        lines.append(f"RUN {json.dumps(pip_cmd)}")

    lines += [
        "COPY snippet.py /app/snippet.py",
        'CMD ["python", "/app/snippet.py"]',
    ]
    return "\n".join(lines) + "\n"


def _run_cmd(cmd: list[str], timeout: int) -> tuple[int, str]:
    # encoding="utf-8", errors="replace" — Docker pip logs often contain
    # non-ASCII bytes (progress bars, mojibake from upstream package metadata)
    # and the Windows default cp1252 codec crashes on them.
    try:
        p = subprocess.run(
            cmd, capture_output=True, timeout=timeout,
            encoding="utf-8", errors="replace",
        )
        return p.returncode, ((p.stdout or "") + (p.stderr or ""))
    except subprocess.TimeoutExpired as e:
        out = e.stdout.decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        err = e.stderr.decode("utf-8", "replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        return -1, f"[timeout after {timeout}s] {err}{out}"
    except FileNotFoundError:
        return -1, "docker CLI not found"


def build_and_run(
    snippet_source: str,
    python_version: str,
    packages: list[str],
    apt_packages: list[str] | None = None,
    build_timeout: int = 180,
    run_timeout: int = 60,
    keep_image: bool = False,
) -> BuildResult:
    """Build a container around the snippet and run it. Returns BuildResult."""
    apt_packages = apt_packages or []
    t0 = time.time()
    tag = f"icse27/run:{uuid.uuid4().hex[:12]}"

    tmp = Path(tempfile.mkdtemp(prefix="icse27_"))
    try:
        (tmp / "snippet.py").write_text(snippet_source, encoding="utf-8", errors="replace")
        (tmp / "Dockerfile").write_text(
            _gen_dockerfile(python_version, packages, apt_packages), encoding="utf-8"
        )

        rc, build_log = _run_cmd(
            ["docker", "build", "-t", tag, "-f", str(tmp / "Dockerfile"), str(tmp)],
            timeout=build_timeout,
        )
        if rc != 0:
            err = parse_docker_error(build_log)
            return BuildResult(
                passed=False, python_version=python_version, packages=packages,
                error_kind=err, log_text=build_log[-4000:],
                duration_sec=time.time() - t0, image_tag=tag,
            )

        rc, run_log = _run_cmd(
            # G3 baseline parity: match MEMRES (FSE'26) docker run flags exactly.
            # MEMRES does NOT block network at run time (see
            # tools/memres/src/enhanced_resolver.py docker run command).
            # Some snippets need network at runtime (e.g. requests.get); blocking
            # would under-report pass rates relative to MEMRES baseline.
            ["docker", "run", "--rm", tag],
            timeout=run_timeout,
        )
        full_log = (build_log + "\n----- RUN -----\n" + run_log)
        if rc == 0:
            return BuildResult(
                passed=True, python_version=python_version, packages=packages,
                error_kind=ErrorKind(family="Pass", package=None, detail="", is_hard=False),
                log_text=full_log[-4000:],
                duration_sec=time.time() - t0, image_tag=tag,
            )
        err = parse_docker_error(run_log)
        return BuildResult(
            passed=False, python_version=python_version, packages=packages,
            error_kind=err, log_text=full_log[-4000:],
            duration_sec=time.time() - t0, image_tag=tag,
        )
    finally:
        if not keep_image:
            _run_cmd(["docker", "rmi", "-f", tag], timeout=30)
        try:
            shutil.rmtree(tmp, ignore_errors=True)
        except OSError:
            pass


def docker_available() -> bool:
    """Quick smoke check used by the entry-point at start-up."""
    rc, _ = _run_cmd(["docker", "version", "--format", "{{.Server.Version}}"], timeout=10)
    return rc == 0
