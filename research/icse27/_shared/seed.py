"""Deterministic seed propagation across the harness.

The current MEMRES/CGAR harness has no seed handling; LLM temperature noise
makes every run different. For ICSE 2027 we need ≥3 seeds with reproducible
trajectories (G6, G9). This module is the single source of randomness.
"""

from __future__ import annotations

import hashlib
import os
import random


def set_global_seed(seed: int) -> None:
    """Seed Python's stdlib random + numpy if present + PYTHONHASHSEED.

    LLM sampling temperature/top_p still adds noise — that's expected.
    What we control here: retry order, candidate enumeration tie-breaks,
    any in-process shuffling. The harness writes the seed into every
    results.csv row so replays know which seed produced what.
    """
    random.seed(seed)
    os.environ.setdefault("PYTHONHASHSEED", str(seed))
    try:  # numpy is optional; many methods won't need it
        import numpy as np  # type: ignore

        np.random.seed(seed)
    except ImportError:
        pass


def derive_seed(base_seed: int, *parts: str | int) -> int:
    """Derive a stable child seed from base_seed + a label tuple.

    Use when a method needs sub-seeds without coupling them
    (e.g. one per agent, one per snippet). Same inputs → same output
    across runs; small inputs → well-spread 32-bit outputs.
    """
    key = "|".join((str(base_seed), *(str(p) for p in parts)))
    digest = hashlib.blake2b(key.encode("utf-8"), digest_size=4).digest()
    return int.from_bytes(digest, "big")
