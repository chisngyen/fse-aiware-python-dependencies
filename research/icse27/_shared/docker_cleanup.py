"""Docker disk hygiene for long experiment runs.

Why this exists
---------------
Each snippet build creates intermediate layers (FROM python:X.Y +
apt + pip install <variable packages>). Across 2,891 HG2.9K snippets
with 5-10 retries each, this produces tens of thousands of unique
layer combinations. Failed builds leave dangling layers that aren't
auto-pruned. Pip downloads repeat inside each fresh container.
Disk balloons 30-50GB per full run.

What this does
--------------
1. Per-snippet light prune: remove stopped containers + recent dangling images.
2. Periodic heavy prune: builder cache cap to a budget.
3. Optional pip-cache mount path (callers wire it into their build).

Everything is best-effort: if Docker is unreachable we log and continue,
never crash the experiment.
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class CleanupPolicy:
    light_every_n_snippets: int = 1     # docker container prune + dangling images
    heavy_every_n_snippets: int = 50    # builder cache prune
    builder_cache_keep_gb: int = 10     # cap builder cache
    dangling_age: str = "10m"           # only prune images older than this
    enabled: bool = True


def _run(cmd: list[str], timeout: int = 60) -> tuple[int, str]:
    try:
        p = subprocess.run(
            cmd, capture_output=True, timeout=timeout,
            encoding="utf-8", errors="replace",
        )
        return p.returncode, ((p.stdout or "") + (p.stderr or ""))
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        return -1, f"{type(e).__name__}: {e}"


def light_prune(policy: CleanupPolicy) -> None:
    if not policy.enabled:
        return
    rc, _ = _run(["docker", "container", "prune", "-f"])
    if rc != 0:
        log.debug("docker container prune failed (rc=%d)", rc)
    _run(["docker", "image", "prune", "-f", "--filter", f"until={policy.dangling_age}"])


def heavy_prune(policy: CleanupPolicy) -> None:
    if not policy.enabled:
        return
    keep_bytes = policy.builder_cache_keep_gb * 1024 * 1024 * 1024
    _run(["docker", "builder", "prune", "-f", "--keep-storage", str(keep_bytes)])


class DockerCleaner:
    """Stateful counter that triggers pruning on the right cadence."""

    def __init__(self, policy: CleanupPolicy | None = None) -> None:
        self.policy = policy or CleanupPolicy()
        self._snippet_count = 0

    def after_snippet(self) -> None:
        self._snippet_count += 1
        if self._snippet_count % self.policy.light_every_n_snippets == 0:
            light_prune(self.policy)
        if self._snippet_count % self.policy.heavy_every_n_snippets == 0:
            heavy_prune(self.policy)

    def shutdown(self) -> None:
        """Final cleanup at end of run."""
        light_prune(self.policy)
        heavy_prune(self.policy)
