"""Pure-Manim, 3blue1brown-style scenes for the MEMRES & CGAR video.

Mirrors `../slide/main.tex` slide-by-slide (24 scenes total).

Design rules
------------
* Dark backdrop (#0E1518) with warm accent (#EB811B).
* No 3D camera flythroughs. All depth is faked with glow + gradients.
* Math reveals via MathTex + TransformMatchingTex / TransformFromCopy.
* Morphs (ReplacementTransform) used where they fall out naturally:
  - slide 5  import → constraint card
  - slide 10 gap card → fix card
  - slide 12 error message → constraint object flying into Session Store
  - slide 13 D(P_i) formula symbol-by-symbol mutation
* Every scene ends on a 1-line punchline that the narrator can land later.
"""
from __future__ import annotations
from manim import *
import numpy as np

from style import (
    BG, PANEL, NAVY, ACCENT, ACCENT_SOFT, TEAL, PURPLE,
    SUCCESS, ALERT, INK, DIM, GHOST,
    TITLE_KW, BODY_KW, MONO_KW,
    backdrop, slide_chrome, glow, bullet_list, reveal_bullets, card, kbd,
    beat, emphasize, focus_on, dramatic_write, deep_box,
    starfield, twinkle, chip, code_panel, flow_arrow, count_up, math_block,
)
from algorithms import (
    DFSTreeAnimator, ConstraintLedger, AgentCard, AgentBus, MorphBar,
    iso_pt, iso_box,
)


# ============================================================
# 1. TITLE
# ============================================================
class Title(Scene):
    """0:00–0:25. Starfield + two-tone hero title + gradient underline."""

    def construct(self):
        backdrop(self)
        stars = starfield(n=90)
        self.add(stars)
        self.play(LaggedStart(*[FadeIn(s) for s in stars],
                              lag_ratio=0.01), run_time=1.0)

        chip_t = Text("ML COURSE PROJECT  ·  2026",
                      font_size=18, color=ACCENT_SOFT,
                      font="Cascadia Code", weight=BOLD)
        chip_bg = RoundedRectangle(
            corner_radius=0.18,
            width=chip_t.width + 0.55, height=chip_t.height + 0.30,
            fill_color=NAVY, fill_opacity=1,
            stroke_color=ACCENT, stroke_width=1.5, stroke_opacity=0.6,
        ).move_to(chip_t)
        chip_m = VGroup(chip_bg, chip_t).move_to(UP * 2.5)

        memres = Text("MEMRES", font_size=92, color=TEAL, weight=BOLD,
                      font="Segoe UI")
        amp = Text("&", font_size=72, color=DIM, weight=BOLD,
                   font="Segoe UI")
        cgar = Text("CGAR", font_size=92, color=ACCENT, weight=BOLD,
                    font="Segoe UI")
        main = VGroup(memres, amp, cgar)\
            .arrange(RIGHT, buff=0.55, aligned_edge=DOWN).move_to(UP * 0.5)

        underline = Rectangle(width=main.width * 0.7, height=0.08,
                              stroke_width=0)
        underline.set_fill(color=[TEAL, ACCENT_SOFT, ACCENT], opacity=1)
        underline.next_to(main, DOWN, buff=0.55)

        sub = Text("Agentic Python Dependency Resolution",
                   font_size=32, color=INK, font="Segoe UI", slant=ITALIC)
        sub.next_to(underline, DOWN, buff=0.55)
        inst = Text("University of Science  ·  VNU-HCM",
                    font_size=20, color=DIM, font="Segoe UI")
        inst.next_to(sub, DOWN, buff=0.9)

        # isometric 3D motif — dim cube drawing in at the corner (hero accent)
        cube = iso_box(LEFT * 5.2 + UP * 1.4, w=1, h=1, d=1, color=ACCENT,
                       scale=0.95, top_op=0.20, front_op=0.13, side_op=0.09,
                       edge_op=0.55, edge_w=1.6)
        self.play(FadeIn(chip_m, shift=DOWN * 0.15),
                  Create(cube[3]), run_time=0.6)
        self.play(FadeIn(VGroup(cube[0], cube[1], cube[2])), run_time=0.4)
        for word, d in ((memres, LEFT * 0.5), (amp, UP * 0.1),
                        (cgar, RIGHT * 0.5)):
            word.save_state()
            word.shift(d).set_opacity(0)
        self.play(*[Restore(w) for w in (memres, amp, cgar)],
                  *[w.animate.set_opacity(1) for w in (memres, amp, cgar)],
                  run_time=1.0, rate_func=smooth)
        beat(self, 0.3)

        underline.stretch_to_fit_width(0.001)
        self.play(underline.animate.stretch_to_fit_width(main.width * 0.7),
                  run_time=0.7, rate_func=smooth)
        self.play(FadeIn(sub, shift=UP * 0.15), run_time=0.6)
        self.play(FadeIn(inst, shift=UP * 0.1), run_time=0.5)
        twinkle(self, stars, duration=1.6)
        beat(self, 0.6)
        self.play(FadeOut(VGroup(chip_m, main, underline, sub, inst, stars,
                                  cube),
                          shift=UP * 0.3), run_time=0.8)


# ============================================================
# 2. OUTLINE
# ============================================================
class Outline(Scene):
    def construct(self):
        slide_chrome(self, "Nội dung chính")
        stars = starfield(n=30, opacity_range=(0.06, 0.18))
        self.add(stars)

        sections = [
            ("01", "Phát biểu bài toán",       ACCENT),
            ("02", "MEMRES — baseline cascade", TEAL),
            ("03", "CGAR — multi-agent + CSP", ACCENT),
            ("04", "Kết quả & hạn chế",         SUCCESS),
        ]

        # Big numerals on the left, thin rule, title on the right
        rows = VGroup()
        for num, ttl, color in sections:
            n = Text(num, font_size=84, weight=BOLD, color=color,
                     font="Segoe UI")
            rule = Line(ORIGIN, RIGHT * 0.9, color=color, stroke_width=3,
                        stroke_opacity=0.85)
            t = Text(ttl, font_size=34, color=INK, font="Segoe UI")
            row = VGroup(n, rule, t).arrange(RIGHT, buff=0.45,
                                               aligned_edge=DOWN)
            rows.add(row)
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.55).move_to(DOWN * 0.2)

        for r in rows:
            self.play(FadeIn(r[0], shift=RIGHT * 0.3),
                       GrowFromEdge(r[1], LEFT),
                       FadeIn(r[2], shift=RIGHT * 0.2),
                       run_time=0.55, rate_func=smooth)
            beat(self, 0.15)
        beat(self, 6.0)   # hold for narration


# ============================================================
# 3. CONTEXT — old code wakes up dead
# ============================================================
class Context(Scene):
    def construct(self):
        slide_chrome(self, "Bối cảnh — mã GitHub cũ", "Bài toán")

        lead = Text("Hàng triệu Python snippet cũ trên GitHub…",
                    font_size=28, color=DIM, font="Segoe UI", slant=ITALIC)
        lead.move_to(UP * 2.0)

        cp = code_panel(
            "# 2014, no requirements.txt\n"
            "import scipy.misc as m\n"
            "from sklearn.cross_validation \\\n"
            "    import train_test_split\n"
            "img = m.imread('cat.jpg')",
            width=7.0, font_size=20,
        )
        cp.move_to(LEFT * 2.4 + DOWN * 0.2)

        # ENV DEAD stamp placed to the RIGHT of the code, not on top of it
        stamp = Text("ENV  DEAD", font_size=56, color=INK, weight=BOLD,
                     font="Segoe UI")
        stamp.rotate(-12 * DEGREES)
        stamp.move_to(RIGHT * 4.4 + DOWN * 0.2)
        stamp.set_opacity(0)
        # Filled red box behind the white text (classic stamp look)
        stamp_ring = SurroundingRectangle(stamp, color=ALERT,
                                           fill_color=ALERT, fill_opacity=0.85,
                                           stroke_color=ALERT, stroke_width=4,
                                           buff=0.22)
        stamp_ring.rotate(-12 * DEGREES, about_point=stamp.get_center())
        stamp_ring.set_opacity(0)

        self.play(FadeIn(lead, shift=UP * 0.2), run_time=0.5)
        beat(self, 0.5)
        self.play(FadeIn(cp, shift=UP * 0.15), run_time=0.7)
        beat(self, 0.8)
        # Arrow from code → stamp (the consequence)
        kill_arrow = Arrow(cp.get_right() + RIGHT * 0.15,
                            stamp_ring.get_left() + LEFT * 0.12,
                            color=ALERT, stroke_width=6, buff=0.05,
                            max_tip_length_to_length_ratio=0.22)
        # z-order: red box + white text pre-added (invisible), arrow grows in
        self.add(stamp_ring, stamp)
        self.play(GrowArrow(kill_arrow),
                  stamp_ring.animate.set_opacity(0.95),
                  stamp.animate.set_opacity(1),
                  run_time=0.7, rate_func=smooth)
        emphasize(self, stamp, color=ALERT, scale=1.10)
        beat(self, 0.8)

        punch = Text("Source còn — môi trường thì không.",
                     font_size=28, color=ACCENT, weight=BOLD,
                     font="Segoe UI", slant=ITALIC)
        punch.to_edge(DOWN, buff=0.6)
        self.play(FadeIn(punch, shift=UP * 0.1), run_time=0.6)
        beat(self, 4.6)   # hold for narration


# ============================================================
# 4. PROBLEM I/O — INPUT → ? → OUTPUT + budget badges
# ============================================================
class ProblemIO(Scene):
    def construct(self):
        slide_chrome(self, "Bài toán & Yêu cầu đánh giá", "Bài toán")

        in_chip = chip("INPUT  ·  orphaned snippet", ALERT)
        in_code = code_panel(
            "import scipy.misc as m\n"
            "from sklearn.cross_validation \\\n"
            "    import train_test_split\n"
            "import cv2\n\n"
            "img = m.imread('photo.jpg')",
            width=5.6, font_size=20, stroke=ALERT, stroke_opacity=0.35,
        )
        miss = VGroup(
            Text("×  no requirements.txt", font_size=17, color=ALERT,
                 font="Cascadia Code"),
            Text("×  no metadata", font_size=17, color=ALERT,
                 font="Cascadia Code"),
            Text("?  Python version unknown", font_size=17, color=ACCENT,
                 font="Cascadia Code"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.10)

        in_chip.next_to(in_code, UP, buff=0.20).align_to(in_code, LEFT)
        in_chip.shift(RIGHT * 0.25)
        miss.next_to(in_code, DOWN, buff=0.20).align_to(in_code, LEFT)
        miss.shift(RIGHT * 0.20)
        in_panel = VGroup(in_chip, in_code, miss).move_to(LEFT * 4.0
                                                            + DOWN * 0.15)

        out_chip = chip("REQUIRED OUTPUT  ·  runnable env", SUCCESS)
        rows = VGroup(
            Text("Python  3.7", font_size=20, **MONO_KW),
            Text("scipy==1.1.0", font_size=20, **MONO_KW),
            Text("scikit-learn==0.19.2", font_size=20, **MONO_KW),
            Text("opencv-python==4.5.5.62", font_size=20, **MONO_KW),
            Text("numpy==1.16.6", font_size=20, **MONO_KW),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.20)
        check = Text("✓  Docker import OK", font_size=22, color=SUCCESS,
                     weight=BOLD, font="Segoe UI")
        sep = Line(LEFT, RIGHT, color=GHOST, stroke_width=1)\
            .set_width(rows.width).set_opacity(0.4)
        out_body = VGroup(rows, sep, check).arrange(DOWN, buff=0.20,
                                                     aligned_edge=LEFT)
        out_panel_card = card(out_body, pad=0.35, stroke=SUCCESS,
                              stroke_opacity=0.30)
        out_chip.next_to(out_panel_card, UP, buff=0.20)\
                .align_to(out_panel_card, LEFT)
        out_chip.shift(RIGHT * 0.25)
        out_panel = VGroup(out_chip, out_panel_card)\
            .move_to(RIGHT * 4.0 + DOWN * 0.15)

        arrow = Arrow(in_code.get_right() + RIGHT * 0.15,
                      out_panel_card.get_left() + LEFT * 0.15,
                      color=ACCENT, stroke_width=5, buff=0.0,
                      max_tip_length_to_length_ratio=0.22)
        q_t = Text("?", font_size=44, weight=BOLD, color=ACCENT,
                   font="Segoe UI")
        q_bg = Circle(radius=0.42, fill_color=BG, fill_opacity=1,
                      stroke_color=ACCENT, stroke_width=2.5)
        qmark = VGroup(q_bg, q_t).move_to(arrow.get_center())

        # Budget badges (drop-in below)
        badges = VGroup(
            chip("K_build ≤ 10", ACCENT_SOFT, font_size=16),
            chip("K_solve ≤ 50", TEAL, font_size=16),
            chip("180 s / build", PURPLE, font_size=16),
        ).arrange(RIGHT, buff=0.30).to_edge(DOWN, buff=0.45)

        self.play(FadeIn(in_panel, shift=RIGHT * 0.2), run_time=0.7)
        beat(self, 0.6)
        self.play(GrowArrow(arrow), run_time=0.5)
        self.play(FadeIn(qmark, scale=0.7), run_time=0.4)
        emphasize(self, qmark, color=ACCENT, scale=1.18)
        self.play(FadeIn(out_panel, shift=LEFT * 0.2), run_time=0.7)
        emphasize(self, check, color=SUCCESS, scale=1.2)
        beat(self, 0.4)
        self.play(LaggedStart(*[FadeIn(b, shift=UP * 0.15) for b in badges],
                              lag_ratio=0.18), run_time=0.8)
        beat(self, 8.4)   # hold for narration


# ============================================================
# 5. DEPENDENCY DOMINO — imports MORPH into constraint cards
# ============================================================
class DependencyDomino(Scene):
    def construct(self):
        slide_chrome(self, "The Dependency Gap", "Bài toán")

        lead = Text("Một dòng import tưởng vô hại…",
                    font_size=28, color=DIM, font="Segoe UI", slant=ITALIC)
        lead.move_to(UP * 1.6)

        # Three imports that will each morph into a constraint card.
        imports_t = VGroup(
            Text("import scipy.misc          # imread() removed in ≥ 1.2",
                 font_size=22, color=INK, font="Cascadia Code"),
            Text("import cv2                 # actually  opencv-python",
                 font_size=22, color=INK, font="Cascadia Code"),
            Text("from sklearn.cross_validation import …  # removed",
                 font_size=22, color=INK, font="Cascadia Code"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.20)
        imports_t.move_to(UP * 0.2)

        self.play(FadeIn(lead, shift=UP * 0.15), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(t, shift=RIGHT * 0.2)
                                for t in imports_t], lag_ratio=0.15),
                  run_time=0.9)
        beat(self, 0.6)

        # MORPH: each import → constraint card
        def constraint_card(headline, sub, color, w=3.5, h=1.3):
            bullet = Text("▸", font_size=22, color=color, weight=BOLD,
                           font="Segoe UI")
            h_text = Text(headline, font_size=20, color=color, weight=BOLD,
                          font="Cascadia Code")
            head = VGroup(bullet, h_text).arrange(RIGHT, buff=0.16,
                                                    aligned_edge=DOWN)
            s_text = Text(sub, font_size=13, color=INK,
                          font="Segoe UI", slant=ITALIC)
            rule = Line(ORIGIN, RIGHT * 2.8, color=color, stroke_width=1.5,
                         stroke_opacity=0.6)
            return VGroup(head, rule, s_text).arrange(
                DOWN, buff=0.10, aligned_edge=LEFT)

        cards = VGroup(
            constraint_card("scipy ≤ 1.1", "API removed in ≥1.2", TEAL),
            constraint_card("cv2 → opencv-python",
                            "name mismatch (misleading)", ACCENT),
            constraint_card("sklearn ≤ 0.19", "module removed in ≥0.20",
                            PURPLE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        cards.move_to(LEFT * 2.5)

        self.play(FadeOut(lead), run_time=0.3)
        # morph imports → constraint cards ONE AT A TIME, each landing as the
        # narrator names it (scipy/imread → cv2/opencv → sklearn). Sequential
        # reveal keeps the visual in lock-step with the spoken walk-through.
        for o, n in zip(imports_t, cards):
            self.play(ReplacementTransform(o, n), run_time=0.7)
            beat(self, 1.4)

        # second column: the knock-on effect as toppling 3D dominoes
        labels = [("scipy", TEAL), ("numpy", ALERT),
                  ("Cython", PURPLE), ("Python", ACCENT_SOFT)]
        gap = 1.05
        dominoes, tops = VGroup(), VGroup()
        for i, (lab, col) in enumerate(labels):
            base = RIGHT * (i * gap) + DOWN * 0.6
            box = iso_box(base, w=0.32, h=1.25, d=0.5, color=col,
                          top_op=0.5, front_op=0.34, side_op=0.20,
                          edge_op=0.7, edge_w=1.6)
            t = Text(lab, font_size=13, color=col, weight=BOLD,
                     font="Cascadia Code").next_to(box, UP, buff=0.10)
            dominoes.add(box)
            tops.add(t)
        domino_grp = VGroup(dominoes, tops).move_to(RIGHT * 3.2 + UP * 0.1)

        arrow_a = Arrow(cards.get_right() + RIGHT * 0.05,
                        domino_grp.get_left() + LEFT * 0.05,
                        color=ACCENT, stroke_width=4, buff=0.05,
                        max_tip_length_to_length_ratio=0.15)
        self.play(GrowArrow(arrow_a), run_time=0.5)
        # dominoes drop in standing
        self.play(LaggedStart(*[FadeIn(d, shift=UP * 0.3) for d in dominoes],
                              *[FadeIn(t, shift=UP * 0.3) for t in tops],
                              lag_ratio=0.10), run_time=0.9)
        beat(self, 1.2)
        # topple wave: each tips forward about its base, knocking the next
        # (slower, with a beat between tips — matches "cả chuỗi domino đổ theo")
        for i, box in enumerate(dominoes):
            pivot = box[1].get_vertices()[1]   # front-bottom-right corner
            self.play(
                Rotate(box, angle=-72 * DEGREES, about_point=pivot,
                       rate_func=rate_functions.ease_in_quad),
                tops[i].animate.set_opacity(0.0),
                run_time=0.40,
            )
        beat(self, 0.8)

        punch = Text("Một import → cả chuỗi ràng buộc.",
                     font_size=26, color=ACCENT, weight=BOLD,
                     font="Segoe UI", slant=ITALIC)
        punch.to_edge(DOWN, buff=0.5)
        self.play(FadeIn(punch, shift=UP * 0.15), run_time=0.6)
        beat(self, 2.6)   # hold for closing line ("cả chuỗi domino đổ theo")


# ============================================================
# 6. COMBINATORIAL EXPLOSION — geometric lattice + entropy math
# ============================================================
class CombinatorialExplosion(Scene):
    def construct(self):
        slide_chrome(self, "Bùng nổ tổ hợp — không gian tìm kiếm", "Bài toán")

        # ---- LEFT: clean isometric wireframe cube (3B1B style) ----
        # base lowered so the cube body is centred on the y-axis (it grows up)
        cube_center = LEFT * 3.8 + DOWN * 1.45

        def iso(x, y, z):
            # axonometric projection: x→right, y→up, z→up-right diagonal
            sx = 1.05  # package axis length unit
            sy = 1.05  # version
            sz = 0.85  # py-version (depth, scaled smaller)
            X = sx * x + sz * z * 0.55
            Y = sy * y + sz * z * 0.45
            return cube_center + np.array([X, Y, 0])

        # 8 cube vertices
        v000, v100 = iso(0, 0, 0), iso(2, 0, 0)
        v010, v110 = iso(0, 2, 0), iso(2, 2, 0)
        v001, v101 = iso(0, 0, 2), iso(2, 0, 2)
        v011, v111 = iso(0, 2, 2), iso(2, 2, 2)

        # Semi-transparent faces for solid 3D feel (3 visible faces)
        # Uniform navy faces with top-bright shading → clean solid 3D body
        # (axis identity is carried by the coloured EDGES + grid, not the fills)
        face_top    = Polygon(v010, v110, v111, v011,
                                color=NAVY, fill_color=NAVY,
                                fill_opacity=0.58, stroke_width=0)
        face_right  = Polygon(v100, v110, v111, v101,
                                color=NAVY, fill_color=NAVY,
                                fill_opacity=0.40, stroke_width=0)
        face_front  = Polygon(v001, v101, v111, v011,
                                color=NAVY, fill_color=NAVY,
                                fill_opacity=0.26, stroke_width=0)
        faces = VGroup(face_top, face_right, face_front)

        # 12 edges — colored by axis: P=ACCENT, V=TEAL, Π=PURPLE
        edge_kw = dict(stroke_width=2.4, stroke_opacity=0.9)
        edges_p = VGroup(
            Line(v000, v100, color=ACCENT, **edge_kw),
            Line(v010, v110, color=ACCENT, **edge_kw),
            Line(v001, v101, color=ACCENT, **edge_kw),
            Line(v011, v111, color=ACCENT, **edge_kw),
        )
        edges_v = VGroup(
            Line(v000, v010, color=TEAL, **edge_kw),
            Line(v100, v110, color=TEAL, **edge_kw),
            Line(v001, v011, color=TEAL, **edge_kw),
            Line(v101, v111, color=TEAL, **edge_kw),
        )
        edges_pi = VGroup(
            Line(v000, v001, color=PURPLE, **edge_kw),
            Line(v100, v101, color=PURPLE, **edge_kw),
            Line(v010, v011, color=PURPLE, **edge_kw),
            Line(v110, v111, color=PURPLE, **edge_kw),
        )

        # Hidden-edge style: back edges dimmer
        for e in (edges_p[2], edges_v[2], edges_pi[2]):
            e.set_stroke(opacity=0.35)

        # Clean lattice GRID on the 3 VISIBLE faces (search-space feel) —
        # replaces scattered dots that muddied the centre.
        def face_grid(face, color, n=4):
            g = VGroup()
            for k in range(1, n):
                t = 2.0 * k / n
                if face == "top":       # y = 2 : vary x and z
                    g.add(Line(iso(t, 2, 0), iso(t, 2, 2)))
                    g.add(Line(iso(0, 2, t), iso(2, 2, t)))
                elif face == "right":   # x = 2 : vary y and z
                    g.add(Line(iso(2, t, 0), iso(2, t, 2)))
                    g.add(Line(iso(2, 0, t), iso(2, 2, t)))
                else:                   # front z = 2 : vary x and y
                    g.add(Line(iso(t, 0, 2), iso(t, 2, 2)))
                    g.add(Line(iso(0, t, 2), iso(2, t, 2)))
            return g.set_stroke(color=color, width=1.2, opacity=0.45)
        dots = VGroup(face_grid("top", TEAL), face_grid("right", ACCENT),
                       face_grid("front", PURPLE))

        # Axis labels — OUTSIDE the cube
        lx = Text("|P|", font_size=22, color=ACCENT, weight=BOLD,
                   font="Segoe UI")
        lx.next_to(v100, DOWN, buff=0.20).shift(RIGHT * 0.50)
        ly = Text("|V|", font_size=22, color=TEAL, weight=BOLD,
                   font="Segoe UI")
        ly.next_to(v010, LEFT, buff=0.20).shift(UP * 0.20)
        lz = Text(r"|Π|", font_size=22, color=PURPLE, weight=BOLD,
                   font="Segoe UI")
        lz.next_to(v111, UR, buff=0.15)

        # Reveal: wireframe edges first, then filled faces, then dots
        self.play(LaggedStart(
            *[Create(e) for e in edges_p],
            *[Create(e) for e in edges_v],
            *[Create(e) for e in edges_pi],
            lag_ratio=0.04), run_time=1.2)
        self.play(LaggedStart(*[FadeIn(f) for f in faces],
                               lag_ratio=0.10), run_time=0.7)
        self.play(FadeIn(lx), FadeIn(ly), FadeIn(lz), run_time=0.5)
        self.play(LaggedStart(*[Create(l) for fg in dots for l in fg],
                               lag_ratio=0.012), run_time=0.9)
        beat(self, 0.3)

        # ---- RIGHT: math derivation cascade ----
        eq1 = MathTex(
            r"\mathcal{S} \;=\; "
            r"\underbrace{P}_{\text{pkgs}} \times "
            r"\underbrace{V}_{\text{versions}} \times "
            r"\underbrace{\Pi}_{\text{Py}}",
            font_size=34, color=INK,
        )
        eq1.move_to(RIGHT * 2.5 + UP * 2.0)

        eq2 = MathTex(
            r"|\mathcal{S}| \;=\; \prod_{i=1}^{n} |D_i|",
            font_size=44, color=INK,
        )
        eq2[0][3].set_color(TEAL)        # |S| color
        eq2[0][5].set_color(ACCENT)      # ∏
        eq2.move_to(RIGHT * 2.5 + UP * 0.4)

        eq3 = MathTex(
            r"\approx 5{\cdot}10^{5} \times 20 \times 5 \;=\;"
            r"\mathbf{5{\cdot}10^{7}}",
            font_size=32, color=INK,
        )
        eq3[0][-7:].set_color(ALERT)
        eq3.move_to(RIGHT * 2.5 + DOWN * 0.95)

        eq4 = MathTex(
            r"\log_2 |\mathcal{S}| \;\approx\; 25.6 \text{ bits}",
            font_size=28, color=DIM,
        )
        eq4.move_to(RIGHT * 2.5 + DOWN * 2.0)

        self.play(Write(eq1), run_time=1.1)
        beat(self, 0.5)
        self.play(TransformMatchingShapes(eq1.copy(), eq2), run_time=0.9)
        beat(self, 0.4)
        self.play(FadeIn(eq3, shift=UP * 0.15, scale=1.1), run_time=0.7)
        emphasize(self, eq3[0][-7:], color=ALERT, scale=1.15)
        self.play(FadeIn(eq4, shift=UP * 0.1), run_time=0.5)
        beat(self, 0.8)

        punch = Text("Brute-force search là vô vọng.",
                      font_size=24, color=ACCENT, weight=BOLD,
                      font="Segoe UI", slant=ITALIC)
        punch.to_edge(DOWN, buff=0.40)
        self.play(FadeIn(punch, shift=UP * 0.15), run_time=0.5)
        beat(self, 1.4)


# ============================================================
# 7. DATASETS — stat cards (no image dependency)
# ============================================================
class Datasets(Scene):
    def construct(self):
        slide_chrome(self, "Datasets", "Bài toán")

        def stat_float(name, role, n, src, color):
            ttl = Text(name, font_size=48, color=color, weight=BOLD,
                       font="Segoe UI")
            r = Text(role, font_size=18, color=DIM, font="Segoe UI",
                     slant=ITALIC)
            rule = Line(ORIGIN, RIGHT * 2.2, color=color,
                         stroke_width=2.5, stroke_opacity=0.85)
            # Pre-size DecimalNumber so layout is correct from the start
            num_t = DecimalNumber(n, num_decimal_places=0,
                                   font_size=92, color=INK)
            n_l = Text("snippets", font_size=18, color=DIM,
                       font="Segoe UI")
            num_grp = VGroup(num_t, n_l).arrange(DOWN, buff=0.10)
            src_t = Text(src, font_size=14, color=DIM, font="Segoe UI",
                         slant=ITALIC)
            g = VGroup(ttl, r, rule, num_grp, src_t).arrange(
                DOWN, buff=0.30)
            # Force every subitem centered to title's x (fix tiny drift)
            cx = ttl.get_x()
            for m in (r, rule, num_grp, src_t):
                m.set_x(cx)
            # Then reset num_t to 0 ready for count-up
            num_t.set_value(0)
            g.num_t = num_t
            g.n = n
            g.cx = cx
            return g

        c1 = stat_float("HG2.9K", "in-distribution", 2891,
                         "Gistable · MSR'18", ACCENT)
        c2 = stat_float("GitChameleon", "OOD generalization", 328,
                         "arXiv 2411.05830", TEAL)
        cols = VGroup(c1, c2).arrange(RIGHT, buff=2.4).move_to(DOWN * 0.1)
        # Pin num_t centered under title even while counting up
        for c in cols:
            c.num_t.add_updater(
                lambda m, c=c: m.set_x(c[0].get_x())
            )

        for c in cols:
            self.play(FadeIn(c, shift=UP * 0.15), run_time=0.5)
        self.play(
            c1.num_t.animate.set_value(c1.n),
            c2.num_t.animate.set_value(c2.n),
            run_time=1.3, rate_func=rate_functions.ease_out_cubic,
        )
        beat(self, 0.6)

        foot = Text("Đánh giá pass-rate dựa trên Docker import "
                    "(HG2.9K) hoặc unit tests (GitChameleon).",
                    font_size=18, color=DIM, slant=ITALIC,
                    font="Segoe UI")
        foot.to_edge(DOWN, buff=0.5)
        self.play(FadeIn(foot, shift=UP * 0.1), run_time=0.5)
        beat(self, 9.6)   # hold for narration


# ============================================================
# 8a. RELATED WORK — 3 hướng
# ============================================================
class RelatedWorkApproaches(Scene):
    def construct(self):
        slide_chrome(self, "Related Work — 3 hướng tiếp cận", "Bài toán")

        approaches = [
            ("Knowledge Graph",
             "PyEGo · ReadPyE",
             "Static graph of dep relations",
             "Stuck at ~47% — no learning",
             TEAL),
            ("Log-Parsing / Regex",
             "PyDFix (ICSE'21)",
             "Regex on pip error logs",
             "Fragile, breaks on new logs",
             PURPLE),
            ("LLM + RAG",
             "PLLM (ASEW'25)",
             "RAG + Gemma-2 + trial/error",
             "Blind retries, ~370s / snippet",
             ACCENT),
        ]

        # Small geometric icons per approach (3B1B-style)
        def icon_kg(color):
            # 5 nodes in a small graph
            pts = [UP * 0.5, LEFT * 0.6 + DOWN * 0.1,
                    RIGHT * 0.6 + DOWN * 0.1,
                    LEFT * 0.35 + DOWN * 0.55,
                    RIGHT * 0.35 + DOWN * 0.55]
            dots = VGroup(*[Dot(p, radius=0.10, color=color) for p in pts])
            edges = VGroup(*[
                Line(pts[i], pts[j], color=color, stroke_width=2,
                      stroke_opacity=0.6)
                for i, j in [(0, 1), (0, 2), (1, 3), (2, 4), (3, 4),
                              (1, 2), (0, 3)]
            ])
            return VGroup(edges, dots)

        def icon_regex(color):
            # 3 stacked log lines with one highlighted "matched" region
            line1 = Line(LEFT * 0.7, RIGHT * 0.7, color=DIM,
                          stroke_width=2.5).shift(UP * 0.30)
            line2 = Line(LEFT * 0.7, RIGHT * 0.7, color=DIM,
                          stroke_width=2.5)
            line3 = Line(LEFT * 0.7, RIGHT * 0.7, color=DIM,
                          stroke_width=2.5).shift(DOWN * 0.30)
            # highlighted match
            hi = Rectangle(width=0.45, height=0.18, color=color,
                            fill_color=color, fill_opacity=0.55,
                            stroke_width=1.2)
            hi.move_to(line2.get_center() + LEFT * 0.15)
            slash_l = Text("/", font_size=24, color=color, weight=BOLD,
                            font="Cascadia Code").shift(LEFT * 1.0)
            slash_r = Text("/", font_size=24, color=color, weight=BOLD,
                            font="Cascadia Code").shift(RIGHT * 1.0)
            return VGroup(line1, line2, line3, hi, slash_l, slash_r)

        def icon_rag(color):
            # cylinder (DB) → arrow → circle (LLM)
            db_top = Ellipse(width=0.5, height=0.14, color=color,
                              fill_color=color, fill_opacity=0.25,
                              stroke_width=2)
            db_bot = Arc(radius=0.25, start_angle=PI, angle=PI,
                          color=color, stroke_width=2)
            db_side_l = Line(LEFT * 0.25 + UP * 0.001,
                              LEFT * 0.25 + DOWN * 0.40,
                              color=color, stroke_width=2)
            db_side_r = Line(RIGHT * 0.25 + UP * 0.001,
                              RIGHT * 0.25 + DOWN * 0.40,
                              color=color, stroke_width=2)
            db_bot.shift(DOWN * 0.40)
            db = VGroup(db_top, db_bot, db_side_l, db_side_r)
            db.shift(LEFT * 0.9 + UP * 0.18)
            arrow = Arrow(LEFT * 0.35, RIGHT * 0.35, color=color,
                           buff=0.0, stroke_width=2.5,
                           max_tip_length_to_length_ratio=0.25)
            llm = Circle(radius=0.32, color=color, fill_color=color,
                          fill_opacity=0.0, stroke_width=2.5)
            llm.shift(RIGHT * 0.95)
            return VGroup(db, arrow, llm)

        ICON_BUILDERS = (icon_kg, icon_regex, icon_rag)

        def make_column(idx, name, examples, summary, limit, color,
                          icon_builder):
            icon = icon_builder(color)
            # Fixed-height slot so all 3 columns align row-by-row
            icon.scale_to_fit_height(min(1.0, icon.height))
            slot = Rectangle(width=2.5, height=1.2,
                              fill_opacity=0, stroke_opacity=0)
            icon.move_to(slot.get_center())
            icon_slot = VGroup(slot, icon)
            num = Text(idx, font_size=46, color=color, weight=BOLD,
                        font="Segoe UI")
            ttl = Text(name, font_size=22, color=color, weight=BOLD,
                        font="Segoe UI")
            head = VGroup(num, ttl).arrange(RIGHT, buff=0.22,
                                              aligned_edge=DOWN)
            ex = Text(examples, font_size=14, color=DIM,
                       font="Cascadia Code", slant=ITALIC)
            rule = Line(ORIGIN, RIGHT * 3.0, color=color, stroke_width=2,
                         stroke_opacity=0.85)
            s = Text(summary, font_size=15, color=INK, font="Segoe UI")
            l = Text("× " + limit, font_size=14, color=ALERT,
                      font="Segoe UI", slant=ITALIC)
            return VGroup(icon_slot, head, ex, rule, s, l).arrange(
                DOWN, buff=0.22, aligned_edge=LEFT)

        cols = VGroup(*[
            make_column(f"0{i+1}", *approaches[i], ICON_BUILDERS[i])
            for i in range(3)
        ])
        cols.arrange(RIGHT, buff=0.95, aligned_edge=UP).move_to(DOWN * 0.1)

        for c in cols:
            self.play(FadeIn(c, shift=UP * 0.2), run_time=0.55)
            beat(self, 0.15)

        punch = Text("Cả 3 hướng đều chạm trần — cần một paradigm mới.",
                     font_size=22, color=ACCENT, weight=BOLD,
                     font="Segoe UI", slant=ITALIC)
        punch.to_edge(DOWN, buff=0.5)
        self.play(FadeIn(punch, shift=UP * 0.15), run_time=0.6)
        beat(self, 8.6)   # hold for narration


# ============================================================
# 8b. RELATED WORK — Timeline with plateau + PLLM breakthrough
# ============================================================
class RelatedWorkTimeline(Scene):
    def construct(self):
        slide_chrome(self, "Related Work — pass-rate qua thời gian",
                     "Bài toán")

        ax = Axes(
            x_range=[2018, 2027, 1], y_range=[30, 95, 10],
            x_length=9.0, y_length=4.4,
            axis_config={"color": DIM, "stroke_width": 1.5,
                          "include_tip": False,
                          "include_numbers": False},
        ).move_to(DOWN * 0.1)
        # Axis labels — horizontal, placed at the endpoints (3B1B style)
        x_lbl = Text("year", font_size=18, color=DIM, font="Segoe UI",
                     slant=ITALIC)
        x_lbl.move_to(ax.c2p(2026.5, 30) + DOWN * 0.50)
        y_lbl = Text("pass rate (%)", font_size=18, color=DIM,
                     font="Segoe UI", slant=ITALIC)
        y_lbl.move_to(ax.c2p(2018, 90) + UP * 0.45 + RIGHT * 0.30)

        # X-axis year ticks
        years_text = VGroup()
        for y in (2019, 2021, 2023, 2025, 2026):
            t = Text(str(y), font_size=14, color=DIM, font="Segoe UI")
            t.move_to(ax.c2p(y, 30) + DOWN * 0.25)
            years_text.add(t)
        # Y ticks
        for p in (40, 50, 60, 70, 80):
            t = Text(f"{p}", font_size=13, color=DIM, font="Segoe UI")
            t.move_to(ax.c2p(2018, p) + LEFT * 0.30)
            years_text.add(t)

        self.play(Create(ax), FadeIn(x_lbl), FadeIn(y_lbl),
                  FadeIn(years_text), run_time=0.9)

        # Plateau line at ~47%
        plateau_y = 47
        plateau = DashedLine(
            ax.c2p(2018, plateau_y), ax.c2p(2025, plateau_y),
            color=ALERT, stroke_width=2, dash_length=0.18,
        ).set_opacity(0.7)
        # plateau label placed safely BELOW the line (above-line area used by dots)
        plateau_t = Text("~47% plateau (KG era)", font_size=16, color=ALERT,
                         font="Segoe UI", slant=ITALIC)
        plateau_t.move_to(ax.c2p(2020, plateau_y) + DOWN * 0.40)
        self.play(Create(plateau), FadeIn(plateau_t), run_time=0.8)
        emphasize(self, plateau_t, color=ALERT, scale=1.08)
        beat(self, 0.5)

        # Method dots — each label placed at an explicit clear position
        # to avoid the auto-positioned UR collisions visible in previous render.
        # All points are HG2.9K pass rate. PLLM uses its 10-run union (54.7%)
        # — the value at which it actually breaks the KG ceiling (deck Table III).
        methods = [
            ("PyEGo",   2022, 45.0, TEAL,        DOWN * 0.35 + LEFT * 0.10),
            ("ReadPyE", 2024, 47.2, TEAL,        UP * 0.40 + LEFT * 0.10),
            ("PLLM",    2025, 54.7, ACCENT_SOFT, UP * 0.30 + LEFT * 0.50),
            ("MEMRES",  2026, 86.3, TEAL,        LEFT * 0.95 + UP * 0.05),
            ("CGAR",    2026.6, 87.1, ACCENT,    RIGHT * 0.10 + UP * 0.45),
        ]
        for name, x, y, color, off in methods:
            dot = Dot(ax.c2p(x, y), color=color, radius=0.10)
            lbl = Text(name, font_size=15, color=color, weight=BOLD,
                       font="Segoe UI")
            lbl.move_to(dot.get_center() + off)
            self.play(GrowFromCenter(dot), FadeIn(lbl, shift=off * 0.3),
                      run_time=0.4)
            if name == "CGAR":
                emphasize(self, dot, color=ACCENT, scale=1.5)

        # Honesty note: PLLM point is the 10-run union, not a single run.
        src_note = Text("PLLM = 54.7% (10-run union, HG2.9K)",
                        font_size=13, color=DIM, font="Segoe UI", slant=ITALIC)
        src_note.move_to(ax.c2p(2020.4, 38))
        self.play(FadeIn(src_note), run_time=0.3)

        # Big up-arrow PLLM → MEMRES — shifted to NOT overlap the points
        arrow = Arrow(ax.c2p(2024.0, 53), ax.c2p(2025.6, 80),
                       color=ACCENT, stroke_width=5, buff=0.05,
                       max_tip_length_to_length_ratio=0.20)
        self.play(GrowArrow(arrow), run_time=0.6)
        emphasize(self, arrow, color=ACCENT, scale=1.05)

        punch = Text("Breakthrough đến từ LLM + agents — không phải KG.",
                     font_size=22, color=ACCENT, weight=BOLD,
                     font="Segoe UI", slant=ITALIC)
        punch.to_edge(DOWN, buff=0.45)
        self.play(FadeIn(punch, shift=UP * 0.15), run_time=0.6)
        beat(self, 5.8)   # hold for narration


# ============================================================
# 9. MEMRES PIPELINE — 4 stages condensed
# ============================================================
class MemresPipeline(Scene):
    def construct(self):
        slide_chrome(self, "MEMRES — Lookup-First, LLM-Last", "MEMRES")

        sub = Text("Pipeline 4 tầng — rẻ tới đắt",
                   font_size=24, color=DIM, font="Segoe UI", slant=ITALIC)
        sub.move_to(UP * 2.6)
        self.play(FadeIn(sub), run_time=0.4)

        # 4 stages as rising isometric 3D tiers — height = cost (rẻ → đắt)
        tiers = [
            ("1", "Oracle",       "replay 2,900 solutions",  ACCENT,  0.6),
            ("2", "Hybrid Eval",  "AST + semantic + LLM",    TEAL,    0.95),
            ("3", "Module Clean", "200+ error patterns",     PURPLE,  1.30),
            ("4", "Cascade",      "6 levels: session → LLM", SUCCESS, 1.70),
        ]
        x0, dx, base_y = -4.6, 2.4, -0.4
        blocks, caps, flow = VGroup(), VGroup(), VGroup()
        for i, (num, name, desc, color, h) in enumerate(tiers):
            base = np.array([x0 + i * dx, base_y, 0.0])
            box = iso_box(base, w=0.85, h=h, d=0.55, color=color,
                          top_op=0.55, front_op=0.40, side_op=0.24,
                          edge_op=0.85, edge_w=2.0)
            num_t = Text(num, font_size=24, color=INK, weight=BOLD,
                         font="Segoe UI").move_to(box[1].get_center())
            name_t = Text(name, font_size=19, color=color, weight=BOLD,
                          font="Segoe UI")
            desc_t = Text(desc, font_size=12, color=DIM, font="Segoe UI",
                          slant=ITALIC)
            cap = VGroup(name_t, desc_t).arrange(DOWN, buff=0.08)\
                .next_to(box, DOWN, buff=0.22)
            blocks.add(VGroup(box, num_t))
            caps.add(cap)
        for i in range(3):
            flow.add(Arrow(blocks[i].get_top() + RIGHT * 0.05,
                           blocks[i + 1].get_top() + LEFT * 0.05,
                           color=ACCENT_SOFT, stroke_width=2.5, buff=0.18,
                           max_tip_length_to_length_ratio=0.25,
                           stroke_opacity=0.7))

        # Reveal each tier as the narrator names it
        # ("Oracle, Hybrid Evaluation, Module Clean, và Confidence Cascade").
        for i in range(4):
            self.play(GrowFromEdge(blocks[i][0], DOWN),
                       FadeIn(blocks[i][1]),
                       FadeIn(caps[i], shift=UP * 0.1),
                       run_time=0.45, rate_func=rate_functions.ease_out_cubic)
            if i < 3:
                self.play(GrowArrow(flow[i]), run_time=0.22)
            beat(self, 0.9)

        # Headline numbers — bare floating, no cards
        def stat(num, lbl, color):
            n = Text(num, font_size=72, color=color, weight=BOLD,
                     font="Segoe UI")
            l = Text(lbl, font_size=14, color=DIM, font="Segoe UI",
                     slant=ITALIC)
            return VGroup(n, l).arrange(DOWN, buff=0.10)

        stats = VGroup(
            stat("86.3%", "HG2.9K pass rate",     ACCENT),
            stat("81.7%", "GitChameleon pass",    TEAL),
            stat("335s",  "avg / snippet",         SUCCESS),
        ).arrange(RIGHT, buff=1.8).move_to(DOWN * 1.7)

        # Numbers land as the narrator reads them ("86,3 … 81,7 … 335 giây").
        for s in stats:
            self.play(FadeIn(s, shift=UP * 0.2, scale=0.85), run_time=0.5)
            emphasize(self, s[0], color=s[0].get_color(), scale=1.12)
            beat(self, 1.3)

        punch = Text("Cascade rẻ trước, LLM chỉ là tầng cuối.",
                     font_size=22, color=ACCENT_SOFT, weight=BOLD,
                     font="Segoe UI", slant=ITALIC)
        punch.to_edge(DOWN, buff=0.45)
        self.play(FadeIn(punch, shift=UP * 0.15), run_time=0.6)
        beat(self, 3.8)   # hold for closing line


# ============================================================
# 10. MEMRES → CGAR — 3 gap cards MORPH into 3 fix cards
# ============================================================
class MemresLimits(Scene):
    def construct(self):
        slide_chrome(self, "Từ MEMRES → CGAR — vá 3 lỗ hổng", "CGAR")

        gaps = [
            ("12.8% dead ends",
             "API removed / source-only wheels"),
            ("335s / snippet",
             "high error cost, no early stop"),
            ("No constraint learning",
             "errors discarded after retry"),
        ]
        fixes = [
            ("Analyzer Agent",
             "extract typed constraints from logs"),
            ("wheel_filter()",
             "skip versions w/o linux wheels"),
            ("Constraint Store (3 tiers)",
             "HARD · SOFT · UPPER bounds"),
        ]

        def text_block(headline, sub, color, prefix):
            p = Text(prefix, font_size=28, color=color, weight=BOLD,
                     font="Segoe UI")
            h = Text(headline, font_size=20, color=color, weight=BOLD,
                     font="Cascadia Code")
            s = Text(sub, font_size=14, color=INK, font="Segoe UI",
                     slant=ITALIC)
            head = VGroup(p, h).arrange(RIGHT, buff=0.18, aligned_edge=DOWN)
            block = VGroup(head, s).arrange(DOWN, buff=0.18,
                                              aligned_edge=LEFT)
            rule = Line(ORIGIN, RIGHT * 3.2, color=color,
                         stroke_width=2, stroke_opacity=0.85)
            rule.next_to(head, DOWN, buff=0.10, aligned_edge=LEFT)
            return VGroup(p, h, rule, s)

        gap_cards = VGroup(*[text_block(g[0], g[1], ALERT, "×")
                              for g in gaps])
        gap_cards.arrange(RIGHT, buff=0.55).move_to(UP * 1.1)

        fix_cards = VGroup(*[text_block(f[0], f[1], SUCCESS, "✓")
                              for f in fixes])
        fix_cards.arrange(RIGHT, buff=0.55).move_to(DOWN * 0.6)

        for g in gap_cards:
            self.play(FadeIn(g, shift=DOWN * 0.2), run_time=0.45)
            beat(self, 0.15)

        # MORPH each gap → fix (downward). Fade out the gap as the fix appears
        for g, f in zip(gap_cards, fix_cards):
            self.play(ReplacementTransform(g, f), run_time=0.7)
            beat(self, 0.25)

        # Final consolidation: morph the 3 fix cards into a single CGAR badge
        cgar_badge = Text("CGAR", font_size=72, color=ACCENT, weight=BOLD,
                          font="Segoe UI")
        cgar_glow = glow(cgar_badge, color=ACCENT, layers=8, opacity=0.06)
        cgar_glow.move_to(ORIGIN)
        beat(self, 0.6)
        self.play(
            *[ReplacementTransform(f, cgar_badge.copy()) for f in fix_cards],
            FadeIn(cgar_glow), run_time=1.0,
        )
        # Formula: paradigm
        morph_eq = MathTex(
            r"\text{Error} \;\longmapsto\; \text{Constraint} \;\longmapsto\; \text{Rule}",
            font_size=28, color=INK,
        )
        morph_eq[0][:5].set_color(ALERT)
        morph_eq[0][-4:].set_color(SUCCESS)
        morph_eq.to_edge(DOWN, buff=0.45)
        self.play(FadeIn(morph_eq, shift=UP * 0.1), run_time=0.7)
        beat(self, 7.4)   # hold for narration


# ============================================================
# 11. PARADIGM SHIFT — random brownian → focused constrained search
# ============================================================
class ParadigmShift(Scene):
    def construct(self):
        slide_chrome(self, "CGAR — Paradigm Shift", "CGAR")

        # ---- LEFT panel: random ricochet (PLLM/MEMRES) ----
        left_lbl = Text("PLLM / MEMRES\nblind retry", font_size=22,
                         color=ALERT, weight=BOLD, font="Segoe UI",
                         line_spacing=0.6)
        left_lbl.move_to(LEFT * 4.0 + UP * 2.7)

        left_frame = RoundedRectangle(
            corner_radius=0.18, width=5.5, height=4.8,
            fill_color=PANEL, fill_opacity=0.0,
            stroke_color=ALERT, stroke_width=1.4, stroke_opacity=0.6,
        ).move_to(LEFT * 4.0 + DOWN * 0.1)

        # ---- RIGHT panel: constrained convergence (CGAR) ----
        right_lbl = Text("CGAR\nlearn → constrain", font_size=22,
                          color=SUCCESS, weight=BOLD, font="Segoe UI",
                          line_spacing=0.6)
        right_lbl.move_to(RIGHT * 4.0 + UP * 2.7)
        right_frame = left_frame.copy().move_to(RIGHT * 4.0 + DOWN * 0.1)
        right_frame.set_stroke(color=SUCCESS, opacity=0.6)

        target = Dot(point=RIGHT * 4.0 + DOWN * 1.7, color=ACCENT,
                      radius=0.20)
        target_g = glow(target, color=ACCENT, layers=9, opacity=0.13)

        self.play(FadeIn(left_frame), FadeIn(right_frame),
                  FadeIn(left_lbl), FadeIn(right_lbl),
                  FadeIn(target_g), run_time=0.7)

        # Random dots inside left panel — clamped to stay inside frame
        rng = np.random.default_rng(7)
        L_CX, L_CY = -4.0, -0.1
        L_HW, L_HH = 2.4, 2.1   # half-width / half-height of inner area

        def left_pt():
            return np.array([L_CX + rng.uniform(-L_HW, L_HW),
                              L_CY + rng.uniform(-L_HH, L_HH), 0.0])

        left_dots = VGroup(*[
            Dot(point=left_pt(), color=ALERT, radius=0.06).set_opacity(0.6)
            for _ in range(18)
        ])
        self.play(LaggedStart(*[FadeIn(d) for d in left_dots],
                               lag_ratio=0.03), run_time=0.8)
        # jitter — but always move to a NEW clamped point, never escape
        for _ in range(4):
            anims = []
            for d in left_dots:
                anims.append(d.animate.move_to(left_pt()))
            self.play(*anims, run_time=0.35, rate_func=smooth)

        # Right side: funnel that NARROWS DOWN to the target (constraints
        # successively shrink the viable region).  Apex = target at bottom.
        R_CX = 4.0
        apex = np.array([R_CX, -1.7, 0.0])
        top_l = np.array([R_CX - 1.9, 1.9, 0.0])
        top_r = np.array([R_CX + 1.9, 1.9, 0.0])
        cone_l = Line(top_l, apex, color=PURPLE, stroke_width=2.5)\
            .set_opacity(0.7)
        cone_r = Line(top_r, apex, color=PURPLE, stroke_width=2.5)\
            .set_opacity(0.7)
        # filled converging beam — the viable region shrinking to the target
        wedge = Polygon(top_l, top_r, apex, fill_color=PURPLE,
                        fill_opacity=0.13, stroke_width=0)
        # faint "constraint level" rungs across the narrowing beam
        rungs = VGroup()
        for f in (0.30, 0.55, 0.78):
            yl = top_l + (apex - top_l) * f
            yr = top_r + (apex - top_r) * f
            rungs.add(Line(yl, yr, color=PURPLE, stroke_width=1.2)
                      .set_opacity(0.35))
        self.play(FadeIn(wedge), Create(cone_l), Create(cone_r),
                   run_time=0.7)
        self.play(LaggedStart(*[Create(r) for r in rungs],
                              lag_ratio=0.2), run_time=0.5)

        # Dots start spread across the top (wide region), converge to apex
        def cone_top_pt():
            return np.array([R_CX + rng.uniform(-1.6, 1.6),
                              rng.uniform(1.4, 1.8), 0.0])

        right_dots = VGroup(*[
            Dot(point=cone_top_pt(), color=SUCCESS,
                radius=0.06).set_opacity(0.75)
            for _ in range(14)
        ])
        self.play(LaggedStart(*[FadeIn(d) for d in right_dots],
                               lag_ratio=0.04), run_time=0.6)
        self.play(*[d.animate.move_to(
            apex + np.array([rng.uniform(-0.18, 0.18),
                              rng.uniform(-0.05, 0.05), 0]))
                     for d in right_dots],
                   run_time=1.2, rate_func=rate_functions.ease_in_out_cubic)
        # the single target already sits at the apex — just emphasize it
        # (no second dot; the intro target was the orphan duplicate)
        emphasize(self, target_g, color=ACCENT, scale=1.15)

        # ---- Math overlay: probability ratio ----
        m_top = MathTex(
            r"\Pr[\text{success} \mid \text{random}] "
            r"\;\approx\; \frac{1}{|\mathcal{S}|}",
            font_size=22, color=ALERT,
        ).move_to(LEFT * 4.0 + DOWN * 3.1)
        m_bot = MathTex(
            r"\Pr[\text{success} \mid \text{CGAR}] "
            r"\;\approx\; \frac{1}{|\,\mathcal{S} \cap C\,|}",
            font_size=22, color=SUCCESS,
        ).move_to(RIGHT * 4.0 + DOWN * 3.1)
        self.play(Write(m_top), Write(m_bot), run_time=1.0)

        punch = Text("Error → Rule.  Random retry → constrained DFS.",
                      font_size=22, color=ACCENT, weight=BOLD,
                      font="Segoe UI", slant=ITALIC)
        punch.to_edge(DOWN, buff=0.10)
        self.play(FadeIn(punch, shift=UP * 0.15), run_time=0.5)
        beat(self, 5.4)   # hold for narration


# ============================================================
# 12. MULTI-AGENT LOOP — full 2-iteration algorithm trace ⭐
# ============================================================
class MultiAgentLoop(Scene):
    def construct(self):
        slide_chrome(self, "CGAR — Multi-Agent Loop", "CGAR")

        # 4 agents as circles on a ring around the Session Store (geometric, 3B1B-style)
        def agent_node(name, role, color, pos):
            c = Circle(radius=0.55, color=color, stroke_width=3,
                        fill_color=PANEL, fill_opacity=0.95)
            c.move_to(pos)
            c_glow = glow(c, color=color, layers=5, opacity=0.05)
            n = Text(name, font_size=20, color=INK, weight=BOLD,
                     font="Segoe UI")
            n.next_to(c, UP, buff=0.18)
            r = Text(role, font_size=13, color=DIM, font="Segoe UI",
                     slant=ITALIC)
            r.next_to(c, DOWN, buff=0.18)
            grp = VGroup(c_glow, n, r)
            grp.center_circle = c
            grp.color_ = color
            return grp

        planner  = agent_node("Planner",  "LLM gen plan",     ACCENT,
                              UP * 2.6)
        executor = agent_node("Executor", "Docker build",     TEAL,
                              RIGHT * 4.4 + DOWN * 0.2)
        analyzer = agent_node("Analyzer", "Log → constraint", ALERT,
                              DOWN * 2.3)
        critic   = agent_node("Critic",   "Strategy",          PURPLE,
                              LEFT * 4.4 + DOWN * 0.2)

        # Taller ledger so 2 constraint cards fit comfortably inside
        ledger = ConstraintLedger("Session Store", width=2.6, height=2.5)
        ledger.move_to(ORIGIN + UP * 0.05)

        # Agents appear one-by-one, held as the narrator names each role
        # ("Planner lên kế hoạch, Executor build trong Docker, …").
        for a in (planner, executor, analyzer, critic):
            self.play(FadeIn(a, shift=UP * 0.2), run_time=0.35)
            beat(self, 1.1)
        self.play(FadeIn(ledger), run_time=0.5)
        beat(self, 1.0)

        # Math: the update rule that this loop implements
        update_rule = MathTex(
            r"C_{t+1} \;=\; C_t \,\cup\, "
            r"\text{Analyze}(\varepsilon_t)",
            font_size=22, color=INK,
        )
        update_rule[0][0].set_color(PURPLE)
        update_rule[0][3].set_color(PURPLE)
        plan_rule = MathTex(
            r"\pi_{t+1} \;=\; "
            r"\arg\min_{x \in D} \; \text{cost}(x) "
            r"\text{ s.t. } C_{t+1}",
            font_size=20, color=INK,
        )
        plan_rule[0][0].set_color(ACCENT)
        plan_rule[0][3].set_color(ACCENT)
        math_box = VGroup(update_rule, plan_rule).arrange(
            DOWN, aligned_edge=LEFT, buff=0.15)
        math_box.to_corner(UL, buff=0.7).shift(DOWN * 0.5 + RIGHT * 0.2)
        self.play(Write(math_box), run_time=1.0)
        beat(self, 0.3)

        bus = AgentBus({"P": planner, "E": executor,
                         "A": analyzer, "C": critic}, ledger)

        # ---- iteration label that morphs in place each round ----
        iter_lbl = None

        def set_iter(n):
            nonlocal iter_lbl
            new = Text(f"Iteration {n}", font_size=20, color=DIM,
                       font="Segoe UI", slant=ITALIC)
            new.to_corner(UR, buff=0.6).shift(DOWN * 0.4)
            if iter_lbl is None:
                self.play(FadeIn(new), run_time=0.3)
            else:
                self.play(ReplacementTransform(iter_lbl, new), run_time=0.3)
            iter_lbl = new

        def emit_plan(label, color):
            # Planner emits a plan token; clear it on arrival so it never
            # lingers over the Executor label.
            tok = chip(label, color, font_size=13)
            bus.send(self, "P", "E", payload=tok, color=color)
            self.play(FadeOut(tok), run_time=0.15)
            # the plan IS argmin cost s.t. C — pulse the rule it implements
            self.play(Indicate(plan_rule, color=ACCENT, scale_factor=1.08),
                      run_time=0.45)

        def fail_and_learn(err_str, cons_body, kind, crit_note):
            # build fails — Executor flashes red
            self.play(executor.center_circle.animate.set_stroke(
                color=ALERT, width=4), run_time=0.2)
            # smaller font + pulled inboard so it never clips the right edge
            err = Text(err_str, font_size=15, color=ALERT, weight=BOLD,
                       font="Cascadia Code")
            err.next_to(executor, UP, buff=0.5).shift(LEFT * 0.5)
            self.play(FadeIn(err, shift=DOWN * 0.1), run_time=0.4)
            beat(self, 0.4)
            # Executor recovers; the error itself travels down to the Analyzer
            self.play(executor.center_circle.animate.set_stroke(
                color=TEAL, width=3), run_time=0.2)
            bus.send(self, "E", "A", payload=err, color=ALERT)
            # MORPH: the error text literally becomes a typed constraint
            # (placed to the RIGHT of the Analyzer so it never covers its label)
            cons = Text(cons_body, font_size=18, color=PURPLE, weight=BOLD,
                        font="Cascadia Code")
            cons.next_to(analyzer, RIGHT, buff=0.5)
            self.play(TransformMatchingShapes(err, cons), run_time=0.8)
            emphasize(self, cons, color=PURPLE, scale=1.12)
            beat(self, 0.2)
            # C_{t+1} = C_t ∪ Analyze(ε_t) — pulse the rule as the store grows
            self.play(Indicate(update_rule, color=PURPLE, scale_factor=1.08),
                      run_time=0.4)
            ledger.push(self, cons_body, kind=kind,
                        enter_from=cons.get_center(), run_time=0.7)
            self.play(FadeOut(cons), run_time=0.15)
            beat(self, 0.9)
            # Critic reads the new constraint, tells the Planner to re-plan
            bus.send(self, "A", "C", color=PURPLE)
            note = Text(crit_note, font_size=14, color=PURPLE,
                        font="Segoe UI", slant=ITALIC)
            note.next_to(critic, UP, buff=0.5).shift(RIGHT * 0.3)
            self.play(FadeIn(note, shift=UP * 0.1),
                      Indicate(critic.center_circle, color=PURPLE,
                               scale_factor=1.12), run_time=0.45)
            bus.send(self, "C", "P", color=ACCENT_SOFT)
            self.play(FadeOut(note), run_time=0.2)
            beat(self, 0.2)

        def build_ok(plan_label):
            emit_plan(plan_label, ACCENT)
            self.play(executor.center_circle.animate.set_stroke(
                color=SUCCESS, width=4), run_time=0.3)
            ok = Text("✓ Build OK", font_size=22, color=SUCCESS, weight=BOLD,
                      font="Segoe UI")
            ok.next_to(executor, UP, buff=0.5)
            self.play(FadeIn(ok, shift=DOWN * 0.1), run_time=0.4)
            emphasize(self, ok, color=SUCCESS, scale=1.15)

        # ===== ITERATION 1: AttributeError → UPPER bound =====
        set_iter(1)
        beat(self, 0.6)
        emit_plan("plan: scipy 1.7", TEAL)
        fail_and_learn("AttributeError: imread", "scipy < 1.2", "UPPER",
                       "reject scipy 1.7")
        beat(self, 0.8)

        # ===== ITERATION 2: python mismatch → HARD pin =====
        set_iter(2)
        beat(self, 0.6)
        emit_plan("plan: scipy 1.1", ACCENT)
        fail_and_learn("py3.6 unsupported", "py == 3.7", "HARD",
                       "pin python 3.7")
        beat(self, 0.8)

        # ===== ITERATION 3: constraints satisfied → build succeeds =====
        set_iter(3)
        beat(self, 0.6)
        build_ok("plan: scipy 1.1 · py3.7")

        punch = Text("Error → Constraint.   Lặp lại, store lớn dần.",
                     font_size=22, color=ACCENT, weight=BOLD,
                     font="Segoe UI", slant=ITALIC)
        punch.to_edge(DOWN, buff=0.30)
        self.play(FadeIn(punch, shift=UP * 0.15), run_time=0.6)
        beat(self, 1.8)


# ============================================================
# 13. CSP FORMULATION ⭐ — math reveal + inset DFS tree
# ============================================================
class CSPFormulation(Scene):
    def construct(self):
        slide_chrome(self, "CGAR — Formulation as CSP", "CGAR")

        # Headline
        head = MathTex(
            r"\mathcal{P} = \langle\,", "X", ",\\ ", "D", ",\\ ", "C",
            r"\,\rangle",
            font_size=72, color=INK,
        )
        head[1].set_color(ACCENT)
        head[3].set_color(TEAL)
        head[5].set_color(PURPLE)
        head.shift(UP * 2.6)
        dramatic_write(self, head, run_time=1.2)
        beat(self, 0.4)

        # X
        x_eq = MathTex(
            r"X = \{\,P_1,\ P_2,\ \ldots,\ P_n,\ \pi\,\}",
            font_size=34, color=INK,
        )
        x_eq[0][0].set_color(ACCENT)
        x_lbl = Text("packages + Python version", font_size=18, color=DIM,
                      font="Segoe UI")
        x_grp = VGroup(x_eq, x_lbl).arrange(DOWN, buff=0.12, aligned_edge=LEFT)
        x_grp.move_to(LEFT * 3.5 + UP * 1.0)

        # X / D / C unfold as the narrator explains each ("X là các package…
        # D là miền version… C là ràng buộc học từ thất bại").
        focus_on(self, head[1])
        self.play(TransformFromCopy(head[1], x_eq[0][0]),
                   FadeIn(x_eq[0][1:], shift=RIGHT * 0.3),
                   FadeIn(x_lbl), run_time=0.9)
        beat(self, 1.4)

        # D — symbol-by-symbol mutation as we build
        d_eq = MathTex(
            r"D(P_i) = \{\, v \,\mid\, "
            r"\mathrm{req\_py}(v)\models\pi \,\land\, "
            r"\mathrm{wheel}(v)\,\}",
            font_size=26, color=INK,
        )
        d_eq[0][0].set_color(TEAL)
        d_lbl = Text("wheel-first, semver descending",
                      font_size=17, color=DIM, font="Segoe UI")
        d_grp = VGroup(d_eq, d_lbl).arrange(DOWN, buff=0.12,
                                              aligned_edge=LEFT)
        d_grp.move_to(LEFT * 3.5 + DOWN * 0.3)

        focus_on(self, head[3])
        self.play(TransformFromCopy(head[3], d_eq[0][0]),
                   FadeIn(d_eq[0][1:], shift=RIGHT * 0.3),
                   FadeIn(d_lbl), run_time=1.0)
        beat(self, 1.4)

        # C
        c_eq = MathTex(
            r"C = C_{\mathrm{hard}}\,\cup\,"
            r"C_{\mathrm{soft}}\,\cup\,C_{\mathrm{ub}}",
            font_size=32, color=INK,
        )
        c_eq[0][0].set_color(PURPLE)
        c_lbl = Text("constraints learned from failures",
                      font_size=17, color=DIM, font="Segoe UI")
        c_grp = VGroup(c_eq, c_lbl).arrange(DOWN, buff=0.12,
                                              aligned_edge=LEFT)
        c_grp.move_to(LEFT * 3.5 + DOWN * 1.7)

        focus_on(self, head[5])
        self.play(TransformFromCopy(head[5], c_eq[0][0]),
                   FadeIn(c_eq[0][1:], shift=RIGHT * 0.3),
                   FadeIn(c_lbl), run_time=0.9)
        beat(self, 1.2)

        # ---- INSET: backtracking tree on the right showing one prune ----
        tree = DFSTreeAnimator(
            "scipy ?", ["1.7", "1.5", "1.3", "1.1", "0.19"],
            node_width=0.95, node_height=0.55, row_buff=0.85,
        )
        all_t = tree.all().scale(0.7).move_to(RIGHT * 3.5 + UP * 0.2)
        self.play(FadeIn(all_t), run_time=0.6)
        # add upper-bound: prune first 3
        cut = DashedLine(RIGHT * 1.7 + UP * 0.0,
                          RIGHT * 5.3 + UP * 0.0,
                          color=ALERT, stroke_width=2.5,
                          dash_length=0.10).set_opacity(0.8)
        ub_t = Text("UB: scipy < 1.2", font_size=14, color=ALERT,
                     font="Cascadia Code", slant=ITALIC)
        ub_t.next_to(cut, UP, buff=0.05).align_to(cut, RIGHT)\
            .shift(LEFT * 0.5)
        self.play(Create(cut), FadeIn(ub_t), run_time=0.5)
        beat(self, 1.6)   # "Một upper bound cắt ngay nhánh không khả thi"
        self.play(tree.fail(0), tree.fail(1), tree.fail(2), run_time=0.8)
        self.play(tree.succeed(3), run_time=0.5)
        beat(self, 4.4)   # "cây tìm kiếm thu về một đường duy nhất"


# ============================================================
# 14. SESSION-SCOPED LEARNING
# ============================================================
class SessionLearning(Scene):
    def construct(self):
        slide_chrome(self, "Session-scoped Learning", "CGAR")

        # 3 snippet panels on the left → write into central ledger →
        # rescued counter ticks up
        def snippet_box(label):
            dot = Dot(radius=0.09, color=ACCENT_SOFT)
            t = Text(label, font_size=18, color=INK,
                     font="Cascadia Code")
            return VGroup(dot, t).arrange(RIGHT, buff=0.20,
                                            aligned_edge=DOWN)

        snips = VGroup(
            snippet_box("snippet #1 (scipy fail)"),
            snippet_box("snippet #2 (uses scipy)"),
            snippet_box("snippet #3 (uses scipy)"),
        ).arrange(DOWN, buff=0.30).move_to(LEFT * 4.2)

        ledger = ConstraintLedger("Constraint Store", width=3.2)
        ledger.scale(0.9).move_to(ORIGIN + RIGHT * 0.5)
        # 3D slab depth behind the store (isometric extrusion up-right)
        _fr = ledger.frame
        _ul, _ur, _dr = _fr.get_corner(UL), _fr.get_corner(UR), _fr.get_corner(DR)
        _dv = np.array([0.34, 0.30, 0.0])
        slab = VGroup(
            Polygon(_ur, _dr, _dr + _dv, _ur + _dv, fill_color=ACCENT,
                    fill_opacity=0.07, stroke_color=ACCENT, stroke_width=1,
                    stroke_opacity=0.35),
            Polygon(_ul, _ur, _ur + _dv, _ul + _dv, fill_color=ACCENT,
                    fill_opacity=0.11, stroke_color=ACCENT, stroke_width=1,
                    stroke_opacity=0.35),
        )
        ledger.add_to_back(slab)   # part of the store → moves/scales with it

        rescue_counter = DecimalNumber(0, num_decimal_places=0,
                                        font_size=56, color=SUCCESS,
                                        unit="")
        rescue_label = Text("snippets rescued", font_size=18, color=DIM,
                            font="Segoe UI", slant=ITALIC)
        rescue_grp = VGroup(rescue_counter, rescue_label).arrange(
            DOWN, buff=0.10)
        rescue_grp.move_to(RIGHT * 4.5)

        self.play(LaggedStart(*[FadeIn(s, shift=RIGHT * 0.2) for s in snips],
                              lag_ratio=0.15), run_time=0.8)
        self.play(FadeIn(ledger), FadeIn(rescue_grp), run_time=0.5)
        beat(self, 0.4)

        # snippet #1 fails → writes constraint
        arr1 = Arrow(snips[0].get_right(), ledger.get_left(),
                      color=ALERT, stroke_width=3, buff=0.1)
        self.play(GrowArrow(arr1), run_time=0.4)
        ledger.push(self, "scipy < 1.2", kind="UPPER", run_time=0.6)
        self.play(FadeOut(arr1), run_time=0.2)

        # snippet #2 reuses constraint → counter +1
        arr2 = Arrow(ledger.get_left(), snips[1].get_right(),
                      color=SUCCESS, stroke_width=3, buff=0.1)
        self.play(GrowArrow(arr2), run_time=0.4)
        self.play(snips[1][0].animate.set_color(SUCCESS),
                   rescue_counter.animate.set_value(1),
                   run_time=0.6)
        self.play(FadeOut(arr2), run_time=0.2)

        # snippet #3 reuses → counter +1 again
        arr3 = Arrow(ledger.get_left(), snips[2].get_right(),
                      color=SUCCESS, stroke_width=3, buff=0.1)
        self.play(GrowArrow(arr3), run_time=0.4)
        self.play(snips[2][0].animate.set_color(SUCCESS),
                   rescue_counter.animate.set_value(2),
                   run_time=0.6)
        self.play(FadeOut(arr3), run_time=0.2)

        # Clear the snippet column + small counter to free space
        self.play(
            FadeOut(snips, shift=LEFT * 0.3),
            FadeOut(rescue_grp, shift=RIGHT * 0.3),
            ledger.animate.scale(0.85).to_edge(LEFT, buff=1.0),
            run_time=0.6,
        )

        # Big headline: 71 + label, centered
        big_n = Text("71", font_size=150, color=SUCCESS, weight=BOLD,
                      font="Segoe UI")
        big_g = glow(big_n, color=SUCCESS, layers=8, opacity=0.06)
        big_grp = VGroup(big_g)
        big_lbl = Text("MEMRES failures rescued\nby shared constraints",
                        font_size=24, color=INK, font="Segoe UI",
                        line_spacing=0.6)
        big_stack = VGroup(big_grp, big_lbl).arrange(DOWN, buff=0.30)
        big_stack.move_to(RIGHT * 2.5 + UP * 0.6)
        self.play(FadeIn(big_stack, shift=UP * 0.2, scale=0.8), run_time=0.7)
        emphasize(self, big_n, color=SUCCESS, scale=1.12)

        # Math: rescue probability (bottom row, centered, clear of footer)
        rescue_eq = MathTex(
            r"\Pr[\text{rescue} \mid s_j] \;=\; "
            r"1 - \prod_{c \in C_{<j}} "
            r"\bigl(1 - \mathbb{1}[c \text{ applies to } s_j]\bigr)",
            font_size=24, color=INK,
        )
        rescue_eq[0][:18].set_color(SUCCESS)
        rescue_eq.to_edge(DOWN, buff=0.50)
        self.play(Write(rescue_eq), run_time=1.2)
        beat(self, 5.6)   # hold for narration


# ============================================================
# 15. PASS RATES — grouped bar chart, 5 tools × 2 datasets
# ============================================================
class PassRates(Scene):
    def construct(self):
        slide_chrome(self, "Pass rate — HG2.9K & GitChameleon", "Kết quả")

        tools = ["PyEGo", "ReadPyE", "PLLM", "SMT-LLM", "MEMRES", "CGAR"]
        hg    = [45.0, 47.2, 44.8, 83.6, 86.3, 87.1]
        gc    = [None, None, 65.5, None, 81.7, 83.2]

        bar_w = 0.40
        pair_gap = 0.08
        group_w = 2 * bar_w + pair_gap
        group_gap = 0.55
        n = len(tools)
        total_w = n * group_w + (n - 1) * group_gap
        x0 = -total_w / 2 + group_w / 2
        max_h = 2.4
        AXIS_Y = -2.55

        axis = Line([-6.0, AXIS_Y, 0], [6.0, AXIS_Y, 0],
                     color=DIM, stroke_width=1.4)
        self.add(axis)
        for pct in (25, 50, 75, 100):
            y = AXIS_Y + max_h * pct / 100
            self.add(DashedLine([-5.8, y, 0], [5.8, y, 0],
                                  color=GHOST, stroke_width=1,
                                  dash_length=0.10).set_opacity(0.35))
            tk = Text(f"{pct}%", font_size=14, color=DIM,
                       font="Segoe UI")
            tk.move_to([-6.35, y, 0])
            self.add(tk)

        sw_hg = Square(0.20, color=TEAL, fill_color=TEAL,
                        fill_opacity=1, stroke_width=0)
        t_hg = Text("HG2.9K (n=2 891)", font_size=18, color=INK,
                     font="Segoe UI").next_to(sw_hg, RIGHT, buff=0.15)
        sw_gc = Square(0.20, color=ACCENT, fill_color=ACCENT,
                        fill_opacity=1, stroke_width=0)
        t_gc = Text("GitChameleon (n=328)", font_size=18, color=INK,
                     font="Segoe UI").next_to(sw_gc, RIGHT, buff=0.15)
        legend = VGroup(VGroup(sw_hg, t_hg), VGroup(sw_gc, t_gc))\
            .arrange(RIGHT, buff=0.55, aligned_edge=DOWN)
        legend.move_to([0, 2.55, 0])
        self.add(legend)

        anims_per_group = []
        for i, name in enumerate(tools):
            cx = x0 + i * (group_w + group_gap)
            tool_lbl = Text(name, font_size=20, color=INK, weight=BOLD,
                             font="Segoe UI")
            tool_lbl.move_to([cx, AXIS_Y - 0.35, 0])
            self.add(tool_lbl)

            group_anims = []
            hx = cx - (bar_w + pair_gap) / 2
            h_h = max_h * (hg[i] / 100)
            bar_h = Rectangle(width=bar_w, height=0.001,
                               fill_color=TEAL, fill_opacity=1,
                               stroke_width=0)
            bar_h.move_to([hx, AXIS_Y, 0], aligned_edge=DOWN)
            self.add(bar_h)
            val_h = Text(f"{hg[i]:.1f}", font_size=13, color=TEAL,
                          weight=BOLD, font="Segoe UI")
            val_h.move_to([hx, AXIS_Y + h_h + 0.20, 0])
            group_anims.append((bar_h, h_h, val_h))

            gx = cx + (bar_w + pair_gap) / 2
            if gc[i] is not None:
                g_h = max_h * (gc[i] / 100)
                bar_g = Rectangle(width=bar_w, height=0.001,
                                   fill_color=ACCENT, fill_opacity=1,
                                   stroke_width=0)
                bar_g.move_to([gx, AXIS_Y, 0], aligned_edge=DOWN)
                self.add(bar_g)
                val_g = Text(f"{gc[i]:.1f}", font_size=13, color=ACCENT,
                              weight=BOLD, font="Segoe UI")
                val_g.move_to([gx, AXIS_Y + g_h + 0.20, 0])
                group_anims.append((bar_g, g_h, val_g))
            else:
                na = Text("n/a", font_size=14, color=DIM, slant=ITALIC,
                           font="Segoe UI")
                na.move_to([gx, AXIS_Y + 0.20, 0])
                self.add(na)

            anims_per_group.append(group_anims)

        for grp in anims_per_group:
            plays = []
            for bar, h, val in grp:
                plays.append(bar.animate.stretch_to_fit_height(
                    h, about_edge=DOWN))
                plays.append(FadeIn(val, shift=DOWN * 0.08))
            self.play(*plays, run_time=0.55,
                       rate_func=rate_functions.ease_out_cubic)

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
        beat(self, 8.0)   # hold for narration


# ============================================================
# 16. ERRORS ELIMINATED
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
        X_NAME = -6.7
        X_PLLM = -1.0
        X_ARROW = 0.0
        X_CGAR = 1.0
        X_WHY = 2.0
        y0 = 1.5
        dy = -0.95

        h_kw = dict(font_size=17, color=DIM, slant=ITALIC,
                     font="Segoe UI")
        hdr_name = Text("error", **h_kw)
        hdr_name.move_to([X_NAME + hdr_name.width / 2, y0 + 0.85, 0])
        hdr_pllm = Text("PLLM", **dict(h_kw, color=ALERT))
        hdr_pllm.move_to([X_PLLM, y0 + 0.85, 0])
        hdr_cgar = Text("CGAR", **dict(h_kw, color=SUCCESS))
        hdr_cgar.move_to([X_CGAR, y0 + 0.85, 0])
        hdr_mech = Text("mechanism", **h_kw)
        hdr_mech.move_to([X_WHY + hdr_mech.width / 2, y0 + 0.85, 0])
        underline = Line([X_NAME, y0 + 0.55, 0], [6.0, y0 + 0.55, 0],
                          color=GHOST, stroke_width=1).set_opacity(0.5)
        self.add(hdr_name, hdr_pllm, hdr_cgar, hdr_mech, underline)

        # Build all 4 rows at once, reveal in a single play()
        names, befores, arrows, afters, whys = [], [], [], [], []
        for i, (name, before, why) in enumerate(errs):
            y = y0 + i * dy
            n = Text(name, font_size=20, color=INK, weight=BOLD,
                      font="Cascadia Code")
            n.move_to([X_NAME + n.width / 2, y, 0])
            b = Text(str(before), font_size=28, color=ALERT, weight=BOLD,
                      font="Segoe UI")
            b.move_to([X_PLLM, y, 0])
            arr = Arrow([X_ARROW - 0.30, y, 0], [X_ARROW + 0.30, y, 0],
                         color=DIM, stroke_width=4, buff=0.05)
            a = Text("0", font_size=28, color=SUCCESS, weight=BOLD,
                      font="Segoe UI")
            a.move_to([X_CGAR, y, 0])
            w = Text(why, font_size=18, color=DIM, slant=ITALIC,
                      font="Segoe UI")
            w.move_to([X_WHY + w.width / 2, y, 0])
            names.append(n); befores.append(b); arrows.append(arr)
            afters.append(a); whys.append(w)

        # Step 1: names + PLLM red numbers all together
        self.play(*[FadeIn(n) for n in names],
                   *[FadeIn(b) for b in befores], run_time=0.6)
        beat(self, 0.4)
        # Step 2: arrows + zeros + mechanisms in one shot
        self.play(*[GrowArrow(a) for a in arrows],
                   *[FadeIn(z, scale=1.3) for z in afters],
                   *[FadeIn(w, shift=RIGHT * 0.15) for w in whys],
                   run_time=0.8)
        beat(self, 0.5)

        # total count-down 1596 → 373 — uniform font_size so baselines align
        FS = 30
        total = VGroup(
            Text("Total failures:", font_size=FS, color=DIM,
                  font="Segoe UI"),
            Text("1,596", font_size=FS, color=ALERT, weight=BOLD,
                  font="Segoe UI"),
            Text("→", font_size=FS, color=DIM, font="Segoe UI"),
            Text("373", font_size=FS, color=SUCCESS, weight=BOLD,
                  font="Segoe UI"),
            Text("(−76.6%)", font_size=FS, color=SUCCESS,
                  font="Segoe UI", slant=ITALIC),
        ).arrange(RIGHT, buff=0.35, aligned_edge=DOWN)
        total.to_edge(DOWN, buff=0.55)
        self.play(FadeIn(total, shift=UP * 0.1), run_time=0.6)
        emphasize(self, total[3], color=SUCCESS, scale=1.2)
        beat(self, 10.8)   # hold for narration


# ============================================================
# 17. OPEN VS CLOSED — GitChameleon comparison
# ============================================================
class OpenVsClosed(Scene):
    def construct(self):
        slide_chrome(self, "GitChameleon — Open vs Closed", "Kết quả")

        rows = [
            ("closed", "GPT-4o",       49.1),
            ("closed", "Gemini 2.5 Pro", 50.0),
            ("closed", "o1",           51.2),
            ("rag",    "GPT-4.1 + RAG", 58.5),
            ("open",   "PLLM (Gemma-2 9B)", 65.5),
            ("open",   "MEMRES",       81.7),
            ("ours",   "CGAR",         83.2),
        ]

        Y0 = 2.1
        DY = -0.55
        for i, (kind, name, val) in enumerate(rows):
            y = Y0 + i * DY
            if kind == "ours":
                color = ACCENT
                fs_name = 24
                fs_val = 28
            elif kind == "open":
                color = SUCCESS
                fs_name = 22
                fs_val = 24
            elif kind == "rag":
                color = ACCENT_SOFT
                fs_name = 21
                fs_val = 22
            else:
                color = ALERT
                fs_name = 21
                fs_val = 22

            name_t = Text(name, font_size=fs_name, color=INK,
                           weight=BOLD if kind == "ours" else NORMAL,
                           font="Segoe UI")
            name_t.move_to([-3.5 + name_t.width / 2, y, 0])

            badge = Text(kind.upper(), font_size=13, color=color,
                          weight=BOLD, font="Cascadia Code")
            badge_g = badge
            badge_g.move_to([-5.6 + badge_g.width / 2, y, 0])

            # bar
            bar_max = 4.0
            bar = Rectangle(width=bar_max * (val / 90), height=0.40,
                              fill_color=color, fill_opacity=0.8,
                              stroke_width=0)
            bar.move_to([1.0 + bar.width / 2, y, 0])

            val_t = Text(f"{val:.1f}%", font_size=fs_val, color=color,
                          weight=BOLD, font="Segoe UI")
            val_t.next_to(bar, RIGHT, buff=0.15)

            self.play(FadeIn(badge_g), FadeIn(name_t), run_time=0.18)
            self.play(GrowFromEdge(bar, LEFT), FadeIn(val_t), run_time=0.4)
            beat(self, 0.10)
            if kind == "ours":
                emphasize(self, val_t, color=ACCENT, scale=1.2)

        punch = Text("Open 9B đập closed enterprise — "
                      "+32.0 pp vs o1.",
                      font_size=22, color=ACCENT, weight=BOLD,
                      font="Segoe UI", slant=ITALIC)
        punch.to_edge(DOWN, buff=0.40)
        self.play(FadeIn(punch, shift=UP * 0.15), run_time=0.6)
        emphasize(self, punch, color=ACCENT, scale=1.08)
        beat(self, 6.8)   # hold for narration


# ============================================================
# 18. SPEED RACE + ABLATION (merged)
# ============================================================
class SpeedRaceAndAblation(Scene):
    def construct(self):
        slide_chrome(self, "Speed & Ablation", "Kết quả")

        # === TOP: speed race (3 bars) ===
        top_t = Text("Speed — GitChameleon, sec / snippet",
                      font_size=20, color=DIM, font="Segoe UI",
                      slant=ITALIC)
        top_t.move_to(UP * 2.7)
        self.play(FadeIn(top_t), run_time=0.3)

        bars_data = [
            ("PLLM",   67.0, DIM),
            ("MEMRES", 30.1, TEAL),
            ("CGAR",   17.8, ACCENT),
        ]
        X_LBL = -6.8
        X_BAR_L = -3.5
        BAR_MAX = 5.0
        Y_TOP = 1.8
        DY_R = -0.7

        for i, (name, val, color) in enumerate(bars_data):
            y = Y_TOP + i * DY_R
            lbl = Text(name, font_size=20, color=color, weight=BOLD,
                        font="Segoe UI")
            lbl.move_to([X_LBL + lbl.width / 2, y, 0])
            tgt_w = BAR_MAX * (val / 100)
            bar = Rectangle(width=0.001, height=0.40,
                             fill_color=color, fill_opacity=0.9,
                             stroke_width=0)
            bar.move_to([X_BAR_L, y, 0], aligned_edge=LEFT)
            counter = DecimalNumber(0, num_decimal_places=1,
                                     font_size=22, color=color, unit=" s")
            counter.next_to(bar.get_right(), RIGHT, buff=0.15)\
                    .set_y(bar.get_y())
            counter.add_updater(
                lambda m, b=bar: m.next_to(b.get_right(), RIGHT,
                                            buff=0.15).set_y(b.get_y())
            )
            self.play(FadeIn(lbl), run_time=0.18)
            self.add(counter)
            self.play(
                bar.animate.stretch_to_fit_width(tgt_w, about_edge=LEFT),
                counter.animate.set_value(val),
                run_time=0.7, rate_func=rate_functions.ease_out_cubic,
            )
            counter.clear_updaters()
            counter.next_to(bar.get_right(), RIGHT, buff=0.15)\
                    .set_y(bar.get_y())
            if name == "CGAR":
                emphasize(self, counter, color=ACCENT, scale=1.2)

        # === BOTTOM: ablation ===
        bot_t = Text("Ablation — rescue eval, n=494", font_size=20,
                      color=DIM, font="Segoe UI", slant=ITALIC)
        bot_t.move_to(DOWN * 0.4)
        self.play(FadeIn(bot_t), run_time=0.3)

        configs = [
            ("Full CGAR",       71, ACCENT,      "—"),
            ("− wheel filter",  40, ALERT,       "↓ 43.7%"),
            ("− upper bound",   23, ALERT,       "↓ 67.6%"),
            ("− session store", 56, ACCENT_SOFT, "↓ 21.1%"),
        ]
        Y_AB = -1.0
        DY_AB = -0.55
        BAR_MAX_AB = 4.2
        BASELINE = 71

        for i, (name, n, color, delta) in enumerate(configs):
            y = Y_AB + i * DY_AB
            lbl = Text(name, font_size=18, color=INK,
                        font="Cascadia Code")
            lbl.move_to([X_LBL + lbl.width / 2, y, 0])
            tgt_w = BAR_MAX_AB * (n / BASELINE)
            bar = Rectangle(width=0.001, height=0.32,
                             fill_color=color, fill_opacity=0.9,
                             stroke_width=0)
            bar.move_to([X_BAR_L, y, 0], aligned_edge=LEFT)
            n_t = Text(str(n), font_size=20, color=color, weight=BOLD,
                        font="Segoe UI")
            n_t.next_to(bar.get_right(), RIGHT, buff=0.15).set_y(y)
            d_t = Text(delta, font_size=15, color=color, slant=ITALIC,
                        font="Segoe UI")
            d_t.next_to(n_t, RIGHT, buff=0.20)

            self.play(FadeIn(lbl), run_time=0.15)
            self.play(
                bar.animate.stretch_to_fit_width(tgt_w, about_edge=LEFT),
                run_time=0.45, rate_func=rate_functions.ease_out_cubic,
            )
            n_t.next_to(bar.get_right(), RIGHT, buff=0.15).set_y(y)
            d_t.next_to(n_t, RIGHT, buff=0.20)
            self.play(FadeIn(n_t), FadeIn(d_t), run_time=0.25)
            beat(self, 0.10)

        # Math: speedup formula
        speedup = MathTex(
            r"S \;=\; \frac{T_{\mathrm{PLLM}}}{T_{\mathrm{CGAR}}}"
            r" \;\approx\; \frac{67.0}{17.8} \;\approx\; 3.8\times "
            r"\;\;(\text{GitCh median})\,, \quad 16.6\times\,(\text{HG2.9K avg})",
            font_size=22, color=INK,
        )
        speedup[0][:2].set_color(ACCENT)
        speedup.to_edge(DOWN, buff=0.30)
        self.play(Write(speedup), run_time=1.2)
        beat(self, 5.4)   # hold for narration


# ============================================================
# 19. HARD FLOOR — irreducible 10.7%
# ============================================================
class HardFloor(Scene):
    def construct(self):
        slide_chrome(self, "Hạn chế — Hard Floor (310 snippets, 10.7%)",
                      "Hạn chế")

        slices = [
            ("Python 2 syntax",         41.6, ALERT),
            ("system / private pkgs",   25.8, ACCENT),
            ("absent from PyPI",        13.3, PURPLE),
            ("native build / glibc",     8.1, TEAL),
            ("removed API, no fallback", 4.0, ACCENT_SOFT),
            ("other",                    7.2, DIM),
        ]

        # Pie on the LEFT, legend on the RIGHT — no in-place labels
        center = LEFT * 3.5 + DOWN * 0.2
        radius = 2.1
        wedges = VGroup()
        start = 90 * DEGREES
        for name, pct, color in slices:
            arc_ang = pct / 100 * TAU
            sector = AnnularSector(
                inner_radius=0.75, outer_radius=radius,
                angle=arc_ang, start_angle=start,
                color=color, fill_color=color, fill_opacity=0.85,
                stroke_color=BG, stroke_width=2,
            ).shift(center)
            wedges.add(sector)
            start -= arc_ang  # clockwise

        # Right-side legend
        legend_rows = VGroup()
        for name, pct, color in slices:
            sw = Square(side_length=0.26, color=color, fill_color=color,
                         fill_opacity=0.95, stroke_width=0)
            pct_t = Text(f"{pct:>4.1f}%", font_size=18, color=color,
                          weight=BOLD, font="Cascadia Code")
            name_t = Text(name, font_size=17, color=INK,
                           font="Segoe UI")
            row = VGroup(sw, pct_t, name_t).arrange(RIGHT, buff=0.20,
                                                      aligned_edge=DOWN)
            legend_rows.add(row)
        legend_rows.arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        legend_rows.move_to(RIGHT * 2.6 + DOWN * 0.1)

        # Animate wedges + legend rows together by slice
        for w, r in zip(wedges, legend_rows):
            self.play(GrowFromCenter(w), FadeIn(r, shift=LEFT * 0.15),
                       run_time=0.40)

        # Center number — inside the inner hole, no overlap with wedges
        center_n = Text("10.7%", font_size=42, color=INK, weight=BOLD,
                         font="Segoe UI").move_to(center + UP * 0.08)
        center_l = Text("irreducible", font_size=13, color=DIM,
                         font="Segoe UI", slant=ITALIC)
        center_l.next_to(center_n, DOWN, buff=0.06)
        self.play(FadeIn(center_n, scale=0.6), FadeIn(center_l), run_time=0.5)
        emphasize(self, center_n, color=INK, scale=1.12)
        beat(self, 8.4)   # hold for narration


# ============================================================
# 20. ARCHITECTURAL LIMITS
# ============================================================
class ArchLimits(Scene):
    def construct(self):
        slide_chrome(self, "Architectural Limits", "Hạn chế")

        items = [
            ("PyPI live dependency",
             "method requires live PyPI metadata; offline = blind",
             ACCENT),
            ("Python-only ecosystem",
             "no support for npm / cargo / go.mod yet",
             TEAL),
            ("Analyzer brittle on weird logs",
             "LLM may mis-parse non-pip / non-Python error formats",
             PURPLE),
            ("Single-worker store",
             "no cross-user / federated learning of constraints",
             ACCENT_SOFT),
        ]

        def lim_block(idx, ttl, sub, color):
            num = Text(idx, font_size=44, color=color, weight=BOLD,
                        font="Segoe UI")
            t = Text(ttl, font_size=22, color=color, weight=BOLD,
                      font="Segoe UI")
            s = Text(sub, font_size=14, color=INK, font="Segoe UI")
            head = VGroup(num, t).arrange(RIGHT, buff=0.30,
                                           aligned_edge=DOWN)
            rule = Line(ORIGIN, RIGHT * 4.8, color=color,
                         stroke_width=2, stroke_opacity=0.7)
            rule.next_to(head, DOWN, buff=0.10, aligned_edge=LEFT)
            s.next_to(rule, DOWN, buff=0.18, aligned_edge=LEFT)
            return VGroup(num, t, rule, s)

        blocks = VGroup(*[lim_block(f"0{i+1}", *items[i])
                            for i in range(4)])
        blocks.arrange_in_grid(rows=2, cols=2,
                                buff=(0.85, 0.65),
                                col_alignments="ll",
                                row_alignments="cc")
        blocks.move_to(DOWN * 0.1)

        for b in blocks:
            self.play(FadeIn(b, shift=UP * 0.15), run_time=0.45,
                       rate_func=rate_functions.ease_out_cubic)
            beat(self, 0.10)
        beat(self, 9.2)   # hold for narration


# ============================================================
# 21. FUTURE WORK
# ============================================================
class FutureWork(Scene):
    def construct(self):
        slide_chrome(self, "Hướng phát triển", "Hạn chế")

        cards_data = [
            ("01", "Multi-language",
             "extend to npm, cargo, go.mod", ACCENT),
            ("02", "Federated Store",
             "privacy-preserving cross-user constraints", TEAL),
            ("03", "Fine-tune Analyzer",
             "domain-specific LLM for error parsing", PURPLE),
            ("04", "Online learning",
             "self-evolving error KB across sessions", SUCCESS),
        ]

        def fut_block(num, ttl, sub, color):
            n = Text(num, font_size=80, color=color, weight=BOLD,
                      font="Segoe UI")
            rule = Line(ORIGIN, RIGHT * 1.7, color=color,
                         stroke_width=2.5, stroke_opacity=0.85)
            t = Text(ttl, font_size=20, color=INK, weight=BOLD,
                      font="Segoe UI")
            s = Text(sub, font_size=12, color=DIM, font="Segoe UI",
                      slant=ITALIC)
            return VGroup(n, rule, t, s).arrange(DOWN, buff=0.15)

        blocks = VGroup(*[fut_block(*d) for d in cards_data])\
            .arrange(RIGHT, buff=0.85).move_to(DOWN * 0.1)

        for b in blocks:
            self.play(FadeIn(b, shift=UP * 0.2), run_time=0.5,
                       rate_func=rate_functions.ease_out_cubic)
            beat(self, 0.10)
        beat(self, 6.4)   # hold for narration


# ============================================================
# 22. SUMMARY — headline numbers + contributions
# ============================================================
class Summary(Scene):
    def construct(self):
        slide_chrome(self, "Tóm tắt & Kết luận", "Kết luận")

        # Left: contributions (use ASCII brackets — DejaVu lacks ⟨⟩ glyph)
        contrib_t = Text("Đóng góp", font_size=24, color=ACCENT, weight=BOLD,
                          font="Segoe UI")
        contribs = bullet_list([
            "Multi-Agent: Planner / Executor / Analyzer / Critic",
            "CSP formulation <X, D, C> + 3-tier constraints",
            "Error → Rule paradigm (session-scoped learning)",
            "Open-weight 9B beats closed enterprise models",
        ], font_size=18)
        left = VGroup(contrib_t, contribs).arrange(DOWN, aligned_edge=LEFT,
                                                    buff=0.30)
        left.move_to(LEFT * 3.5 + UP * 0.2)

        # Right: 4 headline numbers — 2x2 grid with FIXED cell anchors
        right_t = Text("Highlights", font_size=24, color=ACCENT, weight=BOLD,
                        font="Segoe UI")
        right_t.move_to(RIGHT * 3.5 + UP * 2.6)

        def big_stat(value, suffix, label, color, anchor):
            v = DecimalNumber(0, num_decimal_places=1, font_size=42,
                               color=color, unit=suffix)
            v.move_to(anchor)
            l = Text(label, font_size=13, color=DIM, font="Segoe UI",
                     slant=ITALIC)
            l.next_to(v, DOWN, buff=0.18)
            grp = VGroup(v, l)
            grp.target_value = value
            grp.value_mob = v
            return grp

        # Fixed positions so big numbers can't drift into each other
        s1 = big_stat(87.1, "\\%", "HG2.9K", ACCENT,
                       RIGHT * 2.3 + UP * 1.4)
        s2 = big_stat(83.2, "\\%", "GitChameleon", TEAL,
                       RIGHT * 4.7 + UP * 1.4)
        s3 = big_stat(32.0, " pp", "vs o1 (closed)", SUCCESS,
                       RIGHT * 2.3 + DOWN * 0.5)
        s4 = big_stat(17.6, r"\!\times", "vs MEMRES (pass-only)", PURPLE,
                       RIGHT * 4.8 + DOWN * 0.5)
        stats = VGroup(s1, s2, s3, s4)

        self.play(FadeIn(left, shift=RIGHT * 0.2), run_time=0.6)
        beat(self, 0.4)
        self.play(FadeIn(right_t), run_time=0.3)
        self.play(LaggedStart(*[FadeIn(s, shift=UP * 0.2, scale=0.9)
                                 for s in stats],
                               lag_ratio=0.15), run_time=0.6)
        self.play(*[s.value_mob.animate.set_value(s.target_value)
                     for s in stats],
                   run_time=1.4, rate_func=rate_functions.ease_out_cubic)
        beat(self, 0.6)

        # Closing thesis — placed safely above the player chrome zone
        thesis = MathTex(
            r"\mathrm{CGAR} \;=\; "
            r"\mathrm{Multi\text{-}Agent} \;+\; "
            r"\mathrm{CSP}\langle X,D,C\rangle \;+\; "
            r"\mathrm{Session\;Store}",
            font_size=24, color=INK,
        )
        thesis[0][:4].set_color(ACCENT)
        thesis.to_edge(DOWN, buff=0.85)
        self.play(Write(thesis), run_time=1.4)
        beat(self, 6.8)   # hold for narration


# ============================================================
# 23. THANK YOU
# ============================================================
class ThankYou(Scene):
    def construct(self):
        backdrop(self)
        stars = starfield(n=70)
        self.add(stars)
        self.play(LaggedStart(*[FadeIn(s) for s in stars],
                               lag_ratio=0.01), run_time=1.0)

        tk = Text("Thank you", font_size=110, **TITLE_KW)
        tk_glow = glow(tk, color=ACCENT, layers=10, opacity=0.04)
        sub = Text("Questions & Discussion", font_size=32, color=ACCENT,
                    slant=ITALIC, font="Segoe UI")
        underline = Rectangle(width=tk.width * 0.55, height=0.08,
                               stroke_width=0)
        underline.set_fill(color=[TEAL, ACCENT_SOFT, ACCENT], opacity=1)

        tag1 = Text("MEMRES & CGAR", font_size=22, color=INK, weight=BOLD,
                     font="Segoe UI")
        tag2 = Text("Agentic Python Dependency Resolution",
                     font_size=18, color=DIM, slant=ITALIC,
                     font="Segoe UI")
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
