"""
Version Resolver

Smart version selection based on Python version compatibility.
Instead of always using 'latest', pick versions that actually work
with the target Python version.
"""

from typing import Optional, Dict, List


class VersionResolver:

    # Package -> {python_version: compatible_pip_version}
    # These are known-good version ranges for major packages
    COMPAT_MAP = {
        # Web frameworks
        'django': {
            '2.7': '1.11.29',
            '3.5': '2.2.28',
            '3.6': '3.2.25',
            '3.7': '3.2.25',
            '3.8': '',  # latest works
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'flask': {
            '2.7': '1.1.4',
            '3.5': '1.1.4',
            '3.6': '2.0.3',
            '3.7': '2.2.5',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'requests': {
            '2.7': '2.27.1',
            '3.5': '2.25.1',
            '3.6': '2.27.1',
            '3.7': '',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        # Data science
        'numpy': {
            '2.7': '1.16.6',
            '3.5': '1.18.5',
            '3.6': '1.19.5',
            '3.7': '1.21.6',
            '3.8': '1.24.4',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'pandas': {
            '2.7': '0.24.2',
            '3.5': '0.25.3',
            '3.6': '1.1.5',
            '3.7': '1.3.5',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'scipy': {
            '2.7': '1.2.3',
            '3.5': '1.4.1',
            '3.6': '1.5.4',
            '3.7': '1.7.3',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'matplotlib': {
            '2.7': '2.2.5',
            '3.5': '3.0.3',
            '3.6': '3.3.4',
            '3.7': '3.5.3',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'scikit-learn': {
            '2.7': '0.20.4',
            '3.5': '0.22.2',
            '3.6': '0.24.2',
            '3.7': '1.0.2',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'tensorflow': {
            '2.7': '1.15.5',
            '3.5': '1.15.5',
            '3.6': '2.6.5',
            '3.7': '2.10.1',
            '3.8': '2.13.1',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        # Database
        'sqlalchemy': {
            '2.7': '1.3.24',
            '3.5': '1.3.24',
            '3.6': '1.4.51',
            '3.7': '',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'redis': {
            '2.7': '3.5.3',
            '3.5': '3.5.3',
            '3.6': '4.5.5',
            '3.7': '',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'pymongo': {
            '2.7': '3.12.3',
            '3.5': '3.12.3',
            '3.6': '3.13.0',
            '3.7': '',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'psycopg2-binary': {
            '2.7': '2.8.6',
            '3.5': '2.8.6',
            '3.6': '2.9.9',
            '3.7': '',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        # Web scraping
        'scrapy': {
            '2.7': '1.8.2',
            '3.5': '2.5.1',
            '3.6': '2.6.3',
            '3.7': '',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'beautifulsoup4': {
            '2.7': '4.9.3',
            '3.5': '4.9.3',
            '3.6': '',
            '3.7': '',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        # Image processing
        'Pillow': {
            '2.7': '6.2.2',
            '3.5': '7.2.0',
            '3.6': '8.4.0',
            '3.7': '9.5.0',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'opencv-python': {
            '2.7': '4.2.0.32',
            '3.5': '4.2.0.32',
            '3.6': '4.5.5.64',
            '3.7': '4.7.0.72',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        # Utilities
        'six': {
            '2.7': '',
            '3.5': '',
            '3.6': '',
            '3.7': '',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'pyyaml': {
            '2.7': '5.4.1',
            '3.5': '5.4.1',
            '3.6': '',
            '3.7': '',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'python-dateutil': {
            '2.7': '',
            '3.5': '',
            '3.6': '',
            '3.7': '',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'cryptography': {
            '2.7': '3.3.2',
            '3.5': '3.3.2',
            '3.6': '3.4.8',
            '3.7': '41.0.7',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'lxml': {
            '2.7': '4.6.5',
            '3.5': '4.6.5',
            '3.6': '4.9.4',
            '3.7': '',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'boto3': {
            '2.7': '1.17.112',
            '3.5': '1.17.112',
            '3.6': '1.26.165',
            '3.7': '',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'celery': {
            '2.7': '4.4.7',
            '3.5': '4.4.7',
            '3.6': '5.2.7',
            '3.7': '',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'paramiko': {
            '2.7': '2.12.0',
            '3.5': '2.12.0',
            '3.6': '3.4.1',
            '3.7': '',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'jinja2': {
            '2.7': '2.11.3',
            '3.5': '2.11.3',
            '3.6': '3.0.3',
            '3.7': '',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'click': {
            '2.7': '7.1.2',
            '3.5': '7.1.2',
            '3.6': '8.0.4',
            '3.7': '',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'python-memcached': {
            '2.7': '',
            '3.5': '',
            '3.6': '',
            '3.7': '',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'tweepy': {
            '2.7': '3.10.0',
            '3.5': '3.10.0',
            '3.6': '4.14.0',
            '3.7': '',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'gevent': {
            '2.7': '21.12.0',
            '3.5': '21.12.0',
            '3.6': '21.12.0',
            '3.7': '',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'pyzmq': {
            '2.7': '22.3.0',
            '3.5': '22.3.0',
            '3.6': '25.1.2',
            '3.7': '',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'tornado': {
            '2.7': '5.1.1',
            '3.5': '6.1',
            '3.6': '6.1',
            '3.7': '',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'twisted': {
            '2.7': '20.3.0',
            '3.5': '21.2.0',
            '3.6': '22.10.0',
            '3.7': '',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'pycryptodome': {
            '2.7': '3.15.0',
            '3.5': '3.15.0',
            '3.6': '3.19.1',
            '3.7': '',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'PyJWT': {
            '2.7': '1.7.1',
            '3.5': '1.7.1',
            '3.6': '2.8.0',
            '3.7': '',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'pyserial': {
            '2.7': '',
            '3.5': '',
            '3.6': '',
            '3.7': '',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'gitpython': {
            '2.7': '2.1.15',
            '3.5': '3.1.18',
            '3.6': '3.1.31',
            '3.7': '',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'fabric': {
            '2.7': '1.14.1',
            '3.5': '2.7.1',
            '3.6': '3.2.2',
            '3.7': '',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'python-dotenv': {
            '2.7': '0.19.2',
            '3.5': '0.19.2',
            '3.6': '0.21.1',
            '3.7': '',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
        'attrs': {
            '2.7': '21.4.0',
            '3.5': '21.4.0',
            '3.6': '22.2.0',
            '3.7': '',
            '3.8': '',
            '3.9': '',
            '3.10': '',
            '3.11': '',
        },
    }

    def get_compatible_version(self, package: str, python_version: str) -> str:
        """
        Get a compatible version of a package for the given Python version.

        Returns:
            Version string like '1.4.51', or '' for latest
        """
        pkg_lower = package.lower()

        # Check direct match
        if package in self.COMPAT_MAP:
            versions = self.COMPAT_MAP[package]
        elif pkg_lower in {k.lower(): k for k in self.COMPAT_MAP}:
            # Case-insensitive lookup
            for k, v in self.COMPAT_MAP.items():
                if k.lower() == pkg_lower:
                    versions = v
                    break
            else:
                return ''
        else:
            # Unknown package: use latest for Python 3.8+, be conservative for older
            return ''

        # Find best version for this Python
        if python_version in versions:
            return versions[python_version]

        # Try to find closest Python version
        major_minor = python_version.split('.')
        if len(major_minor) == 2:
            major = major_minor[0]
            minor = int(major_minor[1])
            # Try nearby versions
            for offset in [0, -1, 1, -2, 2]:
                try_ver = f"{major}.{minor + offset}"
                if try_ver in versions:
                    return versions[try_ver]

        return ''

    # Alias for backward compatibility
    get_compat_version = get_compatible_version

    def resolve_versions(self, packages: Dict[str, str],
                        python_version: str) -> Dict[str, str]:
        """
        Resolve compatible versions for all packages.

        Args:
            packages: {package_name: current_version}
            python_version: target Python version

        Returns:
            Updated packages dict with compatible versions
        """
        resolved = {}
        for pkg, current_ver in packages.items():
            compat_ver = self.get_compatible_version(pkg, python_version)
            if compat_ver:
                resolved[pkg] = compat_ver
            elif current_ver and current_ver != 'latest':
                resolved[pkg] = current_ver
            else:
                resolved[pkg] = ''  # Use latest
        return resolved
