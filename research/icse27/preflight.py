"""Pre-flight checklist — run this before any real experiment.

Verifies in ~30 seconds:
  1. Repo layout (datasets + tools/ paths exist)
  2. Docker daemon reachable
  3. Ollama HTTP reachable + the configured model is loaded
  4. The LLM responds to a trivial prompt
  5. Docker can actually build + run a hello-world image
  6. (optional) A single real snippet survives end-to-end via the harness

Usage:
    python -m research.icse27.preflight                       # checks 1-5
    python -m research.icse27.preflight --backbone gemma2-9b  # adds LLM check
    python -m research.icse27.preflight --backbone gemma2-9b --snippet sample_0  # full
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import yaml

from research.icse27._shared import (
    CONFIGS_DIR, GITCHAMELEON_DIR, HARD_GISTS_DIR,
    BackboneConfig, LLMBackbone,
    assert_layout_ok, build_and_run, docker_available,
)


GREEN = "[ OK ]"
RED = "[FAIL]"
YELLOW = "[WARN]"


def check(label: str) -> "Check":
    return Check(label)


class Check:
    def __init__(self, label: str) -> None:
        self.label = label
        self.ok = False
        self.detail = ""

    def __enter__(self) -> "Check":
        print(f"  ... {self.label} ", end="", flush=True)
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        tag = GREEN if self.ok else RED
        print(f"{tag} {self.detail}")
        return False  # don't swallow exceptions


def _run(cmd: list[str], timeout: int = 30) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        return -1, f"{type(e).__name__}: {e}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backbone", default=None,
                    help="Backbone YAML name; if given, run LLM checks too")
    ap.add_argument("--snippet", default=None,
                    help="Snippet ID for full end-to-end test (e.g. sample_0)")
    args = ap.parse_args(argv)

    print("=" * 60)
    print("ICSE 2027 pre-flight checklist")
    print("=" * 60)
    failures = 0

    # 1. Repo layout
    with check("repo layout") as c:
        try:
            assert_layout_ok()
            c.ok = True
            c.detail = f"datasets at {HARD_GISTS_DIR.parent.name}/"
        except Exception as e:  # noqa: BLE001
            c.detail = str(e)
            failures += 1

    # 2. Docker daemon
    with check("docker daemon") as c:
        rc, out = _run(["docker", "version", "--format", "{{.Server.Version}}"], timeout=10)
        c.ok = rc == 0 and bool(out.strip())
        c.detail = f"server={out.splitlines()[0] if c.ok else out[:120]}"
        if not c.ok:
            failures += 1

    # 3. Tier ID files exist
    with check("benchmark tier ID files") as c:
        tiers = ["hg2k_smoke", "hg2k_dev", "hg2k_rescue", "hg2k_full"]
        missing = [t for t in tiers
                   if not (CONFIGS_DIR / "benchmarks" / f"{t}.ids.txt").exists()]
        c.ok = not missing
        c.detail = "all present" if c.ok else f"missing: {missing}"
        if not c.ok:
            failures += 1

    backbone: LLMBackbone | None = None
    if args.backbone:
        cfg_path = CONFIGS_DIR / "backbones" / f"{args.backbone}.yaml"

        # 4. Ollama tags includes the configured model
        with check(f"ollama serves {args.backbone}") as c:
            try:
                data = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
                cfg = BackboneConfig(**data)
                import requests
                r = requests.get(f"{cfg.base_url}/api/tags", timeout=5)
                r.raise_for_status()
                tags = {m.get("name") for m in r.json().get("models", [])}
                c.ok = cfg.ollama_model in tags
                c.detail = (f"model={cfg.ollama_model}" if c.ok
                            else f"model {cfg.ollama_model!r} not in {sorted(tags)}")
                if c.ok:
                    backbone = LLMBackbone(cfg)
            except Exception as e:  # noqa: BLE001
                c.detail = f"{type(e).__name__}: {e}"
            if not c.ok:
                failures += 1

        # 5. LLM round-trip
        if backbone:
            with check("LLM responds to trivial prompt") as c:
                t0 = time.time()
                ans = backbone.generate("Say only the word OK.", agent_name="preflight",
                                        max_tokens=8)
                c.ok = bool(ans.strip())
                c.detail = f"latency={time.time()-t0:.1f}s reply={ans.strip()[:40]!r}"
                if not c.ok:
                    failures += 1

    # 6. Docker can build + run something minimal
    with check("docker build+run smoke") as c:
        if not docker_available():
            c.detail = "docker not reachable; skipping"
        else:
            t0 = time.time()
            br = build_and_run(
                snippet_source='print("preflight-ok")\n',
                python_version="3.10",
                packages=[],
                build_timeout=120, run_timeout=15,
            )
            c.ok = br.passed and "preflight-ok" in br.log_text
            c.detail = (f"passed in {time.time()-t0:.1f}s"
                        if c.ok else f"failed: {br.error_kind.family}: "
                                    f"{br.error_kind.detail[:80]}")
            if not c.ok:
                failures += 1

    # 7. (optional) full end-to-end on one snippet
    if args.snippet and backbone:
        with check(f"end-to-end smoke on {args.snippet}") as c:
            from research.icse27._shared import Blackboard, TrajectoryLogger, iter_snippets
            from research.icse27.methods._base import Budget
            from research.icse27.methods.m3_cgar_react import Method as M3
            snip = next((s for s in iter_snippets("gitchameleon", limit=10000)
                         if s.id == args.snippet), None)
            if snip is None:
                snip = next((s for s in iter_snippets("hg2k", limit=10000)
                             if s.id == args.snippet), None)
            if snip is None:
                c.detail = f"snippet {args.snippet} not found"
            else:
                import tempfile
                with tempfile.TemporaryDirectory() as td:
                    bb = Blackboard(persist_path=Path(td) / "bb.jsonl")
                    tl = TrajectoryLogger(Path(td) / "traj")
                    m = M3(backbone=backbone, blackboard=bb, tools=None,
                           config={}, trajectory=tl)
                    tl.start_snippet(snip.id)
                    res = m.resolve(snip, Budget(k_build_max=2))
                    tl.end_snippet(res.passed, 0)
                c.ok = True  # surviving is the test; pass/fail content is the run's job
                c.detail = (f"passed={res.passed} dur={res.duration:.1f}s "
                            f"py={res.python_version} pkgs={res.packages[:4]}")
            if not c.ok:
                failures += 1

    print("=" * 60)
    if failures == 0:
        print("ALL CHECKS PASSED — safe to start real experiments.")
        return 0
    print(f"{failures} check(s) FAILED — fix before running real experiments.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
