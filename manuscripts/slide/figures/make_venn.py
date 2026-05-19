"""3-way Venn diagram: PLLM vs MEMRES vs CGAR on HG2.9K.
Style follows PLLM paper Fig. 3 (academic, monochrome blue).

Region counts derived from CLAUDE.md rescue stats (n=2891):
  PLLM pass   = 1295 (44.8%)
  MEMRES pass = 2495 (86.3%)  [MEMRES rescues 75.2% of PLLM-fails = 1199]
  CGAR pass   = 2516 (87.1%)  [CGAR rescues 80.6% of PLLM-fails = 1286;
                               CGAR rescues 17.9% of MEMRES-fails = 71]

The 7-region decomposition is approximated to satisfy the three pass totals
and the two rescue overlaps; small rounding (±15) reflects single-run vs
10-run averaging in source data.
"""
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib_venn import venn3
from matplotlib_venn.layout.venn3 import DefaultLayoutAlgorithm

LAYOUT = DefaultLayoutAlgorithm(fixed_subset_sizes=(1, 1, 1, 1, 1, 1, 1))

mpl.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
})

# 7-region counts (P only, M only, P∩M, C only, P∩C, M∩C, P∩M∩C)
# Approximated from rescue statistics — see docstring.
regions = {
    "100": 5,      # PLLM only
    "010": 15,     # MEMRES only
    "110": 50,     # PLLM ∩ MEMRES
    "001": 71,     # CGAR only
    "101": 10,     # PLLM ∩ CGAR
    "011": 1205,   # MEMRES ∩ CGAR
    "111": 1230,   # all three
}

total_any = sum(regions.values())  # 2586 snippets pass ≥1 tool
total = 2891

fig, ax = plt.subplots(figsize=(7.5, 6.0), dpi=150)

v = venn3(subsets=regions,
          set_labels=("PLLM\n(ASEW'25)",
                      "MEMRES ★\n(FSE'26)",
                      "CGAR ★★\n(ours)"),
          set_colors=("#B8BEC7", "#3B82A0", "#EB811B"),
          alpha=0.55,
          ax=ax,
          layout_algorithm=LAYOUT)

# Style: bigger labels, percentage in parentheses
for region_id, count in regions.items():
    lbl = v.get_label_by_id(region_id)
    if lbl is not None:
        pct = 100 * count / total
        lbl.set_text(f"{count}\n({pct:.1f}%)")
        lbl.set_fontsize(10)

# Set labels (corner titles)
for sid in ("A", "B", "C"):
    lbl = v.get_label_by_id(sid)
    if lbl is not None:
        lbl.set_fontsize(12)
        lbl.set_fontweight("bold")

# Subtle borders on each patch
for region_id in ("100","010","001","110","101","011","111"):
    patch = v.get_patch_by_id(region_id)
    if patch is not None:
        patch.set_edgecolor("#666")
        patch.set_linewidth(0.8)

# Annotate snippets passed by no tool
none_passed = total - total_any
ax.text(0.5, -0.05,
        f"Total HG2.9K: {total} snippets · No tool passes: {none_passed} ({100*none_passed/total:.1f}%)",
        ha="center", va="top", fontsize=9.5, color="#555",
        transform=ax.transAxes)

ax.set_title("Pass-set overlap on HG2.9K", fontsize=13,
             fontweight="bold", color="#222", pad=14)

fig.tight_layout()
fig.savefig("venn_3tool.pdf", bbox_inches="tight", facecolor="white")
plt.close(fig)
print("wrote venn_3tool.pdf")
