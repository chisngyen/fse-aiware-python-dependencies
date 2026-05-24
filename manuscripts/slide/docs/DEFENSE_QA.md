# Defense Q&A — MEMRES & CGAR (ML Class Project)

> **Mục đích**: Tài liệu phòng thủ slide defense. Mọi claim đều có nguồn (paper / arXiv / repo). Mỗi câu hỏi thầy có thể hỏi đều có chỗ chỉ. Tài liệu này **đối chiếu được với ChatGPT/Gemini** mà không bị conflict.
>
> **Deck**: `main.tex` → `main.pdf`, **32 pages** = 24 main content + 5 section transitions + 3 backup.

---

## 0. Bối cảnh quan trọng (đọc trước khi defense)

| Thành phần | Trạng thái | Nguồn chính |
|---|---|---|
| **PLLM** | Baseline đã publish — ASEW 2025 (TU Delft) | arXiv 2501.16191v2 |
| **MEMRES** | Paper nhóm — **accepted FSE Companion '26** | arXiv 2604.16941v1 · DOI 10.1145/3803437.3808242 |
| **CGAR** | **Chưa publish** — extension đề xuất riêng cho môn ML | Chỉ có trong repo + slide |

⚠️ **Phát biểu mở đầu khi thầy hỏi về tính mới**:
> *"CGAR là phần em propose thêm trên nền MEMRES. MEMRES đã peer-review (FSE'26); CGAR là extension cho môn ML vì có thành phần ML rõ ràng (CSP, multi-agent, learning-from-failure) và vượt MEMRES."*

---

## ⭐ 0.5. Cheat sheet — câu PHẢI thuộc (từ quiz)

> Gộp lại các câu mình đã trả lời sai/không biết trong các round quiz. Mỗi card có **trigger keyword** + **câu đáp 1-2 dòng** + **example/data point** nếu có. Mỗi đêm học 1 category.

### 📚 A. DATASETS — 7 cards

#### A1. HG2.9K "hard" định nghĩa kỹ thuật
**Trigger**: *"Hard nghĩa là gì? Em định lượng cách nào?"*
> *"Hard = gist vẫn fail với `ImportError` sau khi áp dụng **Gistable's naive resolution strategy** (pip install all imports). DockerizeMe paper (ICSE'19) chạy naive pip trên 10K Gistable, 2891 gists vẫn fail → đó là HG2.9K."*

**Keyword**: **naive `pip install` vẫn fail**.

---

#### A2. Snippet count: 2891 / 2890 / 2889
**Trigger**: *"HG2.9K có 2891 hay 2890? Em chạy bao nhiêu?"*
> *"Gốc 2891. MEMRES lọc 1 file empty (0 byte) còn 2890. CGAR thực chạy 2889 (mất thêm 1 timeout extreme). Pass rate 87.1% = 2516/2889."*

**Đừng nói "kệ đi"** — thầy hỏi mà bí là mất điểm tin cậy.

---

#### A3. Gistable stats (3 số phải nhớ)
**Trigger**: *"Gistable original khảo sát gì?"*
> *"Gistable (MSR'18) khảo sát **10,000+ gists**: **24.4%** chạy được không cần sửa; **52%** fail do missing imports; phần còn lại do version conflict/Py2-vs-Py3. HG2.9K là hard subset 2891 trong số đó."*

**3 số card**: `10K / 24.4% / 52%`.

---

#### A4. GitChameleon — 2 paper version
**Trigger**: *"GitChameleon paper có 116 problems, sao slide ghi 328?"*
> *"GitChameleon có 2 phiên bản:*
> *- **v1 (arXiv 2411.05830, Nov'24)**: 116 problems cho code-gen.*
> *- **v2 (arXiv 2507.12367, Jul'25)**: mở rộng 328 examples + closed-weight LLM baselines (GPT-4o, o1...).*
>
> *Em dùng `final_fix_dataset.jsonl` từ v2 — đó là lý do slide ghi 328."*

---

#### A5. "No metadata" vs PyPI runtime query
**Trigger**: *"Em nói snippet no metadata nhưng tool dùng PyPI metadata — mâu thuẫn?"*
> *"Không. 2 khái niệm khác:*
> *- **Snippet (input)** không metadata: không `requirements.txt`, không `setup.py`, không comment version.*
> *- **Tool query PyPI API runtime** qua HTTPS để lấy version list, requires_python, wheel info.*
>
> *Tất cả 3 tool (PLLM RAG, MEMRES PyPI validator, CGAR Candidate Graph Builder) đều query API runtime. Đây là external service, không vi phạm benchmark."*

**Keyword phân biệt**: `input metadata` (no) vs `external service runtime query` (yes).

---

#### A6. requires_dist KHÔNG cover gì (3 thứ)
**Trigger**: *"PyPI có `requires_dist` đủ rồi, sao cần constraint learning từ Docker fail?"*
> *"`requires_dist` chỉ là **static structural info** (install compat). Không cover:*
> *1. **API behavior change runtime** — `scipy.misc.imread` deprecated trong scipy 1.2+; install OK nhưng import fail.*
> *2. **Native build failure** — `numpy 1.16` cần `libopenblas-dev` + `gfortran`; PyPI không nói.*
> *3. **Deep transitive conflict** — scipy 1.5 → numpy>=1.16.5 → Python>=3.5; chained 3+ hops.*
>
> *CGAR học **dynamic constraints** từ Docker error — điều SMT-LLM (chỉ dùng requires_dist) không có."*

---

#### A7. Tại sao GitChameleon mà không phải Repo2Run / DyPyBench?
**Trigger**: *"Sao chọn benchmark này?"*
> *"3 lý do:*
> *1. **Cùng scope snippet-level** — Repo2Run là repo-level (toàn project), DyPyBench là dynamic analysis; khác bài toán.*
> *2. **Comparable LLM baseline có sẵn** — GitChameleon v2 đã eval GPT-4o/Gemini/o1/GPT-4.1+RAG cùng protocol.*
> *3. **OOD complement** — modern code 2014-2023, unit-test driven, bổ sung HG2.9K (legacy 2011-2019, import-only).*
>
> *Future work: thêm Repo2Run nếu mở rộng sang repo-level."*

**⚠️ Đừng coi câu hỏi là vô lý** — mỗi câu thầy hỏi là chance show methodology rationale.

---

### 🤖 B. METHOD — 8 cards

#### B1. Multi-Agent có thực sự là agent không?
**Trigger**: *"4 agent có thật, hay chỉ rename function?"*

**3 tiêu chí operational** (đã có code trong `tools/cgar/src/agents/`):
> *"Mỗi agent thỏa 3 tiêu chí:*
> *1. **Role riêng** — Planner/Executor/Analyzer/Critic với input-output contract khác.*
> *2. **Tool access riêng** — mỗi agent có set tool method khác:*
>   *- Planner: `query_pypi`, `wheel_filter`, `solve`*
>   *- Executor: `build_docker`, `run_import` (no LLM)*
>   *- Analyzer: `parse_error`, `gen_constraint`*
>   *- Critic: `analyze_failures`, `suggest_strategy`*
> *3. **State update khác** vào shared ConstraintStore.*
>
> *Đây là **agentic decomposition** — em không claim fully autonomous, nhưng đủ tiêu chí role+tool+state separation. Code: `tools/cgar/src/agents/`."*

---

#### B2. 4 agent giao tiếp qua gì?
**Trigger**: *"Communication mechanism?"*
> *"2 mechanism:*
> *1. **Shared ConstraintStore** — Analyzer ghi (`add`, `add_combo`, `add_upper_bound`); Planner đọc (`is_infeasible`) để filter. Persistent shared memory, không direct call.*
> *2. **Sequential message passing** — Planner → Executor → (success/fail) → Analyzer → Critic (nếu stuck) → loop.*
>
> *Loose coupling: mỗi agent chỉ biết Store, không biết agent khác tồn tại."*

---

#### B3. HARD vs SOFT — trigger rule
**Trigger**: *"Analyzer quyết HARD/SOFT theo cách nào?"*

> *"**Regex pattern match trên error log** (code: `failure_injector.py`):*
> *- **HARD**: log match deterministic incompatibility (`requires a different Python`, `No matching distribution found`, `python_requires`) → cấm vĩnh viễn sau **1 observation**.*
> *- **SOFT**: log match runtime errors (`ImportError`, `ModuleNotFoundError`, `NonZeroCode`, DLL errors) → cấm tạm thời, cần **≥2 observations** (soft_threshold).*"*

---

#### B4. UPPER bound — example concrete
**Trigger**: *"Cho 1 ví dụ UPPER bound."*
> *"Trigger: regex `cannot import name X from pkg`.*
>
> *Example:*
> *- Snippet: `from keras.layers.wrappers import TimeDistributedDense`*
> *- Cài `keras==2.5`: import fail với `cannot import name 'TimeDistributedDense' from 'keras.layers.wrappers'`*
> *- Analyzer infer API removed → add **UPPER bound `keras < 2.5`**.*
> *- Solver tự loại keras 2.5+ trong attempt sau, pick keras 2.2.*
>
> *Khác HARD: HARD cấm 1 điểm, UPPER cấm cả khoảng `[current, ∞)`. Code: `failure_injector.py: inject_api_removed()`."*

---

#### B5. Backtracking vs SMT — tại sao không Z3 như SMT-LLM?
**Trigger**: *"SMT-LLM dùng Z3, sao em không?"*
> *"3 lý do:*
> *1. **Scale nhỏ** — typical <10 packages × ~10 versions = ~100 candidates; Z3 setup overhead lớn hơn backtrack đơn giản.*
> *2. **Constraint dynamic** — CGAR học SOFT count threshold (≥2). Z3 monotonic — add không revoke được.*
> *3. **Newest-first priority** — backtracking iterate sorted candidates, picks newest viable. Z3 trả về satisfying assignment bất kỳ — khó control preference.*
>
> *Note: SMT-LLM 83.6% (FSE'26), CGAR 87.1% **+3.5pp** với 7× ít LLM calls."*

---

#### B6. Critic vs Analyzer — khác chỗ nào?
**Trigger**: *"Cả 2 đều là LLM xử lý fail, khác gì?"*
> *"Khác **trigger condition** + **scope**:*
> *- **Analyzer**: chạy MỖI lần fail; input = 1 error log; output = 1 typed constraint. Reactive, narrow.*
> *- **Critic**: chỉ kích hoạt khi **stuck** (≥3 fails cùng error type liên tiếp); input = toàn failure history; output = strategy pivot (`switch_python`, `mark_unfixable`, `continue`). Reflective, broad.*
>
> *Tương tự System 1 vs System 2 (Kahneman). Code: `agents/critic_agent.py: is_stuck()`."*

---

#### B7. is_stuck heuristic — tại sao `len(types) <= 1`?
**Trigger**: *"Tại sao stuck = cùng error type, không phải đếm fails?"*

> *"`is_stuck = ≥3 fails consecutive VÀ tất cả cùng error type`.*
>
> *Logic: nếu fail nhưng error type **đổi** giữa các attempt → local fixes đang work (1 lỗi fix xong, lộ ra lỗi tiếp theo). Nếu cùng error type lặp → local fixes KHÔNG đổi failure mode → cần pivot strategic.*
>
> *Ví dụ: SyntaxError × 3 → có thể là Py2 code (cần switch Python, không phải đổi package). Code: `critic_agent.py: is_stuck()`."*

---

#### B8. Novelty defense — Constraint Learning đã có từ 1990s
**Trigger**: *"Dechter 2003 đã có Constraint Learning, em đóng góp gì?"*
> *"Em **không claim novelty CSP theory**. Đóng góp là **system contribution**:*
> *1. **Domain-specific formulation** — Python dep resolution thành CSP tuple ⟨X, D, C⟩.*
> *2. **LLM-as-constraint-extractor** — pretrained LLM 'translator' từ noisy Docker log → typed constraint.*
> *3. **3-tier hierarchy HARD/SOFT/UPPER** — phù hợp uncertainty của error log (deterministic vs observed vs inferred range).*
> *4. **Session-scoped sharing** — constraints học trong 1 repo dùng lại cho snippet kế.*
>
> *Tóm lại: **system design + integration**, không phải solver theory."*

---

### 🎯 Cách dùng cheat sheet

1. **Đêm trước defense**: scan toàn bộ A1-A7 + B1-B8 (~15 cards). Mỗi card đọc 30s.
2. **Highlight 5 cards critical nhất**: A4 (GitCham 2 paper), A6 (requires_dist 3 thứ), B1 (Multi-Agent 3 tiêu chí), B4 (UPPER example), B5 (vs SMT-LLM).
3. **Trong present**: thuộc 2 câu **chủ động** (slide 16 R1 + slide 22 Conclusion) để chặn trước.
4. **Trong Q&A**: nghe câu hỏi → recall keyword → tìm card → đáp.

---

## 1. Slide map (deck mới) — Mapping mọi claim → Nguồn

### Slide 3 — Bối cảnh ("Nghĩa địa" mã nguồn mở)
| Claim | Nguồn |
|---|---|
| Repo Python cũ "chết môi trường" trên GitHub | Gistable (Horton & Parnin, MSR 2018) — 24.4% gist chạy được |

### Slide 4 — Bài toán & Yêu cầu đánh giá (TikZ I/O + 3 cột)
| Claim | Nguồn |
|---|---|
| Input/Output/Success criterion (no metadata, no requirements) | PLLM §I; MEMRES §1 |
| 10 GB VRAM, Gemma-2 9B qua Ollama | MEMRES §3 (i5-14600K + RTX 5070); PLLM §IV.C |
| 10 retries, 180s/build, 500s total | MEMRES §3 |
| Pass rate primary | PLLM §IV.D — "executes without critical runtime errors" |

### Slide 5 — Dependency Gap (code + domino + 500K block)
| Claim | Nguồn |
|---|---|
| `scipy.misc.imread` removed in scipy >= 1.2 | SciPy release notes |
| `cv2` → `opencv-python` naming | PLLM §III.B (Listing 5), MEMRES §2.4 |
| ~500K PyPI packages | PLLM §III.F ("550,000+ modules") |

### Slide 6 — Bùng nổ tổ hợp (figure only)
| Claim | Nguồn |
|---|---|
| Combinatorial explosion | Minh họa từ PLLM §I và MEMRES §1 |

### Slide 7 — Background — Python Dependency Conflicts ⭐ NEW
| Claim | Nguồn |
|---|---|
| Direct vs Transitive conflict | PLLM §I |
| ML/Scientific Python đặc biệt khó (CUDA, BLAS) | PLLM §I (TensorFlow/CUDA versioning) |
| Gistable MSR'18: 10K gists, 24.4% chạy được, 52% missing imports | Horton & Parnin (Gistable paper, MSR 2018) |
| HG2.9K = hard subset 2891 gist | DockerizeMe paper (Horton & Parnin, 2019) |

### Slide 8 — Datasets (image)
| Claim | Nguồn |
|---|---|
| HG2.9K: 2891 (MEMRES dùng 2890 do filter 1 file rỗng) | PLLM §IV.B, MEMRES §3 |
| GitChameleon: 328 (chúng em mở rộng từ 116 gốc) | arXiv 2411.05830 (GitChameleon paper, NeurIPS workshop 2024) |

### Slide 9 — Related Work (3 categories: KG / Regex / LLM+RAG) ⭐ NEW
| Claim | Nguồn |
|---|---|
| KG: cần update DB liên tục | PyEGo §I, ReadPyE §I |
| Regex/log-parse: brittle to format | PLLM §II.A đánh giá PyDFix |
| LLM+RAG: blind trial-error, no constraint learning | Quan sát nhóm về PLLM |

### Slide 10 — Related Work — Tổng hợp (table + timeline scatter) ⭐ NEW
| Claim | Nguồn |
|---|---|
| pip naive ~24% | Ước lượng từ Gistable paper |
| DockerizeMe (ICSE'19, KG Libraries.io) ~30% | Ước lượng |
| PyEGo (ICSE'22) 45.0% | **Reproduction nhóm trên HG2.9K** (CLAUDE.md) |
| ReadPyE (TSE'24) 47.2% | **Reproduction nhóm** |
| PyDFix regex log-parse | PLLM §II.A trích Mukherjee et al. ICSE 2021 |
| GPT-4o / Gemini / o1 / GPT-4.1+RAG | GitChameleon paper (arXiv 2507.12367) |
| PLLM (ASEW'25) 44.8% (single) / 54.7% (10-run union) | PLLM Table III · reproduction nhóm |
| Plateau ~47% on HG2.9K timeline | Observation: ReadPyE 47.2% highest pre-MEMRES |

### Slide 11 — MEMRES Pipeline (image `memres-pipeline.png` + radar)
| Claim | Nguồn |
|---|---|
| 4 stages: Intra-Session Memory / Hybrid Eval / Confidence Cascade / Build Loop + Reflexion | MEMRES Figure 1, §2 |
| 2 side memories: Self-Evolving Memory + Error Pattern KB | MEMRES §2.3, §2.4 |
| Cache hit + Py2 fast bypass LLM | MEMRES §2.1, §2.4 (Py2 detector) |
| MEMRES 86.3% reproduction (paper 86.6% ± 9.3) | Reproduction single-run · MEMRES Table 1 |
| PLLM 44.8% reproduction (paper 54.7% 10-run union) | Cùng |

### Slide 12 — Từ MEMRES đến CGAR (3 gap → 3 fix)
| Claim | Nguồn |
|---|---|
| 12.8% bí đường (API removed, source-only build) | Tính từ MEMRES §3.3 + repo analysis |
| 335s/snippet avg MEMRES | MEMRES Table 1 |
| MEMRES blackbox Docker, không thành ràng buộc | MEMRES §2.2 (cascade dùng heuristics, không có constraint store) |

### Slide 13 — CGAR Overview (`multi-agents.png`)
| Claim | Nguồn |
|---|---|
| 4-stage extension trên MEMRES (Stage 2.5–2.8) | Code repo `tools/cgar/src/` |
| Constraint induction pipeline | CLAUDE.md architecture section |

### Slide 14 — CGAR Multi-Agent Loop (TikZ)
| Claim | Nguồn |
|---|---|
| Planner / Executor / Analyzer / Critic | `tools/cgar/src/cgar_resolver.py` |
| Session Store HARD / SOFT / UPPER | `tools/cgar/src/constraint_store.py` |
| Mỗi fail → +1 constraint → Planner kế tiếp né cả vùng | `tools/cgar/src/failure_injector.py` |
| Tools: `query_pypi`, `wheel_filter`, `build_docker`, `parse_error`, `gen_constraint` | `tools/cgar/src/` |

### Slide 15 — CGAR Formulation as CSP
| Claim | Nguồn |
|---|---|
| Tuple P = ⟨X, D, C⟩ | CSP chuẩn (Russell & Norvig, AIMA) |
| HARD/SOFT/UPPER 3 tiers | Code `constraint_store.py` |
| k=50 attempts max | `tools/cgar/src/constraint_solver.py` |
| Wheel-first sort, semver giảm dần | `tools/cgar/src/candidate_graph_builder.py` (`_has_linux_wheel()`) |

### Slide 16 — CGAR Session-scoped Learning (image)
| Claim | Nguồn |
|---|---|
| Session = 1 repository = nhiều snippets | Design choice trong `constraint_store.py` |
| Session Store rescue 19.7% snippets | **Subset eval n=494 MEMRES-failures**: 71/396 = **17.9%** rescue. **Số 19.7% trên slide là cần update → 17.9%** (xem §5 checklist) |

### Slide 17 — Comprehensive Comparison (R1) — 11 methods × 2 benchmarks
| Claim | Nguồn |
|---|---|
| Full leaderboard cả HG2.9K và GitChameleon | Reproduction + papers |
| CGAR 87.1% HG2.9K | Repo `results/hg2k/cgar/results.csv` (2516/2889) |
| CGAR 83.2% GitCham | Repo `results/gitchameleon/cgar/` (273/328) |
| 22.3s avg | Cùng nguồn |
| Vượt o1 +32.0pp trên GitCham | 83.2 − 51.2 = +32.0pp |
| Nhanh hơn PLLM 16.6× | 369.6 / 22.3 = 16.57 |

### Slide 18 — HG2.9K Error Breakdown (R2) — bar chart PLLM vs CGAR
| Claim | Nguồn |
|---|---|
| SyntaxError 494 → 0, NoMatchDist 282 → 0, NoWheel 83 → 0, AttrError 83 → 0 | Repo error analysis `results/hg2k/cgar/` |
| ImportError 433 → 372 | Residual failure mode |
| Total fails 1596 → 373, Δ = −76.6% | Tính: (1596−373)/1596 |
| Rescue rate theo PLLM error type | Bảng horizontal bar bên phải |

### Slide 19 — GitChameleon Open vs Closed (R3)
| Claim | Nguồn |
|---|---|
| GPT-4o 49.1%, Gemini 50.0%, o1 51.2%, GPT-4.1+RAG 58.5% | GitChameleon paper Table |
| PLLM 65.5%, MEMRES 81.7%, **CGAR 83.2%** | Reproduction |
| Cross-benchmark gap: PLLM −20.7pp, MEMRES −4.6pp, **CGAR −3.9pp** | Tính từ HG2.9K vs GitCham pass rate |
| CGAR (open 9B) vượt o1 (>200B closed) +32.0pp | 83.2 − 51.2 |

### Slide 20 — Speed & Ablation (merged R4+R5)
| Claim | Nguồn |
|---|---|
| Duration GitCham (ℓ=5): PLLM 67/146/104s, MEMRES 30/73/47s, CGAR 17.8/48.5/35.6s | Reproduction (median/P90/fail-avg) |
| Ablation n=494: Full 71, w/o session 56 (−21%), w/o wheel 40 (−44%), w/o upper bound 23 (−68%) | `results/eval-subsets/cgar-rescue/` |
| Upper bound là component quan trọng nhất | Ablation result |

### Slide 21 — Hạn chế (Hard Floor + 4 architectural limits)
| Claim | Nguồn |
|---|---|
| Hard Floor 310 snippets (10.7%) cả PLLM + CGAR đều fail | CLAUDE.md analysis |
| Root cause: Py2 41.6%, system/private 25.8%, NoMatchDist 13.3%, CouldNotBuildWheels 8.1%, API removed 4.0%, Other 7.2% | Repo error analysis |
| 4 hạn chế kiến trúc: PyPI live · single ecosystem · LLM analyzer brittle · single-worker store | Nhóm tự đánh giá |

### Slide 22 — Hướng phát triển (Future Work, 4 cards)
| Claim | Nguồn |
|---|---|
| Mở rộng đa ngôn ngữ (npm, cargo, go.mod) | Đề xuất nhóm |
| Federated Session Store | Đề xuất nhóm |
| Fine-tune Analyzer LLM trên log parsing | Đề xuất nhóm |
| Online Learning (self-evolving KB) | Đề xuất nhóm (lấy ý từ Mobile-Agent-E) |

### Slide 23 — Tóm tắt & Kết luận
| Claim | Nguồn |
|---|---|
| Paradigm shift: thử-sai → học ràng buộc | Định vị của nhóm |
| Plateau ~47% bị vượt qua nhờ "Lỗi → Luật" | Slide 10 timeline + slide 17 results |

### Slide 24 — Thank you (cảm ơn + tên team)
| Logo HCMUS + FSE | Branding |

### Backup slide 30 — Why Gemma-2 9B?
| Claim | Nguồn |
|---|---|
| Bảng Table I + Table II merged: 6 LLM × {RAG ✓, RAG ✗} | PLLM paper §V.A (Table I, II) |
| G2-9B (RAG ✓): 203 fixes, 166 pass 5/5 — top consistency | PLLM Table I, II |
| G2-27B (RAG ✗): 207 fixes nhưng vượt 10 GB VRAM | PLLM Table I, paper §IV.A |

### Backup slide 31 — MEMRES Stage Details (6 cards)
| Claim | Nguồn |
|---|---|
| Stage 1: Jaccard ≥ 0.5, reset giữa runs | MEMRES §2.1 |
| Stage 2: 13 usage patterns, 11 ecosystems, Py2 detector (13 Py2 + 5 Py3 indicators) | MEMRES §2.4 |
| Stage 3 Cascade: L1 Session · L2 Compat Map (40+pkg×8Py) · L3 Templates (23 sets) · L4 Co-occurrence (50K req.txt, pre-2020) · L5 Heuristics (45+ rules) · L6 LLM | MEMRES §2.2 |
| Stage 4: 35+ pip→apt mappings, version fallback, Reflexion | MEMRES §2.4 |
| Self-Evolving Memory: tips + shortcuts, Mobile-Agent-E inspired | MEMRES §2.3 |
| Error Pattern KB: 200+ mappings, 35 corrections, 8 regex | MEMRES §2.4 |
| 68% no-LLM, 15.2s median, 0.34 calls/snippet | MEMRES Table 3 |

### Backup slide 32 — GitChameleon Re-framing
| Claim | Nguồn |
|---|---|
| Gốc 116 problems → mở rộng 328 (`final_fix_dataset.jsonl`) | GitChameleon paper (arXiv 2411.05830) |
| Concat starting_code + solution + test thành 1 snippet.py | `tools/cgar/scripts/convert_gitchameleon.py` |
| Giấu version trong snippet, lưu riêng `ground_truth.csv` | Cùng |
| Success criterion = pass unit test (semantic), không phải chỉ import | Design choice của re-framing |

---

## 2. Câu hỏi thầy có thể hỏi (kèm câu trả lời)

### A. Câu hỏi về xuất xứ & tính mới

**Q1: Paper MEMRES đã publish chưa? Ở đâu?**
> Đã accept tại **FSE Companion 2026** (ACM SIGSOFT). DOI: 10.1145/3803437.3808242. Preprint: arXiv 2604.16941v1 (18 Apr 2026). Tác giả đầu: Trần Chí Nguyên, Đào Sỹ Duy Minh, Huỳnh Trung Kiệt, +3 đồng tác giả, supervisor TS. Vũ Nguyên.

**Q2: CGAR là gì? Có paper không?**
> CGAR (Constraint-Guided Agentic Resolution) là **đề xuất mở rộng của nhóm** trên nền MEMRES, **chưa publish**. Em propose riêng cho môn ML vì: (1) vượt MEMRES (87.1% vs 86.3% HG2.9K, 83.2% vs 81.7% GitCham), (2) có thành phần ML rõ ràng (CSP, multi-agent, learning-from-failure).

**Q3: Đóng góp của em cụ thể là gì?**
> Em first-author paper MEMRES (đã peer-review FSE'26), thiết kế và implement toàn bộ CGAR (`tools/cgar/`). MEMRES là phần đã được academia validate; CGAR là extension cho môn ML.

**Q4: PLLM của ai?**
> PLLM (Bartlett, Liem, Panichella — TU Delft) công bố tại **IEEE/ACM ASEW 2025**. arXiv 2501.16191v2. Đây là **baseline state-of-the-art trước MEMRES**.

---

### B. Câu hỏi về số liệu (potential conflict với ChatGPT)

**Q5: PLLM paper ghi 54.7% nhưng slide em ghi 44.8%, sao khác?**
> Hai con số khác do **cách tính khác**:
> - **PLLM paper Table III**: 1583/2891 = 54.7% là **union 10 runs** — gist nào pass ít nhất 1 lần.
> - **Reproduction nhóm**: 1295/2891 = 44.8% là **single-run** trên cùng harness Docker, cùng Gemma-2 9B + RAG.
>
> Để công bằng so sánh với MEMRES/CGAR cùng harness, em dùng single-run cho cả 3 tool.

**Q6: MEMRES paper ghi 86.6% nhưng slide ghi 86.3%, sao?**
> Paper: **10-run avg = 86.6% ± 9.3** (MEMRES Table 1). Slide: single-run reproduction = 86.3%. Trong khoảng ±0.3% so với mean — fully consistent.

**Q7: 94% giảm thời gian tính ra sao?**
> (369.6 − 22.3) / 369.6 ≈ 94.0% trên HG2.9K. Nguồn: CLAUDE.md results table.

**Q8: CGAR 87.1% trên HG2.9K — đã trừ snippet rỗng chưa?**
> Có. HG2.9K gốc 2891 → bỏ 1 file rỗng (như MEMRES) → 2890. CGAR thực chạy 2889 do 1 snippet timeout extreme. 2516/2889 = 87.05%.

**Q9: Speedup 1.64× MEMRES → CGAR đo trên benchmark nào?**
> Trên **GitChameleon** vì cả 2 đều dùng `-l 5` (5 loop budget). Trên HG2.9K không fair vì MEMRES dùng `-l 10`, CGAR dùng `-l 5`.

**Q10: Ablation n=494 — số rescue 71 — sao chọn subset này?**
> n=494 là **subset MEMRES-failures** trên HG2.9K. Dùng để eval CGAR như "rescue layer" trên MEMRES (xem `results/eval-subsets/cgar-rescue/`). Trong full HG2.9K, CGAR rescue 1286/1596 = 80.6% PLLM-failures.

---

### C. Câu hỏi về methodology

**Q11: Sao chọn Gemma-2 9B mà không dùng GPT-4?**
> Constraint của bài: **mã nguồn mở, ≤10 GB VRAM** (PLLM §IV.A). GPT-4 closed-weight nên không reproduce được. PLLM đã so 6 LLM open-source → G2-9B + RAG balance tốt nhất.
>
> 👉 **Jump tới backup slide 30** để show Table I/II.

**Q12: Sao không dùng Gemma-2 27B vì nó cao hơn?**
> G2-27B no-RAG đạt 207 fixes (cao hơn G2-9B 203) nhưng **27B model size ≈ 16-19 GB VRAM**, vượt budget 10 GB. G2-9B là model lớn nhất fit budget.

**Q13: CGAR cần Docker — không thể chạy offline?**
> Cần build thực tế vì: (1) PyPI có version chỉ source-only — phải build mới biết fail, (2) C-extension cần native libs (apt-get) — chỉ Docker đảm bảo isolation. Đây cũng là design của PLLM (§III.C) và MEMRES (§2.4).

**Q14: CSP của em là cổ điển hay biến thể?**
> **CSP biến thể với constraint learning online**:
> - Cổ điển: variables/domains/constraints cố định trước.
> - CGAR: constraints **được học runtime từ Docker error** qua FailureInjector (`failure_injector.py`). Gần với *Constraint Learning* trong AI (Dechter, "Constraint Processing", 2003).

**Q15: Multi-agent thật sự cần thiết, hay chỉ là pipeline?**
> Mỗi agent có **state riêng + LLM prompt riêng + tool riêng**:
> - **Planner** (LLM): chọn candidates dựa trên constraint store · tools `query_pypi`, `wheel_filter`
> - **Executor** (Tool): build Docker, không LLM · tools `build_docker`, `run_import`
> - **Analyzer** (LLM): phân tích log → typed constraint · tools `parse_error`, `gen_constraint`
> - **Critic** (LLM): self-reflect khi stuck · tools `analyze_failures`, `suggest_strategy`
>
> Kiến trúc theo Mobile-Agent-E (NeurIPS'25) + Reflexion (NeurIPS'23).

**Q16: Session store có overfitting không?**
> Mitigation (MEMRES §3.1 "Threats to Validity"):
> - State **reset hoàn toàn** giữa các batch run độc lập
> - Order-randomized 10 runs, std chỉ ±9.3 snippets
> - Co-occurrence data filter pre-2020 → không leak với HG2.9K
> - KB curation pre-evaluation; 50 entries từ held-out subset (disjoint với HG2.9K)

**Q17: 10.7% hard floor — sao không cố cứu nốt?**
> Root cause analysis:
> - 41.6% Python 2 syntax với package không có Py2 wheel trong manylinux hiện đại
> - 25.8% imports system/private (`idaapi`, `PyV8`, `appscript`)
> - 13.3% package biến mất khỏi PyPI
> - 8.1% C compilation, glibc incompat
>
> Đây là *irreducible floor* — reality của legacy code, không phải limitation tool.

**Q18: GitChameleon là code-generation benchmark — sao dùng làm dep resolution?**
> GitChameleon gốc test LLM "viết code đúng version cho given library". Em **re-frame** thành dep resolution test: concat `starting_code + solution + test` thành 1 snippet, **giấu version**, để resolver discover từ imports.
>
> 👉 **Jump backup slide 32** để show before/after JSON vs converted snippet.
>
> **Tại sao khó hơn HG2.9K**: success = pass unit test (semantic correctness). Cài `torch==2.0` thay vì `1.9` vẫn import OK nhưng assert fail → bắt buộc pick đúng version.

---

### D. Câu hỏi về Related Work

**Q19: Tại sao chỉ so với 3-4 tool? Còn DockerizeMe / V2 / Repo2Run?**
> **Lý do exclude:**
> - **Repo2Run / ExecutionAgent / EnvBench**: scope **repo-level**, không snippet-level (khác bài toán).
> - **DockerizeMe / V2 / PyCRE**: test trên **Gistable** thường, không có HG2.9K result.
> - **DepsRAG**: dùng proprietary LLM backend, không reproducible.
>
> 3 baseline chọn (PyEGo, ReadPyE, PLLM) đại diện 3 paradigm: **KG cổ điển · KG + heuristic · LLM**.

**Q20: Self-evolving agents inspiration là gì?**
> - **Mobile-Agent-E** (Wang et al., NeurIPS SEA 2025): tips + shortcuts paradigm cho GUI agents → MEMRES adapt cho dependency resolution.
> - **Reflexion** (Shinn et al., NeurIPS 2023): verbal RL, agent học từ failure trace → Critic Agent của CGAR dùng pattern này.

**Q21: Constraint Learning có gì mới? Dechter 2003 đã có rồi.**
> Đúng — Constraint Learning (nogood learning trong SAT solving) tồn tại từ 1990s. CGAR **không claim CSP theory novelty** mà claim **system contribution**:
> 1. Integrate CSP solver với multi-agent LLM pipeline
> 2. Inject constraint từ runtime Docker error qua LLM-based Analyzer
> 3. Session-scoped sharing across snippets trong cùng repo

---

### E. Câu hỏi "ChatGPT có thể bắt bug"

**Q22: Mobile-Agent-E là cho GUI agents, không phải dependency — phản biện?**
> Đúng — Mobile-Agent-E gốc dành cho GUI. MEMRES **adapt paradigm tips/shortcuts** (không copy kiến trúc). Adapt được vì: tips = "NL guideline reusable across tasks", shortcuts = "validated solution mapped via similarity" — hai khái niệm này task-agnostic.

**Q23: Reflexion gốc cho code-gen, không phải dep resolution?**
> Reflexion original có 3 domain: decision-making, reasoning, programming. MEMRES dùng **"verbal reinforcement" generic principle** — agent self-reflect verbal trace, áp dụng cho bất kỳ task có observable feedback. Docker build log là feedback hợp lệ.

**Q24: Sao không so với Claude / GPT-4 trên HG2.9K?**
> PLLM paper §VI có test Claude 4 Sonnet (manual): fix được 15 PLLM-failures nhưng **fail toàn bộ PLLM-only successes** vì hallucinate version. Trên GitChameleon: o1 51.2%, GPT-4.1+RAG 58.5% — đều thấp hơn MEMRES/CGAR mà tốn nhiều API cost hơn. Closed-weight cũng vi phạm constraint "open-source LLM" của setup.

**Q25: Bar chart slide 18 cho PLLM 494 SyntaxError → CGAR 0 — quá tốt, có chắc không?**
> Có. **Py2 detector** (đã ở MEMRES) eliminate hầu hết SyntaxError (91% SyntaxError thực ra là Py2 mis-exec, MEMRES §2.4). CGAR thừa hưởng Py2 detector + thêm **wheel filter** loại version không có manylinux wheel → no source-build → no SyntaxError vĩnh viễn. ImportError là failure mode duy nhất còn vì package thật sự không tồn tại.

**Q26: 19.7% session store rescue trên slide 16 với 21% w/o trên slide 20 — conflict?**
> Hai metric khác nhau:
> - **Slide 16**: Session Store rescue **17.9%** (71/396) trên subset MEMRES-failures n=494. **Số 19.7% trong caption hiện tại là cần update → 17.9%**.
> - **Slide 20**: ↓21% khi ablate session store = Δ rescue (71 → 56, giảm 15/71 ≈ 21%).

**Q27: "Plateau ~47%" trên slide 10 — có thực không?**
> Yes. Trên HG2.9K:
> - DockerizeMe 2019: ~30%
> - PyEGo 2022: 45.0%
> - ReadPyE 2024: 47.2%
> - PLLM 2025: 44.8% (single-run reproduction)
>
> 4 phương pháp consecutive đều dưới 50% — đó là plateau. MEMRES (86.6%) là breakthrough đầu tiên.

---

## 3. Số "khó nuốt" — chuẩn bị giải thích chi tiết

| Số | Giải thích sẵn |
|---|---|
| **87.1%** | 2516/2889 HG2.9K — `results/hg2k/cgar/results.csv` |
| **22.3s** | Avg all snippet (pass+fail). Pass-only: 17.0s |
| **94% giảm** | (369.6 − 22.3) / 369.6 trên HG2.9K |
| **0.31 LLM calls/snippet** | CGAR (vs MEMRES 0.34, PLLM 1-5) |
| **17.9% rescue** | CGAR cứu 71/396 MEMRES-failures (subset eval n=494) |
| **+32pp vs o1** | GitCham: CGAR 83.2 − o1 51.2 = +32.0pp |
| **10.7% hard floor** | 310/2891 cả 3 tool đều fail |
| **86.3% vs 86.6%** | Reproduction single-run vs paper 10-run avg ±9.3 |
| **44.8% vs 54.7%** | Reproduction single-run vs paper 10-run union |

---

## 4. References (dán vào appendix slide nếu cần)

```
[1] A. Bartlett, C. Liem, A. Panichella. "The Last Dependency Crusade:
    Solving Python Dependency Conflicts with LLMs." ASEW 2025, pp. 66-73.
    arXiv:2501.16191v2

[2] T. C. Nguyen, S. D. M. Dao, T. K. Huynh, P. H. Pham, L. P. Q. Nguyen,
    V. Nguyen. "MEMRES: A Memory-Augmented Resolver with Confidence
    Cascade for Agentic Python Dependency Resolution." FSE Companion '26.
    DOI: 10.1145/3803437.3808242. arXiv:2604.16941v1

[3] E. Horton, C. Parnin. "DockerizeMe: Automatic Inference of Environment
    Dependencies for Python Code Snippets." ICSE 2019, pp. 328-338.

[4] E. Horton, C. Parnin. "Gistable: Evaluating the executability of
    python code snippets on github." MSR 2018, pp. 217-227.

[5] H. Ye, W. Chen, W. Dou, G. Wu, J. Wei. "Knowledge-Based Environment
    Dependency Inference for Python Programs." ICSE 2022, pp. 1245-1256.

[6] W. Cheng, W. Hu, X. Ma. "ReadPyE: Revisiting Knowledge-Based Inference
    of Python Runtime Environments." IEEE TSE 50(2):258-279, 2024.

[7] S. Mukherjee et al. "PyDFix: Fixing dependency errors for python build
    reproducibility." ICSE 2021.

[8] E. Horton, C. Parnin. "V2: Fast Detection of Configuration Drift in
    Python." ASE 2019, pp. 814-819.

[9] M. Alhanahnah, Y. Boshmaf, B. Baudry. "DepsRAG: Towards Managing
    Software Dependencies using LLMs." NeurIPS Workshop 2024.

[10] J. Du et al. "DependEval: Benchmarking LLMs for Repository
     Dependency Understanding." ACL Findings 2025.

[11] R. Hu, C. Peng, X. Wang, J. Xu, C. Gao. "Repo2Run: Automated Building
     Executable Environment for Code Repository at Scale." NeurIPS 2025.

[12] Z. Wang et al. "Mobile-Agent-E: Self-Evolving Mobile Assistant for
     Complex Tasks." NeurIPS Workshop SEA 2025.

[13] N. Shinn, F. Cassano, E. Berman, A. Gopinath, K. Narasimhan, S. Yao.
     "Reflexion: Language Agents with Verbal Reinforcement Learning."
     NeurIPS 2023.

[14] Gemma Team. "Gemma 2: Improving Open Language Models at a Practical
     Size." arXiv:2408.00118, 2024.

[15] N. Islah, J. Gehring, D. Misra et al. "GitChameleon: Unmasking the
     Version-Switching Capabilities of Code Generation Models."
     arXiv:2411.05830, 2024.

[16] R. Dechter. "Constraint Processing." Morgan Kaufmann, 2003.
     (Constraint Learning theory — for CGAR CSP grounding)
```

---

## 5. Checklist trước presentation

### Slide content
- [x] Outline ghi rõ "+ Backup slides" (đã add note)
- [x] Slide title không có "Project Overview" English mismatch
- [x] Limitations slide có đủ (Hard Floor + 4 architectural)
- [x] Future Work slide đã có
- [x] R1 footnote dấu "—" cho GPT-4.1/o1 trên HG2.9K (đã có)
- [ ] **Slide 16 Session-scoped Learning**: caption "19.7%" → đổi thành **"17.9%"** để match ablation số liệu
- [ ] **Slide 18 ablation**: caption có ghi n=494? — kiểm tra
- [ ] **CGAR-1 (slide 13)** dùng `multi-agents.png` (đã confirm)
- [ ] **Slide 11 MEMRES**: pipeline image `memres-pipeline.png` legible

### Tài liệu mang theo
- [ ] In bản giấy file này, highlight Q5, Q6, Q12, Q22, Q25 (dễ bị bắt)
- [ ] In cheat-sheet Stage Details (page 31 backup) để reference khi present
- [ ] Mang arXiv link cả 2 paper (MEMRES + PLLM) trên điện thoại
- [ ] 2 USB copy slide (phòng máy hội đồng)
- [ ] PDF backup trên Google Drive (link share sẵn)

### Tập present
- [ ] Tập 3 lần với timer 10 phút (thường overrun 20%)
- [ ] Tập riêng phần CGAR Multi-Agent (slide 14) — slide khó nhất giải thích
- [ ] Tập câu mở đầu (30s pitch)
- [ ] Mock Q&A với teammate đóng vai hội đồng

---

## 6. Câu mở đầu (30s pitch)

> *"Kính chào hội đồng. Em là [tên], thành viên nhóm thực hiện đề tài 'MEMRES & CGAR: Agentic Python Dependency Resolution'. Bài toán: nhiều mã nguồn Python cũ trên GitHub bị 'chết môi trường' do dependency conflicts — restore thủ công tốn giờ đến ngày.
>
> Trên nền MEMRES (paper accepted FSE Companion '26 của nhóm em), em propose **CGAR — Constraint-Guided Agentic Resolution**: multi-agent (Planner / Executor / Analyzer / Critic) + CSP với constraint store HARD / SOFT / UPPER, learning ràng buộc từ Docker build failure.
>
> Kết quả: **87.1% pass rate trên HG2.9K, 83.2% trên GitChameleon — vượt o1 closed-weight +32pp** với LLM open-weight chỉ 9B params. Sau đây em sẽ trình bày chi tiết."*

---

## 7. "Cứu cánh" nếu thầy hỏi câu không biết

> *"Câu này em chưa thực nghiệm sâu, nhưng theo phân tích sơ bộ thì [hypothesis có nguồn gốc đáng tin]. Em sẽ kiểm tra lại trong báo cáo bổ sung."*

**ĐỪNG**:
- Bịa số
- Claim CSP theory novelty
- Claim CGAR hơn closed-weight LLM ở mọi mặt
- Nói "tool em là perfect"

**HÃY**:
- Thừa nhận giới hạn: open-weight constraint, single-machine, snippet-level
- Nói rõ "MEMRES là phần peer-review, CGAR là extension chưa publish"
- Khi conflict số với ChatGPT: trích nguồn paper Table cụ thể
- Khi không biết: dùng template §7
