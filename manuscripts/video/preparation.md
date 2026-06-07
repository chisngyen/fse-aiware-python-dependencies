# YouTube upload — MEMRES & CGAR presentation video

File nộp: `renders/cgar_presentation_narrated.mp4` (5:50 · 1080p60 · có voice TV).
Bên dưới là Title + Description sẵn để dán. Chọn 1 title, dán nguyên Description.

---

## TITLE — chọn 1

**(Khuyến nghị) Song ngữ, rõ tên hệ thống + con số mạnh:**
```
CGAR & MEMRES — Tự động hồi sinh môi trường Python cho code cũ (87.1% pass, vượt o1 +32pp)
```

Phương án khác:
```
A. CGAR: Multi-Agent + CSP cho Python Dependency Resolution | FSE-AIWare 2026
B. Hồi sinh code Python cũ bằng Multi-Agent LLM & ràng buộc — CGAR / MEMRES
C. CGAR — Giải phụ thuộc Python bằng agent: nhanh hơn 1.64×, chính xác 87.1%
```

> Mẹo: < 70 ký tự thì YouTube không cắt đuôi trên mobile. Title khuyến nghị hơi dài —
> nếu muốn gọn, dùng phương án C.

---

## DESCRIPTION — dán nguyên khối này

```
CGAR & MEMRES tự động hồi sinh môi trường chạy cho code Python cũ bằng multi-agent + CSP, biến mỗi lần build lỗi thành ràng buộc — "lỗi thành luật". 87.1% pass (HG2.9K), vượt o1 +32pp, nhanh hơn baseline 1.64×. FSE-AIWare 2026 competition.

Team: The Fangs
• Trần Chí Nguyên - 23122044
• Đào Sỹ Duy Minh - 23122041
• Huỳnh Trung Kiệt - 23122039

— Chương —
0:00 Giới thiệu
0:42 Bài toán & bùng nổ tổ hợp
1:51 MEMRES
2:26 CGAR — multi-agent & CSP
4:02 Kết quả & tốc độ
5:31 Kết luận

#Python #LLM #MultiAgent #SoftwareEngineering #FSE2026
```

---

## TAGS (ô Tags khi upload, phân tách bằng dấu phẩy)

```
CGAR, MEMRES, Python dependency resolution, multi-agent LLM, constraint satisfaction,
CSP, dependency conflict, PyPI, Docker, software engineering, FSE 2026, AIWare, ICSE,
agentic AI, Gemma 2, code reproducibility, dependency hell, version resolution
```

---

## Cài đặt khi upload

- **Visibility:** Unlisted (nếu chỉ gửi link cho ban giám khảo) hoặc Public.
- **Category:** Science & Technology.
- **Language / Audio language:** Vietnamese.
- **Resolution:** giữ 1080p (file đã là 1080p60).
- **Thumbnail (tùy):** 1 frame từ scene Multi-Agent Loop (2:40) hoặc Pass Rates
  (4:02) — màu nền đen + cam, hợp nhận diện.
- **Chương:** YouTube tự bật khi Description có khối "— Chương —" bắt đầu từ 0:00
  (mỗi mốc ≥ 10s — đã đảm bảo).

## Pinned comment gợi ý (tùy)

```
Paper & source code: [thêm link sau]
Datasets: HG2.9K (2.891 snippet) · GitChameleon (arXiv 2507.12367)
Câu hỏi/thảo luận rất hoan nghênh 👇
```

---

### English version (nếu cần cho reviewer quốc tế)

**Title:**
```
CGAR & MEMRES — Reviving Python Environments for Legacy Code via Multi-Agent CSP (87.1% pass, beats o1 by +32pp)
```

**Description:**
```
MEMRES & CGAR automatically revive the runtime environment of legacy Python
snippets: given an "orphan" snippet (no requirements, no metadata), they infer
the correct packages, versions, and Python release so every import runs in Docker.

CGAR formulates the task as a Constraint Satisfaction Problem and solves it with a
multi-agent loop (Planner · Executor · Analyzer · Critic) around a shared Session
Store: each failed build becomes a typed constraint that prunes the search space —
turning errors into rules.

Key results (Gemma-2 9B, open-weight):
• 87.1% pass on HG2.9K (2,891 snippets) · 83.2% on GitChameleon (328)
• Beats o1 (closed, enterprise) by +32pp on GitChameleon
• 1.64× faster than MEMRES, 3.61× faster than PLLM
• Eliminates 4 baseline error classes entirely (Syntax, NoMatchingDistribution,
  wheel build, AttributeError)
• Smallest cross-benchmark gap (−3.9pp): solves on live PyPI data, not dataset patterns

Context: FSE-AIWare 2026 competition, toward ICSE 2027.
Narration in Vietnamese with English technical terms. Visuals: pure-Manim, 3B1B-style.

(same chapter list as above)
```
