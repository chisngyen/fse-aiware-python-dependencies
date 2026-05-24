"""Cinematic 3blue1brown-flavored scenes for the MEMRES & CGAR video.

Design rules
------------
* Dark backdrop (#0E1518) with warm accent (#EB811B).
* Hero scenes use ThreeDScene + camera orbits.
* Bullets reveal one-at-a-time with breath beats — no info dumps.
* Math reveals via TransformMatchingTex.
* Every scene ends on a 1-line punchline that the narrator can land.
"""
from __future__ import annotations
from manim import *
import numpy as np

from style import (
    BG, PANEL, NAVY, ACCENT, ACCENT_SOFT, TEAL, PURPLE,
    SUCCESS, ALERT, INK, DIM, GHOST,
    TITLE_KW, BODY_KW, MONO_KW,
    slide_chrome, glow, bullet_list, reveal_bullets, card, kbd,
    beat, emphasize, focus_on, dramatic_write, deep_box,
    starfield, twinkle,
)


# ============================================================
# 1. TITLE — particles converge into the logotype
# ============================================================
class Title(Scene):
    """0:00–0:30. Cinematic open: particles → title → underline → team."""

    def construct(self):
        # Ambient starfield
        stars = starfield(n=90)
        self.add(stars)
        self.play(LaggedStart(*[FadeIn(s) for s in stars],
                              lag_ratio=0.01), run_time=1.0)

        # Eyebrow chip — small pill above title
        chip_t = Text("ML COURSE PROJECT  ·  2026",
                      font_size=18, color=ACCENT_SOFT,
                      font="DejaVu Sans Mono", weight=BOLD)
        chip_bg = RoundedRectangle(
            corner_radius=0.18,
            width=chip_t.width + 0.55, height=chip_t.height + 0.30,
            fill_color=NAVY, fill_opacity=1,
            stroke_color=ACCENT, stroke_width=1.5, stroke_opacity=0.6,
        ).move_to(chip_t)
        chip = VGroup(chip_bg, chip_t).move_to(UP * 2.5)

        # Two-tone hero title: MEMRES (teal) + & (dim) + CGAR (accent)
        memres = Text("MEMRES", font_size=92, color=TEAL,
                      weight=BOLD, font="DejaVu Sans")
        amp    = Text("&", font_size=72, color=DIM,
                      weight=BOLD, font="DejaVu Sans")
        cgar   = Text("CGAR", font_size=92, color=ACCENT,
                      weight=BOLD, font="DejaVu Sans")
        main = VGroup(memres, amp, cgar)\
            .arrange(RIGHT, buff=0.55, aligned_edge=DOWN)\
            .move_to(UP * 0.5)

        # Gradient underline (rectangle with teal→accent gradient)
        underline = Rectangle(
            width=main.width * 0.7, height=0.08,
            stroke_width=0,
        )
        underline.set_fill(color=[TEAL, ACCENT_SOFT, ACCENT], opacity=1)
        underline.next_to(main, DOWN, buff=0.55)

        # Subtitle
        sub = Text("Agentic Python Dependency Resolution",
                   font_size=32, color=INK,
                   font="DejaVu Sans", slant=ITALIC)
        sub.next_to(underline, DOWN, buff=0.55)

        # Institution
        inst = Text("University of Science  ·  VNU-HCM",
                    font_size=20, color=DIM, font="DejaVu Sans")
        inst.next_to(sub, DOWN, buff=0.9)

        # --- animate in ---
        self.play(FadeIn(chip, shift=DOWN * 0.15), run_time=0.5)

        # title: fade + slight scale (start each word slightly displaced)
        for word, dir_shift in ((memres, LEFT * 0.5),
                                (amp,    UP * 0.1),
                                (cgar,   RIGHT * 0.5)):
            word.save_state()
            word.shift(dir_shift).set_opacity(0)
        self.play(
            *[Restore(w) for w in (memres, amp, cgar)],
            *[w.animate.set_opacity(1) for w in (memres, amp, cgar)],
            run_time=1.0, rate_func=smooth,
        )
        beat(self, 0.3)

        # underline grows
        underline.stretch_to_fit_width(0.001)
        self.play(underline.animate.stretch_to_fit_width(main.width * 0.7),
                  run_time=0.7, rate_func=smooth)

        # subtitle + institution
        self.play(FadeIn(sub, shift=UP * 0.15), run_time=0.6)
        self.play(FadeIn(inst, shift=UP * 0.1), run_time=0.5)

        # Twinkle for life
        twinkle(self, stars, duration=1.6)
        beat(self, 0.6)

        # Out
        self.play(
            FadeOut(VGroup(chip, main, underline, sub, inst, stars),
                    shift=UP * 0.3),
            run_time=0.8,
        )


# ============================================================
# 2. OUTLINE — cards slide in
# ============================================================
class Outline(Scene):
    def construct(self):
        slide_chrome(self, "Nội dung chính")
        stars = starfield(n=30, opacity_range=(0.06, 0.18))
        self.add(stars)

        sections = [
            ("01", "Phát biểu bài toán",        ACCENT),
            ("02", "Phương pháp nền MEMRES",   TEAL),
            ("03", "Hạn chế & đề xuất CGAR",   ACCENT),
            ("04", "Đánh giá thực nghiệm",     SUCCESS),
        ]

        def make_tile(num, ttl, color):
            n = Text(num, font_size=64, weight=BOLD,
                     color=color, font="DejaVu Sans")
            t = Text(ttl, font_size=22, color=INK,
                     font="DejaVu Sans")
            rule = Line(LEFT, RIGHT, color=color,
                        stroke_width=2, stroke_opacity=0.6)
            rule.set_width(max(n.width, t.width) + 0.2)
            inner = VGroup(n, rule, t).arrange(DOWN, buff=0.22)
            box = RoundedRectangle(
                corner_radius=0.20,
                width=4.8, height=2.4,
                fill_color=PANEL, fill_opacity=0.65,
                stroke_color=color, stroke_width=1.6,
                stroke_opacity=0.55,
            ).move_to(inner)
            return VGroup(box, inner)

        tiles = VGroup(*[make_tile(*s) for s in sections])
        tiles.arrange_in_grid(rows=2, cols=2, buff=(0.45, 0.35))
        tiles.move_to(DOWN * 0.1)

        for t in tiles:
            self.play(FadeIn(t, shift=UP * 0.2),
                      run_time=0.45, rate_func=smooth)
            beat(self, 0.15)
        beat(self, 1.0)


# ============================================================
# 3. PROBLEM I/O — code panel → environment, with morph
# ============================================================
class ProblemIO(Scene):
    def construct(self):
        slide_chrome(self, "FSE-Competition 2026", "Bài toán")

        # ---- helper: pill chip with colored dot ----
        def chip(text: str, color, size: int = 18):
            t = Text(text, font_size=size, color=color,
                     weight=BOLD, font="DejaVu Sans Mono")
            bg = RoundedRectangle(
                corner_radius=0.12,
                width=t.width + 0.42, height=t.height + 0.22,
                fill_color=NAVY, fill_opacity=1,
                stroke_color=color, stroke_width=1.2, stroke_opacity=0.7,
            ).move_to(t)
            return VGroup(bg, t)

        # ============== LEFT — INPUT ==============
        in_chip = chip("INPUT  ·  orphaned snippet", ALERT)

        in_code = Code(
            code_string=(
                "import scipy.misc as m\n"
                "from sklearn.cross_validation \\\n"
                "    import train_test_split\n"
                "import cv2\n"
                "\n"
                "img = m.imread('photo.jpg')"
            ),
            language="python",
            background="rectangle",
            paragraph_config={"font_size": 24, "font": "DejaVu Sans Mono",
                              "line_spacing": 0.55},
        )
        in_code.scale_to_fit_width(5.6)

        in_card = card(in_code, pad=0.30, stroke=ALERT,
                       stroke_opacity=0.30)
        in_chip.next_to(in_card, UP, buff=0.20).align_to(in_card, LEFT)
        in_chip.shift(RIGHT * 0.25)

        miss = VGroup(
            Text("✗  no requirements.txt", font_size=18,
                 color=ALERT, font="DejaVu Sans Mono"),
            Text("✗  no metadata", font_size=18,
                 color=ALERT, font="DejaVu Sans Mono"),
            Text("?  Python version unknown", font_size=18,
                 color=ACCENT, font="DejaVu Sans Mono"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        miss.next_to(in_card, DOWN, buff=0.30).align_to(in_card, LEFT)
        miss.shift(RIGHT * 0.20)

        in_panel = VGroup(in_chip, in_card, miss)

        # ============== RIGHT — OUTPUT ==============
        out_chip = chip("REQUIRED OUTPUT  ·  runnable env", SUCCESS)
        rows = VGroup(
            Text("Python  3.7",             font_size=22, **MONO_KW),
            Text("scipy==1.1.0",            font_size=22, **MONO_KW),
            Text("scikit-learn==0.19.2",    font_size=22, **MONO_KW),
            Text("opencv-python==4.5.5.62", font_size=22, **MONO_KW),
            Text("numpy==1.16.6",           font_size=22, **MONO_KW),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        check = Text("✓  Docker import OK", font_size=24,
                     color=SUCCESS, weight=BOLD, font="DejaVu Sans")
        sep = Line(LEFT, RIGHT, color=GHOST,
                   stroke_width=1).set_width(rows.width).set_opacity(0.4)
        out_body = VGroup(rows, sep, check).arrange(
            DOWN, buff=0.25, aligned_edge=LEFT)
        out_card = card(out_body, pad=0.40, stroke=SUCCESS,
                        stroke_opacity=0.30)
        out_chip.next_to(out_card, UP, buff=0.20).align_to(out_card, LEFT)
        out_chip.shift(RIGHT * 0.25)
        out_panel = VGroup(out_chip, out_card)

        # ----- match heights so the two cards look paired -----
        in_panel.move_to(LEFT * 3.85 + DOWN * 0.15)
        out_panel.move_to(RIGHT * 3.85 + DOWN * 0.15)

        # ============== MIDDLE — ? in a halo arrow ==============
        arrow = Arrow(
            in_card.get_right() + RIGHT * 0.15,
            out_card.get_left() + LEFT * 0.15,
            color=ACCENT, stroke_width=5, buff=0.0,
            max_tip_length_to_length_ratio=0.22,
        )
        q_t = Text("?", font_size=44, weight=BOLD,
                   color=ACCENT, font="DejaVu Sans")
        q_bg = Circle(radius=0.42, fill_color=BG, fill_opacity=1,
                      stroke_color=ACCENT, stroke_width=2.5)
        qmark = VGroup(q_bg, q_t).move_to(arrow.get_center())

        # ============== animate ==============
        self.play(FadeIn(in_panel, shift=RIGHT * 0.2), run_time=0.7)
        beat(self, 0.8)
        self.play(GrowArrow(arrow), run_time=0.5)
        self.play(FadeIn(qmark, scale=0.7), run_time=0.4)
        emphasize(self, qmark, color=ACCENT, scale=1.18)
        self.play(FadeIn(out_panel, shift=LEFT * 0.2), run_time=0.7)
        emphasize(self, check, color=SUCCESS, scale=1.2)
        beat(self, 1.8)


# ============================================================
# 4. REQUIREMENTS — badges with depth boxes
# ============================================================
class Requirements(Scene):
    """3-column constraint cards: Resource / Time / Model."""

    def construct(self):
        slide_chrome(self, "Requirements & Metrics", "Bài toán")

        # subtitle under chrome
        sub = Text("Ràng buộc của FSE-Competition 2026",
                   font_size=20, color=DIM, slant=ITALIC,
                   font="DejaVu Sans")
        sub.move_to(UP * 2.7)
        self.play(FadeIn(sub), run_time=0.4)

        def make_card(icon, title, color, rows):
            ic_t = Text(icon, font_size=32, color=color,
                        weight=BOLD, font="DejaVu Sans")
            ic_bg = Circle(radius=0.45, color=color,
                           stroke_width=2.5,
                           fill_color=BG, fill_opacity=1).move_to(ic_t)
            ic = VGroup(ic_bg, ic_t)
            ttl = Text(title, font_size=22, color=INK,
                       weight=BOLD, font="DejaVu Sans")
            rule = Line(LEFT * 1.2, RIGHT * 1.2,
                        color=color, stroke_width=2, stroke_opacity=0.85)
            row_objs = VGroup()
            for big, small in rows:
                b = Text(big, font_size=22, color=color,
                         weight=BOLD, font="DejaVu Sans Mono")
                s = Text(small, font_size=14, color=DIM,
                         font="DejaVu Sans", slant=ITALIC)
                row_objs.add(VGroup(b, s).arrange(DOWN, buff=0.06,
                                                  aligned_edge=LEFT))
            row_objs.arrange(DOWN, aligned_edge=LEFT, buff=0.30)

            inner = VGroup(ic, ttl, rule, row_objs).arrange(
                DOWN, buff=0.22)
            rule.set_width(2.6)
            inner = VGroup(ic, ttl, rule, row_objs)\
                .arrange(DOWN, buff=0.22)
            box = RoundedRectangle(
                corner_radius=0.18,
                width=3.4, height=4.7,
                fill_color=PANEL, fill_opacity=0.65,
                stroke_color=color, stroke_width=1.5,
                stroke_opacity=0.5,
            ).move_to(inner)
            return VGroup(box, inner)

        cards = Group(
            make_card("R", "Resource", ACCENT, [
                ("VRAM ≤ 10 GB", "single GPU"),
                ("1 worker",     "sequential"),
            ]),
            make_card("T", "Time", TEAL, [
                ("10 retries",   "per snippet"),
                ("180 s",        "per Docker build"),
                ("500 s",        "wall-clock total"),
            ]),
            make_card("M", "Model", SUCCESS, [
                ("Open-weight", "no GPT-4 / Claude"),
                ("Gemma-2 9B",  "reference baseline"),
            ]),
        )
        # use VGroup arrange since Group ok too
        cards_v = VGroup(*cards).arrange(RIGHT, buff=0.45).move_to(DOWN * 0.2)

        for c in cards_v:
            self.play(FadeIn(c, shift=UP * 0.25),
                      run_time=0.55, rate_func=smooth)
            beat(self, 0.25)

        # footer
        foot = Text("Open-source · reproducible · single GPU",
                    font_size=18, color=ACCENT_SOFT,
                    slant=ITALIC, font="DejaVu Sans")
        foot.to_edge(DOWN, buff=0.5)
        self.play(FadeIn(foot, shift=UP * 0.1), run_time=0.5)
        beat(self, 1.0)


# ============================================================
# 5. DATASETS
# ============================================================
class Datasets(Scene):
    """Slide 5 — show 2 paper screenshots first (animated), then big tabular."""

    def construct(self):
        slide_chrome(self, "Datasets", "Bài toán")

        # ============================================================
        # PHASE 1 — show the two source papers, resized to same height
        # ============================================================
        import os
        slide_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "..", "..")  # video/ → slide/
        gitc_path = os.path.normpath(os.path.join(slide_dir, "gitchamelon.png"))
        mem_path  = os.path.normpath(os.path.join(slide_dir, "memres.png"))

        gitc = ImageMobject(gitc_path)
        mem  = ImageMobject(mem_path)
        # match height (smaller so captions fit cleanly side-by-side)
        target_h = 4.2
        gitc.height = target_h
        mem.height  = target_h

        papers = Group(mem, gitc).arrange(RIGHT, buff=1.2)
        papers.move_to(ORIGIN).shift(UP * 0.4)

        cap_mem  = Text("HG2.9K", font_size=24, color=ACCENT,
                        weight=BOLD, font="DejaVu Sans")
        cap_mem_sub = Text("FSE-Competition 2026", font_size=16,
                           color=DIM, font="DejaVu Sans")
        cap_mem_grp = VGroup(cap_mem, cap_mem_sub).arrange(DOWN, buff=0.1)
        cap_mem_grp.next_to(mem, DOWN, buff=0.3)

        cap_gitc = Text("GitChameleon", font_size=24, color=TEAL,
                        weight=BOLD, font="DejaVu Sans")
        cap_gitc_sub = Text("arXiv 2507.12367", font_size=16,
                            color=DIM, font="DejaVu Sans")
        cap_gitc_grp = VGroup(cap_gitc, cap_gitc_sub).arrange(DOWN, buff=0.1)
        cap_gitc_grp.next_to(gitc, DOWN, buff=0.3)

        captions = VGroup(cap_mem_grp, cap_gitc_grp)

        # Reveal left paper
        self.play(FadeIn(mem, shift=UP * 0.3, scale=0.95),
                  FadeIn(cap_mem_grp, shift=UP * 0.2), run_time=0.9)
        beat(self, 1.2)
        # Reveal right paper
        self.play(FadeIn(gitc, shift=UP * 0.3, scale=0.95),
                  FadeIn(cap_gitc_grp, shift=UP * 0.2), run_time=0.9)
        beat(self, 1.8)

        # ============================================================
        # PHASE 2 — fade papers, reveal big tabular
        # ============================================================
        self.play(FadeOut(papers, shift=DOWN * 0.3),
                  FadeOut(captions, shift=DOWN * 0.2),
                  run_time=0.7)

        rows = [
            ["",                   "HG2.9K",                   "GitChameleon"],
            ["Origin",             "FSE-Competition 2026",     "arXiv 2507.12367"],
            ["Role",               "In-distribution",          "OOD generalization"],
            ["Size",               "2,891 snippets",           "328 problems"],
            ["Source",             "GitHub gists",             "Curated API drift"],
            ["Python 2/3 mix",     "Yes",                      "Python 3 only"],
            ["Has unit tests",     "No  (import-success)",     "Yes  (hidden)"],
            ["Ground-truth shown", "No",                       "No"],
            ["Difficulty",         "Hard — outdated ML/AI",    "Hard — API drift"],
            ["Eval signal",        "Imports run in Docker",    "Tests pass + runtime"],
        ]

        tbl = Table(
            rows,
            include_outer_lines=True,
            line_config={"stroke_color": GHOST, "stroke_width": 1.4},
            element_to_mobject=Text,
            element_to_mobject_config={"font_size": 26, "font": "DejaVu Sans",
                                       "color": INK},
            h_buff=0.7, v_buff=0.28,
        ).scale(0.72)

        # Headers
        hdr = tbl.get_rows()[0]
        hdr[1].set_color(ACCENT)
        hdr[2].set_color(TEAL)

        # Row labels dim
        for r in tbl.get_rows()[1:]:
            r[0].set_color(DIM)

        tbl.move_to(ORIGIN).shift(DOWN * 0.05)

        self.play(FadeIn(tbl, shift=UP * 0.3), run_time=0.8)

        # Highlight role row
        role_row = tbl.get_rows()[2]
        ring = SurroundingRectangle(role_row, color=ACCENT, stroke_width=3,
                                    buff=0.06, corner_radius=0.05)
        self.play(Create(ring), run_time=0.5)
        beat(self, 0.7)
        self.play(FadeOut(ring), run_time=0.4)
        beat(self, 0.7)


# ============================================================
# 6. DEPENDENCY DOMINO  ⭐  — ThreeDScene with real 3D dominoes
# ============================================================
class DependencyDomino(Scene):
    """Narrative cascade: 1 import → chain of constraints → combinatorial blowup."""

    def construct(self):
        slide_chrome(self, "The Dependency Gap", "Bài toán")

        # ============================================================
        # PHASE 1 — Lead-in: a single innocent import
        # ============================================================
        lead = Text("Một dòng import tưởng vô hại…",
                    font_size=30, color=DIM, font="DejaVu Sans", slant=ITALIC)
        lead.move_to(UP * 1.5)

        code_line = Code(
            code_string="img = scipy.misc.imread('photo.jpg')",
            language="python",
            background="rectangle",
            paragraph_config={"font_size": 32, "font": "DejaVu Sans Mono"},
        )
        code_line.move_to(UP * 0.2)

        self.play(FadeIn(lead, shift=UP * 0.2), run_time=0.6)
        beat(self, 0.5)
        self.play(FadeIn(code_line, shift=UP * 0.15), run_time=0.7)
        beat(self, 1.2)

        # Lead-in 2: but it triggers...
        trigger = Text("…lại kéo theo cả một chuỗi ràng buộc",
                       font_size=28, color=ACCENT, weight=BOLD,
                       font="DejaVu Sans", slant=ITALIC)
        trigger.move_to(DOWN * 1.0)
        self.play(FadeIn(trigger, shift=UP * 0.15), run_time=0.6)
        beat(self, 1.4)

        # Clear for the cascade
        self.play(FadeOut(lead), FadeOut(trigger), FadeOut(code_line),
                  run_time=0.5)

        # ============================================================
        # PHASE 2 — Constraint chain (no overlap, clean cards in a row)
        # ============================================================
        chain = [
            ("scipy.misc.imread", "removed in scipy ≥ 1.2",  TEAL),
            ("scipy ≤ 1.1",       "needs Python ≤ 3.7",      ACCENT),
            ("Python ≤ 3.7",      "needs numpy ≤ 1.16",      PURPLE),
            ("numpy ≤ 1.16",      "needs Cython ≤ 0.29",     ALERT),
        ]

        def card_node(headline, sub, color, w=2.7, h=1.4):
            h_text = Text(headline, font_size=17, color=INK,
                          weight=BOLD, font="DejaVu Sans Mono")
            s_text = Text(sub, font_size=14, color=color,
                          font="DejaVu Sans", slant=ITALIC)
            inner = VGroup(h_text, s_text).arrange(DOWN, buff=0.18)
            box = RoundedRectangle(corner_radius=0.12, width=w, height=h,
                                   fill_color=PANEL, fill_opacity=1,
                                   stroke_color=color, stroke_width=2,
                                   stroke_opacity=0.8)
            inner.move_to(box)
            return VGroup(box, inner)

        cards = VGroup(*[card_node(h, s, c) for h, s, c in chain])
        cards.arrange(RIGHT, buff=0.45).move_to(DOWN * 0.1)

        # Big arrows BETWEEN cards
        arrows = VGroup()
        for i in range(len(cards) - 1):
            a = Arrow(cards[i].get_right(), cards[i + 1].get_left(),
                      color=ACCENT, stroke_width=4, buff=0.05,
                      max_tip_length_to_length_ratio=0.18)
            arrows.add(a)

        # Reveal cards one-by-one with chevron arrows growing
        self.play(FadeIn(cards[0], shift=DOWN * 0.2), run_time=0.55)
        beat(self, 0.4)
        for i in range(len(cards) - 1):
            self.play(GrowArrow(arrows[i]), run_time=0.35)
            self.play(FadeIn(cards[i + 1], shift=DOWN * 0.2), run_time=0.45)
            beat(self, 0.35)

        # Brief emphasis ripple
        ripple_anims = []
        for c in cards:
            ripple_anims.append(Indicate(c, scale_factor=1.05, color=ACCENT))
        self.play(LaggedStart(*ripple_anims, lag_ratio=0.25), run_time=1.2)

        # ============================================================
        # PHASE 3 — Punchline
        # ============================================================
        punch1 = Text("~500K packages   ×   chục phiên bản   ×   nhiều Python",
                      font_size=22, color=INK, weight=BOLD, font="DejaVu Sans")
        punch2 = Text("⇒  combinatorial explosion",
                      font_size=30, color=ACCENT, weight=BOLD,
                      font="DejaVu Sans", slant=ITALIC)
        punch = VGroup(punch1, punch2).arrange(DOWN, buff=0.2)
        punch.to_edge(DOWN, buff=0.5)
        self.play(FadeIn(punch, shift=UP * 0.15), run_time=0.7)
        beat(self, 2.0)


# ============================================================
# 7. MEMRES PIPELINE
# ============================================================
class MemresPipeline(Scene):
    """MEMRES detailed: 5 phases — intro → 4 stages animated → results chart."""

    def construct(self):
        # Chỉ hiện slide chrome ở phase intro, sau đó ẩn cho gọn
        self._phase_intro()
        self._phase_oracle()
        self._phase_hybrid()
        self._phase_clean()
        self._phase_cascade()
        # _phase_chart removed — chart now lives in PassRates scene

    # ---- shared slim phase header (3b1b-ish) — no sub-description ----
    def _make_phase_header(self, num_label, title, subtitle=None):
        """Returns VGroup: num + title side by side, thin underline beneath.
        subtitle is accepted but ignored for cleaner look.
        """
        num = Text(num_label, font_size=22, color=ACCENT, weight=BOLD,
                   font="DejaVu Sans")
        ttl = Text(title, font_size=32, color=INK, weight=BOLD,
                   font="DejaVu Sans")
        head_row = VGroup(num, ttl).arrange(RIGHT, buff=0.25,
                                              aligned_edge=DOWN)
        rule = Line(LEFT, RIGHT, color=ACCENT, stroke_width=2.5)
        rule.set_width(head_row.width + 0.4)
        rule.next_to(head_row, DOWN, buff=0.18)
        grp = VGroup(head_row, rule)
        grp.to_edge(UP, buff=0.55)
        return grp

    # ============================================================
    # PHASE 0 — Intro: PLLM brute-force vs MEMRES smart pipeline
    # Palette rule for this scene: ACCENT + INK + DIM only (mono-ish).
    # ============================================================
    def _phase_intro(self):
        # Slide title — shown only here, then dismissed
        slide_ttl = Text("MEMRES — pipeline 4 bước", font_size=36, color=INK,
                         weight=BOLD, font="DejaVu Sans")
        slide_ttl_bar = Rectangle(width=0.12, height=slide_ttl.height + 0.15,
                                   fill_color=ACCENT, fill_opacity=1,
                                   stroke_width=0)
        slide_ttl_bar.next_to(slide_ttl, LEFT, buff=0.2)
        slide_chrome_grp = VGroup(slide_ttl_bar, slide_ttl)
        slide_chrome_grp.to_corner(UL, buff=0.5)

        self.play(FadeIn(slide_chrome_grp, shift=RIGHT * 0.15), run_time=0.5)

        ttl = Text("Thay vì brute-force LLM trial-and-error…",
                   font_size=28, color=DIM, font="DejaVu Sans", slant=ITALIC)
        ttl.move_to(UP * 0.6)

        sub = Text("…MEMRES dùng pipeline 4 bước",
                   font_size=32, color=ACCENT, weight=BOLD,
                   font="DejaVu Sans")
        sub.move_to(DOWN * 0.3)

        stages = ["① Knowledge Oracle", "② Hybrid Eval",
                  "③ Module Clean", "④ Confidence Cascade"]
        chips = VGroup()
        for name in stages:
            t = Text(name, font_size=17, color=INK, weight=BOLD,
                     font="DejaVu Sans")
            bg = RoundedRectangle(corner_radius=0.1,
                                  width=t.width + 0.4, height=t.height + 0.25,
                                  fill_color=PANEL, fill_opacity=1,
                                  stroke_color=ACCENT, stroke_width=1.4,
                                  stroke_opacity=0.7)
            t.move_to(bg)
            chips.add(VGroup(bg, t))
        chips.arrange(RIGHT, buff=0.22).move_to(DOWN * 1.7)

        self.play(FadeIn(ttl, shift=UP * 0.2), run_time=0.5)
        beat(self, 0.7)
        self.play(FadeIn(sub, shift=UP * 0.15), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.2) for c in chips],
                              lag_ratio=0.15), run_time=0.8)
        beat(self, 1.0)
        # Clear everything including the slide title — won't reappear
        self.play(FadeOut(VGroup(slide_chrome_grp, ttl, sub, chips)),
                  run_time=0.5)

    # ============================================================
    # PHASE 1 — Knowledge Oracle: yml files flying in, oracle match
    # ============================================================
    def _phase_oracle(self):
        header = self._make_phase_header(
            "①", "Knowledge Oracle",
            "Replay 2,900 proven PLLM solutions")
        self.play(FadeIn(header, shift=DOWN * 0.15), run_time=0.5)

        # Animation: a stream of yml file icons flowing from left,
        # one of them matches and gets pulled to the "current snippet"
        def yml_icon(label):
            box = RoundedRectangle(corner_radius=0.06, width=0.85, height=1.05,
                                   fill_color=PANEL, fill_opacity=1,
                                   stroke_color=ACCENT, stroke_width=1.2,
                                   stroke_opacity=0.6)
            t = Text(label, font_size=11, color=ACCENT,
                     font="DejaVu Sans Mono")
            t.move_to(box)
            tag = Text(".yml", font_size=9, color=DIM, font="DejaVu Sans Mono")
            tag.next_to(t, DOWN, buff=0.05)
            return VGroup(box, t, tag)

        ymls = VGroup(*[
            yml_icon(s) for s in
            ["a3f...", "b71...", "c92...", "d24...", "e55...", "f08..."]
        ]).arrange(RIGHT, buff=0.18).move_to(LEFT * 1.5 + DOWN * 0.2)

        # current snippet card
        snippet = Code(
            code_string="import scipy.misc\nimport cv2",
            language="python",
            background="rectangle",
            paragraph_config={"font_size": 16, "font": "DejaVu Sans Mono"},
        ).scale(0.95)
        snippet_label = Text("current snippet", font_size=14, color=DIM,
                             font="DejaVu Sans")
        cur = VGroup(snippet_label, snippet).arrange(DOWN, buff=0.15)
        cur.move_to(RIGHT * 4.2 + DOWN * 0.2)

        self.play(FadeIn(cur, shift=LEFT * 0.2), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(y, shift=RIGHT * 0.3) for y in ymls],
                              lag_ratio=0.08), run_time=0.9)

        # Match: 3rd file lights up, arrow flies to snippet
        match = ymls[2]
        ring = SurroundingRectangle(match, color=SUCCESS, stroke_width=3,
                                    buff=0.05, corner_radius=0.06)
        self.play(Create(ring),
                  match.animate.set_stroke(color=SUCCESS, opacity=1),
                  run_time=0.5)
        arrow = Arrow(match.get_right(), cur.get_left(),
                      color=SUCCESS, stroke_width=4, buff=0.1)
        self.play(GrowArrow(arrow), run_time=0.6)
        replay = Text("✓ replay solution", font_size=18, color=SUCCESS,
                      weight=BOLD, font="DejaVu Sans")
        replay.next_to(cur, DOWN, buff=0.3)
        self.play(FadeIn(replay, shift=UP * 0.15), run_time=0.4)
        beat(self, 0.7)

        self.play(FadeOut(VGroup(header, ymls, ring, arrow, cur, replay)),
                  run_time=0.5)

    # ============================================================
    # PHASE 2 — Hybrid Eval: AST + semantic + LLM
    # ============================================================
    def _phase_hybrid(self):
        header = self._make_phase_header("②", "Hybrid Eval")
        self.play(FadeIn(header, shift=DOWN * 0.15), run_time=0.5)

        # Input code on left (persistent)
        code = Code(
            code_string=(
                "import scipy.misc as m\n"
                "import cv2\n"
                "from skimage import io"
            ),
            language="python",
            background="rectangle",
            paragraph_config={"font_size": 17, "font": "DejaVu Sans Mono"},
        ).scale(0.95)
        code.move_to(LEFT * 4.4 + DOWN * 0.2)
        code_lbl = Text("input snippet", font_size=13, color=DIM,
                        font="DejaVu Sans", slant=ITALIC)
        code_lbl.next_to(code, UP, buff=0.12)

        # 3 compact sub-panels on the right — shown all at once
        def mini_panel(head_text, lines):
            t = Text(head_text, font_size=18, color=ACCENT,
                     weight=BOLD, font="DejaVu Sans")
            body = VGroup(*[
                Text(s, font_size=14, color=INK,
                     font="DejaVu Sans Mono")
                for s in lines
            ]).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
            inner = VGroup(t, body).arrange(DOWN, aligned_edge=LEFT,
                                              buff=0.18)
            return inner

        panels = VGroup(
            mini_panel("⚡ Static AST", [
                "extract Import + Call",
                "→ scipy.misc, cv2, skimage",
            ]),
            mini_panel("🔎 Semantic", [
                "cv2 → opencv-python",
                "skimage → scikit-image",
            ]),
            mini_panel("🤖 LLM few-shot", [
                "k=3 examples",
                "→ disambiguate calls",
            ]),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        panels.move_to(RIGHT * 2.8 + DOWN * 0.2)

        # Arrows from code → each panel
        arrows = VGroup(*[
            Arrow(code.get_right(), p.get_left(),
                  color=ACCENT, stroke_width=2.5, buff=0.2,
                  max_tip_length_to_length_ratio=0.08,
                  stroke_opacity=0.6)
            for p in panels
        ])

        # Reveal code first, then all 3 panels in quick succession
        self.play(FadeIn(code, shift=RIGHT * 0.2), FadeIn(code_lbl),
                  run_time=0.5)
        beat(self, 0.3)
        self.play(LaggedStart(*[GrowArrow(a) for a in arrows],
                              lag_ratio=0.15), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(p, shift=LEFT * 0.2) for p in panels],
                              lag_ratio=0.18), run_time=0.9)
        beat(self, 0.9)

        self.play(FadeOut(VGroup(header, code, code_lbl, panels, arrows)),
                  run_time=0.5)

    # ============================================================
    # PHASE 3 — Module Clean: error pattern match + memory growth
    # ============================================================
    def _phase_clean(self):
        # Slim header (3b1b-style) — INK title + thin ACCENT rule
        header = self._make_phase_header(
            "③", "Module Clean",
            "Lỗi → ràng buộc — bộ nhớ tự lớn dần")
        self.play(FadeIn(header, shift=DOWN * 0.15), run_time=0.5)

        # Horizontal narrative flow: error → extract → constraint
        # Three slim sections, vertically centered, well-spaced.

        # ---- Stage A: Docker error (compact) ----
        err_title = Text("Docker error", font_size=14, color=DIM,
                         font="DejaVu Sans", slant=ITALIC)
        err_lines = VGroup(
            Text("ImportError: cannot import",
                 font_size=15, color=INK, weight=BOLD,
                 font="DejaVu Sans Mono"),
            Text("name 'imread' from 'scipy.misc'",
                 font_size=15, color=INK, weight=BOLD,
                 font="DejaVu Sans Mono"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        err_grp = VGroup(err_title, err_lines).arrange(
            DOWN, aligned_edge=LEFT, buff=0.15)

        # ---- Stage B: Pattern KB (slim list, no heavy box) ----
        kb_title = Text("Pattern KB · 200+ entries",
                        font_size=14, color=DIM,
                        font="DejaVu Sans", slant=ITALIC)
        kb_rows = VGroup(
            Text("imread    /  scipy.misc",
                 font_size=14, color=INK, font="DejaVu Sans Mono"),
            Text("cross_val /  sklearn",
                 font_size=14, color=DIM, font="DejaVu Sans Mono"),
            Text("dropout   /  keras",
                 font_size=14, color=DIM, font="DejaVu Sans Mono"),
            Text("…  (+197)",
                 font_size=13, color=DIM, font="DejaVu Sans Mono",
                 slant=ITALIC),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.10)
        kb_grp = VGroup(kb_title, kb_rows).arrange(
            DOWN, aligned_edge=LEFT, buff=0.15)

        # ---- Stage C: emitted constraint ----
        out_title = Text("Emitted constraint", font_size=14, color=DIM,
                         font="DejaVu Sans", slant=ITALIC)
        out_value = Text("scipy ≤ 1.1", font_size=32, color=ACCENT,
                         weight=BOLD, font="DejaVu Sans")
        out_grp = VGroup(out_title, out_value).arrange(
            DOWN, aligned_edge=LEFT, buff=0.15)

        # Lay out horizontally
        stages = VGroup(err_grp, kb_grp, out_grp).arrange(
            RIGHT, buff=1.4, aligned_edge=UP)
        stages.move_to(DOWN * 0.3)

        # Arrows between stages
        arr1 = Arrow(err_grp.get_right(), kb_grp.get_left(),
                     color=ACCENT, stroke_width=2.5, buff=0.2,
                     max_tip_length_to_length_ratio=0.12,
                     stroke_opacity=0.75)
        arr2 = Arrow(kb_grp.get_right(), out_grp.get_left(),
                     color=ACCENT, stroke_width=2.5, buff=0.2,
                     max_tip_length_to_length_ratio=0.12,
                     stroke_opacity=0.75)

        # Reveal Stage A
        self.play(FadeIn(err_grp, shift=RIGHT * 0.2), run_time=0.5)
        beat(self, 0.7)

        # Arrow → Stage B (Pattern KB)
        self.play(GrowArrow(arr1), run_time=0.4)
        self.play(FadeIn(kb_grp, shift=RIGHT * 0.2), run_time=0.5)
        beat(self, 0.4)

        # Match the first KB row (highlight in ACCENT)
        match_ring = SurroundingRectangle(
            kb_rows[0], color=ACCENT, stroke_width=2,
            buff=0.06, corner_radius=0.06)
        self.play(Create(match_ring),
                  kb_rows[0].animate.set_color(ACCENT),
                  run_time=0.5)
        beat(self, 0.5)

        # Memory grows — auto-learned row appears in italics
        new_entry = Text(
            "+  decode_jpeg / PIL  (auto-learned)",
            font_size=13, color=ACCENT_SOFT, font="DejaVu Sans Mono",
            slant=ITALIC)
        new_entry.next_to(kb_rows[-1], DOWN, buff=0.1, aligned_edge=LEFT)
        self.play(FadeIn(new_entry, shift=UP * 0.15), run_time=0.5)
        beat(self, 0.7)

        # Arrow → Stage C
        self.play(GrowArrow(arr2), run_time=0.4)
        self.play(FadeIn(out_grp, shift=RIGHT * 0.2), run_time=0.5)
        # Emphasize the result
        self.play(Indicate(out_value, color=ACCENT, scale_factor=1.1),
                  run_time=0.5)
        beat(self, 0.6)

        self.play(FadeOut(VGroup(header, err_grp, kb_grp, out_grp,
                                  arr1, arr2, match_ring, new_entry)),
                  run_time=0.5)

    # ============================================================
    # PHASE 4 — Confidence Cascade: 6 levels waterfall
    # ============================================================
    def _phase_cascade(self):
        header = self._make_phase_header(
            "④", "Confidence Cascade",
            "6 tầng tra cứu  —  rẻ → đắt, LLM chỉ là tầng cuối")
        self.play(FadeIn(header, shift=DOWN * 0.15), run_time=0.5)

        levels = [
            ("L1", "Session memory",       "O(1) lookup intra-batch"),
            ("L2", "Compat map",            "scipy↔python ↔ numpy rules"),
            ("L3", "Templates",             "ML/DL stack recipes"),
            ("L4", "Co-occurrence mining",  "from 17K PLLM yml files"),
            ("L5", "Heuristics",            "wheel-first + semver"),
            ("L6", "LLM (last resort)",     "Gemma-2 9B call"),
        ]

        rows = VGroup()
        for lid, name, hint in levels:
            tag = Text(lid, font_size=18, color=ACCENT, weight=BOLD,
                       font="DejaVu Sans Mono")
            tag_bg = RoundedRectangle(corner_radius=0.06, width=0.7, height=0.5,
                                       fill_color=PANEL, fill_opacity=1,
                                       stroke_color=ACCENT, stroke_width=1.3,
                                       stroke_opacity=0.7)
            tag.move_to(tag_bg)
            tag_grp = VGroup(tag_bg, tag)

            n = Text(name, font_size=18, color=INK, weight=BOLD,
                     font="DejaVu Sans")
            h = Text(hint, font_size=13, color=DIM, font="DejaVu Sans",
                     slant=ITALIC)
            row = VGroup(tag_grp, n, h).arrange(RIGHT, buff=0.35,
                                                 aligned_edge=DOWN)
            rows.add(row)

        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        rows.move_to(DOWN * 0.2 + LEFT * 1.0)

        for r in rows:
            self.play(FadeIn(r, shift=RIGHT * 0.3), run_time=0.35)
            beat(self, 0.18)

        # vertical accent rule on the left of the cascade
        rule = Line(rows[0].get_left() + LEFT * 0.15 + UP * 0.2,
                    rows[-1].get_left() + LEFT * 0.15 + DOWN * 0.2,
                    color=ACCENT, stroke_width=3)
        cheap = Text("rẻ", font_size=14, color=ACCENT,
                     font="DejaVu Sans", weight=BOLD)
        expensive = Text("đắt", font_size=14, color=ACCENT,
                         font="DejaVu Sans", weight=BOLD)
        cheap.next_to(rule.get_start(), LEFT, buff=0.15)
        expensive.next_to(rule.get_end(), LEFT, buff=0.15)
        self.play(Create(rule), FadeIn(cheap), FadeIn(expensive),
                  run_time=0.6)
        beat(self, 0.6)

        self.play(FadeOut(VGroup(header, rows, rule, cheap, expensive)),
                  run_time=0.5)

    # ============================================================
    # PHASE 5 — Line chart result
    # ============================================================
    def _phase_chart(self):
        header = self._make_phase_header(
            "✓", "Kết quả",
            "MEMRES vs PLLM trên 2 dataset")
        self.play(FadeIn(header, shift=DOWN * 0.15), run_time=0.5)

        # Grouped bar chart: 2 datasets × 2 tools
        BASE_Y = -2.0
        MAX_H  = 3.8
        BAR_W  = 0.7
        GROUP_GAP = 1.4   # gap between dataset groups
        BAR_GAP   = 0.18  # gap between PLLM and MEMRES inside a group

        # X positions: HG2.9K group at -2, GitCham group at +2
        groups = [
            ("HG2.9K",       [("PLLM",   44.8),  ("MEMRES", 86.3)],  -2.2),
            ("GitChameleon", [("PLLM",   65.5),  ("MEMRES", 81.7)],   2.2),
        ]

        # Y-axis grid lines
        grid = VGroup()
        for pct in (20, 40, 60, 80, 100):
            y = BASE_Y + MAX_H * (pct / 100)
            g = DashedLine(LEFT * 5.5 + UP * y, RIGHT * 5.5 + UP * y,
                           color=DIM, stroke_width=0.6,
                           stroke_opacity=0.25, dash_length=0.12)
            tic = Text(f"{pct}%", font_size=14, color=DIM,
                       font="DejaVu Sans")
            tic.move_to(LEFT * 5.9 + UP * y)
            grid.add(g, tic)
        # Baseline
        baseline = Line(LEFT * 5.5 + UP * BASE_Y, RIGHT * 5.5 + UP * BASE_Y,
                        color=DIM, stroke_width=1.5)
        self.play(Create(baseline), FadeIn(grid), run_time=0.6)

        # Bars per group
        all_bars = VGroup()
        all_labels = VGroup()
        for label, bars, gx in groups:
            for j, (tool, v) in enumerate(bars):
                target_h = MAX_H * (v / 100)
                x = gx + (j - 0.5) * (BAR_W + BAR_GAP)
                color = DIM if tool == "PLLM" else ACCENT
                # Start with zero height
                bar = Rectangle(width=BAR_W, height=0.001,
                                 fill_color=color, fill_opacity=1,
                                 stroke_width=0)
                bar.move_to([x, BASE_Y, 0], aligned_edge=DOWN)
                bar.target_h = target_h
                bar.tool_name = tool
                bar.value = v
                bar.x_pos = x
                all_bars.add(bar)

                # Value label on top
                vlbl = Text(f"{v:.1f}%", font_size=18, color=color,
                            weight=BOLD, font="DejaVu Sans")
                vlbl.target_pos = [x, BASE_Y + target_h + 0.25, 0]
                vlbl.set_opacity(0)
                all_labels.add(vlbl)

            # Group X-label below baseline
            glabel = Text(label, font_size=20, color=INK,
                          weight=BOLD, font="DejaVu Sans")
            glabel.move_to([gx, BASE_Y - 0.45, 0])
            all_labels.add(glabel)
            glabel.set_opacity(1)

        # Y-axis title
        y_title = Text("Pass rate", font_size=14, color=DIM,
                       font="DejaVu Sans", slant=ITALIC)
        y_title.rotate(90 * DEGREES)
        y_title.move_to(LEFT * 6.5 + UP * (BASE_Y + MAX_H / 2))

        self.play(FadeIn(y_title),
                  *[FadeIn(g) for g in all_labels if hasattr(g, 'text')
                    and not hasattr(g, 'target_pos')],
                  run_time=0.5)

        # Animate bars growing — anchor to bottom (no extra shift)
        for bar in all_bars:
            self.play(
                bar.animate.stretch_to_fit_height(
                    bar.target_h, about_edge=DOWN),
                run_time=0.55, rate_func=rate_functions.ease_out_cubic,
            )
        # Show value labels
        for vlbl in [l for l in all_labels if hasattr(l, 'target_pos')]:
            vlbl.move_to(vlbl.target_pos)
            self.play(vlbl.animate.set_opacity(1), run_time=0.2)

        # Legend top-right
        legend = VGroup(
            VGroup(
                Square(side_length=0.25, color=DIM, fill_color=DIM,
                       fill_opacity=1, stroke_width=0),
                Text("PLLM (FSE'25)", font_size=16, color=INK,
                     font="DejaVu Sans"),
            ).arrange(RIGHT, buff=0.2),
            VGroup(
                Square(side_length=0.25, color=ACCENT, fill_color=ACCENT,
                       fill_opacity=1, stroke_width=0),
                Text("MEMRES (ours)", font_size=16, color=INK,
                     weight=BOLD, font="DejaVu Sans"),
            ).arrange(RIGHT, buff=0.2),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        legend.move_to(RIGHT * 4.8 + UP * 1.8)
        self.play(FadeIn(legend, shift=LEFT * 0.2), run_time=0.4)
        beat(self, 2.0)

    # original method body fully replaced — old below is unused
    def _legacy(self):

        # ============================================================
        # TOP — 4 stage cards with detailed sub-bullets each
        # ============================================================
        stages = [
            ("Knowledge Oracle",   ACCENT, [
                "Replay 2,900 solutions",
                "from PLLM history (yml)",
            ]),
            ("Hybrid Eval",        TEAL, [
                "Static AST analysis",
                "+ semantic import",
                "+ LLM few-shot",
            ]),
            ("Module Clean",       PURPLE, [
                "200+ error patterns",
                "Self-evolving memory",
                "PyPI name validation",
            ]),
            ("Confidence Cascade", SUCCESS, [
                "6 levels: session",
                "→ compat map → templates",
                "→ co-occur → heur → LLM",
            ]),
        ]

        boxes = VGroup()
        for ttl, color, bullets in stages:
            t = Text(ttl, font_size=20, color=color,
                     weight=BOLD, font="DejaVu Sans")
            bs = VGroup(*[
                Text(b, font_size=13, color=INK, font="DejaVu Sans")
                for b in bullets
            ]).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
            inner = VGroup(t, bs).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
            bg = RoundedRectangle(
                corner_radius=0.12,
                width=2.7, height=2.3,
                fill_color=PANEL, fill_opacity=1,
                stroke_color=color, stroke_width=1.8,
                stroke_opacity=0.7,
            )
            inner.move_to(bg).shift(LEFT * 0.1)
            strip = Rectangle(width=2.7, height=0.06,
                              fill_color=color, fill_opacity=1, stroke_width=0)
            strip.move_to(bg.get_top() + DOWN * 0.03)
            boxes.add(VGroup(bg, strip, inner))
        boxes.arrange(RIGHT, buff=0.22).scale(0.85).shift(UP * 1.4)

        arrows = VGroup(*[
            Arrow(boxes[i].get_right(), boxes[i + 1].get_left(),
                  buff=0.04, color=ACCENT, stroke_width=4,
                  max_tip_length_to_length_ratio=0.4)
            for i in range(len(boxes) - 1)
        ])

        for i, b in enumerate(boxes):
            self.play(FadeIn(b, shift=UP * 0.2), run_time=0.4)
            if i < len(arrows):
                self.play(GrowArrow(arrows[i]), run_time=0.2)
        beat(self, 0.5)

        # ============================================================
        # BOTTOM — Line chart: PLLM vs MEMRES on HG2.9K + GitChameleon
        # ============================================================
        axes = Axes(
            x_range=[-0.5, 1.5, 1],
            y_range=[0, 100, 20],
            x_length=7.0,
            y_length=2.8,
            axis_config={
                "color": DIM,
                "stroke_width": 1.5,
                "include_tip": False,
                "include_numbers": False,
            },
            y_axis_config={
                "include_numbers": True,
                "numbers_to_include": [0, 20, 40, 60, 80, 100],
                "decimal_number_config": {"num_decimal_places": 0,
                                          "color": DIM},
                "font_size": 18,
            },
        )
        axes.move_to(DOWN * 1.4 + LEFT * 1.0)

        # X-axis dataset labels
        x_labels = VGroup(
            Text("HG2.9K",       font_size=16, color=DIM, font="DejaVu Sans"),
            Text("GitChameleon", font_size=16, color=DIM, font="DejaVu Sans"),
        )
        for i, lbl in enumerate(x_labels):
            lbl.move_to(axes.c2p(i, 0) + DOWN * 0.25)

        y_title = Text("Pass rate (%)", font_size=14, color=DIM,
                       font="DejaVu Sans", slant=ITALIC)
        y_title.next_to(axes.y_axis, UP, buff=0.15)

        # Data
        pllm_pts   = [(0, 44.8), (1, 65.5)]
        memres_pts = [(0, 86.3), (1, 81.7)]

        def make_line(points, color, dashed=False):
            pts = [axes.c2p(x, y) for x, y in points]
            line = DashedLine(pts[0], pts[1], color=color, stroke_width=3,
                              dash_length=0.12) if dashed else \
                   Line(pts[0], pts[1], color=color, stroke_width=4)
            dots = VGroup(*[Dot(p, color=color, radius=0.08) for p in pts])
            labels = VGroup()
            for (x, y), p in zip(points, pts):
                lbl = Text(f"{y:.1f}%", font_size=16, color=color,
                           weight=BOLD, font="DejaVu Sans")
                lbl.next_to(p, UP if y > 50 else DOWN, buff=0.1)
                labels.add(lbl)
            return VGroup(line, dots, labels)

        pllm_line   = make_line(pllm_pts,   ALERT, dashed=True)
        memres_line = make_line(memres_pts, SUCCESS, dashed=False)

        # Legend
        legend = VGroup(
            VGroup(
                DashedLine(LEFT * 0.25, RIGHT * 0.25, color=ALERT,
                           stroke_width=3, dash_length=0.08),
                Text("PLLM (FSE'25)", font_size=15, color=INK,
                     font="DejaVu Sans"),
            ).arrange(RIGHT, buff=0.15),
            VGroup(
                Line(LEFT * 0.25, RIGHT * 0.25, color=SUCCESS, stroke_width=4),
                Text("MEMRES (ours)", font_size=15, color=INK,
                     weight=BOLD, font="DejaVu Sans"),
            ).arrange(RIGHT, buff=0.15),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        legend.move_to(RIGHT * 4.5 + DOWN * 1.4)

        # Reveal chart
        self.play(Create(axes), FadeIn(y_title), FadeIn(x_labels),
                  run_time=0.7)
        self.play(Create(pllm_line[0]),
                  FadeIn(pllm_line[1]), FadeIn(pllm_line[2]),
                  run_time=0.6)
        self.play(Create(memres_line[0]),
                  FadeIn(memres_line[1]), FadeIn(memres_line[2]),
                  run_time=0.6)
        self.play(FadeIn(legend, shift=LEFT * 0.2), run_time=0.5)
        beat(self, 2.0)


# ============================================================
# 8. MEMRES LIMITS → CGAR
# ============================================================
class MemresLimits(Scene):
    def construct(self):
        slide_chrome(self, "Vì sao cần cải tiến MEMRES?", "Phương pháp")

        left_ttl = Text("Động lực cải tiến", font_size=26, weight=BOLD,
                        color=ALERT, font="DejaVu Sans")
        issues = bullet_list([
            "Hợp môn ML: heuristic cascade → model-driven",
            "MEMRES còn 13.7% fail, ~335 s mỗi snippet",
            "Lỗi Docker là hộp đen — không tỉa nhánh được",
        ], font_size=20, dot_color=ALERT)
        left = card(VGroup(left_ttl, issues).arrange(
            DOWN, aligned_edge=LEFT, buff=0.35), pad=0.4)

        right_ttl = Text("CGAR — kết quả đã chứng minh",
                         font_size=26, weight=BOLD,
                         color=SUCCESS, font="DejaVu Sans")
        wins = bullet_list([
            "Lỗi → ràng buộc logic (CSP) — formalism của ML",
            "Pass-rate 87.1% / 83.2% (+0.8 / +1.5 pp vs MEMRES)",
            "15× nhanh hơn; cross-dataset chỉ −3.9 pp",
        ], font_size=20, dot_color=SUCCESS)
        right = card(VGroup(right_ttl, wins).arrange(
            DOWN, aligned_edge=LEFT, buff=0.35), pad=0.4)

        left.scale(0.85).move_to(LEFT * 3.6 + DOWN * 0.2)
        right.scale(0.85).move_to(RIGHT * 3.6 + DOWN * 0.2)

        arrow = Arrow(LEFT * 0.2, RIGHT * 0.2, color=ACCENT,
                      stroke_width=10, buff=0.05).scale(1.3).move_to(DOWN * 0.2)

        self.play(FadeIn(left, shift=RIGHT * 0.2), run_time=0.7)
        beat(self, 0.8)
        self.play(GrowArrow(arrow), run_time=0.5)
        self.play(FadeIn(right, shift=LEFT * 0.2), run_time=0.7)
        beat(self, 1.0)


# ============================================================
# 9. CSP FORMULATION  ⭐  — TransformMatchingTex narrative
# ============================================================
class CSPFormulation(Scene):
    def construct(self):
        slide_chrome(self, "CGAR — CSP Formulation", "CGAR")

        # Headline equation
        head = MathTex(
            r"\mathcal{P} = \langle\,", "X", ",\\ ", "D", ",\\ ", "C", r"\,\rangle",
            font_size=72, color=INK,
        )
        # color the three variable letters
        head[1].set_color(ACCENT)        # X
        head[3].set_color(TEAL)          # D
        head[5].set_color(PURPLE)        # C
        head.shift(UP * 2.4)
        dramatic_write(self, head, run_time=1.2)
        beat(self, 0.5)

        # X expansion
        x_eq = MathTex(
            r"X = \{\,P_1,\ P_2,\ \ldots,\ P_n,\ \pi\,\}",
            font_size=38, color=INK,
        )
        x_eq[0][0].set_color(ACCENT)
        x_lbl = Text("packages  +  Python version",
                     font_size=20, color=DIM, font="DejaVu Sans")
        x_grp = VGroup(x_eq, x_lbl).arrange(DOWN, buff=0.15, aligned_edge=LEFT)
        x_grp.move_to(LEFT * 0.0 + UP * 0.5)

        # D expansion
        d_eq = MathTex(
            r"D(P_i) = \{\, v \,\mid\, "
            r"\mathrm{req\_py}(v)\models\pi \,\land\, "
            r"\mathrm{wheel}(v)\,\}",
            font_size=30, color=INK,
        )
        d_eq[0][0].set_color(TEAL)
        d_lbl = Text("wheel-first, semver-descending",
                     font_size=20, color=DIM, font="DejaVu Sans")
        d_grp = VGroup(d_eq, d_lbl).arrange(DOWN, buff=0.15, aligned_edge=LEFT)
        d_grp.move_to(LEFT * 0.0 + DOWN * 0.6)

        # C expansion
        c_eq = MathTex(
            r"C \;=\; C_{\mathrm{hard}}\,\cup\,C_{\mathrm{soft}}\,\cup\,C_{\mathrm{ub}}",
            font_size=38, color=INK,
        )
        c_eq[0][0].set_color(PURPLE)
        c_lbl = Text("constraints learned from build failures",
                     font_size=20, color=DIM, font="DejaVu Sans")
        c_grp = VGroup(c_eq, c_lbl).arrange(DOWN, buff=0.15, aligned_edge=LEFT)
        c_grp.move_to(LEFT * 0.0 + DOWN * 2.0)

        # Reveal X with focus
        focus_on(self, head[1])
        self.play(TransformFromCopy(head[1], x_eq[0][0]),
                  FadeIn(x_eq[0][1:], shift=RIGHT * 0.3),
                  FadeIn(x_lbl), run_time=0.9)
        beat(self, 0.8)

        # D
        focus_on(self, head[3])
        self.play(TransformFromCopy(head[3], d_eq[0][0]),
                  FadeIn(d_eq[0][1:], shift=RIGHT * 0.3),
                  FadeIn(d_lbl), run_time=0.9)
        beat(self, 0.8)

        # C
        focus_on(self, head[5])
        self.play(TransformFromCopy(head[5], c_eq[0][0]),
                  FadeIn(c_eq[0][1:], shift=RIGHT * 0.3),
                  FadeIn(c_lbl), run_time=0.9)
        beat(self, 1.0)


# ============================================================
# 10. BACKTRACKING TREE  ⭐  — ThreeDScene, camera dives in
# ============================================================
class BacktrackingTree(ThreeDScene):
    def construct(self):
        title = Text("Backtracking + constraint pruning",
                     font_size=26, **TITLE_KW)
        bar = Rectangle(width=0.1, height=title.height + 0.12,
                        fill_color=ACCENT, fill_opacity=1, stroke_width=0)
        bar.next_to(title, LEFT, buff=0.18)
        chrome = VGroup(bar, title).to_corner(UL, buff=0.45)
        self.add_fixed_in_frame_mobjects(chrome)

        # Static front view — no perspective rotation (cleaner read)
        self.set_camera_orientation(phi=0 * DEGREES, theta=-90 * DEGREES,
                                    distance=11)

        # Root
        root = self._node3d("scipy ?", color=ACCENT)
        root.move_to(UP * 2.8)

        # Level 1
        v_labels = ["1.7.3", "1.5.4", "1.3.3", "1.1.0", "0.19.0"]
        l1 = VGroup(*[self._node3d(v, color=NAVY) for v in v_labels])
        l1.arrange(RIGHT, buff=0.55).next_to(root, DOWN, buff=1.4)

        edges = VGroup(*[
            Line3D(root.get_bottom() + DOWN * 0.05,
                   n.get_top() + UP * 0.05,
                   color=GHOST, thickness=0.012)
            for n in l1
        ])

        self.play(FadeIn(root), run_time=0.4)
        self.play(LaggedStart(*[Create(e) for e in edges], lag_ratio=0.12),
                  LaggedStart(*[FadeIn(n, shift=DOWN * 0.3) for n in l1],
                              lag_ratio=0.12),
                  run_time=1.3)
        beat(self, 0.5)

        # Failure signal — fixed-frame banner
        banner = Text("AttributeError: imread   ⇒   upper bound  scipy < 1.2",
                      font_size=24, color=ALERT, weight=BOLD,
                      font="DejaVu Sans")
        banner.to_edge(DOWN, buff=0.5)
        self.add_fixed_in_frame_mobjects(banner)
        banner.set_opacity(0)
        self.play(banner.animate.set_opacity(1), run_time=0.5)
        beat(self, 0.6)

        # Cross the first 3 (violate scipy < 1.2)
        crosses = VGroup()
        for n in l1[:3]:
            box = n[0]
            x1 = Line(box.get_corner(UL), box.get_corner(DR),
                      color=ALERT, stroke_width=5)
            x2 = Line(box.get_corner(UR), box.get_corner(DL),
                      color=ALERT, stroke_width=5)
            crosses.add(x1, x2)
        self.play(Create(crosses), run_time=0.7)
        self.play(VGroup(*[l1[i] for i in range(3)], crosses,
                         *[edges[i] for i in range(3)]).animate.set_opacity(0.25),
                  run_time=0.5)

        # Dim 0.19.0 (valid but older — CGAR picks latest valid)
        self.play(VGroup(l1[4], edges[4]).animate.set_opacity(0.35),
                  run_time=0.4)

        # Highlight winning branch — single green highlight (no overlapping boxes)
        chosen = l1[3]
        self.play(
            chosen[0].animate.set_stroke(color=SUCCESS, width=4.5),
            edges[3].animate.set_color(SUCCESS),
            Indicate(chosen, color=SUCCESS, scale_factor=1.15),
            run_time=0.8,
        )

        # Build subtree (winner)
        sub = VGroup(
            self._node3d("python 3.7", color=SUCCESS),
            self._node3d("numpy 1.16",  color=SUCCESS),
        ).arrange(RIGHT, buff=0.6).next_to(chosen, DOWN, buff=1.3)
        sub_edges = VGroup(*[
            Line3D(chosen.get_bottom() + DOWN * 0.05,
                   n.get_top() + UP * 0.05,
                   color=SUCCESS, thickness=0.014)
            for n in sub
        ])
        self.play(LaggedStart(*[Create(e) for e in sub_edges], lag_ratio=0.2),
                  LaggedStart(*[FadeIn(n, shift=DOWN * 0.3) for n in sub],
                              lag_ratio=0.2),
                  run_time=1.0)

        # Success badge
        ok = Text("✓  Build OK", font_size=30, weight=BOLD,
                  color=SUCCESS, font="DejaVu Sans")
        ok.to_edge(DOWN, buff=0.5)
        self.add_fixed_in_frame_mobjects(ok)
        ok.set_opacity(0)
        self.play(banner.animate.set_opacity(0),
                  ok.animate.set_opacity(1), run_time=0.6)
        beat(self, 2.5)

    def _node3d(self, label: str, color):
        t = Text(label, font_size=18, color=INK,
                 font="DejaVu Sans Mono")
        bg = RoundedRectangle(
            width=max(t.width + 0.3, 1.4), height=0.7,
            corner_radius=0.12,
            fill_color=PANEL, fill_opacity=1,
            stroke_color=color, stroke_width=2.5,
        ).move_to(t)
        return VGroup(bg, t)


# ============================================================
# 11. CGAR ARCHITECTURE (Manim version; Blender 3D in parallel)
# ============================================================
class CGARArchitecture(Scene):
    def construct(self):
        slide_chrome(self, "CGAR Multi-Agent Architecture", "CGAR")

        agents = [
            ("Planner",        ["query_pypi", "wheel_filter", "check_constraints"], ACCENT),
            ("Executor",       ["build_docker", "run_import"],                       TEAL),
            ("Error Analyzer", ["parse_error", "lookup_kb", "gen_constraint"],       ALERT),
            ("Critic",         ["analyze_failures", "suggest_strategy"],             SUCCESS),
        ]

        agent_cards = VGroup()
        for name, tools, color in agents:
            head = Text(name, font_size=22, weight=BOLD, color=INK,
                        font="DejaVu Sans")
            head_bar = Rectangle(width=2.7, height=0.5,
                                 fill_color=color, fill_opacity=0.25,
                                 stroke_color=color, stroke_width=2)
            head.move_to(head_bar)
            chips = VGroup(*[kbd(t, font_size=15) for t in tools])
            chips.arrange(DOWN, buff=0.12, aligned_edge=LEFT)
            inner = VGroup(VGroup(head_bar, head), chips).arrange(DOWN, buff=0.22)
            agent_cards.add(card(inner, pad=0.3, fill=PANEL))

        agent_cards.arrange_in_grid(rows=2, cols=2, buff=0.55).scale(0.78)
        agent_cards.shift(DOWN * 0.2)

        # Central memory torus (2D — circle with glow)
        mem = Circle(radius=0.6, color=ACCENT, stroke_width=3,
                     fill_color=ACCENT, fill_opacity=0.18)
        mem.move_to(agent_cards.get_center())
        mem_g = glow(mem, color=ACCENT, layers=8, opacity=0.05)
        mem_lbl = VGroup(
            Text("Session", font_size=14, color=INK, font="DejaVu Sans"),
            Text("Store",   font_size=14, color=INK, weight=BOLD,
                 font="DejaVu Sans"),
        ).arrange(DOWN, buff=0.05).move_to(mem)

        for c in agent_cards:
            self.play(FadeIn(c, shift=UP * 0.15), run_time=0.45)
        self.play(FadeIn(mem_g), FadeIn(mem_lbl), run_time=0.5)

        # Animated dashes
        for c in agent_cards:
            line = DashedLine(c.get_center(), mem.get_center(),
                              color=ACCENT, stroke_width=1.5,
                              dash_length=0.12)
            self.play(Create(line), run_time=0.25)
            self.play(ShowPassingFlash(
                line.copy().set_color(ACCENT_SOFT).set_stroke(width=4),
                time_width=0.6, run_time=0.7,
            ))
        beat(self, 2.0)


# ============================================================
# 12. FAILURE CASES
# ============================================================
class FailureCases(Scene):
    def construct(self):
        slide_chrome(self, "Failure cases → bài học", "CGAR")

        rows = [
            ["What we tried",                 "Why it failed",          "Fix"],
            ["Hardcode API-removed table",    "Brittle, breaks daily",   "LLM error analyzer"],
            ["Reset memory per snippet",      "No cross-learning",       "Session store +19.7%"],
            ["HARD constraints only",         "False bans from flukes",  "Add SOFT (≥2 obs)"],
            ["No wheel filter",               "Source build 3 min hang", "wheel_filter +17.9%"],
            ["Unbounded DFS",                 ">1000 candidate space",   "k=50 + Py-pivot"],
        ]
        tbl = Table(
            rows, include_outer_lines=True,
            line_config={"stroke_color": GHOST, "stroke_width": 1.5},
            element_to_mobject=Text,
            element_to_mobject_config={"font_size": 24, "font": "DejaVu Sans",
                                       "color": INK},
            h_buff=0.6, v_buff=0.35,
        ).scale(0.80)
        tbl.get_rows()[0].set_color(ACCENT)

        for r in tbl.get_rows()[1:]:
            r[1].set_color(ALERT)
            r[2].set_color(SUCCESS)
        tbl.move_to(ORIGIN).shift(DOWN * 0.05)

        self.play(FadeIn(tbl), run_time=0.5)
        beat(self, 0.8)

        lesson = Text("Learn from errors — don't hardcode them.",
                      font_size=24, weight=BOLD, slant=ITALIC,
                      color=ACCENT, font="DejaVu Sans")
        lesson.to_edge(DOWN, buff=0.55)
        self.play(FadeIn(lesson, shift=UP * 0.2), run_time=0.5)
        beat(self, 1.2)


# ============================================================
# 13a. PASS RATES — animated bar chart
# ============================================================
class PassRates(Scene):
    def construct(self):
        slide_chrome(self, "Pass rate — HG2.9K & GitChameleon", "Kết quả")

        tools = ["PyEGo", "ReadPyE", "PLLM", "MEMRES", "CGAR"]
        hg    = [45.0, 47.2, 44.8, 86.3, 87.1]
        gc    = [None, None, 65.5, 81.7, 83.2]

        # ---- layout constants (keep everything inside 14.22 x 8 frame) ----
        bar_w     = 0.40
        pair_gap  = 0.08
        group_w   = 2 * bar_w + pair_gap   # 0.88
        group_gap = 0.55
        n         = len(tools)
        total_w   = n * group_w + (n - 1) * group_gap
        x0        = -total_w / 2 + group_w / 2

        max_h  = 2.4
        AXIS_Y = -2.55

        # ---- axis + gridlines ----
        axis = Line([-6.0, AXIS_Y, 0], [6.0, AXIS_Y, 0],
                    color=DIM, stroke_width=1.4)
        self.add(axis)
        for pct in (25, 50, 75, 100):
            y = AXIS_Y + max_h * pct / 100
            grid = DashedLine([-5.8, y, 0], [5.8, y, 0],
                              color=GHOST, stroke_width=1,
                              dash_length=0.10).set_opacity(0.35)
            self.add(grid)
            tk = Text(f"{pct}%", font_size=14, color=DIM,
                      font="DejaVu Sans")
            tk.move_to([-6.35, y, 0])
            self.add(tk)

        # ---- legend (top-right, below chrome) ----
        sw_hg = Square(0.20, color=TEAL, fill_color=TEAL,
                       fill_opacity=1, stroke_width=0)
        t_hg  = Text("HG2.9K (n=2 889)", font_size=18, color=INK,
                     font="DejaVu Sans").next_to(sw_hg, RIGHT, buff=0.15)
        sw_gc = Square(0.20, color=ACCENT, fill_color=ACCENT,
                       fill_opacity=1, stroke_width=0)
        t_gc  = Text("GitChameleon (n=328)", font_size=18, color=INK,
                     font="DejaVu Sans").next_to(sw_gc, RIGHT, buff=0.15)
        legend = VGroup(VGroup(sw_hg, t_hg), VGroup(sw_gc, t_gc))\
            .arrange(RIGHT, buff=0.55, aligned_edge=DOWN)
        legend.move_to([0, 2.55, 0])
        self.add(legend)

        # ---- bars ----
        anims_per_group = []
        for i, name in enumerate(tools):
            cx = x0 + i * (group_w + group_gap)

            # tool name under axis
            tool_lbl = Text(name, font_size=20, color=INK,
                            weight=BOLD, font="DejaVu Sans")
            tool_lbl.move_to([cx, AXIS_Y - 0.35, 0])
            self.add(tool_lbl)

            group_anims = []

            # HG bar (left)
            hx = cx - (bar_w + pair_gap) / 2
            h_h = max_h * (hg[i] / 100)
            bar_h = Rectangle(width=bar_w, height=0.001,
                              fill_color=TEAL, fill_opacity=1,
                              stroke_width=0)
            bar_h.move_to([hx, AXIS_Y, 0], aligned_edge=DOWN)
            self.add(bar_h)
            val_h = Text(f"{hg[i]:.1f}", font_size=15,
                         color=TEAL, weight=BOLD, font="DejaVu Sans")
            val_h.move_to([hx, AXIS_Y + h_h + 0.20, 0])
            group_anims.append((bar_h, h_h, val_h))

            # GC bar (right)
            gx = cx + (bar_w + pair_gap) / 2
            if gc[i] is not None:
                g_h = max_h * (gc[i] / 100)
                bar_g = Rectangle(width=bar_w, height=0.001,
                                  fill_color=ACCENT, fill_opacity=1,
                                  stroke_width=0)
                bar_g.move_to([gx, AXIS_Y, 0], aligned_edge=DOWN)
                self.add(bar_g)
                val_g = Text(f"{gc[i]:.1f}", font_size=15,
                             color=ACCENT, weight=BOLD, font="DejaVu Sans")
                val_g.move_to([gx, AXIS_Y + g_h + 0.20, 0])
                group_anims.append((bar_g, g_h, val_g))
            else:
                na = Text("n/a", font_size=14, color=DIM,
                          slant=ITALIC, font="DejaVu Sans")
                na.move_to([gx, AXIS_Y + 0.20, 0])
                self.add(na)

            anims_per_group.append(group_anims)

        # animate bars group-by-group (left-to-right)
        for grp in anims_per_group:
            plays = []
            for bar, h, val in grp:
                plays.append(
                    bar.animate.stretch_to_fit_height(h, about_edge=DOWN)
                )
                plays.append(FadeIn(val, shift=DOWN * 0.08))
            self.play(*plays, run_time=0.55,
                      rate_func=rate_functions.ease_out_cubic)

        # halo on the winning CGAR group (last two bars)
        last_group = anims_per_group[-1]
        winner_mobs = VGroup(*[b for b, _, _ in last_group],
                             *[v for _, _, v in last_group])
        ring = SurroundingRectangle(winner_mobs, color=ACCENT,
                                    stroke_width=3, buff=0.18,
                                    corner_radius=0.10)
        self.play(Create(ring), run_time=0.5)
        self.play(ShowPassingFlash(
            ring.copy().set_color(ACCENT_SOFT).set_stroke(width=6),
            time_width=0.7), run_time=0.9)
        beat(self, 2.0)


# ============================================================
# 13b. SPEED RACE — the wow moment
# ============================================================
class SpeedRace(Scene):
    def construct(self):
        slide_chrome(self, "Speed — average seconds / snippet", "Kết quả")

        # two side-by-side panels (different scales — bars not comparable
        # across panels, but each panel internally consistent)
        panels = [
            ("HG2.9K (n=2 889)", -3.55, 400, [
                ("PLLM",   369.6, DIM),
                ("MEMRES", 335.3, TEAL),
                ("CGAR",    22.3, ACCENT),
            ]),
            ("GitChameleon (n=328)", 3.55, 100, [
                ("PLLM",    85.4, DIM),
                ("MEMRES",  38.7, TEAL),
                ("CGAR",    23.6, ACCENT),
            ]),
        ]
        bar_max_w = 2.6
        row_ys    = [1.15, 0.05, -1.05]   # 3 rows per panel

        for title, cx, scale_max, rows in panels:
            head = Text(title, font_size=22, color=INK,
                        weight=BOLD, font="DejaVu Sans")
            head.move_to([cx, 2.25, 0])
            self.play(FadeIn(head), run_time=0.25)

            # axis baseline
            ax_left  = cx - bar_max_w / 2 - 0.25
            ax_right = cx + bar_max_w / 2 + 0.55
            axis = Line([ax_left, row_ys[-1] - 0.45, 0],
                        [ax_right, row_ys[-1] - 0.45, 0],
                        color=DIM, stroke_width=1.2).set_opacity(0.5)
            self.add(axis)

            # gridlines + tick labels (25/50/75/100% of scale_max)
            for frac in (0.25, 0.5, 0.75, 1.0):
                gx = ax_left + bar_max_w * frac
                grid = DashedLine([gx, row_ys[0] + 0.45, 0],
                                  [gx, row_ys[-1] - 0.45, 0],
                                  color=GHOST, stroke_width=1,
                                  dash_length=0.08).set_opacity(0.25)
                self.add(grid)
                tk = Text(f"{int(scale_max*frac)}s", font_size=12,
                          color=DIM, font="DejaVu Sans")
                tk.move_to([gx, row_ys[-1] - 0.75, 0])
                self.add(tk)

            for i, (name, val, color) in enumerate(rows):
                y = row_ys[i]
                lbl = Text(name, font_size=20, color=color,
                           weight=BOLD, font="DejaVu Sans")
                lbl.move_to([cx - bar_max_w / 2 - 0.95, y, 0])

                bar = Rectangle(width=0.001, height=0.42,
                                fill_color=color, fill_opacity=0.92,
                                stroke_width=0)
                bar.move_to([ax_left, y, 0], aligned_edge=LEFT)
                tgt_w = bar_max_w * min(val / scale_max, 1.0)

                counter = DecimalNumber(0, num_decimal_places=1,
                                        font_size=22, color=color,
                                        unit=" s")
                counter.add_updater(
                    lambda m, b=bar: m.next_to(b.get_right(),
                                               RIGHT, buff=0.15)
                                      .set_y(b.get_y())
                )

                self.play(FadeIn(lbl), run_time=0.2)
                self.add(counter)
                self.play(
                    counter.animate.set_value(val),
                    bar.animate.stretch_to_fit_width(tgt_w,
                                                     about_edge=LEFT),
                    run_time=0.9,
                    rate_func=rate_functions.ease_out_cubic,
                )
                counter.clear_updaters()
                counter.next_to(bar.get_right(), RIGHT, buff=0.15)\
                       .set_y(bar.get_y())
                if name == "CGAR":
                    self.play(Indicate(counter, color=ACCENT,
                                       scale_factor=1.2), run_time=0.4)

        # vertical divider between panels
        div = DashedLine([0, 2.0, 0], [0, -2.0, 0],
                         color=GHOST, stroke_width=1,
                         dash_length=0.12).set_opacity(0.4)
        self.add(div)

        punch = Text("CGAR ≈ 15× faster than MEMRES, "
                     "17× than PLLM (HG2.9K)",
                     font_size=24, weight=BOLD,
                     color=ACCENT, font="DejaVu Sans")
        punch.to_edge(DOWN, buff=0.45)
        self.play(FadeIn(punch, shift=UP * 0.15), run_time=0.6)
        beat(self, 2.2)


# ============================================================
# 14a. ERRORS ELIMINATED
# ============================================================
class ErrorElim(Scene):
    def construct(self):
        slide_chrome(self, "Errors eliminated by CGAR  (vs PLLM, HG2.9K)",
                     "Kết quả")

        errs = [
            ("SyntaxError",            494, "Py2 detection"),
            ("NoMatchingDistribution", 282, "live PyPI metadata"),
            ("CouldNotBuildWheels",     83, "wheel filter"),
            ("AttributeError",          83, "upper-bound learning"),
        ]

        # fixed column anchors (centered values for numeric cols)
        X_NAME   = -5.6
        X_PLLM   = -1.0
        X_ARROW  =  0.0
        X_CGAR   =  1.0
        X_WHY    =  2.0
        y0       =  1.5
        dy       = -0.95

        # header strip
        h_kw = dict(font_size=17, color=DIM, slant=ITALIC,
                    font="DejaVu Sans")
        hdr_name = Text("error",     **h_kw)
        hdr_name.move_to([X_NAME + hdr_name.width / 2, y0 + 0.85, 0])
        hdr_pllm = Text("PLLM",      **dict(h_kw, color=ALERT))
        hdr_pllm.move_to([X_PLLM, y0 + 0.85, 0])
        hdr_cgar = Text("CGAR",      **dict(h_kw, color=SUCCESS))
        hdr_cgar.move_to([X_CGAR, y0 + 0.85, 0])
        hdr_mech = Text("mechanism", **h_kw)
        hdr_mech.move_to([X_WHY + hdr_mech.width / 2, y0 + 0.85, 0])
        underline = Line([X_NAME, y0 + 0.55, 0], [6.0, y0 + 0.55, 0],
                         color=GHOST, stroke_width=1).set_opacity(0.5)
        self.add(hdr_name, hdr_pllm, hdr_cgar, hdr_mech, underline)

        for i, (name, before, why) in enumerate(errs):
            y = y0 + i * dy

            n = Text(name, font_size=22, color=INK,
                     weight=BOLD, font="DejaVu Sans Mono")
            n.move_to([X_NAME + n.width / 2, y, 0])

            b = Text(str(before), font_size=28, color=ALERT,
                     weight=BOLD, font="DejaVu Sans")
            b.move_to([X_PLLM, y, 0])

            arr = Arrow([X_ARROW - 0.30, y, 0],
                        [X_ARROW + 0.30, y, 0],
                        color=DIM, stroke_width=4, buff=0.05)

            a = Text("0", font_size=28, color=SUCCESS,
                     weight=BOLD, font="DejaVu Sans")
            a.move_to([X_CGAR, y, 0])

            w = Text(why, font_size=18, color=DIM,
                     slant=ITALIC, font="DejaVu Sans")
            w.move_to([X_WHY + w.width / 2, y, 0])

            self.play(FadeIn(n), FadeIn(b), run_time=0.25)
            self.play(GrowArrow(arr), run_time=0.3)
            self.play(FadeIn(a, scale=1.4),
                      FadeIn(w, shift=RIGHT * 0.15), run_time=0.4)
            beat(self, 0.2)

        floor = Text("Remaining 10.7% — irreducible hard floor "
                     "(Py2 wheels, OS deps, removed APIs).",
                     font_size=20, color=DIM, slant=ITALIC,
                     font="DejaVu Sans")
        floor.to_edge(DOWN, buff=0.55)
        self.play(FadeIn(floor, shift=UP * 0.1), run_time=0.5)
        beat(self, 2.0)


# ============================================================
# 14b. ABLATION
# ============================================================
class Ablation(Scene):
    def construct(self):
        slide_chrome(self, "Ablation Study  (rescue eval, n=396)", "Kết quả")

        configs = [
            ("Full CGAR",       71, ACCENT,      "—"),
            ("− wheel filter",  40, ALERT,       "↓ 43.7%"),
            ("− upper bound",   23, ALERT,       "↓ 67.6%"),
            ("− session store", 56, ACCENT_SOFT, "↓ 21.1%"),
        ]

        # fixed anchors (no `next_to` chains — eliminates drift / overlap)
        X_LABEL = -5.4              # left edge of label column
        X_BAR_L = -2.4              # left edge of bars
        BAR_MAX = 5.4               # max bar width  → right edge at +3.0
        Y_TOP   =  1.7
        DY      = -0.85
        BAR_H   =  0.45
        BASELINE = 71

        # axis baseline + ticks (0, 25, 50, 75, 100% of baseline)
        ax_y = Y_TOP + DY * len(configs) - 0.25
        self.add(Line([X_BAR_L, ax_y, 0],
                      [X_BAR_L + BAR_MAX + 0.1, ax_y, 0],
                      color=DIM, stroke_width=1.2).set_opacity(0.6))
        for frac, label_n in [(0.0, 0), (0.25, 18),
                              (0.5, 35), (0.75, 53), (1.0, 71)]:
            gx = X_BAR_L + BAR_MAX * frac
            grid = DashedLine([gx, Y_TOP + 0.4, 0], [gx, ax_y, 0],
                              color=GHOST, stroke_width=1,
                              dash_length=0.10).set_opacity(0.25)
            self.add(grid)
            tk = Text(str(label_n), font_size=13, color=DIM,
                      font="DejaVu Sans")
            tk.move_to([gx, ax_y - 0.25, 0])
            self.add(tk)

        # baseline reference dashed (highlight 71 line)
        base_x = X_BAR_L + BAR_MAX
        self.add(DashedLine([base_x, Y_TOP + 0.4, 0],
                            [base_x, ax_y, 0],
                            color=ACCENT, stroke_width=2,
                            dash_length=0.12).set_opacity(0.45))

        for i, (name, n, color, delta) in enumerate(configs):
            y = Y_TOP + i * DY

            lbl = Text(name, font_size=22, color=INK,
                       font="DejaVu Sans Mono")
            lbl.move_to([X_LABEL + lbl.width / 2, y, 0])

            bar = Rectangle(width=0.001, height=BAR_H,
                            fill_color=color, fill_opacity=0.92,
                            stroke_width=0)
            bar.move_to([X_BAR_L, y, 0], aligned_edge=LEFT)
            tgt_w = BAR_MAX * (n / BASELINE)
            future_right = X_BAR_L + tgt_w

            n_t = Text(str(n), font_size=24, color=color,
                       weight=BOLD, font="DejaVu Sans")
            n_t.move_to([future_right + 0.30 + n_t.width / 2, y, 0])

            d_t = Text(delta, font_size=18, color=color,
                       slant=ITALIC, font="DejaVu Sans")
            d_t.move_to([future_right + 0.30 + n_t.width + 0.35
                         + d_t.width / 2, y, 0])

            self.play(FadeIn(lbl), run_time=0.2)
            self.play(
                bar.animate.stretch_to_fit_width(tgt_w, about_edge=LEFT),
                run_time=0.55, rate_func=rate_functions.ease_out_cubic,
            )
            self.play(FadeIn(n_t), FadeIn(d_t), run_time=0.3)
            beat(self, 0.2)

        foot = Text("Upper-bound constraint is the single largest "
                    "contributor (−67.6% if removed).",
                    font_size=18, color=DIM, slant=ITALIC,
                    font="DejaVu Sans")
        foot.to_edge(DOWN, buff=0.45)
        self.play(FadeIn(foot, shift=UP * 0.1), run_time=0.5)
        beat(self, 1.6)


# ============================================================
# 15. THANK YOU — cinematic close
# ============================================================
class ThankYou(Scene):
    def construct(self):
        stars = starfield(n=70)
        self.add(stars)
        self.play(LaggedStart(*[FadeIn(s) for s in stars],
                              lag_ratio=0.01), run_time=1.0)

        tk = Text("Thank you", font_size=110, **TITLE_KW)
        tk_glow = glow(tk, color=ACCENT, layers=10, opacity=0.04)
        sub = Text("Questions & Discussion",
                   font_size=32, color=ACCENT, slant=ITALIC, font="DejaVu Sans")
        # gradient underline (matches Title scene)
        underline = Rectangle(
            width=tk.width * 0.55, height=0.08, stroke_width=0,
        )
        underline.set_fill(color=[TEAL, ACCENT_SOFT, ACCENT], opacity=1)

        tag1 = Text("MEMRES & CGAR", font_size=22, color=INK,
                    weight=BOLD, font="DejaVu Sans")
        tag2 = Text("Agentic Python Dependency Resolution",
                    font_size=18, color=DIM, slant=ITALIC,
                    font="DejaVu Sans")
        tag = VGroup(tag1, tag2).arrange(DOWN, buff=0.10)

        stack = VGroup(tk_glow, underline, sub, tag).arrange(DOWN, buff=0.45)

        self.play(FadeIn(tk_glow, scale=0.95), run_time=1.0)
        underline.stretch_to_fit_width(0.001)
        self.play(underline.animate.stretch_to_fit_width(tk.width * 0.55),
                  run_time=0.6, rate_func=smooth)
        self.play(FadeIn(sub, shift=UP * 0.1), run_time=0.5)
        self.play(FadeIn(tag), run_time=0.5)
        twinkle(self, stars, duration=1.6)
        beat(self, 1.0)
        self.play(FadeOut(VGroup(stack, stars), shift=UP * 0.4), run_time=0.8)
