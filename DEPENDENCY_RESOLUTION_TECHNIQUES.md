# Python Dependency Resolution Techniques - Research Summary

**Purpose**: Identify key techniques applicable to improving dependency resolution for Python code snippets (gists) without requirements.txt files.

**Our System Context**:
- Input: Single Python file (no requirements.txt, no setup.py)
- Must determine: Python version, required packages, package versions
- Must compile/run successfully in a Docker container
- Current: 446/1309 conf=0 failures (34%), 75% of failures are Py2.7
- Top failing packages: numpy, scipy, scikit-learn, opencv-python, tensorflow, matplotlib

---

## 1. PyEGo (ICSE 2022)
**"Knowledge-Based Environment Dependency Inference for Python Programs"** — Ye et al.

### Core Technique
PyEGo builds **PyKG** (Python Knowledge Graph), a Neo4j-based knowledge graph capturing relationships between Python packages, their versions, import names, compatible Python versions, and system-level dependencies. Given a Python program, PyEGo (1) detects the compatible Python interpreter version via syntax analysis, (2) extracts import statements and resolves them to PyPI package names using PyKG's import→package mappings, and (3) generates a Dockerfile with the correct Python version, pip packages, and apt-get system packages.

### Key Components
- **ModuleParser**: AST-based import extraction from Python files
- **ImportSolver**: Maps import names to PyPI packages using PyKG (the knowledge graph stores `import_name → package_name` mappings far more comprehensive than pipreqs)
- **PackageSolver**: Resolves compatible version combinations using the knowledge graph's dependency edges
- **OutputGenerator**: Produces Dockerfile with pinned versions
- **Two strategies**: "select-one" (pick most popular matching package) vs "select-all" (try all candidates)

### Key Insight for Our System
**The import→package mapping is the critical bottleneck.** PyEGo's knowledge graph approach is superior to pipreqs' static mapping file because it captures many-to-many relationships (one import name can map to multiple packages). For our system, building/using a comprehensive import→package database would immediately reduce ImportError failures.

### Python 2 Support
**Yes** — PyEGo explicitly handles Python 2 vs 3 detection through syntax analysis (print statements, `urllib2`, etc.) and generates appropriate Dockerfiles with `python:2.7` base images. This is directly tested on the same HG2.9K dataset we use.

### Applicability: ★★★★★ (Highest)
- Same dataset (Hard-Gists / HG2.9K)
- Same task (infer environment for single Python files)
- Open source with results we already have in `pyego-results/`

---

## 2. DockerizeMe / Gistable (ICSE 2019)
**"DockerizeMe: Automatic Inference of Environment Dependencies for Python Code Snippets"** — Horton & Parnin

*Note: The user asked about "V2 (ASE 2019)" but the relevant Horton & Parnin work on Python snippets is DockerizeMe (ICSE 2019) and the Gistable dataset (2018). V2 refers to a different paper about OAuth.*

### Core Technique
DockerizeMe is the **predecessor system** that created the HG2.9K dataset we're working with. It uses a combination of: (1) import statement extraction, (2) a **resource name resolution** database mapping import names to pip packages, (3) heuristic version selection based on popularity and recency, and (4) iterative Docker-based trial-and-error. The Gistable paper found that 75.6% of gists require non-trivial configuration, and that developers' natural assumptions about resource names are correct less than half the time.

### Key Insight for Our System
**Resource name ambiguity is a fundamental challenge.** The import name `cv2` maps to `opencv-python`, `dateutil` maps to `python-dateutil`, `yaml` maps to `PyYAML`, etc. The mapping database is essential. DockerizeMe's finding that human guessing is wrong >50% of the time validates the need for a comprehensive database rather than LLM guessing.

### Python 2 Support
**Yes** — The HG2.9K dataset specifically includes Python 2 snippets and DockerizeMe handles both versions.

### Applicability: ★★★★★ (Highest)
- Created the exact dataset we use
- Established the baseline approach our system builds upon

---

## 3. PLLM (Baseline - 2025)
**"PLLM: RAG+LLM Pipeline for Dependency Resolution"** — Bartlett et al.

### Core Technique
5-stage pipeline: (1) extract imports from code, (2) use LLM (Gemma2) with RAG to generate dependency specifications, (3) build Docker container, (4) analyze error logs, (5) iterate with LLM feedback. Uses historical results and prompt engineering to guide the LLM in selecting correct versions.

### Key Insight for Our System
The iterative error-log-driven approach is sound but slow (~7 min average). The main failures are: ImportError (package doesn't exist or wrong name), SyntaxError (wrong Python version), and build failures (incompatible versions). Pre-validation before Docker build would save significant time.

### Python 2 Support
**Partial** — PLLM handles some Python 2 cases but ~60% of the dataset is Python 2 and this is the primary failure zone.

### Applicability: ★★★★★ (Is the baseline)

---

## 4. Repo2Run (NeurIPS 2025)
**"Automated Building Executable Environment for Code Repository at Scale"** — Hu et al. (ByteDance)

### Core Technique
LLM-agent-based system that **iteratively builds Docker environments** for code repositories. Key innovations: (1) **Adaptive rollback**: when a command fails, restore the environment to its pre-execution state to prevent "pollution" (failed pip installs can leave behind partial dependencies that cause cascading failures). (2) **Waiting list + conflict resolution**: packages are queued in a waiting list, conflicts detected and resolved before installation. (3) **Base image switching**: the agent can dynamically change the Python version (e.g., from 3.10 to 3.11) if it detects version-specific features like `StrEnum`. (4) **Dockerfile synthesis**: successful commands are recorded into a reproducible Dockerfile.

### Key Components
- **External environment**: Result processor truncates long outputs to avoid overwhelming the LLM
- **Internal environment (Docker)**: Environment monitoring (`pip list`, `pipdeptree`), dependency installation, test running, code editing
- **30+ "pollution" packages documented**: e.g., `pip install adb` installs typing/libusb as side effects even when it fails

### Key Insight for Our System
**Rollback on failed installations is critical.** Failed `pip install` can "pollute" the environment by partially installing dependencies. Our system should: (1) snapshot/rollback on failed installs, (2) use a conflict resolution queue rather than sequential `pip install`, and (3) dynamically switch Python versions based on error feedback. Repo2Run achieves 86% success rate on full repositories, far exceeding other approaches.

### Python 2 Support
**No** — Repo2Run focuses on Python 3.10+ repositories from 2024. Not applicable to legacy Python 2 code.

### Applicability: ★★★☆☆ (Medium)
- Great architecture patterns (rollback, conflict resolution)
- But designed for full repos with tests, not standalone snippets
- Requires powerful LLM (GPT-4), conflicts with 10GB VRAM constraint
- No Python 2 support

---

## 5. PYCONF (ICSE 2024)
**"Less is More? An Empirical Study on Configuration Issues in Python PyPI Ecosystem"** — Peng et al.

### Core Technique
PyConf is a **source-level configuration issue detector** that performs three checks at different stages: (1) **Setup check**: validates that `setup.py`/`setup.cfg`/`pyproject.toml` correctly declares dependencies, (2) **Packing check**: ensures all source files are included in the distribution, (3) **Usage check**: verifies that imported modules are actually available after installation. They built the **VLibs benchmark** of library releases that pass all checks. Key finding: **183,864 library releases have configuration issues**, and **68% of issues are only detectable via source-level checking** (not version-level).

### Key Insight for Our System
**Many PyPI packages have broken configurations themselves.** Even if we correctly identify the package and version, the package itself may have broken dependencies or missing files. Our system should: (1) prefer versions known to have correct configurations (use VLibs-like data), (2) avoid versions with known issues, (3) for packages like numpy/scipy, use **pre-built binary wheels** rather than source builds. The finding that PyEGo only achieves 65% on VLibs shows there's fundamental difficulty in the ecosystem.

### Python 2 Support
**Partial** — studies the PyPI ecosystem broadly, but the VLibs benchmark may cover some Python 2 packages.

### Applicability: ★★★★☆ (High)
- Directly relevant — same ecosystem, overlapping authors with Repo2Run
- VLibs benchmark could filter known-good package versions
- Source-level checking could validate our dependency choices

---

## 6. Beyond pip install / Installamatic (2024)
**"Beyond pip install: Evaluating LLM Agents for the Automated Installation of Python Projects"** — Milliken, Kang & Yoo

### Core Technique
Introduces **Installamatic**, an LLM agent that installs Python projects by: (1) **Documentation search phase**: explores README, setup files, and documentation to find installation instructions, (2) **Build/repair phase**: generates and tests Dockerfiles with multiple repair attempts. Achieves 55% success rate on 40 open-source Python projects (at least 1 out of 10 attempts).

### Key Insight for Our System
For standalone snippets without documentation, the documentation-search approach has limited value. However, the **multi-attempt repair** strategy is applicable — try, fail, analyze error, retry with different configuration. The paper confirms that error feedback significantly improves success rates over zero-shot approaches.

### Python 2 Support
**No** — focuses on modern Python projects.

### Applicability: ★★☆☆☆ (Low)
- Designed for full repos with README/docs, not bare snippets
- But validates that iterative error-driven repair is effective

---

## 7. EnvBench (ICLR Workshop 2025)
**"EnvBench: A Benchmark for Automated Environment Setup"** — Eliseeva et al. (JetBrains)

### Core Technique
Benchmark of 329 Python + 665 JVM repositories for evaluating environment setup approaches. Key components: (1) **Deterministic baseline script**: analyzes config files for dependency manager and Python version, installs managed dependencies — succeeds on only 16% of Python repos. (2) **Static analysis metric**: uses `pyright` to count missing imports after setup. (3) **Bash Agent** (ReAct-based): iteratively executes commands in Docker, achieving 6.69% full success on Python repos. (4) Pre-installs `pyenv` with Python 3.8–3.13, Poetry, uv, conda in Docker images.

### Key Insight for Our System
**Even with full repo context, automated Python environment setup remains extremely hard (6.69% success).** Our task (bare snippets) is harder still. The most effective strategy is the **iterative Bash Agent** that executes commands, observes errors, and adapts. Pre-installing multiple Python versions via `pyenv` is a practical approach for our Docker containers. The static analysis approach (counting missing imports via pyright) could be used as a pre-build validation step.

### Python 2 Support
**No** — Python 3.8+ only.

### Applicability: ★★★☆☆ (Medium)
- Validates that iterative approach outperforms single-shot
- Pre-installing multiple Python versions is practical
- pyright-based validation could help

---

## 8. pipreqs
**Popular tool that generates requirements.txt from import statements**

### Core Technique
(1) Walk AST to find all `import` and `from...import` statements in Python files. (2) Filter out stdlib modules using a known list. (3) Map import names to PyPI package names using a **static mapping file** (~1,156 entries). (4) Query PyPI API for latest version. (5) Generate `requirements.txt`.

### Key Mapping Entries (Most Relevant to Our Failures)
```
cv2:opencv-python
sklearn:scikit_learn
PIL:Pillow
bs4:beautifulsoup4
yaml:PyYAML
Crypto:pycryptodome
dateutil:python_dateutil
serial:pyserial
git:GitPython
dns:dnspython
usb:pyusb
magic:python_magic
jwt:PyJWT
```

### Key Insight for Our System
pipreqs' mapping file is the **most comprehensive publicly available import→package mapping** but still incomplete (~1,156 entries). For our system, we should: (1) start with pipreqs' mapping, (2) augment with PyEGo's knowledge graph data, (3) add entries for common scientific packages, (4) handle the many-to-many problem (one import can map to multiple packages).

### Python 2 Support
**Partial** — mapping file includes some Python 2 packages (e.g., `MySQLdb:MySQL-python`, `ConfigParser:pies2overrides`).

### Applicability: ★★★★★ (Highest — immediate use)
- Can directly use the mapping file
- AST-based import extraction is reliable
- Well-maintained, actively used

---

## 9. Additional Techniques and Databases

### Import Name → Package Name Mapping
| Source | Entries | Notes |
|--------|---------|-------|
| pipreqs mapping | ~1,156 | Static file, community-maintained |
| PyEGo PyKG | ~50K+ | Neo4j knowledge graph, mines PyPI metadata |
| PyPI metadata | All | Each package's `top_level.txt` in wheel files |
| stdlib-list | ~300 | Python stdlib modules per version |

### Python 2 vs 3 Detection Heuristics
| Indicator | Python Ver. | Weight |
|-----------|-------------|--------|
| `print "..."` (no parens) | 2 | High |
| `#!/usr/bin/env python2` | 2 | Definitive |
| `urllib2`, `urlparse`, `httplib` | 2 | High |
| `xrange(`, `raw_input(`, `execfile(` | 2 | High |
| `.iteritems()`, `.itervalues()`, `.has_key()` | 2 | High |
| `except Exception, e:` | 2 | High |
| `unicode(`, `basestring` | 2 | Medium |
| `async def`, `await`, `f"..."` | 3 | High |
| `print(...)` with single call | 3 | Low (ambiguous) |
| `from __future__ import print_function` | 2 (compat) | Medium |
| `#!/usr/bin/env python3` | 3 | Definitive |
| `type hints`: `def f(x: int)` | 3.5+ | High |
| `walrus operator`: `:=` | 3.8+ | Definitive |

### Binary Wheel Availability
For Python 2.7 packages, many no longer have binary wheels on PyPI. Strategy:
1. Check `https://pypi.org/pypi/{package}/json` for available wheel files
2. Filter by `python_requires` field
3. For numpy/scipy/scikit-learn on Python 2.7, use **last known working versions**:
   - numpy: 1.16.6 (last Py2.7)
   - scipy: 1.2.3 (last Py2.7)
   - scikit-learn: 0.20.4 (last Py2.7)
   - matplotlib: 2.2.5 (last Py2.7)
   - tensorflow: 1.15.5 (last Py2.7)
   - opencv-python: 4.2.0.32 (last Py2.7)
   - pandas: 0.24.2 (last Py2.7)

### Constraint Satisfaction for Dependencies
**pip's resolver** (since pip 20.3) uses a backtracking resolver. For older Python:
1. Pre-compute version compatibility matrix
2. Use constraint propagation: if package A requires B>=1.0,<2.0, restrict B's versions before attempting install
3. **Key insight from PYCONF**: version-level compatibility is insufficient; source-level verification is needed

---

## Technique Applicability Ranking

### Tier 1: Immediately Applicable (implement now)

| Technique | Source | Impact | Effort |
|-----------|--------|--------|--------|
| Import→package mapping database | pipreqs + PyEGo | Fixes ImportError (top failure) | Low |
| Python 2/3 syntax detection | PyEGo | Fixes SyntaxError (2nd failure) | Low |
| Last-known-good Py2.7 versions DB | Manual + PyPI | Fixes 75% of failures (Py2.7) | Low |
| Pre-validate package on PyPI | PYCONF | Avoid fruitless installs | Low |
| Rollback on failed install | Repo2Run | Prevent environment pollution | Medium |

### Tier 2: High Impact but More Effort

| Technique | Source | Impact | Effort |
|-----------|--------|--------|--------|
| Iterative error-log-driven repair | PLLM/Repo2Run | General improvement | Medium |
| Binary wheel availability check | PyPI API | Avoid build failures | Medium |
| Conflict resolution queue | Repo2Run | Better version resolution | Medium |
| Multi-Python-version Docker images | EnvBench | Try multiple versions | Medium |

### Tier 3: Research-Level (future work)

| Technique | Source | Impact | Effort |
|-----------|--------|--------|--------|
| Full knowledge graph (Neo4j) | PyEGo | Comprehensive resolution | High |
| LLM agent with environment monitoring | Repo2Run | Autonomous resolution | High |
| Source-level configuration validation | PYCONF | Verify before install | High |
| Static analysis (pyright) pre-check | EnvBench | Validate completeness | High |

---

## Recommended Implementation Priority

### Phase 1: Quick Wins (Days 1-2)
1. **Comprehensive import→package mapping**: Merge pipreqs mapping (~1,156 entries) + add scientific package mappings (cv2→opencv-python, sklearn→scikit-learn, etc.)
2. **Python 2.7 last-known-good version database**: Hardcode the last Py2.7-compatible versions for top 50 packages
3. **Better Python version detection**: Score-based system using the indicators table above
4. **PyPI pre-validation**: Check if package exists before attempting install

### Phase 2: Architecture Improvements (Days 3-4)
5. **Rollback mechanism**: Snapshot Docker state before each pip install, rollback on failure
6. **Binary wheel check**: Query PyPI for wheel availability for the target Python version before install
7. **Iterative repair with error classification**: Parse pip error output to classify failure type and apply targeted fix

### Phase 3: Advanced (Days 5+)
8. **Pattern learning from historical results**: Use pllm_results and pyego_results to build a "what worked" database
9. **Multi-version fallback**: Try primary Python version, fall back to secondary if syntax errors detected
10. **Conflict resolution**: When packages conflict, try progressively older versions

---

## Key Takeaway

The single most impactful improvement for our system is a **comprehensive import-name-to-package-name mapping combined with Python-2.7-specific version pinning**. This directly addresses:
- Import name confusion (cv2→opencv-python) — the #1 failure mode (ImportError)
- Python 2 syntax detection — the #2 failure mode (SyntaxError)
- Version compatibility — 75% of failures are Py2.7 where latest package versions don't work

All six papers converge on one insight: **the mapping from what code imports to what pip installs is non-trivial**, and getting this right is the foundation everything else builds on.
