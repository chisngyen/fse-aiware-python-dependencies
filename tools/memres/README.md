# MEMRES

**Multi-Level Confidence Cascade with Self-Evolving Memory for Agentic Python Dependency Resolution**

FSE-AIWare 2026 Competition Entry

## Overview

MEMRES is an agentic system that resolves Python package dependencies for legacy code snippets. It uses a **confidence cascade architecture** where deterministic methods handle the majority of cases, with an LLM (Gemma-2 9B) as a last resort.

### Key Components

1. **Knowledge Oracle** — Reuses proven solutions from PLLM historical data
2. **Confidence Cascade** — 6-level version selection (session memory → compatibility map → templates → co-occurrence → heuristics → LLM)
3. **Self-Evolving Memory** — Tips and shortcuts that accumulate across snippets
4. **Error Pattern KB** — 200+ import→package mappings with runtime self-learning
5. **System Dependency Injection** — Auto-injects `apt-get` libraries for C-extension packages
6. **Python 2 Heuristic Detector** — Resolves SyntaxError failures from Py2/3 misdetection
7. **Semantic Import Analyzer** — Disambiguates imports via code-context analysis

## Quick Start

### Prerequisites
- Docker Desktop
- Ollama with Gemma-2 model (`ollama pull gemma2`)

### Build

```bash
docker build -t memres .
```

### Run (full dataset via docker-compose)

```bash
docker compose up
```

### Run (full dataset via docker run)

```bash
docker run -d --name memres --privileged \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /path/to/hard-gists:/gists:ro \
  -v /path/to/pllm_results:/results:ro \
  -v /path/to/output:/output \
  --add-host host.docker.internal:host-gateway \
  memres:latest python run.py \
    --folder /gists -d /results -o /output \
    -m gemma2 -b http://host.docker.internal:11434 \
    -l 10 -r 0 -w 4 --timeout 180 --resume
```

### Run (single snippet)

```bash
docker run --rm --privileged \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /path/to/hard-gists:/gists:ro \
  -v /path/to/pllm_results:/results:ro \
  -v /path/to/output:/output \
  memres:latest python run.py \
    -f /gists/0a2ac74d800a2eff9540/snippet.py \
    -d /results -o /output --no-llm -l 5 --timeout 120
```

### Parameters

| Flag | Description | Default |
|------|-------------|---------|
| `-f` / `--file` | Single snippet path | — |
| `--folder` | Folder of snippets | — |
| `-m` / `--model` | Ollama model name | `gemma2` |
| `-b` / `--base` | Ollama base URL | `http://host.docker.internal:11434` |
| `-l` / `--loop` | Max resolution loops | `10` |
| `-w` / `--workers` | Parallel workers | `1` |
| `-d` / `--data` | Historical results dir | `/results` |
| `-o` / `--output` | Output directory | `/output` |
| `--no-llm` | Disable LLM calls | `false` |
| `--timeout` | Docker build timeout (s) | `180` |
| `--resume` | Resume from existing CSV | `false` |
| `--retry-failed` | Retry previously failed snippets | `false` |
| `--conf0-only` | Only conf=0 snippets | `false` |
| `--conf-nonzero` | Only conf>0 snippets | `false` |
| `--gist-list` | File with gist IDs to process | — |

### Output (PLLM-compatible)

Results are saved to the output directory:
- `results.csv` — PLLM-compatible CSV (`name,file,result,python_modules,duration,passed`)
- `output_data_X.Y.yml` — Per-snippet YAML (one per snippet, PLLM format)

## Architecture

```
Stage 0: Oracle Lookup     → Historical data replay (conf≥4 → direct, else hint)
Stage 1: Hybrid Evaluation → Static analysis + Semantic Import + LLM (few-shot)
Stage 2: Module Cleaning   → ErrorPatternKB + Self-Evolving Memory + PyPI validation
Stage 3: Version Selection → 6-level Confidence Cascade
Stage 4: Build Loop        → Docker-in-Docker + Reflexion memory + cross-version transfer
```

## License

GPLv3 — See [LICENSE](../../LICENSE)
