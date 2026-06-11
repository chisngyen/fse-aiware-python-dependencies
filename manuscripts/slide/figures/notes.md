# Slide Asset & Reference Notes

Nguồn của các tài nguyên ngoài + số liệu trích dẫn trong deck, để mở ra khi cần kiểm chứng.

## 1. Ảnh AI tạo (external — cần dẫn nguồn)

| Ảnh | File | Nguồn (prompt/share) |
|-----|------|----------------------|
| CGAR Overview | `cgar-overview.png` | https://chatgpt.com/share/6a2a3c91-5640-83ec-8761-25876b30abe3 |
| Session Learning | `session-learning.png` | https://chatgpt.com/share/6a2a3c8b-93f8-83ec-9452-052ef1ef7e87 |
| Bối cảnh | `boicanh.png` | https://chatgpt.com/share/6a2a42c5-5d08-83ec-bd8a-c881712976a9 |

## 2. Hình từ paper gốc

| Ảnh | File | Nguồn |
|-----|------|-------|
| MEMRES pipeline | `memres-pipeline.png` | Hình từ paper MEMRES của nhóm |

## 3. Số liệu trích dẫn (papers — mở refs để check)

### Chart "Related Work: Tổng hợp các phương pháp" (Pass rate HG2.9K)
Nguồn: **Raiders of the Lost Dependency: Fixing Dependency Conflicts in Python using LLMs**, arXiv:2501.16191, Table 1.
- PyEGo (ICSE'22): **45.0%** (1302/2891)
- ReadPyE (TSE'24): **47.2%** (1365/2891)
- PLLM: **54.8%** (1583/2891, 10-run union); single-run ≈ 49.8%
- Trần KG-era ≈ 47% (= ReadPyE)

Link: https://arxiv.org/abs/2501.16191

### Datasets
- **HG2.9K**: hard subset 2891 gist từ Gistable — Horton & Parnin, ICSME 2018 (arXiv:1808.04919).
- **GitChameleon**: 328 snippet có unit test = **GitChameleon 2.0**, arXiv:2507.12367 (bản gốc 2411.05830 chỉ có 116 bài → KHÔNG dùng). Link: https://arxiv.org/abs/2507.12367

### Bảng "Related Work" — venue đã verify
- PyEGo: **ICSE'22** ✓
- ReadPyE: **TSE'24** (IEEE TSE Vol 50, 2024) ✓
- PyDFix: **ISSTA'21** (Mukherjee, Almanza, Rubio-González) — KHÔNG phải ICSE'21. https://dl.acm.org/doi/10.1145/3460319.3464797
- PLLM: **arXiv'25** (2501.16191, Bartlett/Liem/Panichella, TU Delft) — chưa có bằng chứng publish ở ASEW'25.
- **SMT-LLM (FSE'26)**: entry **cùng tham gia cuộc thi FSE-AIWare 2026** như MEMRES/CGAR (không phải paper công bố riêng). Số liệu là do nhóm reproduce trong cùng harness (Gemma-2 9B + Docker). Khi thầy hỏi: đây là tool đối thủ trong competition, không có arXiv riêng.

### GitChameleon 2.0 LLM baselines (closed-weight, từ arXiv:2507.12367)
- GPT-4o 49.1%, Gemini 2.5 Pro 50.0%, o1 51.2%, GPT-4.1+RAG 58.5% (SOTA ~48–51%).

## 4. Hình tự vẽ bằng TikZ (KHÔNG cần dẫn nguồn ngoài)

Tự vẽ trong `main.tex`, không phải ảnh ngoài: Datasets, Dependency domino, Bùng nổ tổ hợp (khối 3D),
CSP search tree, Multi-Agent loop, Related Work 3 hướng, các sơ đồ I/O… → khỏi lo thầy hỏi refs.
