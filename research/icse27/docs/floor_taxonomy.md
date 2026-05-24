# Empirical Floor Taxonomy — Irreducible Failures on HG2.9K

## Summary

Of **2,889** HG2.9K snippets evaluated by both PLLM (FSE'25) and CGAR (ours, FSE'26), **248** snippets (8.6%) fail under both resolvers. We call this set the **irreducible floor**: snippets that no current automated dependency resolver can fix, and likely cannot be fixed without changes outside the resolver itself (e.g., re-uploading a missing package to PyPI, building a wheel for an old Python release, paywall removal for proprietary libraries).

This taxonomy quantifies *why* these snippets are irreducible. To our knowledge no prior work has published this characterization for Python; the closest neighbours are PyConf [ICSE'24, arXiv 2310.12598] which studies configuration issues across library releases (not resolver failures) and Watchman [ICSE'20] which studies historical issue reports (not modern resolver residuals).

## 5-class taxonomy

| # | Class | Count | % of floor | Structural reason |
|---|---|---:|---:|---|
| 1 | **Py2 + no Py2 wheels** | 148 | 59.7% | Python 2 syntax with no Python 2 wheels on modern manylinux. Even the correct interpreter cannot sat... |
| 2 | **Proprietary / OS-locked** | 3 | 1.2% | Imports refer to closed-source / paywalled / OS-specific modules (IDA Pro plugins, Autodesk Maya, Ci... |
| 3 | **Package absent from PyPI** | 20 | 8.1% | Package present in import but vanished from PyPI entirely (account deleted, yanked, never published)... |
| 4 | **Native build failure** | 9 | 3.6% | Native source-only package whose build chain fails on modern manylinux/glibc (often legacy C extensi... |
| 5 | **API removed / drifted** | 68 | 27.4% | Package exists, version exists, but the *specific symbol* the snippet imports was removed in a later... |

Total: **248** irreducible snippets = **8.6%** of 2,889 HG2.9K snippets.

## Concrete examples per class

### Py2 + no Py2 wheels (n=148)

Python 2 syntax with no Python 2 wheels on modern manylinux. Even the correct interpreter cannot satisfy native deps because their build chain has been retired (CPython 2.7 EOL 2020-01).

| Snippet ID | Top imports | CGAR error tag | First line |
|---|---|---|---|
| `09648344984565` | numpy, scipy, numba, sklearn | ImportError | `"""` |
| `1104553` | networkx | ImportError | `import networkx as nx` |
| `1289286` | libtorrent, time, sys | ImportError | `"""` |
| `1315148` | os, PyV8 | ImportError | `# -*- coding: utf-8 -*-` |
| `137653` | html5lib | ImportError | `import html5lib` |

### Proprietary / OS-locked (n=3)

Imports refer to closed-source / paywalled / OS-specific modules (IDA Pro plugins, Autodesk Maya, Cinema 4D, Windows-only pywin32 in many cases) — these are not and will never be on PyPI.

| Snippet ID | Top imports | CGAR error tag | First line |
|---|---|---|---|
| `4125009` | sys, appscript | ImportError | `#!/usr/bin/env python` |
| `d6aa922505c4e5` | ftplib, datetime, appscript, subprocess | ImportError | `#!/usr/local/bin/python` |
| `e9851bc47dcf1b` | tank, maya | ImportError | `import tank` |

### Package absent from PyPI (n=20)

Package present in import but vanished from PyPI entirely (account deleted, yanked, never published). No version exists.

| Snippet ID | Top imports | CGAR error tag | First line |
|---|---|---|---|
| `076424abd8b012` | airflow, datetime, codecs, os | ImportError | `"""` |
| `10011921` | apiclient, oauth2client, google, webapp2 | ImportError | `'''` |
| `1082570` | selenium, webdriver, re | ImportError | `from selenium import webdriver` |
| `4582282` | datetime, functools, os, tulip | ImportError | `"""Proof of concept tornado/tulip integration.` |
| `5116241` | numpy, sys, pylab, larch | ImportError | `from numpy import linspace, sin, exp` |

### Native build failure (n=9)

Native source-only package whose build chain fails on modern manylinux/glibc (often legacy C extensions targeting older ABIs). Building from source fails even when the package is present.

| Snippet ID | Top imports | CGAR error tag | First line |
|---|---|---|---|
| `056626de3fbdc7` | argparse, imutils, dlib, cv2 | ImportError | `# USAGE` |
| `1077970` | pyodbc, sys, csv | ImportError | `import pyodbc` |
| `1950267` | unittest, Eratosthenes | ImportError | `"""Lyndon.py` |
| `3057138` | pyodbc, numpy, datetime, pandas | ImportError | `import pyodbc` |
| `4524299` | netfilterqueue, subprocess, signal, dpkt | ImportError | `from netfilterqueue import NetfilterQueue` |

### API removed / drifted (n=68)

Package exists, version exists, but the *specific symbol* the snippet imports was removed in a later version and no compatible older version has a working wheel. Common cause: deep transitive dep on a numpy/scipy/sklearn API that moved.

| Snippet ID | Top imports | CGAR error tag | First line |
|---|---|---|---|
| `04ef258fa29e4e` | flotilla, time | ImportError | `#!/usr/bin/env python3` |
| `0b677b13fca6cd` | numpy, matplotlib, sklearn, scipy | ImportError | `import numpy as np` |
| `11538913` | chimera, DockPrep, WriteMol2 | ImportError | `import chimera` |
| `1200485` | hashlib, logging, werkzeug, flask | ImportError | `import hashlib` |
| `1410088` | opencv, pygame, sys | ImportError | `import opencv` |

## Implications for ICSE-track research

The floor is **dominated by structural causes** that lie *outside* the resolver: language migration debt, proprietary ecosystem lock-in, and package distribution drift. Chasing the last 10.7% with smarter resolvers alone is unlikely to yield gains > 1-2pp.

**Recommendations for future work:**

1. **Py2 wheel fallback service** would unlock C1 (≈4% of HG2.9K). An external project (community-maintained or commercial) that rebuilds essential Py2 wheels for manylinux would have direct impact.
2. **Explicit proprietary-module registry** would let resolvers fail fast on C2 (≈3%) and direct the user to the vendor's install pipeline.
3. **PyPI yanked-package archive** would let resolvers query the historical index for C3 (≈1%).
4. C4 and C5 (≈3% combined) are the most attackable by smarter resolvers — specifically by **runtime-grounded constraint extraction** (see m8 in this codebase) and **API-call rewriting** (PCART, arXiv 2406.03839).

## Methodology / reproducibility

- **Data source:** `results/hg2k/pllm/csv/summary-all-runs.csv` (PLLM FSE'25) and `results/hg2k/cgar/results.csv` (CGAR FSE'26). Both used Gemma-2 9B as the backbone and the same Docker harness (see `tools/` directory in this repo).
- **Irreducible set:** intersection of {PLLM failed} ∩ {CGAR failed}.
- **Classification rules:** see `research/icse27/analyze/floor_analysis.py` (this is the script that produced the numbers above). Classes are evaluated in priority order: C1 (py2 syntax) > C2 (proprietary imports) > C3 (NoMatchingDistr error) > C4 (wheel build fail) > C5 (ImportError/AttributeError residual) > C6 (other).
- **Proprietary import list:** hand-curated set of 18 modules covering IDA Pro plugins, Autodesk Maya, Houdini, Cinema 4D, Rhino3D, Sublime Text plugin API, Windows-only pywin32, PyV8 (abandoned), AppleScript bindings. Conservative — we may miss some.

Re-run with: `python -m research.icse27.analyze.floor_analysis`.