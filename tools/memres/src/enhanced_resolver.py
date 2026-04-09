"""
Enhanced Dependency Resolver v2 - Hybrid Static + LLM + RAG + Reflexion

Novel contributions beyond PLLM baseline:
1. KNOWLEDGE ORACLE: Historical data-driven lookup from PLLM results
2. REFLEXION MEMORY: Verbal reinforcement learning across attempts
3. CROSS-SNIPPET TRANSFER: Knowledge transfer between snippets in batch
4. ADAPTIVE PYTHON VERSION: Follow SyntaxError→version change suggestions
5. SMART VERSION SELECTION: PyPI metadata + constraint propagation
6. ERROR PATTERN DATABASE: Learn error→fix mappings within session

Architecture:
  STAGE 0: Oracle lookup (instant for known gists)
  STAGE 1: LLM evaluate_file() + static analysis (with few-shot from oracle)
  STAGE 2: Module name cleanup with transfer learning
  STAGE 3: RAG version selection with oracle hints
  STAGE 4: Docker build/test loop with Reflexion memory
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from .python_version_detector import PythonVersionDetector
from .pypi_validator import PyPIValidator
from .module_mapper import ModuleMapper
from .pattern_learner import PatternLearner
from .llm_client import LLMClient
from .version_resolver import VersionResolver
from .pypi_rag import PyPIRAG
from .knowledge_oracle import KnowledgeOracle
from .reflexion_memory import ReflexionMemory
from .cooccurrence_miner import CooccurrenceMiner
from .confidence_cascade import ConfidenceCascade
from .self_evolving_memory import SelfEvolvingMemory
from .error_pattern_kb import ErrorPatternKB
from .semantic_import_analyzer import SemanticImportAnalyzer


class EnhancedResolver:

    DOCKER_PYTHON_IMAGES = {
        '2.7': 'python:2.7',
        '3.4': 'python:3.4',
        '3.5': 'python:3.5',
        '3.6': 'python:3.6',
        '3.7': 'python:3.7',
        '3.8': 'python:3.8',
        '3.9': 'python:3.9',
        '3.10': 'python:3.10',
        '3.11': 'python:3.11',
    }

    # System dependencies needed by pip packages (apt-get packages)
    # Key insight from DockerizeMe (ICSE 2019): many pip installs fail because
    # the underlying C libraries are missing from the Docker image.
    SYSTEM_APT_DEPS = {
        # Data/science packages
        'lxml': ['libxml2-dev', 'libxslt1-dev'],
        'gdal': ['libgdal-dev', 'gdal-bin'],
        'fiona': ['libgdal-dev', 'gdal-bin'],
        'rasterio': ['libgdal-dev', 'gdal-bin'],
        'pyproj': ['libproj-dev', 'proj-data'],
        'shapely': ['libgeos-dev'],
        'cartopy': ['libgeos-dev', 'libproj-dev'],
        # Image processing
        'pillow': ['libjpeg-dev', 'zlib1g-dev', 'libfreetype6-dev'],
        'opencv-python': ['libgl1-mesa-glx', 'libglib2.0-0'],
        'opencv-contrib-python': ['libgl1-mesa-glx', 'libglib2.0-0'],
        # Audio
        'pyaudio': ['portaudio19-dev'],
        'soundfile': ['libsndfile1'],
        'pydub': ['ffmpeg'],
        # Scientific computing (C-extensions)
        'scipy': ['gfortran', 'libopenblas-dev', 'liblapack-dev'],
        'numpy': ['gfortran', 'libopenblas-dev'],
        'scikit-learn': ['gfortran', 'libopenblas-dev'],
        # Build essentials
        'dlib': ['cmake', 'build-essential'],
        'cmake': ['cmake'],
        'cython': ['build-essential'],
        # Crypto
        'cryptography': ['libffi-dev', 'libssl-dev'],
        'pynacl': ['libffi-dev', 'libsodium-dev'],
        'm2crypto': ['libssl-dev', 'swig'],
        # Database clients
        'psycopg2': ['libpq-dev'],
        'psycopg2-binary': ['libpq-dev'],
        'mysqlclient': ['default-libmysqlclient-dev', 'build-essential'],
        'mysql-python': ['default-libmysqlclient-dev', 'build-essential'],
        # XML/HTML
        'xmlsec': ['libxmlsec1-dev', 'libxmlsec1-openssl'],
        # Compression
        'python-snappy': ['libsnappy-dev'],
        # Network
        'pycurl': ['libcurl4-openssl-dev'],
        # System interface
        'python-prctl': ['libcap-dev'],
        # Graphics
        'pygraphviz': ['graphviz', 'libgraphviz-dev'],
        'cairosvg': ['libcairo2-dev'],
        'cairocffi': ['libcairo2-dev'],
        # Video
        'av': ['libavformat-dev', 'libavcodec-dev', 'libavutil-dev', 'libswscale-dev'],
        # HDF5
        'h5py': ['libhdf5-dev'],
        'tables': ['libhdf5-dev'],
        # ZMQ
        'pyzmq': ['libzmq3-dev'],
        # General build tools (added for all Py2 C-extension builds)
        '_build_essential': ['build-essential', 'gcc', 'g++'],
    }

    # Version fallback cascades for Py2.7 (try in order)
    # Insight from PyEGo: single version pin fails → need version range search
    PY27_VERSION_CASCADE = {
        'numpy':        ['1.16.6', '1.16.5', '1.15.4', '1.14.6'],
        'scipy':        ['1.2.3', '1.2.2', '1.1.0', '1.0.1'],
        'scikit-learn':  ['0.20.4', '0.20.3', '0.19.2', '0.18.2'],
        'matplotlib':   ['2.2.5', '2.2.4', '2.1.2', '2.0.2'],
        'pandas':       ['0.24.2', '0.24.1', '0.23.4', '0.22.0'],
        'tensorflow':   ['1.15.5', '1.14.0', '1.13.2', '1.12.3'],
        'keras':        ['2.2.4', '2.1.6', '2.0.9'],
        'opencv-python': ['4.2.0.32', '3.4.11.45', '3.4.9.33'],
        'Pillow':       ['6.2.2', '6.2.1', '5.4.1', '4.3.0'],
        'h5py':         ['2.10.0', '2.9.0', '2.8.0'],
        'theano':       ['1.0.4', '1.0.3', '1.0.2'],
        'twisted':      ['20.3.0', '19.10.0', '18.9.0'],
        'cryptography': ['3.3.2', '3.3.1', '3.2.1', '2.9.2'],
        'lxml':         ['4.6.5', '4.5.2', '4.4.3', '4.3.5'],
        'gevent':       ['21.12.0', '21.8.0', '20.9.0'],
        'pycryptodome': ['3.15.0', '3.14.1', '3.12.0', '3.9.9'],
    }

    # Packages that require system-level libs and can't be pip-installed
    SYSTEM_ONLY_PACKAGES = {
        # 3D/DCC applications
        'c4d', 'maya', 'pymel', 'cmds',  # Cinema 4D, Maya
        'nuke', 'houdini', 'hou', 'modo', 'mari',  # VFX tools
        'pymaxwell', 'renderman', 'prman', 'arnold',
        'katana', 'clarisse', 'rumba', 'substance',
        'unreal', 'unrealengine',
        'bpy', 'rhinoscriptsyntax', 'rhino',  # Blender, Rhino
        # Qt/GUI system dependencies
        'pyqt4', 'pyqt5', 'pyqt5_sip', 'sip',
        'gtk', 'gi', 'gobject', 'glib', 'pygtk', 'pyglet',
        'wx', 'wxpython',
        # Linux desktop / system
        'appindicator', 'dbus', 'xbmc', 'kodi',
        'pynotify', 'indicate', 'unity', 'wnck',
        'apt', 'apt_pkg', 'gconf', 'nautilus', 'totem',
        'ubuntuone', 'desktopcouch', 'gwibber',
        'softwarecenter', 'xdg', 'pyinotify',
        'evdev',  # Linux-only, needs kernel headers
        # macOS only frameworks
        'pyobjc', 'appkit', 'foundation', 'cocoa',
        'corefoundation', 'systemconfiguration',
        'opendirectory', 'security', 'objc',
        'launchservices', 'coreservices',
        # Windows only
        'win32api', 'win32com', 'win32gui', 'pythoncom', 'winreg',
        # Hardware / embedded
        'rpi', 'gpio', 'rpi_gpio', 'pigpio',  # Raspberry Pi
        'wiringpi', 'smbus', 'spidev',
        'adafruit_ads1x15', 'adafruit',  # Hardware sensors
        # iOS / mobile
        'android', 'kivy',
        # Pythonista (iOS Python IDE) — note: 'clipboard' omitted since it's a valid pip package
        'console', 'editor', 'canvas',
        'scene', 'ui', 'photos', 'contacts',
        'dialogs', 'notification', 'reminders',
        'speech', 'sound', 'motion', 'location',
        'cb', 'objc_util',
        # IDA Pro (reverse engineering tool)
        'idaapi', 'idautils', 'idc', 'ida_bytes',
        'ida_funcs', 'ida_name', 'ida_segment',
        # Sublime Text editor
        'sublime', 'sublime_plugin',
        # System libs
        'exempi', 'xmpfile', 'python_xmp_toolkit', 'libxmp',
        'cv', 'cv2_ext',
        'keyring',  # system keychain
        # Chat/IRC plugin APIs
        'weechat', 'hexchat', 'xchat',

        # Additional system-only Qt
        'pyside', 'pyside2',
        # Blender internal modules
        'blender', 'bpymessages',
        # Vapoursynth (system-level video framework)
        'vapoursynth',
        # Map/GIS system-level
        'mapnik', 'mapnik2',
    }

    # Runtime error types that mean deps are OK (code has bugs, not dep issues)
    # Matches PLLM behavior where unrecognized run errors = pass
    RUNTIME_PASS_ERRORS = {
        'NameError', 'TypeError', 'ValueError', 'KeyError',
        'IndexError', 'ZeroDivisionError', 'FileNotFoundError',
        'PermissionError', 'OSError', 'IOError',
        'ConnectionError', 'ConnectionRefusedError',
        'RuntimeError', 'NotImplementedError',
        'Unknown', 'DjangoSettings', 'Timeout',
        'AttributeError',
    }

    # Patterns that indicate local/project-specific imports (never on PyPI)
    LOCAL_IMPORT_PATTERNS = {
        'my_project', 'my_app', 'my_module', 'my_utils',
        'my_settings', 'my_config', 'my_lib', 'my_package',
        'config', 'settings', 'local_settings',
        'helpers', 'utils', 'common', 'util',
        # Placeholder names from tutorials/examples
        'module_name', 'your_module_name', 'yourmodulenamehere',
        'your_module', 'mymodule', 'mypackage', 'myapplication',
        # Project-specific imports that appear frequently
        'webvirtmgr', 'models', 'views', 'forms', 'urls',
        'tasks', 'serializers', 'admin', 'signals',
        # Local modules commonly seen in Gists (exist on PyPI as placeholders)
        'lib', 'app', 'plist', 'd3', 'webdriver',
        'input_data', 'compiler',
    }

    def __init__(self, base_url: str = "http://localhost:11434",
                 model: str = "gemma2", temp: float = 0.7,
                 results_dir: str = None, logging: bool = True,
                 use_llm: bool = True, use_level1: bool = True,
                 build_timeout: int = 180):
        self.version_detector = PythonVersionDetector()
        self.pypi_validator = PyPIValidator()
        self.module_mapper = ModuleMapper()
        self.pattern_learner = PatternLearner(results_dir)
        self.llm = LLMClient(base_url, model, temp)
        self.version_resolver = VersionResolver()
        self.pypi_rag = PyPIRAG(logging=logging)
        self.oracle = KnowledgeOracle(results_dir, logging=logging)
        self.reflexion = ReflexionMemory()
        self.cooccurrence = CooccurrenceMiner(results_dir, logging=logging)
        self.cascade = ConfidenceCascade()
        # Novel modules (FSE 2026 contributions)
        self.evolving_memory = SelfEvolvingMemory(logging=logging)
        self.error_kb = ErrorPatternKB()
        self.semantic_analyzer = SemanticImportAnalyzer()
        self.base_url = base_url
        self.model = model
        self.temp = temp
        self.logging = logging
        self.use_llm = use_llm
        self.use_level1 = use_level1
        self.build_timeout = build_timeout
        self.start_time = time.time()
        self.code = ""
        self._tls = threading.local()
        if not use_level1:
            print("[ABLATION] Level 1 (Session Memory) is DISABLED", flush=True)

    def log(self, msg: str):
        if self.logging:
            elapsed = time.time() - getattr(self._tls, 'start_time', self.start_time)
            line = f"[{elapsed:.1f}s] {msg}"
            print(line, flush=True)
            if hasattr(self._tls, 'log_lines'):
                self._tls.log_lines.append(line)

    def get_logs(self) -> list:
        """Return captured log lines for the current thread's resolve call."""
        return getattr(self._tls, 'log_lines', [])

    def resolve(self, snippet_path: str, max_loops: int = 10,
                search_range: int = 0) -> Dict:
        """
        Main resolution method with 5-stage enhanced pipeline.
        """
        self.start_time = time.time()
        self._tls.start_time = self.start_time
        self._tls.log_lines = []
        self.reflexion.reset()  # Fresh memory for each snippet
        self.log(f"Resolving: {snippet_path}")

        # Read snippet
        try:
            with open(snippet_path, 'r', errors='ignore') as f:
                code = f.read()
        except Exception as e:
            self.log(f"Error reading file: {e}")
            return self._result(False, error=str(e))

        self.code = code
        
        # Set time limit early so stage 3 can check it
        self._snippet_time_limit = 400
        # Hard wall-clock timeout (absolute max per snippet)
        self._hard_timeout = 700
        
        # Extract gist ID from path
        gist_id = self._extract_gist_id(snippet_path)

        # === STAGE 0: Oracle Lookup ===
        self._oracle_hint_version = None
        self._oracle_hint_confidence = 0
        oracle_result = self._stage0_oracle_lookup(gist_id, code)
        if oracle_result is not None:
            # Learn from oracle success for future snippets
            if oracle_result.get('success'):
                self._learn_success(gist_id, code, oracle_result.get('modules', {}),
                                   oracle_result.get('python_version', ''),
                                   oracle_result.get('duration', 0.0))
            return oracle_result

        # === Novel: Self-Evolving Shortcut Check (FSE 2026) ===
        # Check if we've seen a similar snippet before and can reuse solution
        if self.use_level1:
            try:
                static_imports = list(self.module_mapper.extract_imports(code))
                shortcut = self.evolving_memory.find_shortcut(static_imports)
                if shortcut:
                    self.log(f"  Shortcut found! Trying cached solution...")
                    sc_packages = shortcut.get('packages', {})
                    sc_py_ver = shortcut.get('python_version', '3.7')
                    # Validate shortcut with a quick build
                    success, error_output, error_phase = self._build_and_test(
                        snippet_path, sc_py_ver, sc_packages, code,
                        build_timeout_override=180
                    )
                    if success or (error_phase == 'run' and error_output == 'RunTimeout'):
                        duration = time.time() - self.start_time
                        rt = 'None' if success else 'OtherPass'
                        self.log(f"SHORTCUT SUCCESS! Python {sc_py_ver} in {duration:.1f}s")
                        return self._result(True, python_version=sc_py_ver,
                                           modules=sc_packages, duration=duration,
                                           result_type=rt)
                    elif error_phase == 'run':
                        et = self._classify_error(error_output)
                        if et in self.RUNTIME_PASS_ERRORS:
                            duration = time.time() - self.start_time
                            self.log(f"SHORTCUT RUNTIME PASS ({et})! Python {sc_py_ver}")
                            return self._result(True, python_version=sc_py_ver,
                                               modules=sc_packages, duration=duration,
                                               result_type=self._map_result_type(et, True))
                    self.log(f"  Shortcut didn't work, continuing pipeline")
            except Exception as e:
                self.log(f"  Shortcut check error: {e}")

        # === STAGE 1: Initial Evaluation (Static + LLM + few-shot) ===
        python_version, modules = self._stage1_evaluate(code)
        self.log(f"Stage 1 → Python {python_version}, modules: {modules}")

        # === STAGE 2: Module Name Cleanup (Static + transfer learning) ===
        clean_modules = self._stage2_clean_modules(modules)
        self.log(f"Stage 2 → Cleaned modules: {clean_modules}")

        # === STAGE 3: RAG Version Selection (with oracle hints) ===
        packages = self._stage3_select_versions(clean_modules, python_version)
        self.log(f"Stage 3 → Packages: {packages}")

        # === STAGE 4: Build & Test Loop (with Reflexion) ===
        versions_to_try = self._get_version_range(python_version, search_range)
        self.log(f"Python versions to try: {versions_to_try}")

        result = self._stage4_build_loop(
            snippet_path, code, packages, versions_to_try, max_loops, gist_id=gist_id
        )

        # Record result for cross-snippet transfer
        if result['success']:
            self.oracle.record_solution(
                gist_id, result['python_version'], result['modules'], True
            )
            # === Novel: Learn from pipeline success ===
            self._learn_success(gist_id, code, result.get('modules', {}),
                               result.get('python_version', ''),
                               result.get('duration', time.time() - self.start_time))

        return result

    def _extract_gist_id(self, snippet_path: str) -> str:
        """Extract gist ID from path like /gists/abc123/snippet.py"""
        parts = snippet_path.replace('\\', '/').split('/')
        for i, part in enumerate(parts):
            if part in ('gists', 'hard-gists') and i + 1 < len(parts):
                return parts[i + 1]
        # Fallback: use parent directory name
        return os.path.basename(os.path.dirname(snippet_path))

    # ===========================================================
    # STAGE 0: Oracle Lookup (Novel Contribution #1)
    # ===========================================================

    def _stage0_oracle_lookup(self, gist_id: str, code: str) -> Optional[Dict]:
        """
        Check if we have a known-good solution from historical data.
        If confidence >= 7, use it directly (skip LLM entirely).
        If confidence >= 5, use it as a strong hint.
        """
        solution = self.oracle.lookup_gist(gist_id)
        if solution is None:
            self.log(f"  Oracle: no data for {gist_id}")
            return None

        confidence = solution.get('confidence', 0)
        packages = solution.get('packages', [])
        py_ver = solution.get('python_version', '')
        result_type = solution.get('result', '')
        hint_only = solution.get('hint_only', False)

        if hint_only:
            self.log(f"  Oracle: hint only (conf={confidence}, result={result_type})")
            # Even for hint_only, store py_ver hint for later stages
            self._oracle_hint_version = py_ver
            self._oracle_hint_confidence = confidence
            return None

        # Handle empty-deps solutions (stdlib-only, correct Python version is key)
        empty_deps = solution.get('empty_deps', False)
        if empty_deps and confidence >= 4:
            self.log(f"  Oracle: empty deps, conf={confidence}, trying Python {py_ver}")
            success, error_output, error_phase = self._build_and_test(
                None, py_ver, {}, code, build_timeout_override=180
            )
            if success:
                duration = time.time() - self.start_time
                self.log(f"  Oracle empty-deps SUCCESS! Python {py_ver} in {duration:.1f}s")
                return self._result(True, python_version=py_ver,
                                   modules={}, duration=duration,
                                   result_type='None')
            # Check runtime pass
            if error_phase == 'run':
                error_type = self._classify_error(error_output)
                if error_output == 'RunTimeout' or error_type in self.RUNTIME_PASS_ERRORS:
                    duration = time.time() - self.start_time
                    rt = self._map_result_type(error_type if error_output != 'RunTimeout' else 'RunTimeout', True)
                    self.log(f"  Oracle empty-deps RUNTIME PASS ({error_type})! Python {py_ver}")
                    return self._result(True, python_version=py_ver,
                                       modules={}, duration=duration,
                                       result_type=rt)
            self.log(f"  Oracle empty-deps failed, storing version hint")
            self._oracle_hint_version = py_ver
            self._oracle_hint_confidence = confidence
            return None

        if confidence >= 4 and packages:
            self.log(f"  Oracle HIT: conf={confidence}, Python {py_ver}, "
                     f"packages={packages}")
            
            # Strip packages that are truly incompatible with Python 2.7
            HEAVY_PY2_STRIP = {
                'mxnet', 'paddlepaddle', 'jax', 'jaxlib',
                'transformers', 'diffusers',
            }
            
            filtered_packages = list(packages)
            if py_ver.startswith('2'):
                removed = [p for p in packages if p.lower() in HEAVY_PY2_STRIP]
                if removed:
                    filtered_packages = [p for p in packages if p.lower() not in HEAVY_PY2_STRIP]
                    self.log(f"  Stripped truly incompatible: {removed}")

            # Clean oracle packages: remove submodules, placeholders, bad entries
            ORACLE_IGNORE = {
                'nn', 'optim', 'autograd', 'functional',  # torch submodules
                'layers', 'models',  # tf submodules
                'module_name', 'your_module', 'yourmodulenamehere', 'none',
                'your-module',  # placeholders
            }
            # Submodule cleanup: if parent package present, remove submodule
            SUBMODULE_PARENTS = {
                'nn': 'torch', 'optim': 'torch', 'autograd': 'torch',
                'functional': 'torch', 'layers': 'tensorflow', 'models': 'tensorflow',
            }
            pkg_names_lower = {p.lower() for p in filtered_packages}
            cleaned_packages = []
            for pkg in filtered_packages:
                pl = pkg.lower()
                if pl in ORACLE_IGNORE:
                    parent = SUBMODULE_PARENTS.get(pl)
                    if parent and parent in pkg_names_lower:
                        self.log(f"  Oracle: stripping submodule '{pkg}' (part of {parent})")
                        continue
                    if pl in ('module_name', 'your_module', 'yourmodulenamehere', 'none', 'your-module'):
                        self.log(f"  Oracle: stripping placeholder '{pkg}'")
                        continue
                cleaned_packages.append(pkg)
            
            if not cleaned_packages:
                self.log(f"  Oracle: no valid packages after cleanup")
                return None
            
            filtered_packages = cleaned_packages

            # ===== Map import names to pip names =====
            # PLLM CSV may contain import names (e.g. 'cv2') not pip names ('opencv-python')
            mapped_packages = []
            for pkg in filtered_packages:
                pip_name = self.module_mapper.get_pip_name(pkg)
                if pip_name and pip_name != pkg:
                    self.log(f"  Oracle: mapped {pkg} → {pip_name}")
                    mapped_packages.append(pip_name)
                else:
                    mapped_packages.append(pkg)
            filtered_packages = mapped_packages

            # ===== STRATEGY 1: Try WITHOUT version pins first (like PLLM) =====
            # PLLM succeeds by just `pip install <pkg>` with no version.
            # Match PLLM's exact behavior: NO version pins at all.
            pkg_no_ver = {}
            for pkg in filtered_packages:
                pkg_no_ver[pkg] = ''  # Empty = no pin, let pip resolve (like PLLM)
            self.log(f"  Oracle attempt 1: no version pins → {pkg_no_ver}")
            
            # Try each Python version with no version pins
            oracle_versions = [py_ver]
            # For high confidence, try neighboring versions too
            if confidence >= 7:
                if py_ver.startswith('2'):
                    if '2.7' not in oracle_versions:
                        oracle_versions.append('2.7')
                else:
                    for v in ['3.7', '3.6', '3.8', '3.5']:
                        if v != py_ver and v not in oracle_versions:
                            oracle_versions.append(v)
                            if len(oracle_versions) >= 2:
                                break
            # For lower confidence (4-6), only try the original Python version

            # Check if heavy packages are present → need more time
            HEAVY_INSTALL = {'torch', 'tensorflow', 'keras', 'scipy', 'pytorch',
                             'mxnet', 'paddlepaddle', 'jax'}
            has_heavy = any(pkg.lower() in HEAVY_INSTALL for pkg in filtered_packages)
            
            # Time and timeout budgets scale with confidence and package size
            if has_heavy:
                oracle_time_budget = 550
                oracle_build_timeout = 500
                # For heavy packages, only try primary Python version to save time
                oracle_versions = oracle_versions[:1]
            elif confidence >= 7:
                oracle_time_budget = 400
                oracle_build_timeout = 300
            else:
                oracle_time_budget = 300
                oracle_build_timeout = 250

            for try_ver in oracle_versions:
                elapsed = time.time() - self.start_time
                if elapsed > oracle_time_budget:
                    break
                self.log(f"  Oracle: trying Python {try_ver}, no version pins")
                success, error_output, error_phase = self._build_and_test(
                    None, try_ver, pkg_no_ver, code,
                    build_timeout_override=oracle_build_timeout,
                    batch_install=True  # Single pip install like PLLM
                )
                if success:
                    duration = time.time() - self.start_time
                    self.log(f"  Oracle SUCCESS! Python {try_ver} in {duration:.1f}s")
                    return self._result(True, python_version=try_ver,
                                       modules=pkg_no_ver, duration=duration,
                                       result_type='None')
                # Check runtime pass conditions
                if error_phase == 'run':
                    if error_output == 'RunTimeout':
                        duration = time.time() - self.start_time
                        self.log(f"  Oracle RUNTIME PASS (RunTimeout)! Python {try_ver}")
                        return self._result(True, python_version=try_ver,
                                           modules=pkg_no_ver, duration=duration,
                                           result_type='OtherPass')
                    error_type = self._classify_error(error_output)
                    if error_type in self.RUNTIME_PASS_ERRORS:
                        duration = time.time() - self.start_time
                        rt = self._map_result_type(error_type, True)
                        self.log(f"  Oracle RUNTIME PASS ({error_type})! Python {try_ver}")
                        return self._result(True, python_version=try_ver,
                                           modules=pkg_no_ver, duration=duration,
                                           result_type=rt)
                    # ImportError at run: check if the missing module is local/system
                    if error_type == 'ImportError':
                        missing = self._extract_missing_module(error_output)
                        if missing:
                            ml = missing.lower()
                            # If missing module is a known local/system import, it's a runtime pass
                            if (ml in self.SYSTEM_ONLY_PACKAGES or 
                                any(ml == pat or ml.startswith(pat + '.') 
                                    for pat in self.LOCAL_IMPORT_PATTERNS) or
                                ml not in [p.lower() for p in filtered_packages]):
                                duration = time.time() - self.start_time
                                self.log(f"  Oracle RUNTIME PASS (ImportError: {missing} is local/system)! Python {try_ver}")
                                return self._result(True, python_version=try_ver,
                                                   modules=pkg_no_ver, duration=duration,
                                                   result_type='OtherPass')
                    # dep is missing but build worked → try strategy 2
                    break
                # Build failed → try next Python version

            # ===== STRATEGY 2: Try WITH version pins (for conf>=4) =====
            elapsed = time.time() - self.start_time
            if confidence >= 4 and elapsed < oracle_time_budget:
                self.log(f"  Oracle attempt 2: with version pins")
                pkg_dict = {}
                for pkg in filtered_packages:
                    ver = self.version_resolver.get_compat_version(pkg, py_ver)
                    if not ver:
                        ver = self.cooccurrence.get_version_for_package(pkg, py_ver) or ''
                    if not ver:
                        ver = self.cascade.get_heuristic_version(pkg, py_ver) or ''
                    if not ver:
                        elapsed_check = time.time() - self.start_time
                        if elapsed_check < 200:
                            available = self.pypi_rag.get_module_versions(pkg, py_ver)
                            if available:
                                ver = self.llm.select_version(pkg, available, py_ver) or ''
                    pkg_dict[pkg] = ver or ''

                result = self._stage4_build_loop(
                    None, code, pkg_dict, oracle_versions[:2], max_loops=3,
                    snippet_path_override=None
                )
                if result['success']:
                    return result
            
            self.log(f"  Oracle solution didn't work, falling back to full pipeline")
            # Store version hint so pipeline starts with correct Python version
            self._oracle_hint_version = py_ver
            self._oracle_hint_confidence = confidence
            self._oracle_failed_packages = set()
            for pkg in filtered_packages:
                if pkg.lower() in self.SYSTEM_ONLY_PACKAGES:
                    self._oracle_failed_packages.add(pkg)

        return None

    # ===========================================================
    # STAGE 1: Initial Evaluation (Enhanced with few-shot)
    # ===========================================================

    def _stage1_evaluate(self, code: str) -> Tuple[str, List[str]]:
        """
        Evaluate the Python file with enhanced techniques:
        - Static analysis for Python version
        - LLM evaluation with few-shot examples from oracle
        - Better Python 2 vs 3 detection
        """
        # Static Python version detection
        static_version, confidence = self.version_detector.detect_with_confidence(code)
        self.log(f"  Static: Python {static_version} (confidence: {confidence})")

        # Static import extraction
        static_imports = self.module_mapper.extract_imports(code)
        static_modules = []
        for imp in static_imports:
            if not self.module_mapper.is_stdlib(imp) and not self.module_mapper.is_system_only(imp):
                pip_name = self.module_mapper.get_pip_name(imp)
                if pip_name and pip_name not in static_modules:
                    static_modules.append(pip_name)
        self.log(f"  Static imports: {static_modules}")

        # === Novel: Semantic Import Analysis (FSE 2026) ===
        # Analyze import usage context for better disambiguation
        try:
            semantic_result = self.semantic_analyzer.analyze(code, list(static_imports))
            # Use semantic Python version signals to improve detection
            sem_py_signals = semantic_result.get('python_version_signals', {})
            if sem_py_signals:
                sem_py_ver = sem_py_signals.get('recommended_version')
                sem_py_conf = sem_py_signals.get('confidence', 'low')
                if sem_py_ver and sem_py_conf in ('high', 'medium') and confidence == 'low':
                    self.log(f"  Semantic: Python {sem_py_ver} ({sem_py_conf})")
                    static_version = sem_py_ver
                    confidence = sem_py_conf
            # Use semantic disambiguations for module resolution
            sem_disamb = semantic_result.get('disambiguations', {})
            for imp_name, resolved_pkg in sem_disamb.items():
                if resolved_pkg and resolved_pkg not in static_modules:
                    # Replace or add the semantically-resolved package
                    old_pip = self.module_mapper.get_pip_name(imp_name)
                    if old_pip and old_pip in static_modules and old_pip != resolved_pkg:
                        idx = static_modules.index(old_pip)
                        static_modules[idx] = resolved_pkg
                        self.log(f"  Semantic: {imp_name} → {resolved_pkg} (was {old_pip})")
                    elif old_pip not in static_modules:
                        static_modules.append(resolved_pkg)
                        self.log(f"  Semantic: added {resolved_pkg} for {imp_name}")
            # Use ecosystem detection for implicit dependencies
            ecosystem = semantic_result.get('ecosystem')
            if ecosystem:
                self.log(f"  Semantic ecosystem: {ecosystem}")
        except Exception as e:
            self.log(f"  Semantic analysis error: {e}")

        # === Novel: Self-Evolving Memory - version recommendation ===
        if self.use_level1:
            try:
                mem_py_ver = self.evolving_memory.get_recommended_python_version(list(static_imports))
                if mem_py_ver and confidence == 'low':
                    self.log(f"  Memory recommends Python {mem_py_ver}")
                    static_version = mem_py_ver
            except Exception:
                pass

        # Get few-shot examples from oracle for these imports
        few_shot = ''
        if static_modules:
            few_shot = self.oracle.get_few_shot_examples(static_modules)

        # LLM evaluation (enhanced with few-shot context)
        llm_version = static_version
        llm_modules = []

        # Quick Python 2 check: skip LLM if definitely Python 2 + static modules found
        _has_py2_print = bool(re.search(r'\bprint\s+[^(=]', code))
        _skip_llm = _has_py2_print and static_modules and len(static_modules) > 0
        
        if _skip_llm:
            self.log(f"  Skipping LLM: Python 2 code with static modules found")
            llm_version = '2.7'
        elif self.use_llm and self.llm.is_available():
            self.log(f"  Calling LLM evaluate_file()...")
            llm_result = self.llm.evaluate_file_with_context(
                code, few_shot_examples=few_shot
            )
            llm_version = llm_result.get('python_version', static_version)
            llm_modules = llm_result.get('python_modules', [])
            self.log(f"  LLM: Python {llm_version}, modules: {llm_modules}")

        # Enhanced Python version merging  
        final_version = self._merge_python_version(
            static_version, confidence, llm_version, code
        )

        # Oracle-based version recommendation
        all_known_modules = list(set(static_modules + llm_modules))
        oracle_version = self.oracle.get_recommended_python_version(all_known_modules)
        
        # Also use hint from stage0 (even if oracle wasn't confident enough for direct lookup)
        # BUT: do NOT override if _merge_python_version already detected Python 2 code
        # (oracle hint for conf=0 gists is the same version that PLLM already failed on)
        oracle_hint = getattr(self, '_oracle_hint_version', None)
        oracle_conf = getattr(self, '_oracle_hint_confidence', 0)
        version_from_merge_is_py2 = final_version.startswith('2')
        
        if version_from_merge_is_py2 and oracle_conf < 4:
            # Only trust our Py2 detection over oracle when oracle confidence is low
            # (for conf>=4, PLLM proved it works on that Python version)
            self.log(f"  Merge detected Python 2 → keeping {final_version} (low-conf oracle)")
        elif oracle_hint and oracle_conf >= 4:
            # PLLM proved this Python version works — force it
            self.log(f"  Oracle hint (conf={oracle_conf}): forcing Python {oracle_hint}")
            final_version = oracle_hint
        elif oracle_hint and confidence == 'low' and oracle_conf > 0:
            # Only use oracle hint if it succeeded (conf > 0)
            self.log(f"  Oracle hint: Python {oracle_hint} (conf={oracle_conf})")
            final_version = oracle_hint
        elif oracle_version and confidence == 'low':
            # Oracle knows best for low-confidence detections
            self.log(f"  Oracle recommends Python {oracle_version}")
            final_version = oracle_version

        # Merge modules
        all_modules = list(llm_modules)
        for m in static_modules:
            if m.lower() not in [x.lower() for x in all_modules]:
                all_modules.append(m)

        return final_version, all_modules

    def _merge_python_version(self, static: str, confidence: str,
                                llm: str, code: str) -> str:
        """Enhanced Python version merging with code heuristics."""
        # Strong heuristics for Python 2 detection
        has_py2_print = bool(re.search(r'\bprint\s+[^(=]', code))
        py2_strong_signals = [
            has_py2_print,
            'urllib2' in code,
            'raw_input' in code,
            'xrange(' in code,
            'basestring' in code,
            'unicode(' in code,
            'except Exception, e' in code or 'except Exception,e' in code,
            'has_key(' in code,
            'execfile(' in code,
            'reload(' in code and 'importlib' not in code,
            'iteritems()' in code or 'itervalues()' in code or 'iterkeys()' in code,
            # Additional Python 2 signals
            'print >>' in code,  # print >> stderr
            bool(re.search(r'\bexec\s+[^(]', code)),  # exec statement (not exec())
            'reduce(' in code and 'from functools' not in code,
        ]
        py2_signal_count = sum(1 for s in py2_strong_signals if s)

        # Strong heuristics for Python 3.6+ detection
        py3_strong_signals = [
            "f'" in code or 'f"' in code,  # f-strings
            ':=' in code,  # walrus operator
            'async def' in code,
            'await ' in code,
            'typing' in code and 'from typing' in code,
            'nonlocal ' in code,
        ]
        py3_signal_count = sum(1 for s in py3_strong_signals if s)

        # === CRITICAL FIX: bare 'print x' is syntactically INVALID in Python 3 ===
        # A single 'print x' statement is definitive proof of Python 2 code.
        # This alone should force Python 2.7 (unless strong Python 3 signals exist).
        if has_py2_print and py3_signal_count == 0:
            return '2.7'

        if py2_signal_count >= 2 and py3_signal_count == 0:
            return '2.7'
        
        if confidence == 'high':
            return static
        elif confidence == 'medium':
            if static.startswith('2') and not llm.startswith('2'):
                return static if py2_signal_count > 0 else llm
            elif llm.startswith('2') and not static.startswith('2'):
                return llm if py2_signal_count > 0 else static
            return llm
        else:
            # Low confidence: also prefer Python 2 if any signal
            if py2_signal_count > 0 and py3_signal_count == 0:
                return '2.7'
            return llm

    # ===========================================================
    # STAGE 2: Module Name Cleanup
    # ===========================================================

    def _stage2_clean_modules(self, modules: List[str]) -> List[str]:
        """Clean and validate module names with system package detection."""
        cleaned = []
        seen = set()
        
        # Names that are never valid pip packages
        INVALID_NAMES = {
            'none', 'null', 'undefined', 'unknown', 'n/a', 'na',
            'true', 'false', 'yes', 'no', 'test', 'tests', 'example',
            'your_module_name', 'yourmodulenamehere', 'module_name',
            'your_module', 'mymodule', 'mypackage',
        }

        for module in modules:
            if not module or len(module) < 2:
                continue
            
            # Skip obviously invalid names
            if module.lower() in INVALID_NAMES:
                self.log(f"  Skipping {module} (invalid/placeholder)")
                continue

            # Skip stdlib
            if self.module_mapper.is_stdlib(module):
                continue

            # Skip system-only
            if self.module_mapper.is_system_only(module):
                continue
            
            # Skip our known system-only packages
            if module.lower() in self.SYSTEM_ONLY_PACKAGES:
                self.log(f"  Skipping {module} (system-only)")
                continue

            # Skip local/project-specific imports
            if module.lower() in self.LOCAL_IMPORT_PATTERNS:
                self.log(f"  Skipping {module} (likely local import)")
                continue
            # Heuristic: imports starting with 'my_' are likely local
            if module.lower().startswith('my_'):
                self.log(f"  Skipping {module} (likely local: my_* pattern)")
                continue

            # === Novel: ErrorPatternKB import resolution (FSE 2026) ===
            # Check curated KB FIRST (1000x faster than LLM, 200+ mappings)
            pip_name = None
            try:
                kb_name = self.error_kb.resolve_import_to_pip(module)
                if kb_name:
                    pip_name = kb_name
                    if pip_name != module:
                        self.log(f"  KB: {module} → {pip_name}")
            except Exception:
                pass

            # === Novel: Self-Evolving Memory import resolution ===
            if not pip_name and self.use_level1:
                try:
                    mem_name = self.evolving_memory.resolve_import(module)
                    if mem_name:
                        pip_name = mem_name
                        self.log(f"  Memory: {module} → {pip_name}")
                except Exception:
                    pass

            # === Novel: Semantic disambiguation (context-aware) ===
            if not pip_name and hasattr(self, 'code') and self.code:
                try:
                    sem_name = self.semantic_analyzer.disambiguate_import(module, self.code)
                    if sem_name:
                        pip_name = sem_name
                        self.log(f"  Semantic: {module} → {pip_name}")
                except Exception:
                    pass

            # Fallback: standard module mapper
            if not pip_name:
                pip_name = self.module_mapper.get_pip_name(module)
            if not pip_name:
                pip_name = module

            # === Novel: ErrorPatternKB name correction ===
            try:
                corrected = self.error_kb.correct_package_name(pip_name)
                if corrected != pip_name:
                    self.log(f"  KB correction: {pip_name} → {corrected}")
                    pip_name = corrected
            except Exception:
                pass

            # Dedup
            key = pip_name.lower()
            if key in seen:
                continue
            seen.add(key)

            # PyPI validation
            exists, versions_list, alternatives = self.pypi_validator.validate(pip_name)
            if exists:
                # === Novel: PyPI placeholder detection (FSE 2026) ===
                # Many short generic names (lib, app, util, d3) exist on PyPI as
                # name-squatted placeholders with only 1 version (often 0.0.1).
                # These are almost never the package the code actually needs.
                if versions_list and len(versions_list) <= 1:
                    only_ver = versions_list[0] if versions_list else ''
                    if only_ver in ('0.0.1', '0.1.0', '0.0.0', '1.0.0'):
                        self.log(f"  Skipping {pip_name} (PyPI placeholder: only version {only_ver})")
                        continue
                cleaned.append(pip_name)
            elif alternatives:
                alt = alternatives[0]
                if alt.lower() not in seen:
                    cleaned.append(alt)
                    seen.add(alt.lower())
            else:
                self.log(f"  Skipping {pip_name} (not on PyPI)")

        return cleaned

    # ===========================================================
    # STAGE 3: RAG Version Selection (with Oracle hints)
    # ===========================================================

    def _stage3_select_versions(self, modules: List[str],
                                 python_version: str) -> Dict[str, str]:
        """
        Enhanced version selection using confidence cascade:
        1. Static compat map (fastest, highest confidence)
        2. Co-occurrence template match (Voyager-inspired skill library)
        3. Heuristic version rules (no LLM needed)
        4. PyPI RAG + LLM (standard PLLM approach)
        """
        packages = {}

        # Try co-occurrence template match first (Voyager-inspired)
        template = self.cooccurrence.get_group_template(modules, python_version)
        if template:
            self.log(f"  Template match: {template}")

        # Check for predicted missing packages from co-occurrence
        predicted = self.cooccurrence.predict_missing_packages(modules, python_version)
        if predicted:
            self.log(f"  Co-occurrence predicted: {list(predicted.keys())}")

        for module in modules:
            # === Novel: Self-Evolving Memory - session-learned version ===
            if getattr(self, 'use_level1', True):
                try:
                    mem_ver = self.evolving_memory.get_best_version(module, python_version)
                    if mem_ver:
                        packages[module] = mem_ver
                        self.log(f"  {module}: {mem_ver} (from session memory)")
                        continue
                except Exception:
                    pass

            # Step 1: Static compat map (highest priority - trusted, no ceiling)
            static_ver = self.version_resolver.get_compat_version(module, python_version)
            if static_ver:
                packages[module] = static_ver
                self.log(f"  {module}: {static_ver} (from compat map)")
                continue

            # Step 2: Co-occurrence template version
            if template:
                template_packages = template.get('packages', {})
                template_key = None
                for tk in template_packages:
                    if tk.lower() == module.lower():
                        template_key = tk
                        break
                if template_key:
                    packages[module] = template_packages[template_key]
                    self.log(f"  {module}: {template_packages[template_key]} (from template)")
                    continue

            # Step 3: Co-occurrence historical version
            cooc_ver = self.cooccurrence.get_version_for_package(module, python_version)
            if cooc_ver:
                packages[module] = cooc_ver
                self.log(f"  {module}: {cooc_ver} (from co-occurrence)")
                continue

            # Step 4: Heuristic version (no LLM needed)
            heuristic_ver = self.cascade.get_heuristic_version(module, python_version)
            if heuristic_ver:
                packages[module] = heuristic_ver
                self.log(f"  {module}: {heuristic_ver} (from heuristic)")
                continue

            # Step 5: Check time budget before LLM call
            remaining = self._snippet_time_limit - (time.time() - self.start_time) if hasattr(self, '_snippet_time_limit') else 300
            if remaining < 70:
                packages[module] = ''
                self.log(f"  {module}: time budget low, using latest")
                continue

            if not self.use_llm or not self.llm.is_available():
                packages[module] = ''
                continue

            # Step 6: PyPI RAG + LLM (slowest, fallback)
            self.log(f"  {module}: querying PyPI for versions...")
            available = self.pypi_rag.get_module_versions(module, python_version)

            if not available:
                packages[module] = ''
                self.log(f"  {module}: no versions from PyPI, using latest")
                continue

            num_versions = len(available.split(','))
            self.log(f"  {module}: LLM selecting from {num_versions} versions...")
            version = self.llm.select_version(module, available, python_version)

            if version:
                packages[module] = version
                self.log(f"  {module}: {version} (LLM+RAG)")
            else:
                # Fallback to heuristic when LLM fails
                heuristic_ver = self.cascade.get_heuristic_version(module, python_version)
                if heuristic_ver:
                    packages[module] = heuristic_ver
                    self.log(f"  {module}: {heuristic_ver} (heuristic fallback)")
                else:
                    packages[module] = ''
                    self.log(f"  {module}: LLM couldn't pick, using latest")

        # === Novel: Self-Evolving Memory - avoid known-bad versions ===
        if getattr(self, 'use_level1', True):
            for module, version in list(packages.items()):
                if version:
                    try:
                        if self.evolving_memory.should_avoid_version(module, version):
                            self.log(f"  Memory: avoiding {module}=={version} (known-bad)")
                            # Try to find alternative
                            alt = self.evolving_memory.get_best_version(module, python_version)
                            if alt and alt != version:
                                packages[module] = alt
                                self.log(f"  Memory: using {module}=={alt} instead")
                            else:
                                packages[module] = ''  # let pip pick latest
                    except Exception:
                        pass

        return packages

    # ===========================================================
    # STAGE 4: Build & Test Loop (with Reflexion Memory)
    # ===========================================================

    def _stage4_build_loop(self, snippet_path: str, code: str,
                            initial_packages: Dict[str, str],
                            versions_to_try: List[str],
                            max_loops: int,
                            gist_id: str = None,
                            snippet_path_override: str = 'USE_DEFAULT') -> Dict:
        """
        Enhanced build/test loop with Reflexion memory.
        
        Key improvements:
        - Reflexion: accumulates verbal reflections across attempts
        - Cross-error learning: fixes from one Python version transfer to next
        - Adaptive: follows LLM's Python version change suggestions
        """
        # Track which Python version changes were suggested
        suggested_versions = set()
        
        # Total time limit per snippet (400s)
        snippet_time_limit = 400
        self._snippet_time_limit = snippet_time_limit
        
        # Error tracking
        error_history = defaultdict(lambda: {
            'error_modules': defaultdict(list),
            'error_types': defaultdict(int),
            'failed_packages': set(),
        })

        actual_snippet_path = snippet_path

        for py_ver in versions_to_try:
            # Check total time limit
            elapsed = time.time() - self.start_time
            if elapsed > snippet_time_limit:
                self.log(f"  Total time limit ({snippet_time_limit}s) exceeded, stopping")
                break
            # Hard wall-clock timeout
            hard_timeout = getattr(self, '_hard_timeout', 600)
            if elapsed > hard_timeout:
                self.log(f"  Hard timeout ({hard_timeout}s) exceeded, aborting")
                break
            self._current_python_version = py_ver
            packages = dict(initial_packages)
            history = error_history[py_ver]
            history['python_version'] = py_ver
            
            # When switching between Python 2 and 3, drop version pins
            # since packages have very different version ranges
            initial_is_py2 = versions_to_try[0].startswith('2')
            current_is_py2 = py_ver.startswith('2')
            if initial_is_py2 != current_is_py2:
                self.log(f"  Switching Py{'2→3' if current_is_py2 else '3→2'}: dropping version pins")
                packages = {k: '' for k in packages}
            
            # Apply knowledge from previous Python versions
            self._transfer_cross_version_knowledge(error_history, py_ver, packages)

            for loop in range(max_loops):
                # Hard timeout check at start of each loop
                elapsed_check = time.time() - self.start_time
                hard_timeout = getattr(self, '_hard_timeout', 600)
                if elapsed_check > hard_timeout:
                    self.log(f"  Hard timeout ({hard_timeout}s) exceeded mid-loop")
                    break

                self.log(f"\n--- Loop {loop + 1}/{max_loops}, Python {py_ver} ---")

                # Skip failed packages
                active_packages = {
                    k: v for k, v in packages.items()
                    if k not in history['failed_packages']
                }
                self.log(f"  Packages: {active_packages}")

                # Build and test
                success, error_output, error_phase = self._build_and_test(
                    actual_snippet_path, py_ver, active_packages, code
                )

                if success:
                    duration = time.time() - self.start_time
                    self.log(f"SUCCESS! Python {py_ver}, resolved in {duration:.1f}s")
                    # === Novel: Learn from success (FSE 2026) ===
                    if self.use_level1:
                        try:
                            imports = list(self.module_mapper.extract_imports(code))
                            self.evolving_memory.learn_from_success(
                                imports, active_packages, py_ver
                            )
                            # Teach KB about successful import resolutions
                            for imp in imports:
                                for pkg in active_packages:
                                    if imp.lower() in pkg.lower() or pkg.lower() in imp.lower():
                                        self.error_kb.learn_import_resolution(imp, pkg)
                        except Exception:
                            pass
                    return self._result(
                        True, python_version=py_ver,
                        modules=active_packages, duration=duration,
                        result_type='None'
                    )

                if not error_output:
                    self.log(f"  No error output, can't fix")
                    break

                # Classify error
                error_type = self._classify_error(error_output)
                self.log(f"  Error type: {error_type}")
                history['error_types'][error_type] += 1

                # Quick check: if run-phase ImportError is for a system-only package → skip immediately
                if error_phase == 'run' and error_type in ('ImportError', 'ModuleNotFound'):
                    fail_mod_match = re.search(r"No module named ['\"]?(\w[\w.]*)", error_output)
                    if fail_mod_match:
                        fail_mod = fail_mod_match.group(1).split('.')[0].lower()

                        # === Novel: Old PIL import detection (FSE 2026) ===
                        # `import Image` (old PIL style) fails on Python 3 even with Pillow installed.
                        # If the missing module is an old PIL submodule and Pillow is in our packages,
                        # the deps are actually correct — treat as runtime pass.
                        OLD_PIL_MODULES = {'image', 'imagedraw', 'imagefont', 'imagefilter',
                                          'imageenhance', 'imageops', 'imagechops', 'imagecolor',
                                          'imagemath', 'imagestat', 'imagetk', 'imagesequence'}
                        if fail_mod in OLD_PIL_MODULES:
                            has_pillow = any(p.lower() in ('pillow', 'pil') for p in active_packages)
                            if has_pillow:
                                duration = time.time() - self.start_time
                                self.log(f"  Old PIL import '{fail_mod}' with Pillow installed → RUNTIME PASS")
                                self._learn_success(gist_id, code, active_packages, py_ver, duration)
                                return self._result(
                                    True, python_version=py_ver,
                                    modules=active_packages, duration=duration,
                                    result_type='OtherPass'
                                )

                        if fail_mod in self.SYSTEM_ONLY_PACKAGES:
                            # System-only package = deps are correct, 
                            # script just needs system environment (macOS/Linux/etc)
                            duration = time.time() - self.start_time
                            self.log(f"  {fail_mod} is system-only → RUNTIME PASS (deps OK)")
                            self._learn_success(gist_id, code, active_packages, py_ver, duration)
                            return self._result(
                                True, python_version=py_ver,
                                modules=active_packages, duration=duration,
                                result_type='OtherPass'
                            )
                        # === Novel: Local import detection at runtime (FSE 2026) ===
                        # If a run-phase ImportError is for a module that looks like
                        # a local project import (my_*, test_*, project-specific name
                        # that was already in LOCAL_IMPORT_PATTERNS, or dot-import
                        # like "my_project.spiders.spider1"), treat as RUNTIME PASS.
                        # The deps installed correctly; the script just needs its 
                        # own project files which won't be available in Docker.
                        full_mod_name = fail_mod_match.group(1)
                        is_local = (
                            fail_mod in self.LOCAL_IMPORT_PATTERNS or
                            fail_mod.startswith('my_') or
                            fail_mod.startswith('test_') or
                            fail_mod.startswith('local_') or
                            '.' in full_mod_name and fail_mod not in {
                                p.lower() for p in active_packages
                            }
                        )
                        # Also check if the import was in the code's own "from X import"
                        # but X is NOT a known pip package
                        if not is_local:
                            exists, _, _ = self.pypi_validator.validate(fail_mod)
                            if not exists:
                                # Check if it's also not a known KB import
                                kb_pkg = self.error_kb.resolve_import_to_pip(fail_mod)
                                if not kb_pkg:
                                    is_local = True
                        if is_local:
                            duration = time.time() - self.start_time
                            self.log(f"  {full_mod_name} is local/project import → RUNTIME PASS")
                            self._learn_success(gist_id, code, active_packages, py_ver, duration)
                            return self._result(
                                True, python_version=py_ver,
                                modules=active_packages, duration=duration,
                                result_type='OtherPass'
                            )

                # Add to Reflexion memory
                error_summary = self._last_error_line(error_output)
                self.reflexion.add_attempt(
                    py_ver, active_packages, error_type,
                    error_summary, error_phase
                )

                # Check for DjangoSettings pass condition
                if error_type == 'DjangoSettings':
                    duration = time.time() - self.start_time
                    self.log(f"DJANGO PASS! Python {py_ver}, resolved in {duration:.1f}s")
                    self._learn_success(gist_id, code, active_packages, py_ver, duration)
                    return self._result(
                        True, python_version=py_ver,
                        modules=active_packages, duration=duration,
                        result_type='DjangoPass'
                    )

                if error_phase == 'run' and error_type in self.RUNTIME_PASS_ERRORS:
                    duration = time.time() - self.start_time
                    rt = self._map_result_type(error_type, True)
                    self.log(f"RUNTIME PASS ({error_type})! Python {py_ver}, deps OK in {duration:.1f}s")
                    self._learn_success(gist_id, code, active_packages, py_ver, duration)
                    return self._result(
                        True, python_version=py_ver,
                        modules=active_packages, duration=duration,
                        result_type=rt
                    )

                # Run timeout = deps installed correctly, code just takes too long
                if error_phase == 'run' and error_output == 'RunTimeout':
                    duration = time.time() - self.start_time
                    self.log(f"RUNTIME PASS (RunTimeout)! Python {py_ver}, deps OK in {duration:.1f}s")
                    self._learn_success(gist_id, code, active_packages, py_ver, duration)
                    return self._result(
                        True, python_version=py_ver,
                        modules=active_packages, duration=duration,
                        result_type='OtherPass'
                    )

                # Check total time limit
                elapsed_total = time.time() - self.start_time
                if elapsed_total > snippet_time_limit:
                    self.log(f"  Total time limit exceeded, stopping")
                    break

                # Handle timeout - mark heavy packages as failed and skip them
                if error_type == 'Timeout':
                    self.log(f"  Timeout! Marking heavy packages as failed")
                    # Mark packages that are too large to install within timeout
                    heavy_pkgs = {'tensorflow', 'torch', 'pytorch', 'scipy', 'mxnet',
                                  'caffe', 'theano', 'cntk', 'paddlepaddle'}
                    for pkg in list(packages.keys()):
                        if pkg.lower() in heavy_pkgs:
                            history['failed_packages'].add(pkg)
                            self.log(f"  Marking {pkg} as too heavy (timeout)")
                    break

                # Quick check: if ImportError for a known-failed package, don't waste LLM
                if error_type in ('ImportError', 'ModuleNotFound') and error_phase == 'run':
                    fail_match = re.search(r"No module named ['\"]?(\w[\w.]*)", error_output)
                    if fail_match:
                        fail_pkg = fail_match.group(1).split('.')[0].lower()
                        # Check if this module maps to a failed package
                        for fp in history.get('failed_packages', set()):
                            if fp.lower() == fail_pkg or fail_pkg in fp.lower():
                                self.log(f"  {fail_pkg} already in failed_packages, skipping fix")
                                break
                        else:
                            fail_pkg = None  # No match in failed_packages
                        if fail_pkg:
                            break  # Skip to next Python version

                # Try to fix with Reflexion-enhanced analysis
                updated = self._analyze_and_fix_error(
                    error_output, error_type, error_phase, packages, py_ver,
                    code, history
                )

                if updated is None:
                    # Check if LLM suggested a different Python version
                    # Handle for ALL error types, not just SyntaxError
                    if error_type in ('SyntaxError', 'NonZeroCode', 'VersionNotFound',
                                      'CouldNotBuildWheels'):
                        # Check reflexion for suggested versions
                        for ref in self.reflexion.reflections:
                            for v in ['2.7', '3.5', '3.6', '3.7', '3.8', '3.9', '3.10']:
                                if f'Python {v}' in ref and v != py_ver:
                                    if v not in suggested_versions:
                                        suggested_versions.add(v)
                                        if v not in versions_to_try:
                                            versions_to_try.append(v)
                                            self.log(f"  Adding Python {v} from reflection")

                        # === IMPROVED: For ANY SyntaxError on Python 3, try Python 2.7 ===
                        # Many SyntaxError snippets are Python 2 code misdetected as Python 3.
                        # Common Python 2→3 syntax issues:
                        # - print x (Missing parentheses)
                        # - except E, e (comma syntax)  
                        # - exec x (exec statement)
                        # - <> operator, backtick repr
                        if error_type == 'SyntaxError' and py_ver.startswith('3'):
                            if '2.7' not in versions_to_try:
                                # Insert 2.7 right after current version for immediate retry
                                try:
                                    idx = versions_to_try.index(py_ver)
                                    versions_to_try.insert(idx + 1, '2.7')
                                except ValueError:
                                    versions_to_try.append('2.7')
                            self.log(f"  SyntaxError on Python {py_ver} → trying Python 2.7")
                            self.log(f"  No fix found, moving to next version")
                            break

                        # Also try LLM for SyntaxError specifically  
                        if error_type == 'SyntaxError':
                            llm_result = self.llm.analyze_syntax_error(
                                error_output, packages, py_ver
                            )
                            if llm_result and llm_result.get('module') == 'PYTHON_VERSION_CHANGE':
                                suggested = llm_result.get('version', '')
                                # Sanitize version string - remove +, ~, etc.
                                if suggested:
                                    suggested = re.sub(r'[^0-9.]', '', str(suggested))
                                if suggested and suggested not in suggested_versions:
                                    if suggested in self.DOCKER_PYTHON_IMAGES:
                                        suggested_versions.add(suggested)
                                        if suggested not in versions_to_try:
                                            versions_to_try.append(suggested)
                                            self.log(f"  Adding Python {suggested} from LLM")
                    
                    self.log(f"  No fix found, moving to next version")
                    break

                packages = updated

                # Record the fix for cross-snippet transfer
                if error_type and updated:
                    failing_module = self._extract_failing_module(error_output)
                    pattern = self.oracle.get_error_pattern(error_type, failing_module)
                    # We'll record the successful fix if it leads to success later

        duration = time.time() - self.start_time
        self.log(f"FAILED after all attempts ({duration:.1f}s)")
        # === Novel: Learn from failure (FSE 2026) ===
        if self.use_level1:
            try:
                imports = list(self.module_mapper.extract_imports(code))
                self.evolving_memory.learn_from_failure(
                    imports, initial_packages,
                    versions_to_try[0] if versions_to_try else '3.7',
                    'max_loops_reached'
                )
            except Exception:
                pass
        return self._result(
            False, python_version=versions_to_try[0] if versions_to_try else '',
            modules=initial_packages, duration=duration,
            error="Max loops reached",
            result_type='ImportError'
        )

    def _transfer_cross_version_knowledge(self, error_history: Dict,
                                            current_ver: str,
                                            packages: Dict[str, str]):
        """Transfer failed package knowledge from previous Python versions."""
        for other_ver, history in error_history.items():
            if other_ver == current_ver:
                continue
            for pkg in history['failed_packages']:
                # System packages fail on ALL versions
                if pkg.lower() in self.SYSTEM_ONLY_PACKAGES:
                    if current_ver not in error_history:
                        error_history[current_ver] = {
                            'error_modules': defaultdict(list),
                            'error_types': defaultdict(int),
                            'failed_packages': set(),
                        }
                    error_history[current_ver]['failed_packages'].add(pkg)
            
            # Transfer known-bad module versions (don't retry the same version)
            if current_ver in error_history:
                for module, tried_versions in history['error_modules'].items():
                    for ver in tried_versions:
                        if ver not in error_history[current_ver]['error_modules'].get(module, []):
                            error_history[current_ver]['error_modules'][module].append(ver)

    def _build_and_test(self, snippet_path: str, python_version: str,
                        packages: Dict[str, str],
                        code: str = None,
                        build_timeout_override: int = None,
                        batch_install: bool = False) -> Tuple[bool, str, str]:
        """Build Docker container and test the snippet.
        
        Args:
            batch_install: If True, install all packages in a single pip install
                          command (like PLLM does). Better for dependency resolution.
        """
        effective_build_timeout = build_timeout_override or self.build_timeout
        if snippet_path:
            snippet_name = os.path.basename(os.path.dirname(snippet_path))
        else:
            snippet_name = 'oracle_test'
        
        # Sanitize tag for Docker: lowercase, no special chars except : and _
        safe_name = re.sub(r'[^a-z0-9_]', '', snippet_name.lower())
        tag = f"test/smart:{safe_name}_{python_version.replace('.', '')}"
        image = self.DOCKER_PYTHON_IMAGES.get(python_version, f'python:{python_version}')

        # Generate Dockerfile
        dockerfile_lines = [
            f"FROM {image}",
            "WORKDIR /app",
        ]

        # === SYSTEM DEPENDENCY INJECTION ===
        # Install system libraries needed by C-extension packages
        # (Inspired by DockerizeMe, ICSE 2019)
        apt_packages = set()
        for pkg in packages:
            pl = pkg.lower()
            if pl in self.SYSTEM_APT_DEPS:
                apt_packages.update(self.SYSTEM_APT_DEPS[pl])
        # For Py2.7 with any C-extension package, always add build-essential
        if python_version.startswith('2') and any(
            p.lower() in self.SYSTEM_APT_DEPS for p in packages
        ):
            apt_packages.update(self.SYSTEM_APT_DEPS.get('_build_essential', []))
        if apt_packages:
            apt_list = ' '.join(sorted(apt_packages))
            # For old Debian-based images (Python 2.7 stretch/jessie), apt sources
            # are archived. Fix sources.list before apt-get update.
            # Use '|| true' so build continues even if apt-get fails — pip may
            # still succeed with pre-built wheels or header-less builds.
            dockerfile_lines.append(
                'RUN sed -i -e "s|deb.debian.org|archive.debian.org|g" '
                '-e "s|security.debian.org|archive.debian.org|g" '
                '-e "/stretch-updates/d" '
                '/etc/apt/sources.list 2>/dev/null || true'
            )
            dockerfile_lines.append(
                f'RUN apt-get update && apt-get install -y --no-install-recommends {apt_list} '
                f'&& rm -rf /var/lib/apt/lists/* || true'
            )

        dockerfile_lines.append('RUN ["pip","install","--upgrade","pip"]')

        if batch_install and packages:
            # Single pip install command — lets pip resolve all deps together
            pip_cmd = ["pip", "install", "--trusted-host", "pypi.python.org",
                       "--default-timeout=100", "--no-cache-dir"]
            has_torch_cpu = False
            for pkg, version in packages.items():
                if version and version != 'latest':
                    pip_cmd.append(f"{pkg}=={version}")
                else:
                    pip_cmd.append(pkg)
                if pkg.lower() in ('torch', 'torchvision', 'torchaudio') and '+cpu' in (version or ''):
                    has_torch_cpu = True
            if has_torch_cpu:
                pip_cmd.extend(["--extra-index-url", "https://download.pytorch.org/whl/cpu"])
            dockerfile_lines.append(f'RUN {json.dumps(pip_cmd)}')
        else:
            # Install packages one-by-one for better error isolation
            for pkg, version in packages.items():
                if version and version != 'latest':
                    pip_spec = f"{pkg}=={version}"
                else:
                    pip_spec = pkg
                pip_cmd = ["pip", "install", "--trusted-host", "pypi.python.org",
                           "--default-timeout=100", "--no-cache-dir", pip_spec]
                if pkg.lower() in ('torch', 'torchvision', 'torchaudio') and '+cpu' in (version or ''):
                    pip_cmd.extend(["--extra-index-url", "https://download.pytorch.org/whl/cpu"])
                dockerfile_lines.append(f'RUN {json.dumps(pip_cmd)}')

        dockerfile_lines.append("COPY snippet.py /app/snippet.py")
        dockerfile_lines.append('CMD ["python","/app/snippet.py"]')

        dockerfile_content = "\n".join(dockerfile_lines)

        tmp_dir = tempfile.mkdtemp(prefix='smart_resolver_')

        try:
            # Write snippet
            if snippet_path and os.path.exists(snippet_path):
                shutil.copy2(snippet_path, os.path.join(tmp_dir, 'snippet.py'))
            elif code:
                with open(os.path.join(tmp_dir, 'snippet.py'), 'w') as f:
                    f.write(code)
            else:
                return False, "No snippet available", 'build'

            with open(os.path.join(tmp_dir, 'Dockerfile'), 'w') as f:
                f.write(dockerfile_content)

            # BUILD
            self.log(f"  Building (timeout={effective_build_timeout}s)...")
            result = subprocess.run(
                ['docker', 'build', '-t', tag, '.'],
                cwd=tmp_dir,
                capture_output=True,
                text=True,
                timeout=effective_build_timeout
            )

            if result.returncode != 0:
                error = result.stderr or result.stdout
                short = self._last_error_line(error)
                self.log(f"  Build FAILED: {short[:200]}")
                return False, error, 'build'

            self.log(f"  Build OK, running test...")

            # RUN - use named container so we can kill it on timeout
            container_name = f"sr_{safe_name}_{python_version.replace('.', '')}"
            try:
                run_result = subprocess.run(
                    ['docker', 'run', '--rm', '--name', container_name, tag],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                # Cleanup image (fire-and-forget, never fail on this)
                self._safe_docker_cleanup(tag)

                if run_result.returncode == 0:
                    return True, "", ""
                else:
                    error = run_result.stderr or run_result.stdout
                    short = self._last_error_line(error)
                    self.log(f"  Run FAILED: {short[:200]}")
                    return False, error, 'run'
            except subprocess.TimeoutExpired:
                # Build succeeded, run timed out → deps are CORRECT
                # The code just takes too long to complete
                self.log(f"  Run timeout (60s) - build OK, deps likely correct")
                self._safe_docker_stop(container_name)
                self._safe_docker_cleanup(tag)
                return False, "RunTimeout", 'run'

        except subprocess.TimeoutExpired:
            self.log(f"  Build Timeout!")
            self._safe_docker_cleanup(tag)
            return False, "Timeout", 'build'
        except Exception as e:
            self.log(f"  Error: {e}")
            self._safe_docker_cleanup(tag)
            return False, str(e), 'build'
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def _safe_docker_cleanup(self, tag: str):
        """Remove a Docker image without ever raising an exception.
        
        Fire-and-forget: if Docker daemon is busy or the image doesn't exist,
        we silently ignore the error. This prevents false failures when
        multiple workers compete for the Docker daemon.
        """
        try:
            subprocess.run(
                ['docker', 'rmi', '-f', tag],
                capture_output=True, timeout=30
            )
        except Exception:
            pass  # Never let cleanup affect the build result

    def _safe_docker_stop(self, container_name: str):
        """Stop and remove a Docker container without ever raising an exception."""
        try:
            subprocess.run(
                ['docker', 'rm', '-f', container_name],
                capture_output=True, timeout=15
            )
        except Exception:
            pass

    # ===========================================================
    # Error Analysis (Enhanced with Reflexion + Transfer Learning)
    # ===========================================================

    def _analyze_and_fix_error(self, error_output: str, error_type: str,
                                error_phase: str, packages: Dict[str, str], 
                                python_version: str,
                                code: str, history: Dict) -> Optional[Dict[str, str]]:
        """
        Enhanced error analysis with:
        1. Cross-snippet transfer: check if we've seen this error before
        2. Regex quick fix (fast)
        3. Reflexion-enhanced LLM fix (uses accumulated reflections)
        """
        updated = dict(packages)

        # Check cross-snippet transfer first
        failing_module = self._extract_failing_module(error_output)
        pattern = self.oracle.get_error_pattern(error_type, failing_module)
        known_fix = self.oracle.get_known_fix(pattern)
        if known_fix:
            module = known_fix.get('module', '')
            version = known_fix.get('version')
            if module and module in updated and version:
                # Check if this fix was already tried
                tried = history['error_modules'].get(module, [])
                if version not in tried:
                    self.log(f"  Transfer learning: known fix for {pattern}")
                    history['error_modules'][module].append(version)
                    updated[module] = version
                    return updated
                else:
                    self.log(f"  Transfer learning: fix {module}=={version} already tried")
                    # If module failed 3+ times, skip it entirely
                    if len(tried) >= 3:
                        self.log(f"  {module} failed 3+ times, marking as unfixable")
                        history['failed_packages'].add(module)
                        if module in updated:
                            del updated[module]
                        return updated

        # Regex quick fix
        regex_fix = self._try_regex_fix(error_output, error_type, updated, history)
        if regex_fix is not None:
            return regex_fix

        # === Novel: ErrorPatternKB quick fix (FSE 2026) ===
        # 1000x faster than LLM - check curated error→fix database first
        try:
            kb_fix = self.error_kb.quick_fix(error_output, error_type, error_phase, updated, python_version)
            if kb_fix is not None:
                self.log(f"  KB quick fix applied: {kb_fix}")
                # Validate the fix isn't already tried
                for mod, ver in kb_fix.items():
                    if mod not in updated or updated[mod] != ver:
                        tried = history['error_modules'].get(mod, [])
                        if ver and ver not in tried:
                            history['error_modules'][mod].append(ver)
                return kb_fix
        except Exception as e:
            self.log(f"  KB quick fix error: {e}")

        # === Novel: ErrorPatternKB import resolution for ImportError ===
        if error_type in ('ImportError', 'ModuleNotFound'):
            try:
                fail_match = re.search(r"No module named ['\"]?(\w[\w.]*)", error_output)
                if fail_match:
                    missing_mod = fail_match.group(1).split('.')[0]
                    kb_pkg = self.error_kb.resolve_import_to_pip(missing_mod)
                    if kb_pkg and kb_pkg not in updated and kb_pkg not in history.get('failed_packages', set()):
                        exists, _, _ = self.pypi_validator.validate(kb_pkg)
                        if exists:
                            updated[kb_pkg] = ''
                            self.log(f"  KB: adding {kb_pkg} for missing {missing_mod}")
                            return updated
            except Exception:
                pass

        # Reflexion-enhanced LLM fix
        if self.use_llm and self.llm.is_available():
            # Check time budget before expensive LLM calls
            remaining = self._snippet_time_limit - (time.time() - self.start_time)
            if remaining < 70:  # Need at least 70s for LLM call + build
                self.log(f"  Time budget low ({remaining:.0f}s), skipping LLM fix")
                return None

            llm_fix = self._try_reflexion_llm_fix(
                error_output, error_type, error_phase, updated,
                python_version, code, history
            )
            if llm_fix is not None:
                # Record this fix for transfer learning
                if failing_module:
                    fix_info = {}
                    # Detect what changed
                    for k, v in llm_fix.items():
                        if k not in updated or updated[k] != v:
                            fix_info = {'module': k, 'version': v}
                            break
                    if fix_info:
                        self.oracle.record_error_fix(pattern, fix_info)
                
                return llm_fix

        return None

    def _extract_failing_module(self, error: str) -> str:
        """Extract the failing module name from error output."""
        # pip install failure
        match = re.search(r"pip install.*?(\S+)['\"]?\s*returned a non-zero", error)
        if match:
            spec = match.group(1).strip("'\"")
            return spec.split('==')[0]
        
        # Import error
        match = re.search(r"No module named ['\"]?(\w[\w.]*)", error)
        if match:
            return match.group(1).split('.')[0]
        
        # Version not found
        match = re.search(r"No matching distribution found for (\S+)", error)
        if match:
            return match.group(1).split('==')[0]
        
        return ''

    def _try_reflexion_llm_fix(self, error: str, error_type: str,
                                 error_phase: str,
                                 packages: Dict[str, str], 
                                 python_version: str,
                                 code: str, history: Dict) -> Optional[Dict[str, str]]:
        """
        Reflexion-enhanced LLM error fixing.
        Key difference from PLLM: accumulated reflections improve each attempt.
        """
        updated = dict(packages)

        # Build available versions context
        avail_context_parts = []
        for pkg in packages:
            versions_str = self.pypi_rag.get_module_versions(pkg, python_version)
            if versions_str:
                excluded = list(history['error_modules'].get(pkg, []))
                ex_text = f" (exclude: {', '.join(excluded)})" if excluded else ""
                avail_context_parts.append(f"  {pkg}: [{versions_str[:300]}]{ex_text}")
        
        available_versions = '\n'.join(avail_context_parts)

        # Get Reflexion context
        reflection_context = self.reflexion.get_reflection_context()

        # Use Reflexion-enhanced analysis for all error types
        llm_result = self.llm.analyze_error_with_reflection(
            error, error_type, packages, python_version, code,
            reflection_context=reflection_context,
            available_versions=available_versions
        )

        # Also try error-specific handlers as fallback
        if not llm_result:
            llm_result = self._try_specific_error_handler(
                error, error_type, packages, python_version, history
            )

        # Apply LLM result
        if llm_result:
            module = llm_result.get('module', '')
            version = llm_result.get('version')

            self.log(f"  LLM fix: {module} → {version}")

            if not module:
                return None

            # Handle Python version change
            if module in ('PYTHON_VERSION_CHANGE', 'python', 'Python', 'python_version'):
                self.log(f"  LLM suggests different Python version: {version}")
                # Generate reflection for this
                self.reflexion.add_attempt(
                    python_version, packages, error_type,
                    f"Python version mismatch, suggest {version}",
                    error_phase
                )
                # Record the suggestion for the outer loop to pick up
                if version and re.match(r'^\d+\.\d+$', str(version)):
                    self.reflexion.reflections.append(
                        f"STRONG VERSION HINT: Switch to Python {version}"
                    )
                return None  # Will try in outer loop

            # Validate module name
            pip_name = self.module_mapper.get_pip_name(module)
            if pip_name:
                module = pip_name

            # Skip system packages
            if module.lower() in self.SYSTEM_ONLY_PACKAGES:
                history['failed_packages'].add(module)
                return None

            # Skip already-failed packages
            if module in history['failed_packages']:
                self.log(f"  {module} already in failed packages, skipping")
                return None

            # Validate on PyPI before adding new package
            if module not in updated:
                exists, _, _ = self.pypi_validator.validate(module)
                if not exists:
                    self.log(f"  {module} not on PyPI, marking failed")
                    history['failed_packages'].add(module)
                    return None

            if version is None:
                # Remove module
                if module in updated:
                    history['failed_packages'].add(module)
                    del updated[module]
                    return updated
                return None

            # Check if version already tried
            tried = history['error_modules'].get(module, [])
            if version in tried:
                self.log(f"  Version {version} already tried for {module}")
                # Use RAG to find alternative
                versions_str = self.pypi_rag.get_versions_excluding(
                    module, python_version, tried
                )
                if versions_str:
                    new_version = self.llm.select_version(
                        module, versions_str, python_version,
                        ', '.join(tried)
                    )
                    if new_version and new_version not in tried:
                        version = new_version
                    else:
                        return None
                else:
                    return None

            # Track this version attempt
            history['error_modules'][module].append(version)

            updated[module] = version
            return updated

        return None

    def _try_specific_error_handler(self, error: str, error_type: str,
                                      packages: Dict[str, str],
                                      python_version: str,
                                      history: Dict) -> Optional[Dict]:
        """Fallback to error-type-specific LLM handlers."""
        avail_map = {}
        excluded_map = {}
        for pkg in packages:
            versions_str = self.pypi_rag.get_module_versions(pkg, python_version)
            if versions_str:
                avail_map[pkg] = versions_str
            excluded = list(history['error_modules'].get(pkg, []))
            if excluded:
                excluded_map[pkg] = excluded

        if error_type == 'VersionNotFound':
            pkg_match = re.search(
                r'(?:No matching distribution|Could not find a version).*?(\S+)',
                error
            )
            if pkg_match:
                spec = pkg_match.group(1)
                module_name = spec.split('==')[0].split('>=')[0]
                versions_str = self.pypi_rag.get_module_versions(module_name, python_version)
                excluded_str = ', '.join(history['error_modules'].get(module_name, []))
                return self.llm.analyze_version_not_found(
                    error, module_name, versions_str, excluded_str
                )

        elif error_type == 'NonZeroCode':
            return self.llm.analyze_non_zero_code(
                error, packages, avail_map, excluded_map
            )

        elif error_type == 'ImportError':
            return self.llm.analyze_import_error(
                error, packages, avail_map, excluded_map
            )

        elif error_type == 'ModuleNotFound':
            return self.llm.analyze_module_not_found(
                error, packages, python_version
            )

        elif error_type == 'SyntaxError':
            return self.llm.analyze_syntax_error(error, packages, python_version)

        elif error_type == 'DependencyConflict':
            return self.llm.analyze_dependency_conflict(error, packages)

        elif error_type == 'AttributeError':
            return self.llm.analyze_attribute_error(
                error, packages, avail_map, excluded_map, python_version
            )

        # Generic fallback
        suggestion = self.llm.analyze_generic_error(
            error, self.code, python_version, packages
        )
        if suggestion:
            self.log(f"  LLM generic: {suggestion}")
            return self._parse_generic_to_action(suggestion)

        return None

    def _parse_generic_to_action(self, suggestion: str) -> Optional[Dict]:
        """Parse generic LLM suggestion to module action dict."""
        if 'ADD_PACKAGE' in suggestion:
            parts = suggestion.split('ADD_PACKAGE:')
            if len(parts) > 1:
                spec = parts[1].strip().split()[0]
                if '==' in spec:
                    pkg, ver = spec.split('==', 1)
                    return {'module': pkg, 'version': ver}
                return {'module': spec, 'version': ''}

        if 'PIN_VERSION' in suggestion:
            parts = suggestion.split('PIN_VERSION:')
            if len(parts) > 1:
                spec = parts[1].strip().split()[0]
                if '==' in spec:
                    pkg, ver = spec.split('==', 1)
                    return {'module': pkg, 'version': ver}

        if 'CHANGE_VERSION' in suggestion:
            parts = suggestion.split('python_version=')
            if len(parts) > 1:
                ver = parts[1].strip().split()[0]
                return {'module': 'PYTHON_VERSION_CHANGE', 'version': ver}

        if 'UNFIXABLE' in suggestion:
            return None

        return None

    def _classify_error(self, error: str) -> str:
        """Classify error type with enhanced patterns."""
        if 'Could not find a version' in error:
            return 'VersionNotFound'
        elif 'No matching distribution found' in error:
            return 'VersionNotFound'
        elif 'dependency conflicts' in error or 'dependency conflict' in error:
            return 'DependencyConflict'
        elif 'DJANGO_SETTINGS_MODULE' in error:
            return 'DjangoSettings'
        elif 'ImportError' in error:
            return 'ImportError'
        elif 'ModuleNotFoundError' in error:
            return 'ModuleNotFound'
        elif 'AttributeError' in error:
            return 'AttributeError'
        elif 'InvalidVersion' in error or 'InvalidRequirement' in error:
            return 'InvalidVersion'
        elif 'non-zero code' in error or 'returned a non-zero' in error:
            return 'NonZeroCode'
        elif 'SyntaxError' in error:
            return 'SyntaxError'
        elif 'Could not build wheels' in error:
            return 'CouldNotBuildWheels'
        elif 'NameError' in error:
            return 'NameError'
        elif 'TypeError' in error:
            return 'TypeError'
        elif 'ValueError' in error:
            return 'ValueError'
        elif 'KeyError' in error:
            return 'KeyError'
        elif 'IndexError' in error:
            return 'IndexError'
        elif 'FileNotFoundError' in error or 'IOError' in error:
            return 'FileNotFoundError'
        elif 'ConnectionError' in error or 'ConnectionRefusedError' in error:
            return 'ConnectionError'
        elif 'ServerSelectionTimeoutError' in error:
            return 'ConnectionError'  # MongoDB connection timeout = deps OK
        elif 'TimeoutError' in error and 'Connection' in error:
            return 'ConnectionError'  # Connection timeouts during run = deps OK
        elif 'OSError' in error or 'PermissionError' in error:
            return 'OSError'
        elif 'RuntimeError' in error:
            return 'RuntimeError'
        elif 'ZeroDivisionError' in error:
            return 'ZeroDivisionError'
        elif 'NotImplementedError' in error:
            return 'NotImplementedError'
        elif 'Timeout' in error:
            return 'Timeout'
        else:
            return 'Unknown'

    def _extract_missing_module(self, error: str) -> Optional[str]:
        """Extract the missing module name from an ImportError/ModuleNotFoundError message."""
        match = re.search(r"No module named ['\"]?(\w[\w.]*)", error)
        if match:
            return match.group(1).split('.')[0]  # Return top-level module
        return None

    def _try_regex_fix(self, error: str, error_type: str,
                        packages: Dict[str, str],
                        history: Dict) -> Optional[Dict[str, str]]:
        """Try regex-based quick fixes."""
        updated = dict(packages)
        changed = False

        if error_type == 'DjangoSettings':
            return updated  # Django pass condition

        if error_type == 'NameError':
            return updated  # Usually not fixable - code issue, not deps

        # Runtime errors that don't need dep fixes
        if error_type in ('TypeError', 'ValueError', 'KeyError', 'IndexError',
                          'ZeroDivisionError', 'FileNotFoundError',
                          'ConnectionError', 'OSError', 'RuntimeError',
                          'NotImplementedError', 'Unknown'):
            return updated  # Not fixable through deps

        if error_type == 'VersionNotFound':
            for match in re.finditer(r'No matching distribution found for (\S+)', error):
                spec = match.group(1)
                pkg = spec.split('==')[0].split('>=')[0].split('<=')[0]
                if pkg in updated:
                    old_ver = updated.get(pkg, '')
                    if old_ver:
                        history['error_modules'][pkg].append(old_ver)
                    
                    # Check if this is a system-only package that can't be pip installed
                    if pkg.lower() in self.SYSTEM_ONLY_PACKAGES:
                        self.log(f"  {pkg}: system-only, removing")
                        history['failed_packages'].add(pkg)
                        del updated[pkg]
                        return updated
                    
                    # Check if this is a local/placeholder import
                    if pkg.lower() in self.LOCAL_IMPORT_PATTERNS:
                        self.log(f"  {pkg}: local/placeholder, removing")
                        history['failed_packages'].add(pkg)
                        del updated[pkg]
                        return updated
                    
                    # Try heuristic version first
                    heuristic_ver = self.cascade.get_heuristic_version(
                        pkg, self._current_python_version if hasattr(self, '_current_python_version') else '3.7'
                    )
                    tried = history['error_modules'].get(pkg, [])
                    if heuristic_ver and heuristic_ver not in tried:
                        self.log(f"  Heuristic fix: {pkg} → {heuristic_ver}")
                        updated[pkg] = heuristic_ver
                        history['error_modules'][pkg].append(heuristic_ver)
                        return updated
                    
                    # Try without version pin (let pip choose latest compatible)
                    if old_ver and '' not in tried:
                        self.log(f"  Trying {pkg} without version pin (was {old_ver})")
                        updated[pkg] = ''
                        history['error_modules'][pkg].append('')
                        return updated
                    
                    # On Python 2.7, remove to save time
                    py_ver = getattr(self, '_current_python_version', '3.7')
                    if py_ver.startswith('2'):
                        self.log(f"  {pkg}: version not found on Python 2.7, removing")
                        history['failed_packages'].add(pkg)
                        del updated[pkg]
                        return updated
                    return None  # Fall through to LLM

        if error_type == 'NonZeroCode':
            match = re.search(
                r"pip install.*?(\S+)['\"]?\s*returned a non-zero", error
            )
            if match:
                spec = match.group(1).strip("'\"")
                pkg = spec.split('==')[0]
                if pkg in updated:
                    old_ver = updated.get(pkg, '')
                    if old_ver:
                        history['error_modules'][pkg].append(old_ver)
                    # Heavy packages that fail once → mark as unfixable immediately
                    heavy_pkgs = {'tensorflow', 'torch', 'pytorch', 'scipy', 'mxnet',
                                  'caffe', 'theano', 'cntk', 'paddlepaddle'}
                    if pkg.lower() in heavy_pkgs:
                        self.log(f"  {pkg} is heavy and failed, marking as unfixable")
                        history['failed_packages'].add(pkg)
                        del updated[pkg]
                        return updated
                    # If package failed 3+ times, mark as unfixable
                    if len(history['error_modules'].get(pkg, [])) >= 3:
                        self.log(f"  {pkg} failed 3+ times, marking as unfixable")
                        history['failed_packages'].add(pkg)
                        del updated[pkg]
                        return updated
                    # Try heuristic version before expensive LLM call
                    heuristic_ver = self.cascade.get_heuristic_version(
                        pkg, self._current_python_version if hasattr(self, '_current_python_version') else '3.7'
                    )
                    tried = history['error_modules'].get(pkg, [])
                    if heuristic_ver and heuristic_ver not in tried:
                        self.log(f"  Heuristic fix: {pkg} → {heuristic_ver}")
                        updated[pkg] = heuristic_ver
                        history['error_modules'][pkg].append(heuristic_ver)
                        return updated
                    # On Python 2.7, most packages that fail NonZeroCode won't
                    # have alternative versions. Remove package to save time.
                    py_ver = getattr(self, '_current_python_version', '3.7')
                    if py_ver.startswith('2'):
                        self.log(f"  {pkg} failed on Python 2.7, removing to save time")
                        history['failed_packages'].add(pkg)
                        del updated[pkg]
                        return updated
                    # Check time budget before falling through to LLM
                    remaining = self._snippet_time_limit - (time.time() - self.start_time) if hasattr(self, '_snippet_time_limit') else 300
                    if remaining < 80:
                        self.log(f"  Time budget low ({remaining:.0f}s), removing {pkg}")
                        history['failed_packages'].add(pkg)
                        del updated[pkg]
                        return updated
                    return None  # Fall through to LLM

        if error_type == 'CouldNotBuildWheels':
            for match in re.finditer(r'Could not build wheels for (\w[\w-]*)', error):
                pkg = match.group(1)
                if pkg in updated:
                    # Before giving up, try version cascade for Py2.7
                    if history.get('python_version', '').startswith('2'):
                        cascade = self.PY27_VERSION_CASCADE.get(pkg.lower(), [])
                        tried = history.get('tried_versions', {}).get(pkg, set())
                        current = updated.get(pkg, '')
                        if current:
                            tried.add(current)
                        for fallback_ver in cascade:
                            if fallback_ver not in tried:
                                self.log(f"  Version cascade: {pkg} → trying {fallback_ver}")
                                updated[pkg] = fallback_ver
                                if 'tried_versions' not in history:
                                    history['tried_versions'] = {}
                                if pkg not in history['tried_versions']:
                                    history['tried_versions'][pkg] = set()
                                history['tried_versions'][pkg].add(fallback_ver)
                                changed = True
                                return updated if changed else None
                    # No more versions to try — remove the package
                    history['failed_packages'].add(pkg)
                    del updated[pkg]
                    changed = True

        if error_type in ('ImportError', 'ModuleNotFound'):
            for match in re.finditer(r"No module named ['\"]?(\w[\w.]*)", error):
                module = match.group(1).split('.')[0]
                if module.lower() in ('no', 'the', 'a'):
                    continue
                # Check if it's a system-only package
                if module.lower() in self.SYSTEM_ONLY_PACKAGES:
                    history['failed_packages'].add(module)
                    continue
                pip_name = self.module_mapper.get_pip_name(module)
                if pip_name and pip_name not in updated and pip_name not in history['failed_packages']:
                    exists, _, _ = self.pypi_validator.validate(pip_name)
                    if exists:
                        return None  # Let LLM pick version
                    else:
                        history['failed_packages'].add(pip_name)

        return updated if changed else None

    # ===========================================================
    # Utilities
    # ===========================================================

    def _learn_success(self, gist_id: str, code: str, packages: Dict[str, str], py_ver: str, duration: float):
        """Record successful resolution for novel self-evolving memory."""
        if not self.use_level1:
            return
        try:
            imports = list(self.module_mapper.extract_imports(code))
            error_hist = self.reflexion.get_history() if hasattr(self, 'reflexion') and hasattr(self.reflexion, 'get_history') else []
            self.evolving_memory.learn_from_success(
                gist_id=gist_id,
                python_version=py_ver,
                packages=packages,
                imports=imports,
                duration=duration,
                error_history=error_hist
            )
            for imp in imports:
                for pkg in packages:
                    if imp.lower() in pkg.lower() or pkg.lower() in imp.lower():
                        self.error_kb.learn_import_resolution(imp, pkg)
        except Exception:
            pass

    def _get_version_range(self, base_version: str, search_range: int) -> List[str]:
        """Generate list of Python versions to try, prioritizing base version."""
        versions = ['2.7', '3.5', '3.6', '3.7', '3.8', '3.9', '3.10', '3.11']

        if base_version not in versions:
            return [base_version]

        idx = versions.index(base_version)
        start = max(0, idx - search_range)
        end = min(len(versions), idx + search_range + 1)

        result = versions[start:end]
        if base_version in result:
            result.remove(base_version)
            result.insert(0, base_version)

        # Always include at least one fallback for Python 2↔3 mismatch
        if search_range == 0 and base_version.startswith('2'):
            # Python 2 code might actually need 3.x if detection was wrong
            if '3.6' not in result:
                result.append('3.6')
        elif search_range == 0 and base_version.startswith('3'):
            # Python 3 code might actually be Python 2
            if '2.7' not in result:
                result.append('2.7')

        return result

    def _last_error_line(self, error: str) -> str:
        """Extract last meaningful error line."""
        lines = [l for l in error.strip().split('\n') if l.strip()]
        return lines[-1] if lines else "Unknown error"

    # PLLM-compatible result type mapping
    _RUNTIME_PASS_RESULT_MAP = {
        'NameError': 'OtherPass', 'TypeError': 'OtherPass',
        'ValueError': 'OtherPass', 'KeyError': 'OtherPass',
        'IndexError': 'OtherPass', 'ZeroDivisionError': 'OtherPass',
        'FileNotFoundError': 'OtherPass', 'PermissionError': 'OtherPass',
        'OSError': 'OtherPass', 'IOError': 'OtherPass',
        'ConnectionError': 'OtherPass', 'ConnectionRefusedError': 'OtherPass',
        'RuntimeError': 'OtherPass', 'NotImplementedError': 'OtherPass',
        'Unknown': 'OtherPass', 'AttributeError': 'OtherPass',
        'RunTimeout': 'OtherPass',
        'DjangoSettings': 'DjangoPass',
    }

    def _map_result_type(self, error_type: str, success: bool) -> str:
        """Map internal error type to PLLM-compatible result type."""
        if success and not error_type:
            return 'None'
        if success:
            return self._RUNTIME_PASS_RESULT_MAP.get(error_type, 'OtherPass')
        # Failure: keep original error type
        return error_type or 'Unknown'

    def _result(self, success: bool, **kwargs) -> Dict:
        """Create result dictionary."""
        result_type = kwargs.get('result_type', '')
        if not result_type:
            result_type = 'None' if success else 'Unknown'
        return {
            'success': success,
            'python_version': kwargs.get('python_version', ''),
            'modules': kwargs.get('modules', {}),
            'duration': kwargs.get('duration', time.time() - self.start_time),
            'error': kwargs.get('error', ''),
            'result_type': result_type,
            'start_time': getattr(self, 'start_time', time.time()),
        }
