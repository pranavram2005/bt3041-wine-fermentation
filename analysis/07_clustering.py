"""
Step 7 - Clustering.

Same 215 fermentations and the same 15 standardised features as the PCA, so
the two steps are directly comparable.

What this script answers: do fermentations fall into natural groups, and do
those groups correspond to strain?  The brief's own question is whether
samples with similar fermentation profiles form distinct groups - so the key
output is not the dendrogram, it is the CROSS-TABULATION of cluster against
each design factor, plus an Adjusted Rand Index that scores the match
numerically instead of by eye.

Choices:
  - k is chosen by silhouette over k = 2..10, NOT set to 9 because there are
    9 strains.  Setting k = 9 would assume the answer.
  - Both Ward (hierarchical) and k-means are run.  Agreement between two
    methods that make different assumptions is the stability check the brief
    asks for, alongside a bootstrap resample.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, adjusted_rand_score

sys.path.insert(0, str(Path(__file__).parent))
import common as CM

FEATURES = [
    "InitialSugar", "FinalResidualSugar", "SugarConsumedTotal",
    "FracFermentedFinal", "FinalEthanol", "EthanolYield_pct_per_gL",
    "FinalGlycerol", "FinalAcetate", "FinalSuccinate", "MalateConsumed",
    "T50_h", "T90_h", "MaxRate_gL_h", "MaxViable", "FinalViability",
]
RNG = 0

units = pd.read_csv(CM.TABLES / "02_unit_level_features.csv")
units["Temperature"] = pd.Categorical(units["Temperature"], CM.TEMP_ORDER, ordered=True)
d = units.dropna(subset=FEATURES).copy().reset_index(drop=True)
X = StandardScaler().fit_transform(d[FEATURES].to_numpy())

print("=" * 78)
print("STEP 7 - CLUSTERING  (n = %d fermentations, %d standardised features)"
      % (len(d), len(FEATURES)))
print("=" * 78)

# --------------------------------------------------------------- choosing k
Z = linkage(X, method="ward")
rows = []
for k in range(2, 11):
    ward_lab = fcluster(Z, k, criterion="maxclust")
    km_lab = KMeans(n_clusters=k, n_init=25, random_state=RNG).fit_predict(X)
    rows.append({
        "k": k,
        "silhouette_ward": silhouette_score(X, ward_lab),
        "silhouette_kmeans": silhouette_score(X, km_lab),
        "inertia_kmeans": KMeans(n_clusters=k, n_init=25,
                                 random_state=RNG).fit(X).inertia_,
        "ward_vs_kmeans_ARI": adjusted_rand_score(ward_lab, km_lab),
    })
sel = pd.DataFrame(rows)
print("\nChoosing k (silhouette, elbow, and agreement between the two methods):")
print(sel.round(4).to_string(index=False))
CM.dump(sel.round(4), "07_k_selection", "silhouette / inertia / method agreement, k = 2-10")

BEST_K = int(sel.loc[sel["silhouette_ward"].idxmax(), "k"])
print("\nBest k by Ward silhouette: %d" % BEST_K)

# --------------------------------------------------------------- the clusters
d["ward"] = fcluster(Z, BEST_K, criterion="maxclust")
d["kmeans"] = KMeans(n_clusters=BEST_K, n_init=50, random_state=RNG).fit_predict(X) + 1
print("Ward vs k-means agreement at k = %d: ARI = %.3f"
      % (BEST_K, adjusted_rand_score(d["ward"], d["kmeans"])))

# --------------------------------------------- do clusters correspond to labels?
print("\n" + "-" * 78)
print("DO THE CLUSTERS MATCH THE DESIGN FACTORS?  (ARI: 1 = perfect, 0 = chance)")
print("-" * 78)
ari = []
for name, lab in [("Strain", d["Strain"]), ("Temperature", d["Temperature"]),
                  ("MS (initial sugar)", d["MS"])]:
    ari.append({"label": name, "n_groups": lab.nunique(),
                "ARI_ward": adjusted_rand_score(lab.astype(str), d["ward"]),
                "ARI_kmeans": adjusted_rand_score(lab.astype(str), d["kmeans"])})
ari = pd.DataFrame(ari)
print(ari.round(4).to_string(index=False))
CM.dump(ari.round(4), "07_cluster_label_agreement",
        "Adjusted Rand Index, clusters vs each design factor")

for name, col in [("Strain", "Strain"), ("Temperature", "Temperature"), ("MS", "MS")]:
    ct = pd.crosstab(d[col], d["ward"])
    print("\nWard clusters x %s:" % name)
    print(ct.to_string())
    CM.dump(ct, "07_crosstab_ward_x_%s" % name.lower(),
            "cluster membership by %s" % name)

# ------------------------------------------------------- what defines a cluster
prof = d.groupby("ward", observed=True)[FEATURES].mean().T
prof["spread_across_clusters"] = prof.std(axis=1)
prof = prof.sort_values("spread_across_clusters", ascending=False)
print("\nCluster profiles (mean of each feature, raw units):")
print(prof.round(2).to_string())
CM.dump(prof.round(4), "07_cluster_profiles", "mean feature value per Ward cluster")

size = d["ward"].value_counts().sort_index()
print("\nCluster sizes:", dict(size))

# ------------------------------------------------------------------ stability
# Resample 80% of the fermentations 100 times, re-cluster, and measure how well
# the labels agree with the full-data labels on the units that were kept.
rng = np.random.default_rng(RNG)
stab = []
for i in range(100):
    idx = rng.choice(len(d), size=int(0.8 * len(d)), replace=False)
    lab = fcluster(linkage(X[idx], method="ward"), BEST_K, criterion="maxclust")
    stab.append(adjusted_rand_score(d["ward"].to_numpy()[idx], lab))
stab = np.array(stab)
print("\nStability - 100 x 80%% resamples, Ward re-run:")
print("    mean ARI vs full-data clusters = %.3f  (sd %.3f, min %.3f)"
      % (stab.mean(), stab.std(), stab.min()))
CM.dump(pd.DataFrame({"resample": np.arange(1, 101), "ARI_vs_full": stab}).round(4),
        "07_stability_resampling", "100 x 80% resample ARI")

d[["Unit", "Strain", "Temperature", "MS", "Rep", "ward", "kmeans"]].to_csv(
    CM.TABLES / "07_cluster_assignments.csv", index=False)
print("  table  -> outputs/tables/07_cluster_assignments.csv")

# ------------------------------------------------------------------ figures
# fig15 - dendrogram, leaves coloured by temperature
fig, ax = plt.subplots(figsize=(11.5, 4.4))
dn = dendrogram(Z, ax=ax, color_threshold=Z[-(BEST_K - 1), 2],
                above_threshold_color=CM.INK3, no_labels=True)
ax.axhline(Z[-(BEST_K - 1), 2], color=CM.INK3, ls="--", lw=1)
ax.text(ax.get_xlim()[1], Z[-(BEST_K - 1), 2], " cut at k = %d " % BEST_K,
        ha="right", va="bottom", fontsize=8, color=CM.INK2)
ax.set_ylabel("Ward linkage distance")
ax.set_xlabel("215 fermentations")
CM.despine(ax)
rect = CM.titles(fig, "Hierarchical clustering of 215 fermentations",
                 "Ward linkage on 15 standardised outcomes; cut at k = %d (best silhouette)"
                 % BEST_K, top=0.86)
fig.tight_layout(rect=rect)
CM.save(fig, "fig15_dendrogram", "Ward dendrogram")

# fig16 - clusters in PC space, beside the temperature truth
scores = PCA(n_components=2).fit_transform(X)
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.2, 4.6))
for c in sorted(d["ward"].unique()):
    m = (d["ward"] == c).to_numpy()
    a1.scatter(scores[m, 0], scores[m, 1], s=26, alpha=0.85,
               color=CM.SERIES[(c - 1) % len(CM.SERIES)],
               label="cluster %d (n=%d)" % (c, m.sum()),
               edgecolor="white", linewidth=0.4)
a1.set_title("Ward clusters")
a1.legend(loc="best", fontsize=7.5)
for temp in CM.TEMP_ORDER:
    m = (d["Temperature"] == temp).to_numpy()
    a2.scatter(scores[m, 0], scores[m, 1], s=26, alpha=0.85,
               color=CM.TEMP_COLORS[temp],
               label="TVAR" if temp == "TVAR" else temp + " degC",
               edgecolor="white", linewidth=0.4)
a2.set_title("actual temperature regime")
a2.legend(loc="best", ncol=2, fontsize=7.5)
for a in (a1, a2):
    a.set_xlabel("PC1")
    a.set_ylabel("PC2")
    CM.despine(a)
rect = CM.titles(fig, "The clusters the data finds, against the design",
                 "Clusters vs strain ARI = %.3f; vs temperature ARI = %.3f; vs initial sugar ARI = %.3f"
                 % (ari.loc[0, "ARI_ward"], ari.loc[1, "ARI_ward"], ari.loc[2, "ARI_ward"]),
                 top=0.87)
fig.tight_layout(rect=rect)
CM.save(fig, "fig16_clusters_vs_design", "clusters in PC space vs temperature")

# fig17 - silhouette curve
fig, ax = plt.subplots(figsize=(6.4, 3.8))
ax.plot(sel["k"], sel["silhouette_ward"], "o-", color=CM.SERIES[0], label="Ward")
ax.plot(sel["k"], sel["silhouette_kmeans"], "s--", color=CM.SERIES[1], label="k-means")
ax.axvline(BEST_K, color=CM.INK3, ls=":", lw=1)
ax.set_xlabel("number of clusters k")
ax.set_ylabel("mean silhouette")
ax.legend()
CM.despine(ax)
rect = CM.titles(fig, "Choosing k",
                 "k chosen by silhouette, not set to 9 to match the 9 strains", top=0.86)
fig.tight_layout(rect=rect)
CM.save(fig, "fig17_silhouette_k", "silhouette vs k")

print("\nDone. Tables 07_*.csv and figures fig15-fig17 written.")
