"""Generate two horizontal bar charts: HG2.9K and GitChameleon pass rates.
Style: modern, minimal, Metropolis-friendly. Output saved next to this script.
"""
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,
    "axes.edgecolor": "#888",
    "axes.linewidth": 0.6,
    "xtick.color": "#444",
    "ytick.color": "#222",
    "axes.labelcolor": "#222",
})

ACCENT  = "#EB811B"   # CGAR — orange
SECOND  = "#3B82A0"   # MEMRES — teal-blue
NEUTRAL = "#B8BEC7"   # baselines — muted grey
CLOSED  = "#7E8794"   # closed-weight LLMs — darker grey
TEXT    = "#222"

def hbar(ax, labels, values, colors, title, dataset_n, highlight_idx,
         xlabel="Pass rate (%)"):
    y = list(range(len(labels)))
    bars = ax.barh(y, values, color=colors, edgecolor="white", linewidth=0.8,
                   height=0.68)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=10.5)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel(xlabel, fontsize=10, color="#555")
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.tick_params(axis="x", length=0, labelsize=9)
    ax.tick_params(axis="y", length=0)
    ax.xaxis.grid(True, linestyle=":", linewidth=0.6, color="#D0D4DB",
                  zorder=0)
    ax.set_axisbelow(True)

    # value labels
    for i, (bar, v) in enumerate(zip(bars, values)):
        weight = "bold" if i in highlight_idx else "normal"
        col = ACCENT if i == highlight_idx[-1] else TEXT
        ax.text(v + 1.2, bar.get_y() + bar.get_height() / 2,
                f"{v:.1f}%", va="center", ha="left",
                fontsize=10.5, color=col, fontweight=weight)

    ax.set_title(title, fontsize=13, fontweight="bold", loc="left",
                 color=TEXT, pad=12)
    ax.text(0, -0.9, f"n = {dataset_n}", fontsize=9, color="#777",
            transform=ax.transData)


# ─── HG2.9K (in-distribution, 2891 snippets) ────────────────────────────
hg_data = [
    ("pip naive*",   24.4, NEUTRAL),
    ("DockerizeMe*", 30.0, NEUTRAL),
    ("PLLM (ASEW'25)",  44.8, NEUTRAL),
    ("PyEGo (ICSE'22)", 45.0, NEUTRAL),
    ("ReadPyE (TSE'24)",47.2, NEUTRAL),
    ("MEMRES ★ (FSE'26)", 86.3, SECOND),
    ("CGAR ★★ (ours)",    87.1, ACCENT),
]
# ─── GitChameleon (out-of-distribution, 328 snippets) ───────────────────
gc_data = [
    ("GPT-4o",         49.1, CLOSED),
    ("Gemini 2.5 Pro", 50.0, CLOSED),
    ("o1 (best closed)", 51.2, CLOSED),
    ("GPT-4.1 + RAG",  58.5, CLOSED),
    ("PLLM (Gemma-2 9B)", 65.5, NEUTRAL),
    ("MEMRES ★",       81.7, SECOND),
    ("CGAR ★★ (ours)", 83.2, ACCENT),
]

def render(data, n, title, outfile):
    fig, ax = plt.subplots(figsize=(7.0, 3.6), dpi=150)
    labels  = [d[0] for d in data]
    values  = [d[1] for d in data]
    colors  = [d[2] for d in data]
    highlight_idx = [len(data) - 2, len(data) - 1]  # MEMRES + CGAR
    hbar(ax, labels, values, colors, title, n, highlight_idx)
    fig.tight_layout()
    fig.savefig(outfile, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", outfile)


render(hg_data, "2 891", "HG2.9K — in-distribution",   "perf_hg2k.pdf")
render(gc_data, "328",   "GitChameleon — out-of-distribution", "perf_gitcham.pdf")
