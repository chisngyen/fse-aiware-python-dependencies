# Tools

| Directory | Description | Status |
|-----------|-------------|--------|
| `pllm/` | Baseline — RAG + LLM pipeline | Published baseline (Bartlett et al., FSE'25) |
| `memres/` | MEMRES — multi-level confidence cascade with self-evolving memory | Our FSE'26 competition entry |
| `cgar/` | CGAR — Constraint-Guided Agentic Resolution (built on MEMRES) | Our improved entry |

See each tool's `README.md` for build and run instructions.

## Layout conventions

Our two tools (`memres/`, `cgar/`) follow the same structure for consistency:

```
<tool>/
├── Dockerfile
├── README.md
├── docker-compose*.yml      # one or more variants per benchmark
├── requirements.txt
├── run.py                   # entry point
├── src/                     # tool modules
└── tests/                   # unit tests (cgar only)
└── scripts/                 # one-shot utilities (cgar only)
```

`pllm/` follows its own upstream layout (`helpers/` instead of `src/`,
`Pipfile` instead of `requirements.txt`, `test_executor.py` as entry).
We **deliberately do not refactor it** — keeping the upstream structure
makes our reproduction directly comparable to the published version
and lets us pull future updates without conflict.
