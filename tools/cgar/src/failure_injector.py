"""
FailureInjector — Stage 2.7

Converts Docker build/runtime failure logs into ConstraintStore records.

Classification:
  HARD  — Python version marker violations, no-matching-distribution errors.
          These are certain: the package CANNOT work in this configuration.
  SOFT  — ImportError, NonZeroCode, DLL errors.
          These are likely incompatible but may be context-dependent.
          Require soft_threshold observations to become infeasible.

Combo recording: For ImportError (runtime failure), records the entire
package-version assignment as a bad combo, since the error may be caused
by interactions between packages rather than a single package.
"""

import re
from typing import Dict, Optional, Tuple

from .constraint_store import ConstraintStore, ConstraintType


# Patterns that indicate Python version incompatibility (HARD)
_HARD_PATTERNS = [
    r"requires a different Python",
    r"not in '>=",
    r"not in '~=",
    r"Could not find a version that satisfies",
    r"No matching distribution found",
    r"python_requires",
]

# Patterns that indicate runtime import failure (SOFT)
_SOFT_PATTERNS = [
    r"ImportError",
    r"ModuleNotFoundError",
    r"DLL load failed",
    r"cannot import name",
]


def normalize_error_signature(error_log: str) -> str:
    """
    Produce a stable signature from an error log by removing line numbers,
    memory addresses, and file paths.
    """
    sig = error_log[:500]  # Cap length
    sig = re.sub(r'line \d+', 'line N', sig)
    sig = re.sub(r'0x[0-9a-fA-F]+', '0xADDR', sig)
    sig = re.sub(r'/[^\s]+\.py', 'FILE.py', sig)
    sig = re.sub(r'\\[^\s]+\.py', 'FILE.py', sig)
    sig = ' '.join(sig.split())  # Normalize whitespace
    return sig


def classify_error(error_log: str,
                   assignment: Dict[str, str]) -> Tuple[ConstraintType, str]:
    """
    Classify an error log as HARD or SOFT constraint.
    Returns (ConstraintType, normalized_signature).
    """
    sig = normalize_error_signature(error_log)
    for pattern in _HARD_PATTERNS:
        if re.search(pattern, error_log, re.IGNORECASE):
            return ConstraintType.HARD, sig
    return ConstraintType.SOFT, sig


class FailureInjector:
    """
    Converts Docker failure information into ConstraintStore records.

    Called after each failed Docker build/test cycle in the agentic loop.
    """

    def __init__(self, store: ConstraintStore):
        self.store = store

    def inject(self, assignment: Dict[str, str], python_version: str,
               error_log: str, error_type: str) -> None:
        """
        Inject failure constraints from a failed Docker attempt.

        For HARD errors: record each package-version as individually infeasible.
        For SOFT errors (ImportError etc.): record the combo + increment
        per-package soft counts.
        """
        constraint_type, sig = classify_error(error_log, assignment)

        if constraint_type == ConstraintType.HARD:
            # Find which specific package the error is about
            culprit = self._identify_culprit(error_log, assignment)
            if culprit:
                self.store.add(
                    culprit, assignment.get(culprit, ''), python_version,
                    ConstraintType.HARD, sig, confidence=1.0
                )
            else:
                # Can't identify culprit → mark all as soft
                for pkg, ver in assignment.items():
                    if ver:
                        self.store.add(pkg, ver, python_version,
                                       ConstraintType.SOFT, sig, confidence=0.6)
        else:
            # SOFT: record combo + per-package soft
            versioned = {k: v for k, v in assignment.items() if v}
            if versioned:
                self.store.add_combo(versioned, python_version, sig, confidence=0.8)
            for pkg, ver in assignment.items():
                if ver:
                    self.store.add(pkg, ver, python_version,
                                   ConstraintType.SOFT, sig, confidence=0.5)

    def _identify_culprit(self, error_log: str, assignment: Dict[str, str]) -> Optional[str]:
        """Try to identify which specific package caused the error."""
        for pkg in assignment:
            if re.search(re.escape(pkg), error_log, re.IGNORECASE):
                return pkg
        return None
