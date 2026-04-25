import pytest
from src.failure_injector import FailureInjector, classify_error
from src.constraint_store import ConstraintStore, ConstraintType


def test_requires_python_violation_is_hard():
    error_log = "ERROR: Package 'tensorflow' requires a different Python: 2.7.18 not in '>=3.6'"
    assignment = {'tensorflow': '1.15.5'}
    constraint_type, sig = classify_error(error_log, assignment)
    assert constraint_type == ConstraintType.HARD


def test_import_error_is_soft():
    error_log = "ImportError: cannot import name 'reduce' from 'functools'"
    assignment = {'keras': '2.2.4'}
    constraint_type, sig = classify_error(error_log, assignment)
    assert constraint_type == ConstraintType.SOFT


def test_no_matching_distribution_is_hard():
    error_log = "ERROR: Could not find a version that satisfies the requirement numpy==99.0.0"
    assignment = {'numpy': '99.0.0'}
    constraint_type, sig = classify_error(error_log, assignment)
    assert constraint_type == ConstraintType.HARD


def test_inject_stores_per_package_constraint():
    store = ConstraintStore()
    injector = FailureInjector(store)
    assignment = {'tensorflow': '1.15.5', 'keras': '2.2.4'}
    error_log = "ERROR: Package 'tensorflow' requires a different Python: 2.7.18 not in '>=3.6'"
    injector.inject(assignment, python_version='2.7', error_log=error_log, error_type='NonZeroCode')
    # tensorflow should be hard-constrained for 2.7
    assert store.is_infeasible('tensorflow', '1.15.5', '2.7')


def test_inject_stores_combo_for_import_error():
    store = ConstraintStore(soft_threshold=1)
    injector = FailureInjector(store)
    assignment = {'numpy': '1.16.6', 'keras': '2.2.4', 'tensorflow': '1.15.5'}
    error_log = "ImportError: DLL load failed"
    injector.inject(assignment, python_version='2.7', error_log=error_log, error_type='ImportError')
    assert store.is_combo_infeasible(assignment, '2.7')


def test_normalize_error_signature_consistent():
    from src.failure_injector import normalize_error_signature
    log1 = "ImportError: No module named 'cv2' at line 5"
    log2 = "ImportError: No module named 'cv2' at line 9"
    # Same error different line → same signature
    assert normalize_error_signature(log1) == normalize_error_signature(log2)
