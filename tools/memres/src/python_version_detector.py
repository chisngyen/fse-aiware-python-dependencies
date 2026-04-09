"""
Smart Python Version Detector

Analyzes Python source code to determine the correct Python version.
Uses shebang, syntax patterns, and import analysis.
"""

import re


class PythonVersionDetector:

    # Python 2 specific patterns with weights
    PY2_INDICATORS = {
        r'#!/usr/bin/env python2': 100,
        r'#!/usr/bin/python2': 100,
        r'\bprint\s+["\']': 15,        # print "hello" (statement)
        r'\bprint\s+[^(]': 10,         # print something (no parentheses)
        r'\.iteritems\(\)': 15,
        r'\.itervalues\(\)': 15,
        r'\.iterkeys\(\)': 15,
        r'\bxrange\s*\(': 15,
        r'\.has_key\s*\(': 15,
        r'\bexecfile\s*\(': 15,
        r'\braw_input\s*\(': 15,
        r'\bunicode\s*\(': 10,
        r'\bbasestring\b': 10,
        r'\blong\b': 5,
        r'from\s+__future__\s+import': 5,  # compatibility, but signals py2
        r'\burllib2\b': 20,
        r'\burlparse\b': 15,
        r'\bConfigParser\b': 10,
        r'\bQueue\b': 5,
        r'\bSocketServer\b': 10,
        r'\bSimpleHTTPServer\b': 15,
        r'\bBaseHTTPServer\b': 15,
        r'\bhttplib\b': 15,
        r'\bcookielib\b': 10,
        r'\bHTMLParser\b': 5,
        r'except\s+\w+\s*,\s*\w+': 15,  # except Exception, e:
        r'raise\s+\w+\s*,': 10,          # raise Exception, "msg"
    }

    # Python 3 specific patterns with weights
    PY3_INDICATORS = {
        r'#!/usr/bin/env python3': 100,
        r'#!/usr/bin/python3': 100,
        r'\basync\s+def\b': 20,
        r'\bawait\s+': 20,
        r'\basync\s+for\b': 20,
        r'\basync\s+with\b': 20,
        r'f"[^"]*\{': 15,              # f-strings
        r"f'[^']*\{": 15,              # f-strings
        r'\bnonlocal\s+': 10,
        r':\s*\w+\s*=': 5,             # type hints (x: int = 5)
        r'->\s*\w+': 5,                # return type hints
        r'\burllib\.request\b': 15,
        r'\burllib\.parse\b': 15,
        r'\bconfigparser\b': 10,
        r'\bpathlib\b': 10,
        r'\bdataclasses\b': 15,
        r'from\s+typing\s+import': 10,
        r'\bsecrets\b': 5,
        r'\bbreakpoint\s*\(': 10,
        r'print\s*\(': 3,              # print() - works in both but more py3
    }

    # Python version to use for specific python versions
    PYTHON_VERSIONS = {
        '2': '2.7',
        '2.7': '2.7',
        '2.6': '2.7',
        '3': '3.8',
        '3.5': '3.7',
        '3.6': '3.7',
        '3.7': '3.7',
        '3.8': '3.8',
        '3.9': '3.8',
        '3.10': '3.8',
        '3.11': '3.8',
        '3.12': '3.8',
    }

    def detect(self, code: str) -> str:
        """
        Detect Python version from source code.
        Returns version string like '2.7', '3.7', '3.8'
        """
        py2_score = 0
        py3_score = 0

        for pattern, weight in self.PY2_INDICATORS.items():
            if re.search(pattern, code):
                py2_score += weight

        for pattern, weight in self.PY3_INDICATORS.items():
            if re.search(pattern, code):
                py3_score += weight

        if py2_score > py3_score:
            return '2.7'
        elif py3_score > py2_score:
            return '3.8'
        else:
            return '3.8'  # Default to 3.8

    def detect_with_confidence(self, code: str) -> tuple:
        """
        Returns (version, confidence) where confidence is 'high', 'medium', or 'low'
        """
        py2_score = 0
        py3_score = 0

        for pattern, weight in self.PY2_INDICATORS.items():
            if re.search(pattern, code):
                py2_score += weight

        for pattern, weight in self.PY3_INDICATORS.items():
            if re.search(pattern, code):
                py3_score += weight

        total = py2_score + py3_score
        if total == 0:
            return '3.8', 'low'

        diff = abs(py2_score - py3_score)
        version = '2.7' if py2_score > py3_score else '3.8'

        if diff > 30:
            return version, 'high'
        elif diff > 10:
            return version, 'medium'
        else:
            return version, 'low'
