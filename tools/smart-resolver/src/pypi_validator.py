"""
PyPI Validator

Validates that packages and versions exist on PyPI before attempting installation.
Reduces wasted Docker builds on non-existent packages.
"""

import json
import requests
from typing import Tuple, List, Optional


class PyPIValidator:

    PYPI_BASE_URL = "https://pypi.org/pypi"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.cache = {}
        self.session = requests.Session()

    def package_exists(self, package: str) -> bool:
        """Check if a package exists on PyPI."""
        exists, _, _ = self.validate(package)
        return exists

    def validate(self, package: str, version: Optional[str] = None) -> Tuple[bool, List[str], List[str]]:
        """
        Validate a package (and optionally a version) exists on PyPI.

        Returns:
            (exists, available_versions, alternatives)
        """
        package = package.strip().lower()

        if not package or len(package) < 2:
            return False, [], []

        # Check cache
        if package in self.cache:
            data = self.cache[package]
            if data is None:
                return False, [], self._suggest_alternatives(package)

            available = list(data.get('releases', {}).keys())
            if version:
                return version in available, available[-20:], []
            return True, available[-20:], []

        # Query PyPI
        try:
            url = f"{self.PYPI_BASE_URL}/{package}/json"
            response = self.session.get(url, timeout=self.timeout)

            if response.status_code == 404:
                self.cache[package] = None
                return False, [], self._suggest_alternatives(package)

            if response.status_code == 200:
                data = response.json()
                self.cache[package] = data
                available = list(data.get('releases', {}).keys())

                if version:
                    return version in available, available[-20:], []
                return True, available[-20:], []

        except (requests.RequestException, json.JSONDecodeError):
            # Network error - assume exists to avoid false negatives
            return True, [], []

        return False, [], self._suggest_alternatives(package)

    def get_latest_version(self, package: str) -> Optional[str]:
        """Get the latest version of a package from PyPI."""
        package = package.strip().lower()

        if package in self.cache and self.cache[package]:
            return self.cache[package].get('info', {}).get('version')

        try:
            url = f"{self.PYPI_BASE_URL}/{package}/json"
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                self.cache[package] = data
                return data.get('info', {}).get('version')
        except requests.RequestException:
            pass

        return None

    def _suggest_alternatives(self, package: str) -> List[str]:
        """Suggest alternative package names for common mistakes."""
        alternatives_map = {
            # Common typos and mistakes
            'cv2': ['opencv-python'],
            'opencv': ['opencv-python'],
            'sklearn': ['scikit-learn'],
            'yaml': ['pyyaml'],
            'Image': ['Pillow'],
            'PIL': ['Pillow'],
            'bs4': ['beautifulsoup4'],
            'serial': ['pyserial'],
            'usb': ['pyusb'],
            'wx': ['wxPython'],
            'gi': ['PyGObject'],
            'apt': [],
            'apt_pkg': [],
            'Crypto': ['pycryptodome'],
            'dateutil': ['python-dateutil'],
            'dotenv': ['python-dotenv'],
            'jwt': ['PyJWT'],
            'magic': ['python-magic'],
            'mysql': ['mysqlclient', 'mysql-connector-python'],
            'psycopg2': ['psycopg2-binary'],
            'lxml': ['lxml'],
            'dbus': [],
            'gi.repository': ['PyGObject'],
        }

        pkg_lower = package.lower()
        if pkg_lower in alternatives_map:
            return alternatives_map[pkg_lower]
        if package in alternatives_map:
            return alternatives_map[package]

        return []
