import pytest
from unittest.mock import patch, MagicMock
from src.candidate_graph_builder import CandidateGraphBuilder, PackageConstraint


NUMPY_PYPI_RESPONSE = {
    "info": {"name": "numpy", "requires_python": ">=3.9"},
    "releases": {
        "1.16.6": [{"requires_python": None}],
        "1.24.3": [{"requires_python": ">=3.8"}],
        "1.26.3": [{"requires_python": ">=3.9"}],
        "2.0.0": [{"requires_python": ">=3.9"}],
    }
}

KERAS_PYPI_RESPONSE = {
    "info": {"name": "keras", "requires_python": ">=3.6"},
    "releases": {
        "2.2.4": [{"requires_python": None}],
        "2.9.0": [{"requires_python": ">=3.7"}],
        "3.0.0": [{"requires_python": ">=3.8"}],
    }
}


def _mock_get(url, timeout=10):
    resp = MagicMock()
    resp.status_code = 200
    if 'numpy' in url:
        resp.json.return_value = NUMPY_PYPI_RESPONSE
    elif 'keras' in url:
        resp.json.return_value = KERAS_PYPI_RESPONSE
    else:
        resp.status_code = 404
        resp.json.return_value = {}
    return resp


@patch('src.candidate_graph_builder.requests.get', side_effect=_mock_get)
def test_candidates_filtered_by_python_version(mock_get):
    builder = CandidateGraphBuilder()
    candidates = builder.get_candidates('numpy', '3.8')
    versions = [c['version'] for c in candidates]
    # 1.26.3 requires >=3.9, should be excluded for 3.8
    assert '1.26.3' not in versions
    # 1.24.3 requires >=3.8, should be included
    assert '1.24.3' in versions


@patch('src.candidate_graph_builder.requests.get', side_effect=_mock_get)
def test_candidates_newest_first(mock_get):
    builder = CandidateGraphBuilder()
    candidates = builder.get_candidates('numpy', '3.9')
    versions = [c['version'] for c in candidates]
    assert versions == sorted(versions, key=lambda v: [int(x) for x in v.split('.')], reverse=True)


@patch('src.candidate_graph_builder.requests.get', side_effect=_mock_get)
def test_unknown_package_returns_empty(mock_get):
    builder = CandidateGraphBuilder()
    candidates = builder.get_candidates('nonexistent_pkg_xyz', '3.8')
    assert candidates == []


@patch('src.candidate_graph_builder.requests.get', side_effect=_mock_get)
def test_cache_prevents_double_request(mock_get):
    builder = CandidateGraphBuilder()
    builder.get_candidates('numpy', '3.8')
    builder.get_candidates('numpy', '3.8')
    # PyPI should only be called once due to caching
    assert mock_get.call_count == 1


@patch('src.candidate_graph_builder.requests.get', side_effect=_mock_get)
def test_build_graph_multiple_packages(mock_get):
    builder = CandidateGraphBuilder()
    graph = builder.build_graph(['numpy', 'keras'], '3.8')
    assert 'numpy' in graph
    assert 'keras' in graph
    assert len(graph['numpy']) > 0
    assert len(graph['keras']) > 0
