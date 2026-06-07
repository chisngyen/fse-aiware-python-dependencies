"""Shared style + helpers — 3blue1brown-flavored cinematic palette.

Dark navy backdrop, glow, depth via shading, smooth narrative pacing.
"""
from __future__ import annotations
from manim import *
import numpy as np

# ---- Palette (cinematic — dark backdrop like 3b1b) ----
BG          = "#0E1518"   # near-black (spec) — 3blue1brown style, colors pop
PANEL       = "#162226"   # card surface
NAVY        = "#23373B"
ACCENT      = "#EB811B"   # mLightBrown, signature warm
ACCENT_SOFT = "#F4A75A"
TEAL        = "#4FB3BF"
PURPLE      = "#9B7EDE"
SUCCESS     = "#5CD68A"
ALERT       = "#FF6B6B"
INK         = "#ECEFF1"
DIM         = "#8A9AA5"
GHOST       = "#3A4750"

config.background_color = BG


# ============================================================
# Backdrop — 3b1b depth: deep base + soft center-lift vignette
# ============================================================
def backdrop(scene: Scene) -> VGroup:
    """Near-black (#0E1518) 3blue1brown backdrop. (No vignette — colors pop
    on the solid dark base.) slide_chrome() calls this; scenes without chrome
    call it first."""
    scene.camera.background_color = BG
    return VGroup()


# ---- Typography ----
TITLE_KW = dict(font="Segoe UI", weight=BOLD, color=INK)
BODY_KW  = dict(font="Segoe UI", color=INK)
MONO_KW  = dict(font="Cascadia Code", color=INK)


# ============================================================
# Chrome — persistent slide title chip with accent bar
# ============================================================
def slide_chrome(scene: Scene, title: str, section: str | None = None,
                 fixed_in_frame: bool = False):
    backdrop(scene)
    title_t = Text(title, font_size=28, **TITLE_KW).to_corner(UL, buff=0.45)
    accent_bar = Rectangle(
        width=0.10, height=title_t.height + 0.12,
        fill_color=ACCENT, fill_opacity=1, stroke_width=0,
    ).next_to(title_t, LEFT, buff=0.18)
    chrome = VGroup(accent_bar, title_t)

    if section:
        section_t = Text(section, font_size=16, color=DIM, font="Segoe UI")
        section_t.to_corner(UR, buff=0.45)
        chrome.add(section_t)

    if fixed_in_frame and hasattr(scene, "add_fixed_in_frame_mobjects"):
        scene.add_fixed_in_frame_mobjects(*chrome)
    else:
        scene.add(chrome)
    return chrome


# ============================================================
# Glow — soft halo around mobject (fakes bloom)
# ============================================================
def glow(mobject: Mobject, color=ACCENT, layers: int = 10,
         radius: float = 0.35, opacity: float = 0.08) -> VGroup:
    out = VGroup()
    for i in range(layers):
        t = (i + 1) / layers
        copy = mobject.copy()
        copy.set_stroke(color=color, width=2 + 14 * t, opacity=opacity * (1 - t))
        if hasattr(copy, "set_fill"):
            copy.set_fill(color=color, opacity=0)
        out.add(copy)
    out.add(mobject)
    return out


# ============================================================
# Bullets + cards (dark theme)
# ============================================================
def bullet_list(items: list[str], font_size: int = 26, dot_color=ACCENT) -> VGroup:
    rows = VGroup()
    for s in items:
        dot = Text("▸", font_size=font_size - 6, color=dot_color, weight=BOLD)
        txt = Text(s, font_size=font_size, **BODY_KW)
        row = VGroup(dot, txt).arrange(RIGHT, buff=0.25, aligned_edge=DOWN)
        rows.add(row)
    rows.arrange(DOWN, aligned_edge=LEFT, buff=0.32)
    return rows


def reveal_bullets(scene: Scene, bullets: VGroup, lag: float = 0.5):
    for row in bullets:
        scene.play(FadeIn(row, shift=0.3 * RIGHT), run_time=0.45)
        scene.wait(lag)


def card(content: Mobject, fill=PANEL, stroke=GHOST,
         pad: float = 0.4, radius: float = 0.18,
         stroke_opacity: float = 0.7) -> VGroup:
    bg = RoundedRectangle(
        corner_radius=radius,
        width=content.width + 2 * pad,
        height=content.height + 2 * pad,
        fill_color=fill, fill_opacity=1,
        stroke_color=stroke, stroke_width=1.5,
        stroke_opacity=stroke_opacity,
    ).move_to(content)
    return VGroup(bg, content)


def kbd(s: str, font_size: int = 20) -> VGroup:
    t = Text(s, font_size=font_size, font="Cascadia Code", color=ACCENT_SOFT)
    bg = RoundedRectangle(
        corner_radius=0.08,
        width=t.width + 0.22, height=t.height + 0.14,
        fill_color=NAVY, fill_opacity=1,
        stroke_color=ACCENT, stroke_width=1, stroke_opacity=0.5,
    ).move_to(t)
    return VGroup(bg, t)


# ============================================================
# Narrative beats — 3b1b-style pacing helpers
# ============================================================
def beat(scene: Scene, t: float = 0.8):
    """A breath between revelations. Use liberally — silence sells the story."""
    scene.wait(t)


def emphasize(scene: Scene, mobject: Mobject, color=ACCENT,
              scale: float = 1.12, run_time: float = 0.6):
    scene.play(Indicate(mobject, color=color, scale_factor=scale),
               run_time=run_time)


def focus_on(scene: Scene, target: Mobject, color=ACCENT, run_time: float = 0.6):
    scene.play(FocusOn(target, color=color), run_time=run_time)


def dramatic_write(scene: Scene, mobject: Mobject, run_time: float = 1.6):
    scene.play(Write(mobject, run_time=run_time, rate_func=smooth))


def cross_fade(scene: Scene, old: Mobject, new: Mobject, run_time: float = 0.8):
    scene.play(FadeOut(old, shift=UP * 0.2),
               FadeIn(new, shift=DOWN * 0.2),
               run_time=run_time)


# ============================================================
# Depth — 3D-feeling 2D rects (gradient + drop shadow)
# ============================================================
def deep_box(width: float, height: float,
             top=ACCENT, bot=NAVY, shadow: bool = True) -> VGroup:
    """A rect with a gradient fill and a soft drop shadow — fakes depth."""
    box = RoundedRectangle(
        corner_radius=0.15, width=width, height=height,
        stroke_color=INK, stroke_width=1.2, stroke_opacity=0.4,
    )
    box.set_fill(color=[top, bot], opacity=1)
    if not shadow:
        return VGroup(box)
    shadow_box = box.copy()
    shadow_box.set_fill(color=BLACK, opacity=0.45)
    shadow_box.set_stroke(opacity=0)
    shadow_box.shift(DOWN * 0.10 + RIGHT * 0.06)
    shadow_box.scale(1.02)
    return VGroup(shadow_box, box)


# ============================================================
# Particle pool — random ambient stars / dust
# ============================================================
def starfield(n: int = 60, color=INK, opacity_range=(0.1, 0.35),
              size_range=(0.012, 0.04), seed: int = 42) -> VGroup:
    rng = np.random.default_rng(seed)
    stars = VGroup()
    for _ in range(n):
        x = rng.uniform(-7.2, 7.2)
        y = rng.uniform(-4.0, 4.0)
        r = rng.uniform(*size_range)
        o = rng.uniform(*opacity_range)
        d = Dot(point=[x, y, 0], radius=r, color=color)
        d.set_opacity(o)
        stars.add(d)
    return stars


def twinkle(scene: Scene, stars: VGroup, duration: float = 2.0):
    """Subtle opacity wobble on each star — adds life."""
    anims = []
    for s in stars:
        anims.append(s.animate.set_opacity(s.get_fill_opacity() * 0.4))
    scene.play(*anims, rate_func=there_and_back, run_time=duration)


# ============================================================
# Math + code helpers (3B1B-style reveals)
# ============================================================
def math_block(tex: str, font_size: int = 36, color=INK,
               glow_color=None) -> VGroup:
    """`MathTex` with optional halo for centerpiece equations."""
    m = MathTex(tex, font_size=font_size, color=color)
    if glow_color is None:
        return VGroup(m)
    return glow(m, color=glow_color, layers=6, opacity=0.06)


def code_panel(code: str, language: str = "python",
               font_size: int = 22, width: float | None = None,
               stroke=GHOST, stroke_opacity: float = 0.5,
               formatter_style: str = "monokai") -> VGroup:
    """Code mobject wrapped in a card with consistent padding.

    `formatter_style` picks a Pygments theme; default `monokai` keeps comments
    a readable light gray on the dark panel (the stock theme's comments were
    too dark to read)."""
    c = Code(
        code_string=code, language=language, background="rectangle",
        formatter_style=formatter_style,
        paragraph_config={"font_size": font_size, "font": "Cascadia Code",
                          "line_spacing": 0.55},
    )
    if width is not None:
        c.scale_to_fit_width(width)
    return card(c, pad=0.30, stroke=stroke, stroke_opacity=stroke_opacity)


def flow_arrow(start, end, color=ACCENT, stroke_width: float = 4,
               label: str | None = None, label_color=DIM):
    """Arrow with optional label, used in pipeline + agent diagrams."""
    a = Arrow(start, end, color=color, stroke_width=stroke_width, buff=0.08,
              max_tip_length_to_length_ratio=0.16)
    if label is None:
        return a
    t = Text(label, font_size=16, color=label_color,
             font="Segoe UI", slant=ITALIC)
    t.move_to(a.get_center() + UP * 0.25)
    return VGroup(a, t)


def count_up(scene: Scene, decimal: "DecimalNumber", target: float,
             duration: float = 1.5, rate=None):
    """Animate a DecimalNumber from its current value up to target."""
    if rate is None:
        rate = rate_functions.ease_out_cubic
    scene.play(decimal.animate.set_value(target),
               run_time=duration, rate_func=rate)


def chip(text: str, color=ACCENT, font_size: int = 18,
         fill=NAVY, stroke_opacity: float = 0.7) -> VGroup:
    """Bare label: small colored dot + text, no rounded-rect pill.

    Designed to look 3blue1brown-style: minimal furniture, color does the work.
    The `fill`/`stroke_opacity` kwargs are accepted but ignored for back-compat.
    """
    dot = Dot(radius=0.08, color=color)
    t = Text(text, font_size=font_size, color=color, weight=BOLD,
             font="Cascadia Code")
    return VGroup(dot, t).arrange(RIGHT, buff=0.18, aligned_edge=DOWN)
