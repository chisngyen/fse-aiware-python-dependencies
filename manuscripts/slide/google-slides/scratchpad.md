# CGAR Deck — Google Slides conversion

## Decisions (defaults after timeout)
- Keep full main deck (~22 slides) + 4 section dividers + 8 backup slides
- Refined teal + orange academic theme
- Recreate TikZ diagrams cleanly in HTML/CSS
- Vietnamese text preserved
- Image placeholders (image-slot) for logos + AI illustrations
- Google-Slides-safe: Be Vietnam Pro (Vietnamese-native) + JetBrains Mono (code), via Google Fonts <link>

## Type scale (1920×1080), floor 24px
- display 80 / h1(title) 50 / h2 34 / lead 30 / body 26 / small 24 / code 24

## Palette
- ink #16242A (deep teal bg) / teal #23373B / paper #F6F4EF / card #FFF
- accent orange #E0772B / muted #5C6B6E / hairline rgba(22,36,42,.12)
- success #2E7D5B / alert(terracotta) #B5483F / gold #C5A33F / steel #2E7CA6 / navy #2C3E6B
- constraint encoding: HARD=terracotta, SOFT=gold, UPPER=steel

## Title sequence (chapter list)
1 Title
2 Nội dung chính
3 [§] Bài toán
4 Bối cảnh: Mã Python "chết môi trường"
5 Bài toán & Yêu cầu đánh giá
6 Khoảng cách phụ thuộc
7 Bùng nổ tổ hợp
8 Bộ dữ liệu đánh giá
9 Công trình liên quan: 3 hướng tiếp cận
10 Công trình liên quan: Tổng hợp
11 [§] MEMRES
12 MEMRES: Lookup-First, LLM-Last
13 Từ MEMRES đến CGAR: Vá 3 lỗ hổng
14 [§] CGAR
15 CGAR: Tổng quan 3 Agent
16 CGAR: Vòng lặp Multi-Agent
17 CGAR: Miền giá trị D đến từ đâu?
18 CGAR: Tích lũy ràng buộc
19 CGAR: Học ràng buộc từ phản hồi
20 CGAR: Học theo phạm vi Session
21 [§] Kết quả
22 So sánh tổng thể
23 HG2.9K: Phân rã lỗi
24 GitChameleon: Open vs Closed
25 Tốc độ & Ablation
26 Hạn chế: Hard Floor & giới hạn kiến trúc
27 Hướng phát triển
28 Tài liệu tham khảo
29 Cảm ơn
B1 Filter & Constraint Solver (I/O)
B2 Agent Communication
B3 Session Store Data Structures
B4 LLM Call Mechanics
B5 Build Loop & Anti-Hallucination
B6 Planner Prompt
B7 Analyzer Prompt
B8 Critic Prompt

## Slide chrome
- Content: paper bg, kicker (mono uppercase orange 24) + title (50/700 teal), hairline; content below.
- Dividers: deep teal bg, big number + section name + orange rule.
- Avoid generic left-accent cards; color-left only for constraint encoding (meaningful).
