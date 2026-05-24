"""Shared infrastructure for ICSE 2027 agentic-resolution experiments.

Every method file under research/icse27/methods/ imports from here.
Modules are intentionally small and independently testable.
"""

from .paths import (
    PROJECT_ROOT, HARD_GISTS_DIR, GITCHAMELEON_DIR, ICSE27_DIR,
    METHODS_DIR, CONFIGS_DIR, DEFAULT_RESULTS_DIR, MEMRES_DIR, CGAR_DIR, PLLM_DIR,
    assert_layout_ok,
)
from .seed import set_global_seed, derive_seed
from .dataset import Snippet, iter_snippets, load_ground_truth
from .results_store import ResultRow, ResultsStore, CSV_COLUMNS
from .docker_cleanup import CleanupPolicy, DockerCleaner
from .dev_subset import build_subset, materialize_tier, load_tier_ids, TIER_SIZES
from .llm_backbones import BackboneConfig, LLMBackbone, LLMUsage, load_backbone
from .blackboard import Blackboard, Constraint, ConstraintKind, Reflection, DebateEntry
from .trajectory_logger import TrajectoryLogger, replay as replay_trajectory
from .tools_lib import (
    PypiMetadata, query_pypi, pypi_release_dates, wheel_filter,
    parse_docker_error, solve_csp, imports_to_packages, extract_imports,
    ErrorKind,
)
from .docker_harness import BuildResult, build_and_run, docker_available
from .method_helpers import (
    CGAR_HG2K, MEMRES_HG2K, PLLM_HG2K,
    CGAR_GITCH, MEMRES_GITCH, PLLM_GITCH,
    looks_like_python2, STDLIB,
    load_resolver_csv, passed as csv_passed, packages_of, py_of,
    ResolverIndexes, cascade_replay,
    parse_plan_array, soft_vote,
    filter_stdlib, whitelist_by_imports,
)

__all__ = [
    # paths
    "PROJECT_ROOT", "HARD_GISTS_DIR", "GITCHAMELEON_DIR", "ICSE27_DIR",
    "METHODS_DIR", "CONFIGS_DIR", "DEFAULT_RESULTS_DIR",
    "MEMRES_DIR", "CGAR_DIR", "PLLM_DIR", "assert_layout_ok",
    # seed
    "set_global_seed", "derive_seed",
    # dataset
    "Snippet", "iter_snippets", "load_ground_truth",
    # results
    "ResultRow", "ResultsStore", "CSV_COLUMNS",
    # docker cleanup
    "CleanupPolicy", "DockerCleaner",
    # subsets
    "build_subset", "materialize_tier", "load_tier_ids", "TIER_SIZES",
    # llm
    "BackboneConfig", "LLMBackbone", "LLMUsage", "load_backbone",
    # blackboard
    "Blackboard", "Constraint", "ConstraintKind", "Reflection", "DebateEntry",
    # trajectory
    "TrajectoryLogger", "replay_trajectory",
    # tools
    "PypiMetadata", "query_pypi", "pypi_release_dates", "wheel_filter",
    "parse_docker_error", "solve_csp", "imports_to_packages",
    "extract_imports", "ErrorKind",
    # docker
    "BuildResult", "build_and_run", "docker_available",
    # method helpers
    "CGAR_HG2K", "MEMRES_HG2K", "PLLM_HG2K",
    "CGAR_GITCH", "MEMRES_GITCH", "PLLM_GITCH",
    "looks_like_python2", "STDLIB",
    "load_resolver_csv", "csv_passed", "packages_of", "py_of",
    "ResolverIndexes", "cascade_replay",
    "parse_plan_array", "soft_vote",
    "filter_stdlib", "whitelist_by_imports",
]
