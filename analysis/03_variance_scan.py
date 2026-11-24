"""
Step 3 - Descriptive variance scan (still EDA, not hypothesis testing).

For each unit-level outcome, how much of the total variance is associated with
Strain, Temperature, InitialSugar and their interaction? These are DESCRIPTIVE
effect sizes (partial eta^2 from a full-factorial decomposition) reported
WITHOUT p-values, to show the group where the signal is before they choose and
justify their own tests and hypotheses.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))
import common as C

units = pd.read_csv(C.TABLES / "02_unit_level_features.csv")
units["Temperature"] = pd.Categorical(units["Temperature"], C.TEMP_ORDER, ordered=True)

OUTCOMES = ["T50_h", "T90_h", "MaxRate_gL_h", "FinalResidualSugar", "FinalEthanol",
            "EthanolYield_pct_per_gL", "FinalGlycerol", "FinalAcetate",
            "FinalSuccinate", "MalateConsumed", "MaxViable", "FinalViability"]


def eta_squared(d, y):
    """Type-I sums of squares for Strain + Temperature + MS + Strain:Temperature."""
    d = d.dropna(subset=[y])
    gm = d[y].mean()
    sst = ((d[y] - gm) ** 2).sum()
    out = {}
    for name, keys in [("Strain", ["Strain"]), ("Temperature", ["Temperature"]),
                       ("InitialSugar", ["MS"]),
                       ("Strain x Temperature", ["Strain", "Temperature"])]:
        g = d.groupby(keys, observed=True)[y].agg(["mean", "count"])
        ss = (g["count"] * (g["mean"] - gm) ** 2).sum()
        out[name] = ss
    # the interaction cell SS contains both main effects - remove them
    out["Strain x Temperature"] = max(
        out["Strain x Temperature"] - out["Strain"] - out["Temperature"], 0.0)
    res = {k: 100 * v / sst for k, v in out.items()}
    res["Residual / replicate"] = max(100 - sum(res.values()), 0.0)
    res["N"] = len(d)
    return res


rows = {y: eta_squared(units, y) for y in OUTCOMES}
var = pd.DataFrame(rows).T
cols = ["Temperature", "Strain", "InitialSugar", "Strain x Temperature",
        "Residual / replicate"]
var = var[cols + ["N"]]
print("Share of variance (%) in each unit-level outcome:\n")
print(var.round(1).to_string())
C.dump(var.round(2), "03_variance_decomposition",
       "descriptive % of variance, no p-values")

# ------------------------------------------------------------------ figure
plot = var[cols].loc[var["Temperature"].sort_values(ascending=True).index]
fig, ax = plt.subplots(figsize=(9.6, 5.4))
left = np.zeros(len(plot))
shades = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#d8d7d1"]
for col, colr in zip(cols, shades):
    v = plot[col].to_numpy()
    ax.barh(range(len(plot)), v, left=left, height=0.74, color=colr,
            edgecolor=C.SURFACE, linewidth=2, label=col)   # 2px surface gap
    for i, (val, l) in enumerate(zip(v, left)):
        if val >= 7:
            ax.annotate(f"{val:.0f}", (l + val / 2, i), ha="center", va="center",
                        fontsize=7.5,
                        color=C.SURFACE if col != "Residual / replicate" else C.INK2)
    left += v
ax.set_yticks(range(len(plot)))
ax.set_yticklabels(plot.index)
ax.set_xlabel("Share of total variance (%)")
ax.set_xlim(0, 100)
ax.grid(axis="y", visible=False)
ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.30), ncol=5,
          columnspacing=1.4, handlelength=1.1)
C.despine(ax)
rect = C.titles(fig, "Each outcome has a different dominant factor",
                "Descriptive share of variance in each unit-level outcome "
                "(n = 216 fermentations), ordered by the temperature share.\n"
                "Temperature drives the kinetics; initial sugar drives ethanol, "
                "glycerol and acetate; strain leads only for peak cell count.\n"
                "Descriptive only - no p-values. Labels shown for shares ≥ 7 %.",
                top=0.85)
rect[1] = 0.11
fig.tight_layout(rect=rect)
C.save(fig, "fig08_variance_decomposition")

print("\nOutcomes where Strain explains the most variance:")
print(var["Strain"].sort_values(ascending=False).head(5).round(1).to_string())
