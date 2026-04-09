"""
Module Mapper

Maps module names to correct pip package names.
Handles Python 2→3 migrations, built-in detection, and system packages.
"""

import re
from typing import Optional, List, Set


class ModuleMapper:

    # Python 2 import name → Python 3 import name
    PY2_TO_PY3_IMPORTS = {
        'urllib2': 'urllib.request',
        'urlparse': 'urllib.parse',
        'ConfigParser': 'configparser',
        'Queue': 'queue',
        'SocketServer': 'socketserver',
        'SimpleHTTPServer': 'http.server',
        'BaseHTTPServer': 'http.server',
        'CGIHTTPServer': 'http.server',
        'Cookie': 'http.cookies',
        'cookielib': 'http.cookiejar',
        'htmlentitydefs': 'html.entities',
        'HTMLParser': 'html.parser',
        'httplib': 'http.client',
        'repr': 'reprlib',
        'Tkinter': 'tkinter',
        'tkFileDialog': 'tkinter.filedialog',
        'tkMessageBox': 'tkinter.messagebox',
        'tkColorChooser': 'tkinter.colorchooser',
        'tkFont': 'tkinter.font',
        'ScrolledText': 'tkinter.scrolledtext',
        'thread': '_thread',
        'cPickle': 'pickle',
        'cStringIO': 'io',
        'StringIO': 'io',
        'dbm': 'dbm',
        'commands': 'subprocess',
        'UserDict': 'collections',
        'UserList': 'collections',
        'UserString': 'collections',
    }

    # Import name → pip package name
    # Combined from our mapping + PLLM's module_link.json for maximum coverage
    IMPORT_TO_PACKAGE = {
        # Core mappings
        'cv2': 'opencv-python',
        'sklearn': 'scikit-learn',
        'yaml': 'pyyaml',
        'Image': 'Pillow',
        'PIL': 'Pillow',
        'pil': 'pillow',
        'bs4': 'beautifulsoup4',
        'serial': 'pyserial',
        'usb': 'pyusb',
        'wx': 'wxPython',
        'gi': 'pygobject',
        'Crypto': 'pycryptodome',
        'crypto': 'pycryptodome',
        'cryptodome': 'pycryptodomex',
        'dateutil': 'python-dateutil',
        'dotenv': 'python-dotenv',
        'load_dotenv': 'python-dotenv',
        'jwt': 'PyJWT',
        'magic': 'python-magic',
        'psycopg2': 'psycopg2-binary',
        'attr': 'attrs',
        'skimage': 'scikit-image',
        'Bio': 'biopython',
        'bio': 'biopython',
        'lxml': 'lxml',
        'docx': 'python-docx',
        'pptx': 'python-pptx',
        'git': 'gitpython',
        'Levenshtein': 'python-Levenshtein',
        'dialog': 'pythondialog',
        'memcache': 'python-memcached',
        'MySQLdb': 'mysqlclient',
        'mysqldb': 'mysqlclient',
        'Tkinter': 'tkinter',
        'flask_restful': 'flask-restful',
        'flask_sqlalchemy': 'flask-sqlalchemy',
        'flask_login': 'flask-login',
        'flask_wtf': 'flask-wtf',
        'pymongo': 'pymongo',
        'bson': 'pymongo',  # bson is bundled with pymongo, standalone bson conflicts
        'tweepy': 'tweepy',
        'mechanize': 'mechanize',
        'gevent': 'gevent',
        'celery': 'celery',
        'zmq': 'pyzmq',
        'OpenSSL': 'pyopenssl',
        'openssl': 'pyopenssl',
        # From PLLM module_link.json
        'apiclient': 'google-api-python-client',
        'googleapiclient': 'google-api-python-client',
        'dns': 'dnspython3',
        'editor': 'python-editor',
        'ffmpeg': 'python-ffmpeg',
        'freetype': 'freetype-py',
        'github': 'pygithub',
        'jose': 'python-jose',
        'mega': 'python-mega',
        'messaging': 'python-messaging',
        'more_itertools': 'more-itertools',
        'multipart': 'python-multipart',
        'nomad': 'python-nomad',
        'nova': 'python-novaclient',
        'objc': 'pyobjc',
        'osgeo': 'gdal',
        'paho': 'paho-mqtt',
        'mosquitto': 'paho-mqtt',
        'chess': 'python-chess',
        'daemon': 'python-daemon',
        'twitter': 'python-twitter',
        'visa': 'pyvisa',
        'web': 'web-py',
        'wordpress_xmlrpc': 'python-wordpress-xmlrpc',
        'xmpp': 'xmpppy',
        'socks': 'pysocks',
        'jnius': 'pyjnius',
        # Django ecosystem
        'rest_framework': 'djangorestframework',
        'tastypie': 'django-tastypie',
        'guardian': 'django-guardian',
        'haystack': 'django-haystack',
        'debug_toolbar': 'django-debug-toolbar',
        'compressor': 'django-compressor',
        'storages': 'django-storages',
        'registration': 'django-registration',
        'imagekit': 'django-imagekit',
        'pipeline': 'django-pipeline',
        'social_auth': 'django-social-auth',
        'cms': 'django-cms',
    }

    # Modules that are part of Python stdlib (no pip install needed)
    STDLIB_MODULES = {
        # Common stdlib
        'abc', 'aifc', 'argparse', 'array', 'ast', 'asynchat', 'asyncio',
        'asyncore', 'atexit', 'audioop', 'base64', 'bdb', 'binascii',
        'binhex', 'bisect', 'builtins', 'bz2', 'calendar', 'cgi', 'cgitb',
        'chunk', 'cmath', 'cmd', 'code', 'codecs', 'codeop', 'collections',
        'colorsys', 'compileall', 'concurrent', 'configparser', 'contextlib',
        'contextvars', 'copy', 'copyreg', 'cProfile', 'crypt', 'csv',
        'ctypes', 'curses', 'dataclasses', 'datetime', 'dbm', 'decimal',
        'difflib', 'dis', 'distutils', 'doctest', 'email', 'encodings',
        'enum', 'errno', 'faulthandler', 'fcntl', 'filecmp', 'fileinput',
        'fnmatch', 'formatter', 'fractions', 'ftplib', 'functools', 'gc',
        'getopt', 'getpass', 'gettext', 'glob', 'grp', 'gzip', 'hashlib',
        'heapq', 'hmac', 'html', 'http', 'idlelib', 'imaplib', 'imghdr',
        'imp', 'importlib', 'inspect', 'io', 'ipaddress', 'itertools',
        'json', 'keyword', 'lib2to3', 'linecache', 'locale', 'logging',
        'lzma', 'mailbox', 'mailcap', 'marshal', 'math', 'mimetypes',
        'mmap', 'modulefinder', 'multiprocessing', 'netrc', 'nis', 'nntplib',
        'numbers', 'operator', 'optparse', 'os', 'ossaudiodev', 'parser',
        'pathlib', 'pdb', 'pickle', 'pickletools', 'pipes', 'pkgutil',
        'platform', 'plistlib', 'poplib', 'posix', 'posixpath', 'pprint',
        'profile', 'pstats', 'pty', 'pwd', 'py_compile', 'pyclbr',
        'pydoc', 'queue', 'quopri', 'random', 're', 'readline', 'reprlib',
        'resource', 'rlcompleter', 'runpy', 'sched', 'secrets', 'select',
        'selectors', 'shelve', 'shlex', 'shutil', 'signal', 'site',
        'smtpd', 'smtplib', 'sndhdr', 'socket', 'socketserver', 'sqlite3',
        'ssl', 'stat', 'statistics', 'string', 'stringprep', 'struct',
        'subprocess', 'sunau', 'symtable', 'sys', 'sysconfig', 'syslog',
        'tabnanny', 'tarfile', 'telnetlib', 'tempfile', 'termios', 'test',
        'textwrap', 'threading', 'time', 'timeit', 'tkinter', 'token',
        'tokenize', 'trace', 'traceback', 'tracemalloc', 'tty', 'turtle',
        'turtledemo', 'types', 'typing', 'unicodedata', 'unittest', 'urllib',
        'uu', 'uuid', 'venv', 'warnings', 'wave', 'weakref', 'webbrowser',
        'winreg', 'winsound', 'wsgiref', 'xdrlib', 'xml', 'xmlrpc',
        'zipapp', 'zipfile', 'zipimport', 'zlib',
        # Python 2 stdlib additions
        'urllib2', 'urlparse', 'ConfigParser', 'Queue', 'SocketServer',
        'SimpleHTTPServer', 'BaseHTTPServer', 'httplib', 'cookielib',
        'HTMLParser', 'htmlentitydefs', 'thread', 'cPickle', 'cStringIO',
        'StringIO', 'commands', 'UserDict', 'UserList', 'UserString',
        'Tkinter', 'tkFileDialog', 'tkMessageBox', 'repr',
    }

    # System-only packages (require apt-get, not pip)
    SYSTEM_ONLY = {
        'gtk', 'appindicator', 'dbus', 'apt', 'apt_pkg', 'glib',
        'gobject', 'pynotify', 'indicate', 'unity', 'wnck',
        'RPi', 'rpi', 'pigpio', 'wiringpi', 'smbus', 'spidev',  # Raspberry Pi
        'c4d', 'maya', 'pyqt4', 'sip',  # 3D/UI frameworks
        'bpy', 'rhinoscriptsyntax', 'nuke', 'houdini', 'hou',  # 3D software
        'sublime', 'xbmc', 'kodi',  # editors/media
    }

    def is_stdlib(self, module: str) -> bool:
        """Check if module is part of Python standard library."""
        base_module = module.split('.')[0]
        return base_module in self.STDLIB_MODULES

    def is_system_only(self, module: str) -> bool:
        """Check if module requires system installation (not pip)."""
        base_module = module.split('.')[0]
        return base_module in self.SYSTEM_ONLY

    def get_pip_name(self, import_name: str) -> Optional[str]:
        """Convert import name to pip package name."""
        if import_name in self.IMPORT_TO_PACKAGE:
            return self.IMPORT_TO_PACKAGE[import_name]
        return import_name

    def map_module(self, module: str, python_version: str) -> Optional[str]:
        """
        Map a module to its correct pip package name.

        Returns:
            - None if module is stdlib or system-only (no install needed)
            - Correct pip package name otherwise
        """
        base_module = module.split('.')[0]

        # Skip stdlib
        if self.is_stdlib(base_module):
            return None

        # Skip system-only
        if self.is_system_only(base_module):
            return None

        # Map import name to pip name
        pip_name = self.get_pip_name(base_module)

        return pip_name

    def extract_imports(self, code: str) -> List[str]:
        """Extract all import module names from Python source code."""
        imports = set()

        # Match: import X, from X import Y
        for match in re.finditer(r'^import\s+(\S+)', code, re.MULTILINE):
            mod = match.group(1).split(',')[0].split('.')[0].strip()
            if mod:
                imports.add(mod)

        for match in re.finditer(r'^from\s+(\S+)\s+import', code, re.MULTILINE):
            mod = match.group(1).split('.')[0].strip()
            if mod and mod != '__future__':
                imports.add(mod)

        return list(imports)

    def get_installable_packages(self, code: str, python_version: str) -> List[str]:
        """
        Extract imports from code and return list of pip-installable packages.
        Filters out stdlib, system-only, and maps to correct pip names.
        """
        imports = self.extract_imports(code)
        packages = []

        for imp in imports:
            mapped = self.map_module(imp, python_version)
            if mapped is not None:
                packages.append(mapped)

        # Add implicit dependencies
        final = set(packages)
        for pkg in list(final):
            for dep in self.IMPLICIT_DEPS.get(pkg, []):
                final.add(dep)
        return list(final)

    # Packages that implicitly need other packages
    IMPLICIT_DEPS = {
        'keras': ['tensorflow'],
        'flask-restful': ['flask'],
        'flask-sqlalchemy': ['flask', 'sqlalchemy'],
        'flask-login': ['flask'],
        'flask-wtf': ['flask'],
        'celery': ['kombu'],
    }
