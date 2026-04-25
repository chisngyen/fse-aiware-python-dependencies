import pytest
from src.constraint_store import ConstraintStore, InfeasibleRecord, ConstraintType


def test_add_and_query_hard_constraint():
    store = ConstraintStore()
    store.add(
        package='tensorflow', version='1.15.5', python_version='2.7',
        error_type=ConstraintType.HARD, error_signature='requires-python >=3.6',
        confidence=1.0
    )
    assert store.is_infeasible('tensorflow', '1.15.5', '2.7')


def test_soft_constraint_below_threshold_not_infeasible():
    store = ConstraintStore(soft_threshold=3)
    store.add(
        package='numpy', version='1.16.6', python_version='3.8',
        error_type=ConstraintType.SOFT, error_signature='ImportError: numpy',
        confidence=0.7
    )
    # Only 1 observation, below threshold of 3
    assert not store.is_infeasible('numpy', '1.16.6', '3.8')


def test_soft_constraint_above_threshold_is_infeasible():
    store = ConstraintStore(soft_threshold=2)
    for _ in range(2):
        store.add(
            package='numpy', version='1.16.6', python_version='3.8',
            error_type=ConstraintType.SOFT, error_signature='ImportError: numpy',
            confidence=0.7
        )
    assert store.is_infeasible('numpy', '1.16.6', '3.8')


def test_combo_constraint():
    store = ConstraintStore()
    combo = {'tensorflow': '1.15.5', 'keras': '2.2.4', 'numpy': '1.16.6'}
    store.add_combo(combo, python_version='2.7', error_signature='ImportError', confidence=0.9)
    assert store.is_combo_infeasible(combo, '2.7')


def test_get_infeasible_versions_for_package():
    store = ConstraintStore()
    store.add('numpy', '1.14.0', '2.7', ConstraintType.HARD, 'build-fail', 1.0)
    store.add('numpy', '1.15.0', '2.7', ConstraintType.HARD, 'build-fail', 1.0)
    bad = store.get_infeasible_versions('numpy', '2.7')
    assert '1.14.0' in bad
    assert '1.15.0' in bad


def test_different_python_version_not_infeasible():
    store = ConstraintStore()
    store.add('scipy', '1.2.3', '2.7', ConstraintType.HARD, 'build-fail', 1.0)
    assert not store.is_infeasible('scipy', '1.2.3', '3.8')
