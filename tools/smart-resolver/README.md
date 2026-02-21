# SmartResolver

**Multi-Level Confidence Cascade with Self-Evolving Memory for Agentic Python Dependency Resolution**

FSE-AIWare 2026 Competition Entry

## Overview

SmartResolver is an agentic system that resolves Python package dependencies for legacy code snippets. It uses a **confidence cascade architecture** where deterministic methods handle the majority of cases, with an LLM (Gemma-2 9B) as a last resort.

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
- Docker
- Ollama with Gemma-2 model (`ollama pull gemma2`)

### Build

```bash
docker build -t smart-resolver .
```

### Run (single snippet)

```bash
docker run --rm --privileged \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /path/to/hard-gists:/data/snippets \
  -v /path/to/results:/data/results \
  -v ./output:/app/output \
  smart-resolver python run.py \
    -f /data/snippets/0a2ac74d800a2eff9540/snippet.py \
    -d /data/results -o /app/output \
    --no-llm -l 5 --timeout 120
```

### Run (full dataset)

```bash
docker run --rm --privileged \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /path/to/hard-gists:/data/snippets \
  -v /path/to/results:/data/results \
  -v ./output:/app/output \
  smart-resolver python run.py \
    --folder /data/snippets \
    -d /data/results -o /app/output \
    --no-llm -w 1 -l 5 --timeout 120
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
| `--conf0-only` | Only conf=0 snippets | `false` |
| `--conf-nonzero` | Only conf>0 snippets | `false` |

### Output

Results are saved to the output directory:
- `results.csv` — Per-snippet results (snippet_id, success, python_version, modules, duration, error)
- `results.json` — Full detailed results

## Architecture

```
Stage 0: Oracle Lookup     → Historical data replay
Stage 1: Hybrid Evaluation → Static analysis + LLM
Stage 2: Module Cleaning   → KB + filtering
Stage 3: Version Selection → 6-level Confidence Cascade
Stage 4: Build Loop        → Docker + Reflexion memory
```

## License

GPLv3 — See [LICENSE](../../LICENSE)
