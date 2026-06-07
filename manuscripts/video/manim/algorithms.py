"""Reusable algorithm-animation mobjects.

These keep the 3B1B-style centerpiece scenes (CSP, Multi-Agent Loop, etc.)
small and let the morph/algorithm logic be testable per-mobject.
"""
from __future__ import annotations
from manim import *
import numpy as np

from style import (
    BG, PANEL, NAVY, ACCENT, ACCENT_SOFT, TEAL, PURPLE,
    SUCCESS, ALERT, INK, DIM, GHOST, kbd, glow,
)


# ============================================================
# Isometric faked-3D toolkit (no real 3D camera — CLAUDE.md rule)
# ============================================================
def iso_pt(center, x, y, z, sx=1.05, sy=1.05, sz=0.85):
    """Project lattice (x=right, y=up, z=depth-diagonal) to a 2D screen point."""
    return center + np.array([sx * x + sz * z * 0.55,
                              sy * y + sz * z * 0.45, 0.0])


def iso_box(center, w=1.0, h=1.0, d=1.0, color=ACCENT, scale=1.0,
            stroke=INK, top_op=0.55, front_op=0.38, side_op=0.22,
            edge_op=0.65, edge_w=1.5):
    """Faked-3D isometric cuboid: 3 shaded faces (top brightest) + visible
    edges, as a VGroup. w=width(x,right), h=height(y,up), d=depth(z,up-right).
    Origin corner sits at `center`."""
    s = scale

    def P(x, y, z):
        return iso_pt(center, x * s, y * s, z * s)

    c000, c100 = P(0, 0, 0), P(w, 0, 0)
    c010, c110 = P(0, h, 0), P(w, h, 0)
    c001, c101 = P(0, 0, d), P(w, 0, d)
    c011, c111 = P(0, h, d), P(w, h, d)
    side = Polygon(c100, c101, c111, c110, fill_color=color,
                   fill_opacity=side_op, stroke_width=0)
    front = Polygon(c000, c100, c110, c010, fill_color=color,
                    fill_opacity=front_op, stroke_width=0)
    top = Polygon(c010, c110, c111, c011, fill_color=color,
                  fill_opacity=top_op, stroke_width=0)
    edges = VGroup(
        Line(c000, c100), Line(c100, c110), Line(c110, c010), Line(c010, c000),
        Line(c010, c011), Line(c011, c111), Line(c111, c110),
        Line(c100, c101), Line(c101, c111),
    ).set_stroke(color=stroke, width=edge_w, opacity=edge_op)
    return VGroup(side, front, top, edges)


# ============================================================
# DFSTreeAnimator — backtracking tree with constraint pruning
# ============================================================
class DFSTreeAnimator:
    """A 2D tree of `RoundedRectangle` nodes you can incrementally animate.

    Build once with `(root_label, children_labels)`, then play `.visit(i)`,
    `.fail(i)`, `.succeed(i)`, `.add_constraint_cut(x_threshold, ...)`,
    `.expand(parent_idx, [labels])` — each returns an Animation/group.
    """

    def __init__(self, root_label: str, children_labels: list[str],
                 root_color=ACCENT, child_color=NAVY,
                 node_width: float = 1.45, node_height: float = 0.7,
                 row_buff: float = 1.3):
        self.root = self._node(root_label, root_color, node_width, node_height)
        self.children = VGroup(*[
            self._node(c, child_color, node_width, node_height)
            for c in children_labels
        ]).arrange(RIGHT, buff=0.45).next_to(self.root, DOWN, buff=row_buff)
        # center horizontally under root
        self.children.set_x(self.root.get_x())
        self.edges = VGroup(*[
            Line(self.root.get_bottom() + DOWN * 0.02,
                 c.get_top() + UP * 0.02,
                 color=GHOST, stroke_width=2)
            for c in self.children
        ])
        self.crosses = {}            # idx -> VGroup(X1, X2)
        self.row_buff = row_buff
        self.node_width = node_width
        self.node_height = node_height
        self._subtree = None         # set by .expand()

    def _node(self, label, color, w, h):
        t = Text(label, font_size=18, color=INK, font="Cascadia Code")
        bg = RoundedRectangle(
            width=max(t.width + 0.3, w), height=h, corner_radius=0.12,
            fill_color=PANEL, fill_opacity=1,
            stroke_color=color, stroke_width=2.5,
        ).move_to(t)
        return VGroup(bg, t)

    def all(self) -> VGroup:
        return VGroup(self.root, self.edges, self.children)

    def visit(self, idx: int) -> AnimationGroup:
        n = self.children[idx]
        return AnimationGroup(
            Indicate(n, color=ACCENT, scale_factor=1.12),
            n[0].animate.set_stroke(color=ACCENT, width=3.5),
        )

    def fail(self, idx: int) -> AnimationGroup:
        n = self.children[idx]
        box = n[0]
        x1 = Line(box.get_corner(UL), box.get_corner(DR),
                  color=ALERT, stroke_width=4)
        x2 = Line(box.get_corner(UR), box.get_corner(DL),
                  color=ALERT, stroke_width=4)
        cross = VGroup(x1, x2)
        self.crosses[idx] = cross
        return AnimationGroup(
            Create(cross),
            n.animate.set_opacity(0.35),
            self.edges[idx].animate.set_opacity(0.25),
        )

    def succeed(self, idx: int) -> AnimationGroup:
        n = self.children[idx]
        return AnimationGroup(
            n[0].animate.set_stroke(color=SUCCESS, width=4.5),
            self.edges[idx].animate.set_color(SUCCESS).set_stroke(width=3.5),
            Indicate(n, color=SUCCESS, scale_factor=1.15),
        )

    def expand(self, parent_idx: int, labels: list[str],
               color=SUCCESS) -> AnimationGroup:
        parent = self.children[parent_idx]
        sub = VGroup(*[
            self._node(l, color, self.node_width, self.node_height)
            for l in labels
        ]).arrange(RIGHT, buff=0.5).next_to(parent, DOWN, buff=self.row_buff)
        sub.set_x(parent.get_x())
        sub_edges = VGroup(*[
            Line(parent.get_bottom() + DOWN * 0.02,
                 n.get_top() + UP * 0.02,
                 color=color, stroke_width=2.2)
            for n in sub
        ])
        self._subtree = VGroup(sub_edges, sub)
        return AnimationGroup(
            LaggedStart(*[Create(e) for e in sub_edges], lag_ratio=0.18),
            LaggedStart(*[FadeIn(n, shift=DOWN * 0.25) for n in sub],
                        lag_ratio=0.18),
            lag_ratio=0.05,
        )

    def subtree(self) -> VGroup | None:
        return self._subtree


# ============================================================
# ConstraintLedger — Session Store visualization
# ============================================================
class ConstraintLedger(VGroup):
    """A vertical card list. Each `add(text, kind)` appends a typed card.

    kinds: 'HARD' (ALERT), 'SOFT' (ACCENT_SOFT), 'UPPER' (PURPLE).
    """
    KIND_COLOR = {"HARD": ALERT, "SOFT": ACCENT_SOFT, "UPPER": PURPLE}

    def __init__(self, title: str = "Session Store", width: float = 3.3,
                 max_visible: int = 4, height: float = 3.4):
        super().__init__()
        self.width_ = width
        self.max_visible = max_visible
        self.cards = VGroup()

        # frame
        self.title_t = Text(title, font_size=18, color=ACCENT, weight=BOLD,
                            font="Segoe UI")
        self.frame = RoundedRectangle(
            corner_radius=0.18, width=width, height=height,
            fill_color=PANEL, fill_opacity=0.92,
            stroke_color=ACCENT, stroke_width=1.6, stroke_opacity=0.7,
        )
        self.title_t.move_to(self.frame.get_top() + DOWN * 0.30)
        rule = Line(LEFT, RIGHT, color=ACCENT,
                    stroke_width=1.5, stroke_opacity=0.6)
        rule.set_width(width - 0.5)
        rule.next_to(self.title_t, DOWN, buff=0.10)
        self.rule = rule
        self.empty_t = Text("(empty)", font_size=14, color=DIM,
                            font="Segoe UI", slant=ITALIC)
        self.empty_t.next_to(rule, DOWN, buff=0.30)

        self.add(self.frame, self.title_t, self.rule, self.empty_t,
                 self.cards)

    def make_card(self, text: str, kind: str,
                   font_kind: int = 10, font_body: int = 13) -> VGroup:
        color = self.KIND_COLOR.get(kind, ACCENT)
        stripe = Rectangle(width=0.08, height=0.36,
                           fill_color=color, fill_opacity=1, stroke_width=0)
        kind_t = Text(kind, font_size=font_kind, color=color, weight=BOLD,
                      font="Cascadia Code")
        body_t = Text(text, font_size=font_body, color=INK,
                       font="Cascadia Code")
        inner = VGroup(kind_t, body_t).arrange(DOWN, aligned_edge=LEFT,
                                                buff=0.03)
        row = VGroup(stripe, inner).arrange(RIGHT, buff=0.10,
                                              aligned_edge=UP)
        # bg snugly fits content + small pad — so it looks centered in the
        # parent frame, not stretched with weird left/right whitespace.
        bg = RoundedRectangle(
            corner_radius=0.06,
            width=row.width + 0.30, height=row.height + 0.14,
            fill_color=NAVY, fill_opacity=0.92,
            stroke_color=color, stroke_width=1.0, stroke_opacity=0.55,
        ).move_to(row)
        return VGroup(bg, row)

    def push(self, scene: Scene, text: str, kind: str = "SOFT",
             enter_from=None, run_time: float = 0.6):
        """Animate a new card sliding in. Returns the card mobject."""
        card_m = self.make_card(text, kind)
        n = len(self.cards)
        # Explicit absolute positioning inside the frame (next_to was unreliable
        # after .move_to() on the parent VGroup).
        head_offset = 0.85     # space reserved for title + rule + buff
        gap = 0.14             # vertical gap between cards
        card_h = card_m.height
        frame_top_y = self.frame.get_top()[1]
        frame_x = self.frame.get_x()
        # First card's CENTER y:
        first_center_y = frame_top_y - head_offset - card_h / 2
        target_y = first_center_y - n * (card_h + gap)
        card_m.move_to([frame_x, target_y, 0])
        if n == 0:
            scene.play(FadeOut(self.empty_t), run_time=0.15)
            self.remove(self.empty_t)
        self.cards.add(card_m)

        # Simpler & reliable: always FadeIn at the computed target.
        # (Previous enter_from + Restore was repositioning incorrectly
        # due to interaction with the parent VGroup's move_to.)
        if enter_from is not None:
            # Animate a temporary copy flying in from enter_from,
            # then settle at target — keeps the morph metaphor without
            # corrupting the final position.
            start_pos = enter_from if isinstance(enter_from, np.ndarray) \
                else enter_from.get_center()
            ghost = card_m.copy().set_opacity(0.8)
            ghost.move_to(start_pos)
            scene.play(ghost.animate.move_to(card_m.get_center())
                                     .set_opacity(0.0),
                        FadeIn(card_m, shift=DOWN * 0.1),
                        run_time=run_time, rate_func=smooth)
            scene.remove(ghost)
        else:
            scene.play(FadeIn(card_m, shift=DOWN * 0.15),
                        run_time=run_time)
        # quick halo on the frame
        scene.play(Indicate(self.frame, color=ACCENT, scale_factor=1.02),
                    run_time=0.3)
        return card_m


# ============================================================
# AgentCard + AgentBus — multi-agent flow
# ============================================================
def AgentCard(name: str, role: str, tools: list[str], color=ACCENT,
              width: float = 2.6) -> VGroup:
    """Agent rounded-rect with name, role, tool chips."""
    head = Text(name, font_size=20, color=INK, weight=BOLD,
                font="Segoe UI")
    head_bar = RoundedRectangle(
        corner_radius=0.06, width=width - 0.2, height=0.48,
        fill_color=color, fill_opacity=0.25,
        stroke_color=color, stroke_width=1.6, stroke_opacity=0.8,
    )
    head.move_to(head_bar)
    role_t = Text(role, font_size=12, color=DIM, font="Segoe UI",
                  slant=ITALIC)
    chips = VGroup(*[kbd(t, font_size=13) for t in tools])
    chips.arrange(DOWN, aligned_edge=LEFT, buff=0.08)
    inner = VGroup(VGroup(head_bar, head), role_t, chips).arrange(
        DOWN, buff=0.14)
    bg = RoundedRectangle(
        corner_radius=0.14,
        width=width, height=inner.height + 0.36,
        fill_color=PANEL, fill_opacity=0.92,
        stroke_color=color, stroke_width=1.6, stroke_opacity=0.55,
    ).move_to(inner)
    g = VGroup(bg, inner)
    g.agent_color = color
    return g


class AgentBus:
    """Knows agent positions; can send a payload mobject between agents."""

    def __init__(self, agents: dict[str, VGroup], store: ConstraintLedger | None = None):
        # agents: name -> AgentCard mobject already placed in scene
        self.agents = agents
        self.store = store

    def send(self, scene: Scene, src: str, dst: str,
             payload: Mobject | None = None, color=ACCENT,
             run_time: float = 0.9) -> None:
        a = self.agents[src]
        b = self.agents[dst]
        path = CubicBezier(
            a.get_center(),
            a.get_center() + 1.5 * (UP if a.get_y() < 0 else DOWN),
            b.get_center() + 1.5 * (UP if b.get_y() < 0 else DOWN),
            b.get_center(),
        )
        flash = path.copy().set_stroke(color=color, width=4, opacity=0.8)
        if payload is None:
            scene.play(ShowPassingFlash(flash, time_width=0.5,
                                         run_time=run_time))
            return
        payload.move_to(a.get_center())
        scene.play(
            ShowPassingFlash(flash, time_width=0.4, run_time=run_time),
            MoveAlongPath(payload, path, run_time=run_time),
        )


# ============================================================
# MorphBar — horizontal bar that grows with synced DecimalNumber
# ============================================================
class MorphBar:
    """A horizontal bar + counter you can grow with one play() call."""

    def __init__(self, label: str, value: float, max_val: float,
                 bar_max_w: float = 3.0, bar_h: float = 0.42,
                 color=ACCENT, unit: str = ""):
        self.label_t = Text(label, font_size=20, color=color, weight=BOLD,
                            font="Segoe UI")
        self.bar = Rectangle(width=0.001, height=bar_h,
                              fill_color=color, fill_opacity=0.92,
                              stroke_width=0)
        self.counter = DecimalNumber(0, num_decimal_places=1,
                                     font_size=22, color=color, unit=unit)
        self.target_w = bar_max_w * min(value / max_val, 1.0)
        self.value = value
        self.color = color

    def place(self, label_pos, bar_left_pos):
        """Anchor positions. label_pos is right edge of label column."""
        self.label_t.move_to(label_pos)
        self.bar.move_to(bar_left_pos, aligned_edge=LEFT)
        self.counter.next_to(self.bar.get_right(), RIGHT, buff=0.15)\
                    .set_y(self.bar.get_y())
        return VGroup(self.label_t, self.bar, self.counter)

    def grow(self, scene: Scene, run_time: float = 0.9):
        bar = self.bar
        counter = self.counter
        counter.add_updater(
            lambda m: m.next_to(bar.get_right(), RIGHT, buff=0.15)
                       .set_y(bar.get_y())
        )
        scene.play(
            bar.animate.stretch_to_fit_width(self.target_w, about_edge=LEFT),
            counter.animate.set_value(self.value),
            run_time=run_time, rate_func=rate_functions.ease_out_cubic,
        )
        counter.clear_updaters()
        counter.next_to(bar.get_right(), RIGHT, buff=0.15).set_y(bar.get_y())
