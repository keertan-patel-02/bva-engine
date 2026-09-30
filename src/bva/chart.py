import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

KP = {
    "surface": "#ffffff", "ink": "#1b1f1d", "ink_muted": "#5b625c",
    "border": "#dee1da", "border_strong": "#c4c9bf",
    "accent": "#3f6b52", "danger": "#b0473a",
}

mpl.rcParams.update({
    "font.family": ["IBM Plex Sans", "DejaVu Sans"],
    "figure.facecolor": KP["surface"],
    "axes.facecolor": KP["surface"],
    "axes.edgecolor": KP["border_strong"],
    "axes.labelcolor": KP["ink_muted"],
    "axes.titlecolor": KP["ink"],
    "text.color": KP["ink"],
    "xtick.color": KP["ink_muted"],
    "ytick.color": KP["ink_muted"],
    "grid.color": KP["border"],
    "axes.spines.top": False,
    "axes.spines.right": False,
})

ANCHORS = {"Budget Revenue", "Actual Revenue"}
def build_waterfall(output_dir, bridge_df, entity_id, period):
    path = output_dir / f"waterfall_{entity_id}_{period}.png"
    x_labels = bridge_df["component"]
    heights = bridge_df["amount"]
    is_anchor = bridge_df["component"].isin(ANCHORS)
    bottoms = bridge_df["amount"].cumsum().shift(fill_value=0)
    bottoms[is_anchor] = 0
    colors = [KP["border_strong"] if a else (KP["accent"]  if v > 0 else KP["danger"]) for a, v in zip(is_anchor, bridge_df["amount"])]

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    bars = ax.bar(x_labels, heights, bottom=bottoms, color=colors)
    ax.bar_label(bars, fmt="{:,.0f}", padding=3, fontsize=9, color=KP["ink_muted"])
    ax.set_title(f"Rooms Revenue Bridge - {entity_id}, {period}", pad=14)
    ax.set_ylabel("Revenue ($)")
    tops = bottoms + heights
    padding = tops.max() - tops.min()
    ax.set_ylim(tops.min()-padding, tops.max() + padding)
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)

    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path