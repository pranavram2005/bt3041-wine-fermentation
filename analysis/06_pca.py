"""
Step 6 - Principal Component Analysis.

Runs on the 216-row unit-level table (one row per fermentation), NOT the raw
repeated-measures sheet.

Documented analytical choices (the brief asks for these explicitly):

  1. FEATURES - 15 unit-level numeric outcomes.  Excluded:
       - `T_total_h`: total elapsed sampling time is a property of the
         sampling schedule, not of the yeast; it is almost perfectly
         determined by temperature and would hand PC1 to the design.
       - `Dry`: a binary flag derived from FinalResidualSugar, so redundant.
       - the 10 volatile aroma compounds: assayed at only 5 of 9 sampling
         points, so they never entered the unit-level table.  Including them
         would mean imputing a whole block.  Excluded, and said so.
  2. MISSING VALUES - `GALA|TVAR|250|R1` never reached 90% sugar consumption,
     so its T90_h is undefined.  That single unit is dropped rather than
     imputed (n = 215), because imputing a completion time for a fermentation
     that never completed would invent the result.
  3. SCALING - StandardScaler, mandatory.  The columns run from ~0.5 g/L
     acetate to ~1e8 cells/mL; unscaled, PC1 would simply be cell count.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

sys.path.insert(0, str(Path(__file__).parent))
import common as CM

FEATURES = [
    "InitialSugar", "FinalResidualSugar", "SugarConsumedTotal",
    "FracFermentedFinal", "FinalEthanol", "EthanolYield_pct_per_gL",
    "FinalGlycerol", "FinalAcetate", "FinalSuccinate", "MalateConsumed",
    "T50_h", "T90_h", "MaxRate_gL_h", "MaxViable", "FinalViability",
]

units = pd.read_csv(CM.TABLES / "02_unit_level_features.csv")
units["Temperature"] = pd.Categorical(units["Temperature"], CM.TEMP_ORDER, ordered=True)

n_before = len(units)
d = units.dropna(subset=FEATURES).copy()
print("=" * 78)
print("STEP 6 - PCA")
print("=" * 78)
print("Fermentations: %d of %d (dropped %d with an undefined T90)"
      % (len(d), n_before, n_before - len(d)))
print("Features: %d" % len(FEATURES))
print("Dropped units:", sorted(set(units["Unit"]) - set(d["Unit"])))

X = StandardScaler().fit_transform(d[FEATURES].to_numpy())
pca = PCA().fit(X)
scores = pca.transform(X)

# ------------------------------------------------------------------ variance
ev = pd.DataFrame({
    "PC": ["PC%d" % (i + 1) for i in range(len(pca.explained_variance_ratio_))],
    "eigenvalue": pca.explained_variance_,
    "explained_var_pct": 100 * pca.explained_variance_ratio_,
    "cumulative_pct": 100 * np.cumsum(pca.explained_variance_ratio_),
})
print("\nExplained variance:")
print(ev.round(2).head(8).to_string(index=False))
CM.dump(ev.round(4), "06_explained_variance", "eigenvalues and % variance per PC")

k_kaiser = int((pca.explained_variance_ > 1).sum())
n_80 = int((ev["cumulative_pct"] < 80).sum() + 1)
print("\nComponents to retain: %d by Kaiser (eigenvalue > 1), %d to reach 80%%"
      % (k_kaiser, n_80))

# ------------------------------------------------------------------ loadings
load = pd.DataFrame(pca.components_[:5].T, index=FEATURES,
                    columns=["PC%d" % (i + 1) for i in range(5)])
print("\nLoadings (first 5 PCs):")
print(load.round(3).to_string())
CM.dump(load.round(4), "06_loadings", "variable loadings on PC1-PC5")

for pc in ["PC1", "PC2", "PC3"]:
    top = load[pc].abs().sort_values(ascending=False).head(5).index
    print("\n%s is driven by:" % pc)
    for v in top:
        print("    %-26s %+.3f" % (v, load.loc[v, pc]))

sc = pd.DataFrame(scores[:, :5], columns=["PC%d" % (i + 1) for i in range(5)])
sc = pd.concat([d[["Unit", "Strain", "Temperature", "MS", "Rep"]]
                .reset_index(drop=True), sc], axis=1)
CM.dump(sc.round(4), "06_pc_scores", "PC1-PC5 scores per fermentation")

# ------------------------------------------------- does strain or temp separate?
# Silhouette in the retained PC space, using the known labels as if they were
# clusters.  This quantifies what the scatter plots show by eye: a label with a
# higher silhouette groups fermentations more tightly in metabolic space.
space = scores[:, :k_kaiser]
sep = []
for name, lab in [("Strain", d["Strain"]), ("Temperature", d["Temperature"]),
                  ("MS (initial sugar)", d["MS"])]:
    sep.append({"label": name, "n_groups": lab.nunique(),
                "silhouette_in_PC_space": silhouette_score(space, lab.astype(str))})
sep = pd.DataFrame(sep)
print("\nHow well each design factor groups fermentations in PC space")
print("(silhouette: 1 = tight separate groups, 0 = none, negative = overlapping)")
print(sep.round(4).to_string(index=False))
CM.dump(sep.round(4), "06_label_separation",
        "silhouette of each design factor in retained PC space")

# ------------------------------------------------------------------ figures
# fig12 - scree
fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.8))
x = np.arange(1, len(ev) + 1)
a1.bar(x, ev["explained_var_pct"], color=CM.SEQ_HUE, edgecolor="none")
a1.axhline(100 / len(FEATURES), color=CM.INK3, ls="--", lw=1)
a1.text(len(ev), 100 / len(FEATURES) + 1.2, "equal-share (%.1f%%)" % (100 / len(FEATURES)),
        ha="right", color=CM.INK3, fontsize=8)
a1.set_xlabel("component")
a1.set_ylabel("variance explained (%)")
a1.set_title("Scree")
a2.plot(x, ev["cumulative_pct"], "o-", color=CM.SEQ_HUE)
a2.axhline(80, color=CM.INK3, ls="--", lw=1)
a2.text(len(ev), 81.5, "80%", ha="right", color=CM.INK3, fontsize=8)
a2.set_xlabel("components retained")
a2.set_ylabel("cumulative variance (%)")
a2.set_title("Cumulative")
for a in (a1, a2):
    CM.despine(a)
rect = CM.titles(fig, "PCA on 15 fermentation outcomes",
                 "n = %d fermentations, standardised; %d components have eigenvalue > 1"
                 % (len(d), k_kaiser), top=0.86)
fig.tight_layout(rect=rect)
CM.save(fig, "fig12_pca_scree", "scree and cumulative variance")

# fig13 - PC1/PC2 coloured by temperature, then by strain
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.2, 4.8))
for temp in CM.TEMP_ORDER:
    m = (d["Temperature"] == temp).to_numpy()
    a1.scatter(scores[m, 0], scores[m, 1], s=26, alpha=0.85,
               color=CM.TEMP_COLORS[temp],
               label="TVAR" if temp == "TVAR" else temp + " degC",
               edgecolor="white", linewidth=0.4)
a1.set_title("coloured by temperature regime")
a1.legend(title="", loc="best", ncol=2)

strains = sorted(d["Strain"].unique())
for i, s in enumerate(strains):
    m = (d["Strain"] == s).to_numpy()
    a2.scatter(scores[m, 0], scores[m, 1], s=26, alpha=0.85,
               color=CM.SERIES[i % len(CM.SERIES)],
               marker=["o", "s", "^", "D"][i // len(CM.SERIES)],
               label=s, edgecolor="white", linewidth=0.4)
a2.set_title("coloured by strain")
a2.legend(loc="best", ncol=3, fontsize=7)

for a in (a1, a2):
    a.set_xlabel("PC1 (%.1f%%)" % ev.loc[0, "explained_var_pct"])
    a.set_ylabel("PC2 (%.1f%%)" % ev.loc[1, "explained_var_pct"])
    a.axhline(0, color=CM.GRID, lw=0.8)
    a.axvline(0, color=CM.GRID, lw=0.8)
    CM.despine(a)
rect = CM.titles(fig, "Same 215 fermentations, same axes, two labellings",
                 "Temperature separates them; strain does not. Silhouette %.3f vs %.3f."
                 % (sep.loc[1, "silhouette_in_PC_space"],
                    sep.loc[0, "silhouette_in_PC_space"]), top=0.87)
fig.tight_layout(rect=rect)
CM.save(fig, "fig13_pca_scatter", "PC1-PC2 by temperature and by strain")

# fig14 - biplot: loadings of PC1/PC2
fig, ax = plt.subplots(figsize=(6.6, 6.0))
ax.scatter(scores[:, 0], scores[:, 1], s=16, color=CM.GRID, zorder=1)
sf = 0.9 * max(np.abs(scores[:, :2]).max(), 1)
for v in FEATURES:
    vx, vy = load.loc[v, "PC1"] * sf, load.loc[v, "PC2"] * sf
    ax.annotate("", xy=(vx, vy), xytext=(0, 0),
                arrowprops=dict(arrowstyle="->", color=CM.SERIES[0], lw=1.2))
    ax.text(vx * 1.08, vy * 1.08, v, fontsize=7.5, color=CM.INK,
            ha="center", va="center")
ax.axhline(0, color=CM.GRID, lw=0.8)
ax.axvline(0, color=CM.GRID, lw=0.8)
ax.set_xlabel("PC1 (%.1f%%)" % ev.loc[0, "explained_var_pct"])
ax.set_ylabel("PC2 (%.1f%%)" % ev.loc[1, "explained_var_pct"])
CM.despine(ax)
rect = CM.titles(fig, "What the components mean",
                 "Arrows = variable loadings; grey points = the 215 fermentations",
                 top=0.90)
fig.tight_layout(rect=rect)
CM.save(fig, "fig14_pca_biplot", "PC1-PC2 loadings biplot")

print("\nDone. Tables 06_*.csv and figures fig12-fig14 written.")
