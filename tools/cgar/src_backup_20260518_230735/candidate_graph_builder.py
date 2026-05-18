"""
CandidateGraphBuilder — Stage 2.5

Queries PyPI JSON API to build a candidate version graph for a set of packages.
Each candidate includes its requires_python marker and requires_dist constraints.
Results are cached per session to avoid redundant network calls.
"""

import re
import time
from typing import Dict, List, Optional

import requests
from packaging.specifiers import SpecifierSet
from packaging.version import Version, InvalidVersion


PYPI_JSON_URL = "https://pypi.org/pypi/{package}/json"


class PackageConstraint:
    """A version constraint on a package imposed by another package's requires_dist."""
    def __init__(self, package: str, specifier: str, source: str):
        self.package = package.lower()
        self.specifier = specifier
        self.source = source
        self._spec = SpecifierSet(specifier, prereleases=False)

    def is_satisfied_by(self, version: str) -> bool:
        try:
            return version in self._spec
        except Exception:
            return True  # Unknown specifier → don't prune


class CandidateGraphBuilder:
    """
    Builds a candidate version graph from live PyPI metadata.

    For each package, returns versions compatible with the target Python version,
    sorted newest-first. Caches PyPI responses for the session lifetime.
    """

    def __init__(self, timeout: int = 8):
        self.timeout = timeout
        self._cache: Dict[str, dict] = {}  # package_name → raw PyPI JSON

    def _fetch_pypi(self, package: str) -> Optional[dict]:
        pkg_lower = package.lower()
        if pkg_lower in self._cache:
            return self._cache[pkg_lower]
        try:
            url = PYPI_JSON_URL.format(package=pkg_lower)
            resp = requests.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                self._cache[pkg_lower] = data
                return data
        except Exception:
            pass
        self._cache[pkg_lower] = None
        return None

    def _python_compat(self, requires_python: Optional[str], python_version: str) -> bool:
        """Check if a package release supports the given Python version."""
        if not requires_python:
            return True
        try:
            spec = SpecifierSet(requires_python)
            # Normalize python_version to a full version string
            pv = python_version if python_version.count('.') >= 1 else python_version + '.0'
            return pv in spec
        except Exception:
            return True

    def _has_linux_wheel(self, release_files: list, python_version: str) -> bool:
        """
        Check if a release has a pre-built wheel usable on linux/x86_64
        for the given Python version. Falls back to True if only sdist exists
        (pip may still build it) but returns False if the release is empty.
        """
        if not release_files:
            return False

        py_tag = "cp" + python_version.replace(".", "")   # e.g. cp36, cp38
        has_wheel = False
        has_sdist = False

        for f in release_files:
            filename = f.get("filename", "")
            if filename.endswith(".whl"):
                has_wheel = True
                # Accept if: any=any, linux x86_64, or manylinux, or pure python
                fn = filename.lower()
                if (
                    "-none-any.whl" in fn               # pure python wheel
                    or "manylinux" in fn                 # manylinux (most common)
                    or "linux_x86_64" in fn
                    or f"-{py_tag}-" in fn               # version-specific
                    or "-py3-" in fn
                    or "-py2.py3-" in fn
                ):
                    return True
            elif filename.endswith((".tar.gz", ".zip")):
                has_sdist = True

        # Has wheel(s) but none matched → likely Windows/macOS only
        if has_wheel:
            return False
        # Only sdist → pip will try to build from source; allow but mark
        return has_sdist

    def get_candidates(self, package: str, python_version: str,
                       max_candidates: int = 8) -> List[Dict]:
        """
        Return candidate versions for `package` on `python_version`.

        Each candidate: {'version': str, 'requires_python': str, 'requires_dist': list,
                         'has_wheel': bool}
        Sorted by: wheel-available first, then newest-first.
        Returns [] if package not found on PyPI.
        """
        data = self._fetch_pypi(package)
        if not data:
            return []

        releases = data.get('releases', {})
        candidates = []

        for ver_str, release_files in releases.items():
            # Skip pre-releases and post-releases
            try:
                v = Version(ver_str)
                if v.is_prerelease or v.is_postrelease or v.is_devrelease:
                    continue
            except InvalidVersion:
                continue

            # Check requires_python from release file metadata (most accurate)
            rp = None
            for f in release_files:
                if f.get('requires_python'):
                    rp = f['requires_python']
                    break
            # Fallback to info-level requires_python
            if rp is None:
                rp = data.get('info', {}).get('requires_python')

            if not self._python_compat(rp, python_version):
                continue

            has_wheel = self._has_linux_wheel(release_files, python_version)

            candidates.append({
                'version': ver_str,
                'requires_python': rp,
                'requires_dist': [],
                'has_wheel': has_wheel,
            })

        # Sort: wheel-available first, then newest-first within each group
        def sort_key(c):
            try:
                v = Version(c['version'])
                return (0 if c['has_wheel'] else 1, -v.major, -v.minor, -v.micro)
            except Exception:
                return (1, 0, 0, 0)
        candidates.sort(key=sort_key)

        return candidates[:max_candidates]

    def build_graph(self, packages: List[str], python_version: str) -> Dict[str, List[Dict]]:
        """
        Build candidate graph for all packages.
        Returns {package_name: [candidates]} dict.
        """
        graph = {}
        for pkg in packages:
            graph[pkg] = self.get_candidates(pkg, python_version)
        return graph
