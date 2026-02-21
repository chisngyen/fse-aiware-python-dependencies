"""
PyPI RAG (Retrieval-Augmented Generation)

Queries PyPI for available module versions and provides them as context
for LLM version selection. This is the key differentiator from naive LLM approaches.

Inspired by PLLM's approach but enhanced with:
- Smarter date-based filtering
- Version compatibility pre-checking
- Caching to reduce API calls
"""

import json
import os
import re
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple


# Python version release/EOL dates for filtering
PYTHON_VERSION_DATES = {
    '2.7': {'release': '2010-07-03', 'eol': '2020-01-01'},
    '3.3': {'release': '2012-09-29', 'eol': '2017-09-29'},
    '3.4': {'release': '2014-03-15', 'eol': '2019-03-18'},
    '3.5': {'release': '2015-09-12', 'eol': '2020-09-13'},
    '3.6': {'release': '2016-12-22', 'eol': '2021-12-23'},
    '3.7': {'release': '2018-06-26', 'eol': '2023-06-27'},
    '3.8': {'release': '2019-10-14', 'eol': '2024-10-14'},
    '3.9': {'release': '2020-10-05', 'eol': '2025-10-05'},
    '3.10': {'release': '2021-10-04', 'eol': '2026-10-04'},
    '3.11': {'release': '2022-10-24', 'eol': '2027-10-24'},
    '3.12': {'release': '2023-10-02', 'eol': '2028-10-02'},
}


class PyPIRAG:
    """Query PyPI for module version lists to feed as context to LLM."""

    def __init__(self, cache_dir: str = '/tmp/pypi_cache', logging: bool = True):
        self.cache_dir = cache_dir
        self.logging = logging
        self.session = requests.Session()
        self.session.headers.update({'Accept': 'application/json'})
        self._memory_cache = {}  # In-memory cache for this session
        os.makedirs(cache_dir, exist_ok=True)

    def get_module_versions(self, module_name: str, python_version: str,
                            max_versions: int = 50) -> str:
        """
        Get available versions for a module, filtered by Python version compatibility.
        Returns a comma-separated string of versions (for LLM context).
        """
        cache_key = f"{module_name}_{python_version}"

        # Check memory cache
        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key]

        # Check file cache
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.txt")
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                versions_str = f.read().strip()
            if versions_str:
                self._memory_cache[cache_key] = versions_str
                return versions_str

        # Query PyPI
        versions = self._query_pypi_versions(module_name, python_version)

        if not versions:
            return ''

        # Sort versions
        versions.sort(key=self._version_sort_key)

        # Limit to last N versions (most relevant)
        if len(versions) > max_versions:
            versions = versions[-max_versions:]

        versions_str = ', '.join(versions)

        # Save to cache
        self._memory_cache[cache_key] = versions_str
        try:
            with open(cache_file, 'w') as f:
                f.write(versions_str)
        except Exception:
            pass

        return versions_str

    def _query_pypi_versions(self, module_name: str,
                              python_version: str) -> List[str]:
        """Query PyPI JSON API for available versions."""
        try:
            url = f"https://pypi.org/pypi/{module_name}/json"
            response = self.session.get(url, timeout=15)

            if response.status_code != 200:
                if self.logging:
                    print(f"  PyPI: {module_name} not found (HTTP {response.status_code})")
                return []

            data = response.json()
            releases = data.get('releases', {})

            if not releases:
                return []

            # Get date range for Python version
            start_date, end_date = self._get_date_range(python_version)

            compatible_versions = []
            all_versions = []

            for version, release_info in releases.items():
                if not release_info:
                    continue

                # Skip yanked releases
                if all(r.get('yanked', False) for r in release_info):
                    continue

                # Skip pre-release / dev versions for cleaner results
                if self._is_prerelease(version):
                    continue

                all_versions.append(version)

                # Check date compatibility
                upload_date = None
                for r in release_info:
                    if r.get('upload_time'):
                        try:
                            upload_date = datetime.strptime(
                                r['upload_time'].split('T')[0], '%Y-%m-%d'
                            ).date()
                            break
                        except (ValueError, IndexError):
                            continue

                if upload_date:
                    # Check if version was released in a compatible timeframe
                    if start_date and end_date:
                        if start_date <= upload_date <= end_date:
                            compatible_versions.append(version)
                            continue

                # Check python_requires compatibility
                for r in release_info:
                    py_req = r.get('requires_python', '')
                    if py_req:
                        if self._check_python_requires(py_req, python_version):
                            compatible_versions.append(version)
                            break
                    else:
                        # No python requirement specified — likely compatible
                        compatible_versions.append(version)
                        break

            # If we have compatible versions, use them; otherwise fall back to all
            if compatible_versions:
                return list(set(compatible_versions))
            elif all_versions:
                # Return all versions but log warning
                if self.logging:
                    print(f"  PyPI: {module_name} - no date-filtered versions, using all {len(all_versions)}")
                return all_versions

            return []

        except (requests.RequestException, json.JSONDecodeError) as e:
            if self.logging:
                print(f"  PyPI query failed for {module_name}: {e}")
            return []

    def _get_date_range(self, python_version: str) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Get the relevant date range for a Python version."""
        if python_version not in PYTHON_VERSION_DATES:
            return None, None

        info = PYTHON_VERSION_DATES[python_version]
        try:
            release = datetime.strptime(info['release'], '%Y-%m-%d').date()
            eol = datetime.strptime(info['eol'], '%Y-%m-%d').date()
            # Extend range slightly: packages released 1 year before Python
            # release are often compatible, and packages until EOL
            from datetime import timedelta
            start = release - timedelta(days=365)
            end = eol + timedelta(days=180)
            return start, end
        except (ValueError, KeyError):
            return None, None

    def _check_python_requires(self, requires_python: str,
                                 python_version: str) -> bool:
        """Check if a python_requires spec is compatible with our version."""
        if not requires_python:
            return True

        try:
            major, minor = python_version.split('.')
            ver_tuple = (int(major), int(minor))

            # Simple checks for common patterns
            if f'>={major}.{minor}' in requires_python:
                return True
            if f'=={major}.{minor}' in requires_python:
                return True
            if f'>={major}' in requires_python and f'<{major}' not in requires_python:
                return True

            # Check exclusion patterns
            if f'!={major}.{minor}' in requires_python:
                return False
            if f'<{major}.{minor}' in requires_python:
                return False

            # For Python 2, check specific patterns
            if python_version.startswith('2'):
                if '>=3' in requires_python and '>=2' not in requires_python:
                    return False  # Python 3 only
                return True

            return True  # Default to compatible
        except (ValueError, AttributeError):
            return True

    def _is_prerelease(self, version: str) -> bool:
        """Check if a version string looks like a pre-release."""
        version_lower = version.lower()
        # Allow rc and beta but not dev
        if '.dev' in version_lower or 'dev' == version_lower:
            return True
        if 'alpha' in version_lower or '.a' in version_lower:
            return True
        return False

    def _version_sort_key(self, version: str) -> List:
        """Create a sortable key from a version string."""
        parts = []
        for part in re.split(r'[.\-]', version):
            try:
                parts.append((0, int(part)))
            except ValueError:
                parts.append((1, part))
        return parts

    def get_versions_excluding(self, module_name: str, python_version: str,
                                exclude: List[str] = None) -> str:
        """
        Get available versions, excluding previously tried ones.
        Returns comma-separated string for LLM context.
        """
        all_versions = self.get_module_versions(module_name, python_version)
        if not all_versions:
            return ''

        if not exclude:
            return all_versions

        versions_list = [v.strip() for v in all_versions.split(',')]
        filtered = [v for v in versions_list if v not in exclude]
        return ', '.join(filtered)

    def validate_module_exists(self, module_name: str) -> bool:
        """Quick check if a module exists on PyPI."""
        try:
            url = f"https://pypi.org/pypi/{module_name}/json"
            response = self.session.get(url, timeout=10)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def get_latest_version(self, module_name: str) -> Optional[str]:
        """Get the absolute latest version from PyPI."""
        try:
            url = f"https://pypi.org/pypi/{module_name}/json"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('info', {}).get('version')
        except (requests.RequestException, json.JSONDecodeError):
            pass
        return None
