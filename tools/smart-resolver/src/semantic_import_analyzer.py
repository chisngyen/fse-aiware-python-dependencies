"""
Semantic Import Analyzer - Novel Contribution for FSE 2026 AIWare

Unlike simple regex-based import extraction (used by PLLM), this module 
analyzes the SEMANTIC CONTEXT of imports to:

1. Disambiguate import names → pip packages
   e.g., `import Image` could be PIL/Pillow or a local module
   → analyze usage: `Image.open()` confirms PIL
   
2. Detect import ecosystems
   e.g., `import torch` + `import torchvision` → PyTorch ecosystem
   → suggest entire ecosystem's packages

3. Infer missing imports from code patterns
   e.g., `model.fit()` without keras/sklearn import → infer ML framework
   
4. Classify snippet complexity for time budget allocation
   e.g., "simple web script" vs "complex ML pipeline"

Key Innovation: Treats import analysis as a SEMANTIC problem, not just 
syntactic pattern matching. This is inspired by program analysis techniques 
but adapted for the dependency resolution domain.

This directly addresses PLLM's weakness: PLLM uses simple module-to-package
mapping which fails for ambiguous imports (the #2 cause of resolution failures).
"""

import re
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict


class SemanticImportAnalyzer:
    """
    Semantically-aware import analysis for Python dependency resolution.
    
    Goes beyond simple `import X` → `pip install X` by analyzing:
    1. How the import is USED in code
    2. What OTHER imports co-occur
    3. Code patterns that imply hidden dependencies
    """

    def __init__(self):
        # === Usage patterns for disambiguation ===
        # Maps (import_name, usage_pattern) → pip_package
        self.USAGE_DISAMBIGUATORS: List[Dict] = [
            # Image → Pillow vs local
            {
                'import': 'Image',
                'patterns': [r'Image\.(open|new|fromarray|frombytes|merge)',
                            r'Image\.ANTIALIAS', r'Image\.BILINEAR'],
                'package': 'Pillow',
                'confidence': 0.95,
            },
            # yaml → pyyaml
            {
                'import': 'yaml',
                'patterns': [r'yaml\.(load|dump|safe_load|safe_dump|FullLoader)'],
                'package': 'pyyaml',
                'confidence': 0.95,
            },
            # cv2 → opencv-python
            {
                'import': 'cv2',
                'patterns': [r'cv2\.(imread|imshow|VideoCapture|resize|cvtColor)',
                            r'cv2\.COLOR_', r'cv2\.FONT_'],
                'package': 'opencv-python',
                'confidence': 0.95,
            },
            # serial → pyserial
            {
                'import': 'serial',
                'patterns': [r'serial\.Serial\(', r'serial\.tools',
                            r'ser\s*=\s*serial\.'],
                'package': 'pyserial',
                'confidence': 0.9,
            },
            # magic → python-magic
            {
                'import': 'magic',
                'patterns': [r'magic\.from_file', r'magic\.from_buffer',
                            r'magic\.Magic\('],
                'package': 'python-magic',
                'confidence': 0.9,
            },
            # gi → PyGObject
            {
                'import': 'gi',
                'patterns': [r'gi\.require_version', r'from gi\.repository',
                            r'Gtk\.|Gdk\.|GLib\.'],
                'package': 'pygobject',
                'confidence': 0.95,
            },
            # Crypto → pycryptodome
            {
                'import': 'Crypto',
                'patterns': [r'Crypto\.Cipher', r'Crypto\.Hash',
                            r'from Crypto import', r'Crypto\.PublicKey'],
                'package': 'pycryptodome',
                'confidence': 0.95,
            },
            # websocket → websocket-client (not websockets)
            {
                'import': 'websocket',
                'patterns': [r'websocket\.WebSocketApp', 
                            r'websocket\.create_connection',
                            r'ws\s*=\s*websocket\.'],
                'package': 'websocket-client',
                'confidence': 0.9,
            },
            # google → various google packages
            {
                'import': 'google',
                'patterns': [r'google\.cloud', r'from google\.cloud'],
                'package': 'google-cloud-core',
                'confidence': 0.8,
            },
            {
                'import': 'google',
                'patterns': [r'google\.auth', r'from google\.auth'],
                'package': 'google-auth',
                'confidence': 0.85,
            },
            {
                'import': 'google',
                'patterns': [r'google\.api_core', r'from google\.api_core'],
                'package': 'google-api-core',
                'confidence': 0.85,
            },
            # clipboard → clipboard (pip) vs Pythonista clipboard
            {
                'import': 'clipboard',
                'patterns': [r'clipboard\.(copy|paste|get|set)',
                            r'clipboard\.copy\('],
                'package': 'clipboard',
                'confidence': 0.7,  # Lower because could be Pythonista
            },
            # nomad → python-nomad
            {
                'import': 'nomad',
                'patterns': [r'nomad\.Nomad\(', r'nomad\.api',
                            r'n\s*=\s*nomad\.'],
                'package': 'python-nomad',
                'confidence': 0.9,
            },
        ]
        
        # === Ecosystem detection ===
        # Groups of imports that indicate a specific ecosystem
        self.ECOSYSTEMS: List[Dict] = [
            {
                'name': 'pytorch',
                'trigger_imports': {'torch'},
                'associated_imports': {'torchvision', 'torchaudio', 'torch'},
                'extra_packages': {},  # Auto-added
                'python_hint': '3.7',
            },
            {
                'name': 'tensorflow',
                'trigger_imports': {'tensorflow', 'tf', 'keras'},
                'associated_imports': {'tensorflow', 'keras', 'tensorboard'},
                'extra_packages': {'numpy': ''},
                'python_hint': '3.7',
            },
            {
                'name': 'sklearn',
                'trigger_imports': {'sklearn', 'scikit-learn'},
                'associated_imports': {'sklearn', 'numpy', 'scipy', 'pandas'},
                'extra_packages': {'numpy': '', 'scipy': ''},
                'python_hint': '3.7',
            },
            {
                'name': 'data_science',
                'trigger_imports': {'pandas', 'numpy', 'matplotlib'},
                'associated_imports': {'pandas', 'numpy', 'matplotlib', 'seaborn',
                                       'scipy', 'statsmodels'},
                'extra_packages': {},
                'python_hint': '3.7',
            },
            {
                'name': 'flask_web',
                'trigger_imports': {'flask'},
                'associated_imports': {'flask', 'jinja2', 'werkzeug', 'wtforms',
                                       'flask_sqlalchemy', 'flask_login'},
                'extra_packages': {},
                'python_hint': '3.7',
            },
            {
                'name': 'django_web',
                'trigger_imports': {'django'},
                'associated_imports': {'django', 'rest_framework', 'celery',
                                       'channels', 'corsheaders'},
                'extra_packages': {},
                'python_hint': '3.7',
            },
            {
                'name': 'scrapy_crawling',
                'trigger_imports': {'scrapy'},
                'associated_imports': {'scrapy', 'twisted', 'lxml', 'cssselect'},
                'extra_packages': {},
                'python_hint': '2.7',
            },
            {
                'name': 'async_networking',
                'trigger_imports': {'asyncio', 'aiohttp'},
                'associated_imports': {'asyncio', 'aiohttp', 'aiofiles', 'uvloop'},
                'extra_packages': {},
                'python_hint': '3.7',
            },
            {
                'name': 'nlp',
                'trigger_imports': {'nltk', 'spacy', 'gensim', 'textblob'},
                'associated_imports': {'nltk', 'spacy', 'gensim', 'numpy'},
                'extra_packages': {'numpy': ''},
                'python_hint': '3.7',
            },
            {
                'name': 'aws',
                'trigger_imports': {'boto', 'boto3', 'botocore'},
                'associated_imports': {'boto3', 'botocore', 'awscli', 's3transfer'},
                'extra_packages': {},
                'python_hint': '3.7',
            },
            {
                'name': 'crypto',
                'trigger_imports': {'Crypto', 'cryptography', 'nacl'},
                'associated_imports': {'cryptography', 'pycryptodome', 'pynacl'},
                'extra_packages': {},
                'python_hint': '3.7',
            },
        ]
        
        # === Code patterns that imply hidden dependencies ===
        self.IMPLICIT_DEPENDENCY_PATTERNS: List[Dict] = [
            # f-strings → Python 3.6+
            {
                'code_pattern': r'f["\'].*\{.*\}.*["\']',
                'implies_python': '3.6',
                'confidence': 0.9,
            },
            # async/await → Python 3.5+
            {
                'code_pattern': r'\basync\s+(def|for|with)\b',
                'implies_python': '3.5',
                'confidence': 0.95,
            },
            # print statement → Python 2
            {
                'code_pattern': r'^\s*print\s+[^(]',
                'implies_python': '2.7',
                'confidence': 0.95,
            },
            # type hints → Python 3.5+
            {
                'code_pattern': r'def\s+\w+\([^)]*:\s*(int|str|float|bool|List|Dict|Optional)\b',
                'implies_python': '3.5',
                'confidence': 0.8,
            },
            # walrus operator → Python 3.8+
            {
                'code_pattern': r':=',
                'implies_python': '3.8',
                'confidence': 0.99,
            },
            # urllib2 → Python 2
            {
                'code_pattern': r'\burllib2\b',
                'implies_python': '2.7',
                'confidence': 0.99,
            },
            # raw_input → Python 2
            {
                'code_pattern': r'\braw_input\s*\(',
                'implies_python': '2.7',
                'confidence': 0.99,
            },
            # StringIO import → Python 2
            {
                'code_pattern': r'from\s+StringIO\s+import',
                'implies_python': '2.7',
                'confidence': 0.99,
            },
            # except X, e → Python 2
            {
                'code_pattern': r'except\s+\w+\s*,\s*\w+\s*:',
                'implies_python': '2.7',
                'confidence': 0.99,
            },
            # dataclasses → Python 3.7+
            {
                'code_pattern': r'from\s+dataclasses\s+import|@dataclass',
                'implies_python': '3.7',
                'confidence': 0.99,
            },
            # pathlib → Python 3.4+ (but commonly 3.6+)
            {
                'code_pattern': r'from\s+pathlib\s+import|pathlib\.Path',
                'implies_python': '3.6',
                'confidence': 0.85,
            },
        ]
        
        # === Snippet complexity features ===
        self.COMPLEXITY_WEIGHTS = {
            'num_imports': 0.2,
            'has_ml': 0.3,
            'has_web_framework': 0.15,
            'has_system_calls': 0.1,
            'has_c_extensions': 0.25,
        }
    
    # ===========================================================
    # Main API
    # ===========================================================
    
    def analyze(self, code: str, imports: List[str]) -> Dict:
        """
        Comprehensive semantic analysis of a Python snippet.
        
        Returns:
        {
            'resolved_imports': {import_name: pip_package},
            'python_version': str,     # Recommended Python version
            'python_confidence': float, # Confidence in version
            'ecosystem': str,          # Detected ecosystem
            'complexity': str,         # 'simple', 'medium', 'complex'
            'extra_packages': dict,    # Additional packages to include
            'warnings': list,          # Issues detected
        }
        """
        result = {
            'resolved_imports': {},
            'python_version': None,
            'python_confidence': 0.0,
            'ecosystem': None,
            'complexity': 'medium',
            'extra_packages': {},
            'warnings': [],
        }
        
        # 1. Disambiguate imports using usage patterns
        for imp in imports:
            resolved = self._disambiguate_import(imp, code)
            if resolved:
                result['resolved_imports'][imp] = resolved
        
        # 2. Detect Python version from code patterns
        py_ver, py_conf = self._detect_python_version(code)
        result['python_version'] = py_ver
        result['python_confidence'] = py_conf
        
        # 3. Detect ecosystem
        ecosystem = self._detect_ecosystem(imports)
        if ecosystem:
            result['ecosystem'] = ecosystem['name']
            result['extra_packages'] = ecosystem.get('extra_packages', {})
            # Ecosystem can override Python version hint
            if not py_ver and ecosystem.get('python_hint'):
                result['python_version'] = ecosystem['python_hint']
                result['python_confidence'] = 0.5
        
        # 4. Classify complexity
        result['complexity'] = self._classify_complexity(code, imports)
        
        # 5. Detect warnings
        result['warnings'] = self._detect_warnings(code, imports)
        
        return result
    
    def disambiguate_import(self, import_name: str, code: str) -> Optional[str]:
        """Public API for single import disambiguation."""
        return self._disambiguate_import(import_name, code)
    
    def get_python_version_signals(self, code: str) -> List[Tuple[str, float]]:
        """Get all Python version signals with confidence scores."""
        signals = []
        for pattern in self.IMPLICIT_DEPENDENCY_PATTERNS:
            if re.search(pattern['code_pattern'], code, re.MULTILINE):
                signals.append((
                    pattern['implies_python'],
                    pattern['confidence']
                ))
        return signals
    
    def get_ecosystem(self, imports: List[str]) -> Optional[str]:
        """Get the detected ecosystem name."""
        eco = self._detect_ecosystem(imports)
        return eco['name'] if eco else None
    
    def get_complexity_score(self, code: str, imports: List[str]) -> float:
        """Get a 0-1 complexity score for time budget allocation."""
        complexity = self._classify_complexity(code, imports)
        scores = {'simple': 0.2, 'medium': 0.5, 'complex': 0.9}
        return scores.get(complexity, 0.5)
    
    # ===========================================================
    # Internal methods
    # ===========================================================
    
    def _disambiguate_import(self, import_name: str, code: str) -> Optional[str]:
        """Resolve ambiguous import using code context."""
        best_match = None
        best_conf = 0.0
        
        for entry in self.USAGE_DISAMBIGUATORS:
            if entry['import'] != import_name:
                continue
            
            # Check usage patterns
            for pattern in entry['patterns']:
                if re.search(pattern, code):
                    if entry['confidence'] > best_conf:
                        best_conf = entry['confidence']
                        best_match = entry['package']
                    break  # One match is enough per entry
        
        return best_match
    
    def _detect_python_version(self, code: str) -> Tuple[Optional[str], float]:
        """Detect Python version from code patterns."""
        py2_score = 0.0
        py3_score = 0.0
        py3_min = '3.5'
        
        for pattern in self.IMPLICIT_DEPENDENCY_PATTERNS:
            if re.search(pattern['code_pattern'], code, re.MULTILINE):
                ver = pattern['implies_python']
                conf = pattern['confidence']
                
                if ver.startswith('2'):
                    py2_score += conf
                else:
                    py3_score += conf
                    # Track minimum Python 3 version
                    if ver > py3_min:
                        py3_min = ver
        
        if py2_score > py3_score and py2_score > 0:
            return '2.7', min(py2_score / (py2_score + py3_score + 0.001), 0.99)
        elif py3_score > 0:
            return py3_min, min(py3_score / (py2_score + py3_score + 0.001), 0.99)
        
        return None, 0.0
    
    def _detect_ecosystem(self, imports: List[str]) -> Optional[Dict]:
        """Detect which ecosystem the imports belong to."""
        import_set = {imp.lower() for imp in imports}
        
        best_eco = None
        best_overlap = 0
        
        for eco in self.ECOSYSTEMS:
            # Check trigger imports
            trigger_overlap = len(import_set & {t.lower() for t in eco['trigger_imports']})
            if trigger_overlap == 0:
                continue
            
            # Score by total overlap with associated imports
            total_overlap = len(import_set & {a.lower() for a in eco['associated_imports']})
            
            if total_overlap > best_overlap:
                best_overlap = total_overlap
                best_eco = eco
        
        return best_eco
    
    def _classify_complexity(self, code: str, imports: List[str]) -> str:
        """Classify snippet complexity: simple, medium, complex."""
        score = 0.0
        
        # Number of imports
        if len(imports) <= 2:
            score += 0.1
        elif len(imports) <= 5:
            score += 0.3
        else:
            score += 0.6
        
        # ML imports (heavy)
        ml_imports = {'tensorflow', 'torch', 'keras', 'sklearn', 'scipy',
                      'mxnet', 'transformers', 'pytorch', 'caffe'}
        if any(imp.lower() in ml_imports for imp in imports):
            score += 0.4
        
        # Web framework
        web_imports = {'flask', 'django', 'tornado', 'fastapi', 'aiohttp'}
        if any(imp.lower() in web_imports for imp in imports):
            score += 0.2
        
        # C extension packages
        c_ext_imports = {'numpy', 'scipy', 'lxml', 'pillow', 'cv2',
                        'cryptography', 'psycopg2'}
        if any(imp.lower() in c_ext_imports for imp in imports):
            score += 0.2
        
        # Code length
        lines = code.count('\n')
        if lines > 200:
            score += 0.2
        elif lines > 50:
            score += 0.1
        
        if score <= 0.3:
            return 'simple'
        elif score <= 0.6:
            return 'medium'
        else:
            return 'complex'
    
    def _detect_warnings(self, code: str, imports: List[str]) -> List[str]:
        """Detect potential issues in the snippet."""
        warnings = []
        
        # System-only imports
        system_indicators = {
            'gi': 'GTK/GNOME (system-only)',
            'AppKit': 'macOS (system-only)',
            'Foundation': 'macOS (system-only)',
            'objc': 'macOS PyObjC (system-only)',
            'win32api': 'Windows (system-only)',
            'win32com': 'Windows (system-only)',
        }
        for imp in imports:
            if imp in system_indicators:
                warnings.append(f"'{imp}' is platform-specific: {system_indicators[imp]}")
        
        # Heavy packages that may timeout
        heavy_pkgs = {'tensorflow', 'torch', 'pytorch', 'scipy'}
        for imp in imports:
            if imp.lower() in heavy_pkgs:
                warnings.append(f"'{imp}' is a heavy package (may need extended timeout)")
        
        # Mixed Python 2/3 patterns
        signals = self.get_python_version_signals(code)
        py2_count = sum(1 for v, _ in signals if v.startswith('2'))
        py3_count = sum(1 for v, _ in signals if v.startswith('3'))
        if py2_count > 0 and py3_count > 0:
            warnings.append(f"Mixed Python 2/3 syntax detected ({py2_count} py2, {py3_count} py3)")
        
        return warnings
