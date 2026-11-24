"""
Draw the fermentation overview used on slide 2 of the presentation.

This is a presentation asset, not an analysis output: it illustrates what
alcoholic fermentation is and how the experiment is laid out, so the audience
has the process in mind before any numbers appear. Drawn here rather than
taken from stock art so the palette and type match every other figure.

Output: outputs/figures/fig18_fermentation_overview.png
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Ellipse, FancyArrowPatch, Circle

sys.path.insert(0, str(Path(__file__).parent))
import common as CM

INK, INK2, INK3 = CM.INK, CM.INK2, CM.INK3
BLUE, ORANGE, GREEN = CM.SERIES[0], CM.SERIES[1], CM.SERIES[2]
AMBER = "#eda100"


def flask(ax, cx, cy, w, h, fill_frac, fill_color, label, sub):
    """A simple conical flask with liquid in it."""
    neck_w, neck_h = w * 0.26, h * 0.30
    body = [(cx - w / 2, cy - h / 2),
            (cx + w / 2, cy - h / 2),
            (cx + neck_w / 2, cy - h / 2 + (h - neck_h)),
            (cx + neck_w / 2, cy + h / 2),
            (cx - neck_w / 2, cy + h / 2),
            (cx - neck_w / 2, cy - h / 2 + (h - neck_h))]
    ax.add_patch(Polygon(body, closed=True, facecolor="white",
                         edgecolor=INK2, linewidth=1.5, zorder=2))
    # liquid: a trapezoid filling the lower part of the cone
    lh = (h - neck_h) * fill_frac
    y0 = cy - h / 2
    half_at = lambda yy: (w / 2) - ((w - neck_w) / 2) * (yy / (h - neck_h))
    liq = [(cx - half_at(0), y0), (cx + half_at(0), y0),
           (cx + half_at(lh), y0 + lh), (cx - half_at(lh), y0 + lh)]
    ax.add_patch(Polygon(liq, closed=True, facecolor=fill_color, alpha=0.85,
                         edgecolor="none", zorder=3))
    ax.text(cx, cy - h / 2 - 0.30, label, ha="center", va="top",
            fontsize=11, fontweight="bold", color=INK)
    ax.text(cx, cy - h / 2 - 0.62, sub, ha="center", va="top",
            fontsize=9.5, color=INK2)


fig, ax = plt.subplots(figsize=(7.4, 6.1))
ax.set_xlim(0, 10)
ax.set_ylim(0, 8.6)
ax.axis("off")
ax.set_facecolor(CM.SURFACE)
fig.patch.set_facecolor(CM.SURFACE)

# ---------------------------------------------------------------- the process
ax.text(0.2, 8.35, "THE PROCESS", fontsize=10, fontweight="bold", color=INK3)

flask(ax, 1.75, 6.45, 2.0, 2.1, 0.80, AMBER,
      "Synthetic must", "210–250 g/L sugar")
flask(ax, 8.25, 6.45, 2.0, 2.1, 0.68, "#8f2d56",
      "Wine", "12–14 % ethanol")

# yeast cell, budding, between the two flasks
ax.add_patch(Ellipse((5.0, 6.85), 1.05, 0.80, facecolor="white",
                     edgecolor=GREEN, linewidth=1.6, zorder=4))
ax.add_patch(Ellipse((5.62, 7.22), 0.46, 0.36, facecolor="white",
                     edgecolor=GREEN, linewidth=1.4, zorder=4))
ax.add_patch(Ellipse((4.85, 6.80), 0.26, 0.20, facecolor=GREEN, alpha=0.30,
                     edgecolor="none", zorder=5))
ax.text(5.0, 6.10, "yeast", ha="center", va="top", fontsize=10.5,
        fontweight="bold", color=GREEN)
ax.text(5.0, 5.80, "S. cerevisiae", ha="center", va="top", fontsize=9,
        style="italic", color=INK2)

for x0, x1 in [(2.95, 4.35), (5.70, 7.10)]:
    ax.add_patch(FancyArrowPatch((x0, 6.45), (x1, 6.45),
                                 arrowstyle="-|>", mutation_scale=16,
                                 linewidth=1.6, color=INK2, zorder=1))

# CO2 escaping the wine flask
for i, (dx, dy, r) in enumerate([(-0.18, 1.35, 0.075), (0.10, 1.62, 0.055),
                                 (-0.02, 1.88, 0.095)]):
    ax.add_patch(Circle((8.25 + dx, 6.45 + dy), r, facecolor="none",
                        edgecolor=INK3, linewidth=1.1, zorder=4))
ax.text(8.95, 8.15, "CO₂", fontsize=10, color=INK3, ha="left", va="center")

# ---------------------------------------------------------------- the equation
ax.plot([0.2, 9.8], [4.55, 4.55], color=CM.GRID, linewidth=1.0)
ax.text(5.0, 4.05, "C₆H₁₂O₆    →    2 C₂H₅OH   +   2 CO₂",
        ha="center", va="center", fontsize=14, color=INK, fontweight="bold")
ax.text(5.0, 3.58, "one glucose  →  two ethanol  +  two carbon dioxide",
        ha="center", va="center", fontsize=9.5, color=INK2)

# ---------------------------------------------------------------- the design
ax.plot([0.2, 9.8], [3.00, 3.00], color=CM.GRID, linewidth=1.0)
ax.text(0.2, 2.68, "THE EXPERIMENT", fontsize=10, fontweight="bold",
        color=INK3)

chips = [("9", "strains", BLUE), ("4", "temperature\nregimes", ORANGE),
         ("2", "sugar\nlevels", AMBER), ("3", "replicates", GREEN)]
for i, (n, lab, col) in enumerate(chips):
    cx = 1.25 + i * 2.1
    ax.text(cx, 1.70, n, ha="center", va="center", fontsize=25,
            fontweight="bold", color=col)
    ax.text(cx, 1.02, lab, ha="center", va="center", fontsize=9.5,
            color=INK2, linespacing=1.3)
    if i < 3:
        ax.text(cx + 1.05, 1.70, "×", ha="center", va="center", fontsize=15,
                color=INK3)

ax.text(5.0, 0.28, "216 independent fermentations, each sampled 9 times",
        ha="center", va="center", fontsize=10.5, fontweight="bold", color=INK)

fig.tight_layout(pad=0.4)
CM.save(fig, "fig18_fermentation_overview", "slide-2 process schematic")
