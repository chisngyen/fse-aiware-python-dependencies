"""
Confidence Cascade - Adaptive Resolution Strategy

Novel Contribution: Inspired by Adaptive Graph of Thoughts (Pandey et al., 2025)
and Self-Debugging rubber duck reasoning (Chen et al., 2023).

Key ideas:
1. Decompose dependency resolution into independent sub-problems
2. Use a confidence cascade: Oracle → Template → Heuristic → LLM
3. When LLM is unavailable/slow, use structured heuristic reasoning
4. Adaptive time budgeting per sub-problem

This implements a "No-LLM Fallback" strategy that can still achieve
reasonable accuracy when the LLM server is overloaded or unavailable.
"""

import re
from typing import Dict, List, Optional, Tuple


class ConfidenceCascade:
    """
    Multi-level confidence cascade for package version selection.
    
    Levels (tried in order):
    1. Static compat map (highest confidence, instant)
    2. Co-occurrence template (high confidence, instant)
    3. Heuristic rules (medium confidence, instant)
    4. LLM selection (variable confidence, slow)
    """

    # Heuristic version rules for common packages
    # Format: {package: {python_version_prefix: version}}
    HEURISTIC_VERSIONS = {
        # NumPy
        'numpy': {
            '2.7': '1.16.6', '3.5': '1.18.5', '3.6': '1.19.5',
            '3.7': '1.21.6', '3.8': '1.24.3', '3.9': '1.26.3',
            '3.10': '1.26.3', '3.11': '1.26.3',
        },
        # Pandas
        'pandas': {
            '2.7': '0.24.2', '3.6': '1.1.5', '3.7': '1.3.5',
            '3.8': '2.0.3', '3.9': '2.1.4', '3.10': '2.1.4',
        },
        # Scipy
        'scipy': {
            '2.7': '1.2.3', '3.6': '1.5.4', '3.7': '1.7.3',
            '3.8': '1.10.1', '3.9': '1.11.4',
        },
        # Matplotlib
        'matplotlib': {
            '2.7': '2.2.5', '3.6': '3.3.4', '3.7': '3.5.3',
            '3.8': '3.7.5', '3.9': '3.8.2',
        },
        # Requests
        'requests': {
            '2.7': '2.27.1', '3.6': '2.27.1', '3.7': '2.31.0',
            '3.8': '2.31.0', '3.9': '2.31.0',
        },
        # Flask
        'flask': {
            '2.7': '1.1.4', '3.6': '2.0.3', '3.7': '2.2.5',
            '3.8': '3.0.0',
        },
        # Django
        'django': {
            '2.7': '1.11.29', '3.6': '3.2.25', '3.7': '3.2.25',
            '3.8': '4.2.9',
        },
        # SQLAlchemy
        'sqlalchemy': {
            '2.7': '1.3.24', '3.6': '1.4.51', '3.7': '1.4.51',
            '3.8': '2.0.23',
        },
        # Pillow (PIL)
        'pillow': {
            '2.7': '6.2.2', '3.6': '8.4.0', '3.7': '9.5.0',
            '3.8': '10.1.0',
        },
        # BeautifulSoup
        'beautifulsoup4': {
            '2.7': '4.9.3', '3.6': '4.11.2', '3.7': '4.12.2',
            '3.8': '4.12.2',
        },
        # lxml
        'lxml': {
            '2.7': '4.6.5', '3.6': '4.9.3', '3.7': '4.9.3',
            '3.8': '4.9.3',
        },
        # Scrapy
        'scrapy': {
            '2.7': '1.8.2', '3.6': '2.5.1', '3.7': '2.8.0',
        },
        # Redis
        'redis': {
            '2.7': '3.5.3', '3.6': '4.4.4', '3.7': '4.6.0',
        },
        # Celery
        'celery': {
            '2.7': '4.4.7', '3.6': '5.2.7', '3.7': '5.3.6',
        },
        # Click
        'click': {
            '2.7': '7.1.2', '3.6': '8.0.4', '3.7': '8.1.7',
        },
        # PyYAML
        'pyyaml': {
            '2.7': '5.4.1', '3.6': '6.0', '3.7': '6.0.1',
        },
        # Jinja2
        'jinja2': {
            '2.7': '2.11.3', '3.6': '3.0.3', '3.7': '3.1.2',
        },
        # Six (compatibility)
        'six': {
            '2.7': '1.16.0', '3.6': '1.16.0', '3.7': '1.16.0',
        },
        # Boto3
        'boto3': {
            '2.7': '1.17.112', '3.6': '1.26.165', '3.7': '1.34.14',
        },
        # Boto
        'boto': {
            '2.7': '2.49.0',
        },
        # Paramiko
        'paramiko': {
            '2.7': '2.11.0', '3.6': '3.1.0', '3.7': '3.4.0',
        },
        # Peewee
        'peewee': {
            '2.7': '3.9.6', '3.6': '3.15.4', '3.7': '3.17.0',
        },
        # PyMongo
        'pymongo': {
            '2.7': '3.12.3', '3.6': '4.3.3', '3.7': '4.6.1',
        },
        # NLTK
        'nltk': {
            '2.7': '3.4.5', '3.6': '3.6.7', '3.7': '3.8.1',
        },
        # NetworkX  
        'networkx': {
            '2.7': '2.2', '3.6': '2.6.3', '3.7': '2.8.8',
            '3.8': '3.2.1',
        },
        # Gym
        'gym': {
            '3.6': '0.21.0', '3.7': '0.26.2', '3.8': '0.26.2',
        },
        # H5py
        'h5py': {
            '2.7': '2.10.0', '3.6': '3.1.0', '3.7': '3.7.0',
            '3.8': '3.9.0',
        },
        # Simplejson
        'simplejson': {
            '2.7': '3.17.6', '3.6': '3.19.2', '3.7': '3.19.2',
        },
        # Tornado
        'tornado': {
            '2.7': '5.1.1', '3.6': '6.1', '3.7': '6.3.3',
        },
        # Gevent
        'gevent': {
            '2.7': '21.12.0', '3.6': '21.12.0', '3.7': '23.9.1',
        },
        # Keras
        'keras': {
            '2.7': '2.2.4', '3.6': '2.3.1', '3.7': '2.10.0',
            '3.8': '2.13.1',
        },
        # Theano  
        'theano': {
            '2.7': '1.0.4', '3.6': '1.0.5', '3.7': '1.0.5',
        },
        # PyMC3
        'pymc3': {
            '2.7': '3.4.1', '3.6': '3.11.5', '3.7': '3.11.5',
        },
        # Scikit-learn
        'scikit-learn': {
            '2.7': '0.20.4', '3.6': '0.24.2', '3.7': '1.0.2',
            '3.8': '1.3.2',
        },
        # Cryptography
        'cryptography': {
            '2.7': '3.3.2', '3.6': '3.4.8', '3.7': '41.0.7',
        },
        # PyCryptodome
        'pycryptodome': {
            '2.7': '3.9.9', '3.6': '3.15.0', '3.7': '3.19.0',
        },
        # Twisted
        'twisted': {
            '2.7': '20.3.0', '3.6': '21.7.0', '3.7': '22.10.0',
        },
        # Aiohttp
        'aiohttp': {
            '3.6': '3.8.6', '3.7': '3.9.1', '3.8': '3.9.1',
        },
        # Arrow
        'arrow': {
            '2.7': '0.17.0', '3.6': '1.2.3', '3.7': '1.3.0',
        },
        # Dateutil
        'python-dateutil': {
            '2.7': '2.8.2', '3.6': '2.8.2', '3.7': '2.8.2',
        },
        # PyTZ
        'pytz': {
            '2.7': '2021.3', '3.6': '2023.3.post1', '3.7': '2023.3.post1',
        },
        # Tqdm
        'tqdm': {
            '2.7': '4.64.1', '3.6': '4.66.1', '3.7': '4.66.1',
        },
    }

    def __init__(self):
        pass

    def get_heuristic_version(self, package: str,
                               python_version: str) -> Optional[str]:
        """
        Get version using heuristic rules (no LLM needed).
        Returns None if no heuristic available.
        """
        pkg_lower = package.lower()
        
        if pkg_lower in self.HEURISTIC_VERSIONS:
            versions = self.HEURISTIC_VERSIONS[pkg_lower]
            
            # Exact match
            if python_version in versions:
                return versions[python_version]
            
            # Try major version match
            major = python_version.split('.')[0]
            if major == '2' and '2.7' in versions:
                return versions['2.7']
            
            # Find closest version
            py_parts = python_version.split('.')
            py_num = float(f"{py_parts[0]}.{py_parts[1]}") if len(py_parts) >= 2 else 0
            
            best_ver = None
            best_dist = float('inf')
            for ver_key, ver_val in versions.items():
                key_parts = ver_key.split('.')
                key_num = float(f"{key_parts[0]}.{key_parts[1]}") if len(key_parts) >= 2 else 0
                dist = abs(py_num - key_num)
                if dist < best_dist:
                    best_dist = dist
                    best_ver = ver_val
            
            return best_ver
        
        return None

    def cascade_version_select(self, package: str, python_version: str,
                                compat_map_version: str = None,
                                cooccurrence_version: str = None,
                                template_version: str = None) -> Tuple[str, str]:
        """
        Cascade through version selection methods.
        Returns (version, source) tuple.
        """
        # Level 1: Static compat map (highest priority)
        if compat_map_version:
            return compat_map_version, 'compat_map'
        
        # Level 2: Co-occurrence mining (historical data)
        if cooccurrence_version:
            return cooccurrence_version, 'cooccurrence'
        
        # Level 3: Template match
        if template_version:
            return template_version, 'template'
        
        # Level 4: Heuristic rules
        heuristic = self.get_heuristic_version(package, python_version)
        if heuristic:
            return heuristic, 'heuristic'
        
        # Level 5: No version (will use latest or LLM)
        return '', 'unknown'

    def estimate_unfixable(self, modules: List[str],
                            system_only: set) -> float:
        """
        Estimate the probability that a snippet is unfixable.
        Returns 0.0-1.0 confidence that it CANNOT be fixed.
        
        Used for early termination to save time.
        """
        if not modules:
            return 0.0
        
        system_count = sum(1 for m in modules 
                          if m.lower() in system_only)
        total = len(modules)
        
        if total == 0:
            return 0.0
        
        # If ALL imports are system-only, definitely unfixable
        if system_count == total:
            return 0.95
        
        # If majority are system-only, likely unfixable
        ratio = system_count / total
        return ratio * 0.8

    def smart_python_version_from_imports(self, modules: List[str]) -> Optional[str]:
        """
        Infer Python version from the package ecosystem.
        Some packages only work on specific Python versions.
        """
        modules_lower = {m.lower() for m in modules}
        
        # Python 2 only packages
        py2_only = {'mechanize', 'cookielib', 'htmlparser', 'cstringio',
                    'urlparse', 'httplib', 'basehttpserver', 'simplehttpserver'}
        if modules_lower & py2_only:
            return '2.7'
        
        # Python 3.7+ packages (need typing_extensions, dataclasses, etc.)
        py37_plus = {'dataclasses', 'contextvars'}
        if modules_lower & py37_plus:
            return '3.7'
        
        # Async-heavy → at least 3.6
        async_pkgs = {'aiohttp', 'asyncpg', 'httpx', 'fastapi', 'uvicorn'}
        if modules_lower & async_pkgs:
            return '3.7'
        
        # Modern ML → 3.7+
        modern_ml = {'transformers', 'diffusers', 'accelerate', 'datasets'}
        if modules_lower & modern_ml:
            return '3.8'
        
        return None
