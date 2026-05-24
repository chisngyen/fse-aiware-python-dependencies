"""Single entry point for every ICSE 2027 experiment.

Example
-------
    python -m research.icse27.run_experiment \\
        --method m2_cgar_rule_replay \\
        --backbone gemma2-9b \\
        --benchmark hg2k_smoke \\
        --seed 0 \\
        --resume

Output structure
----------------
    <out>/
      results.csv         — schema = name,file,result,python_modules,duration,passed,seed,backbone,method
      heartbeat.json      — pid + currently-processed snippet, guards against double-runners
      trajectories/<id>.jsonl — per-snippet agent step log
      blackboard.jsonl    — append-only constraint/reflection/debate log
      run.json            — run metadata (args, start_time, n_snippets, llm_usage)
"""

from __future__ import annotations

import argparse
import importlib
import json
import logging
import signal
import sys
import time
from pathlib import Path

import yaml

from research.icse27._shared import (
    PROJECT_ROOT, ICSE27_DIR, CONFIGS_DIR, DEFAULT_RESULTS_DIR,
    assert_layout_ok, set_global_seed,
    iter_snippets, load_tier_ids,
    ResultRow, ResultsStore,
    DockerCleaner, CleanupPolicy,
    LLMBackbone, BackboneConfig,
    Blackboard, TrajectoryLogger,
)
from research.icse27.methods._base import Budget, Resolution

log = logging.getLogger("icse27.run")


def _load_backbone(name: str) -> LLMBackbone | None:
    """Return None if user passed ``none`` (replay methods don't need an LLM)."""
    if name.lower() in ("none", "", "no_llm"):
        return None
    cfg_path = CONFIGS_DIR / "backbones" / f"{name}.yaml"
    if not cfg_path.exists():
        raise FileNotFoundError(f"Backbone config not found: {cfg_path}")
    data = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    return LLMBackbone(BackboneConfig(**data))


def _load_benchmark_config(name: str) -> dict:
    cfg_path = CONFIGS_DIR / "benchmarks" / f"{name}.yaml"
    if not cfg_path.exists():
        raise FileNotFoundError(f"Benchmark config not found: {cfg_path}")
    return yaml.safe_load(cfg_path.read_text(encoding="utf-8"))


def _load_method(name: str):
    """Import methods/<name>.py and return its ``Method`` class."""
    mod = importlib.import_module(f"research.icse27.methods.{name}")
    cls = getattr(mod, "Method", None)
    if cls is None:
        raise AttributeError(f"methods/{name}.py must expose a class named ``Method``")
    return cls


def _default_out(method: str, backbone: str, benchmark: str, seed: int) -> Path:
    return DEFAULT_RESULTS_DIR / method / backbone / benchmark / f"seed{seed}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="run_experiment")
    parser.add_argument("--method", required=True,
                        help="Method module under research/icse27/methods/")
    parser.add_argument("--backbone", default="none",
                        help="Backbone YAML name under configs/backbones/, or 'none' for replay methods")
    parser.add_argument("--benchmark", required=True,
                        help="Benchmark YAML name under configs/benchmarks/")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--limit", type=int, default=None,
                        help="Stop after N snippets (debugging)")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--out", default=None, help="Override output directory")
    parser.add_argument("--no-docker-clean", action="store_true",
                        help="Disable periodic docker prune (testing only)")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    assert_layout_ok()
    set_global_seed(args.seed)

    bench = _load_benchmark_config(args.benchmark)
    method_cls = _load_method(args.method)
    backbone = _load_backbone(args.backbone)
    backbone_label = backbone.name if backbone else "none"

    # Fail-fast LLM probe: catch "Ollama not running" before processing snippets.
    if backbone is not None:
        probe = backbone.generate("ping", agent_name="preflight", max_tokens=4)
        if not probe.strip():
            log.error(
                "Backbone %r is unreachable (empty reply). Start Ollama "
                "(`ollama serve` or open Ollama Desktop) and ensure model "
                "%r is pulled, then retry.",
                backbone_label, backbone.config.ollama_model,
            )
            return 4

    out_dir = Path(args.out) if args.out else _default_out(
        args.method, backbone_label, args.benchmark, args.seed
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    store = ResultsStore(out_dir=out_dir)
    if not args.resume and store.num_rows() > 0:
        log.warning("results.csv has %d existing rows; pass --resume or move them aside",
                    store.num_rows())
        return 2
    store.claim_run_or_raise()

    bb = Blackboard(persist_path=out_dir / "blackboard.jsonl")
    traj = TrajectoryLogger(out_dir / "trajectories")
    method = method_cls(backbone=backbone, blackboard=bb,
                        tools=None, config=bench, trajectory=traj)
    budget = Budget(k_build_max=bench.get("k_build_max", 5))
    cleaner = DockerCleaner(CleanupPolicy(enabled=not args.no_docker_clean))

    # Snippet selection
    ids_file_name = bench.get("ids_file") or ""
    allowed: set[str] | None = None
    if ids_file_name:
        ids_path = CONFIGS_DIR / "benchmarks" / ids_file_name
        allowed = load_tier_ids(ids_path)
        if not allowed:
            log.error("ids_file %s is empty or missing", ids_path)
            return 3

    done = store.completed_ids() if args.resume else set()
    log.info("method=%s backbone=%s benchmark=%s seed=%d out=%s resume_done=%d allowed=%s",
             args.method, backbone_label, bench["benchmark"], args.seed, out_dir,
             len(done), (len(allowed) if allowed is not None else "all"))

    # Graceful Ctrl-C
    stopping = {"flag": False}

    def _sigint(_sig, _frm):
        log.warning("Ctrl-C received; will exit after current snippet")
        stopping["flag"] = True

    signal.signal(signal.SIGINT, _sigint)

    run_meta = {
        "method": args.method, "backbone": backbone_label,
        "benchmark": args.benchmark, "seed": args.seed,
        "start_time": time.time(), "args": vars(args),
    }
    (out_dir / "run.json").write_text(json.dumps(run_meta, indent=2, default=str),
                                       encoding="utf-8")

    n_processed = 0
    try:
        for snippet in iter_snippets(bench["benchmark"]):
            if allowed is not None and snippet.id not in allowed:
                continue
            if snippet.id in done:
                continue
            if args.limit is not None and n_processed >= args.limit:
                break

            with store.processing(snippet.id):
                traj.start_snippet(snippet.id)
                t0 = time.perf_counter()
                try:
                    res: Resolution = method.resolve(snippet, budget)
                except Exception as e:  # noqa: BLE001 — never crash the whole run
                    log.exception("method.resolve crashed on %s", snippet.id)
                    res = Resolution(passed=False, result_tag=f"MethodCrash:{type(e).__name__}",
                                     duration=time.perf_counter() - t0)
                duration = res.duration or (time.perf_counter() - t0)
                traj.end_snippet(res.passed, n_steps=0)

                row = ResultRow(
                    name=snippet.id,
                    file=f"output_data_{res.python_version}.yml" if res.python_version else "",
                    result=res.result_tag or ("None" if res.passed else "Unknown"),
                    python_modules=";".join(str(p) for p in (res.packages or [])),
                    duration=duration, passed=res.passed,
                    seed=args.seed, backbone=backbone_label, method=args.method,
                )
                store.append(row)

            cleaner.after_snippet()
            n_processed += 1
            if stopping["flag"]:
                break
    finally:
        cleaner.shutdown()
        store.release()
        if backbone is not None:
            usage_path = out_dir / "llm_usage.json"
            usage_path.write_text(
                json.dumps(backbone.usage.__dict__, default=str, indent=2),
                encoding="utf-8",
            )
        run_meta["end_time"] = time.time()
        run_meta["n_processed"] = n_processed
        (out_dir / "run.json").write_text(json.dumps(run_meta, indent=2, default=str),
                                           encoding="utf-8")

    log.info("done; processed %d new snippets; results.csv now has %d rows",
             n_processed, store.num_rows())
    return 0


if __name__ == "__main__":
    sys.exit(main())
