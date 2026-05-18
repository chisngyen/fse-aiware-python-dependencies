"""
ConstraintStore — Persistent session memory of infeasible package-version assignments.

Novelty: Converts Docker build/runtime failures into reusable solver constraints
that prune the search space across all snippets in a session.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, FrozenSet, Optional, Set, Tuple


class ConstraintType(Enum):
    HARD = "hard"    # Certain from metadata (e.g., requires-python marker fails)
    SOFT = "soft"    # Observed from Docker failure (may be context-dependent)


@dataclass
class InfeasibleRecord:
    package: str
    version: str
    python_version: str
    error_type: ConstraintType
    error_signature: str
    confidence: float
    count: int = 1


class ConstraintStore:
    """
    Session-scoped memory of infeasible package-version-python assignments.

    Hard constraints: added when PyPI metadata proves incompatibility.
    Soft constraints: added from Docker failures; require `soft_threshold`
    observations before being treated as infeasible.
    Combo constraints: specific multi-package assignments that failed together.
    """

    def __init__(self, soft_threshold: int = 2):
        self.soft_threshold = soft_threshold
        # (package, version, python_version) → InfeasibleRecord
        self._records: Dict[Tuple[str, str, str], InfeasibleRecord] = {}
        # frozenset of (pkg, ver) pairs + python_version → error_signature
        self._combo_records: Dict[Tuple[FrozenSet, str], str] = {}
        # (package, python_version) → exclusive upper bound version string
        # e.g. keras 2.3.0 removed TimeDistributedDense → upper_bound = "2.3.0"
        self._upper_bounds: Dict[Tuple[str, str], str] = {}

    def add(self, package: str, version: str, python_version: str,
            error_type: ConstraintType, error_signature: str,
            confidence: float = 1.0) -> None:
        key = (package.lower(), version, python_version)
        if key in self._records:
            self._records[key].count += 1
            self._records[key].confidence = max(self._records[key].confidence, confidence)
        else:
            self._records[key] = InfeasibleRecord(
                package=package, version=version, python_version=python_version,
                error_type=error_type, error_signature=error_signature,
                confidence=confidence, count=1,
            )

    def add_combo(self, packages: Dict[str, str], python_version: str,
                  error_signature: str, confidence: float = 0.8) -> None:
        key_set = frozenset((k.lower(), v) for k, v in packages.items() if v)
        self._combo_records[(key_set, python_version)] = error_signature

    def is_infeasible(self, package: str, version: str, python_version: str) -> bool:
        key = (package.lower(), version, python_version)
        record = self._records.get(key)
        if record is None:
            return False
        if record.error_type == ConstraintType.HARD:
            return True
        return record.count >= self.soft_threshold

    def is_combo_infeasible(self, packages: Dict[str, str], python_version: str) -> bool:
        key_set = frozenset((k.lower(), v) for k, v in packages.items() if v)
        return (key_set, python_version) in self._combo_records

    def add_upper_bound(self, package: str, python_version: str, exclusive_upper: str) -> None:
        """Record that `package >= exclusive_upper` is infeasible (API removed)."""
        key = (package.lower(), python_version)
        existing = self._upper_bounds.get(key)
        if existing is None or self._version_lt(exclusive_upper, existing):
            self._upper_bounds[key] = exclusive_upper

    def get_upper_bound(self, package: str, python_version: str) -> Optional[str]:
        """Return the exclusive upper bound for this package, or None."""
        return self._upper_bounds.get((package.lower(), python_version))

    def is_above_upper_bound(self, package: str, version: str, python_version: str) -> bool:
        """Return True if version >= upper_bound (i.e., API already removed)."""
        ub = self.get_upper_bound(package, python_version)
        if not ub or not version:
            return False
        return not self._version_lt(version, ub)

    @staticmethod
    def _version_lt(a: str, b: str) -> bool:
        """Return True if version a < b."""
        try:
            from packaging.version import Version
            return Version(a) < Version(b)
        except Exception:
            return a < b

    def get_infeasible_versions(self, package: str, python_version: str) -> Set[str]:
        return {
            rec.version
            for (pkg, ver, pyver), rec in self._records.items()
            if pkg == package.lower() and pyver == python_version
            and self.is_infeasible(pkg, ver, pyver)
        }

    def stats(self) -> Dict:
        hard = sum(1 for r in self._records.values() if r.error_type == ConstraintType.HARD)
        soft = sum(1 for r in self._records.values() if r.error_type == ConstraintType.SOFT)
        return {'hard': hard, 'soft': soft, 'combos': len(self._combo_records), 'upper_bounds': len(self._upper_bounds)}
