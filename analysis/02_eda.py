"""
Step 2 - Exploratory data analysis.

Deliverables required by the project brief, section 4 (EDA):
  * means / medians / SD / min / max
  * distributions of the measurements
  * change over time
  * distributions compared across strains
  * correlations between numerical variables

It also builds the UNIT-LEVEL table (one row per fermentation, 216 rows) that
later hypothesis testing, PCA and clustering should use, because the raw sheet
is repeated-measures and its rows are not independent.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

sys.path.insert(0, str(Path(__file__).parent))
import common as C

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 100)

df = C.load()
print(f"loaded {df.shape[0]} observations, {df.Unit.nunique()} fermentation units\n")

KEY = ["ResidualSugar", "Ethanol", "Glycerol", "Acetate", "Malate",
       "Succinate", "Citrate", "Viable", "Total", "Viability"]


# =============================================================== 1. DESCRIPTIVES
print("1. DESCRIPTIVE STATISTICS")

num = [c for c in C.MEASURED if c in df.columns] + \
      ["ResidualSugar", "SugarConsumed", "FracFermented", "Viability"]
desc = df[num].describe().T[["count", "mean", "50%", "std", "min", "max"]]
desc.columns = ["N", "Mean", "Median", "SD", "Min", "Max"]
desc.insert(0, "Unit", [C.UNITS.get(v, "") for v in desc.index])
desc.insert(1, "Block", [next((b for b, vs in C.BLOCKS.items() if v in vs), "Derived")
                         for v in desc.index])
desc["CV_%"] = (100 * desc.SD / desc.Mean.replace(0, np.nan))
C.dump(desc.round(3), "02_descriptives_all_timepoints",
       "pooled over time - for scale/skew only, NOT for comparisons")

# descriptives at the endpoint only (t8): one value per fermentation unit
end = df[df.Time_name == "t8"].copy()
by_strain = end.groupby("Strain", observed=True)[KEY].agg(["mean", "std"]).round(3)
C.dump(by_strain, "02_endpoint_by_strain", "t8, n=24 units per strain")

print("   final-sample (t8) means by strain:")
print(end.groupby("Strain", observed=True)[
    ["ResidualSugar", "Ethanol", "Glycerol", "Acetate", "Viability"]
].mean().round(2).to_string())


# ========================================================= 2. UNIT-LEVEL TABLE
print("\n2. UNIT-LEVEL FEATURE TABLE (the analysis-ready table)")


def time_to_fraction(g, frac):
    """Clock time at which `frac` of the initial sugar has been consumed.

    Linear interpolation on the cumulative-maximum of FracFermented, so the
    flagged non-monotonic early samples cannot drag the curve backwards.
    Returns NaN if the fermentation never reaches `frac`.
    """
    g = g.sort_values("Time")
    y = g["FracFermented"].cummax().to_numpy()
    t = g["Time"].to_numpy()
    if not np.isfinite(y).any() or np.nanmax(y) < frac:
        return np.nan
    i = int(np.argmax(y >= frac))
    if i == 0:
        return float(t[0])
    y0, y1, t0_, t1_ = y[i - 1], y[i], t[i - 1], t[i]
    if y1 == y0:
        return float(t1_)
    return float(t0_ + (frac - y0) * (t1_ - t0_) / (y1 - y0))


recs = []
for u, g in df.groupby("Unit", observed=True):
    g = g.sort_values("Time")
    last = g.iloc[-1]
    # mean fermentation rate over the steepest measured interval (g/L/h)
    dsug = g["ResidualSugar"].cummin().diff().to_numpy()[1:]
    dt = g["Time"].diff().to_numpy()[1:]
    rate = np.where(dt > 0, -dsug / dt, np.nan)
    recs.append({
        "Unit": u,
        "Strain": last["Strain"], "Temperature": last["Temperature"],
        "MS": last["MS"], "Rep": last["Rep"],
        "InitialSugar": last["InitialSugar"],
        "FinalResidualSugar": last["ResidualSugar"],
        "SugarConsumedTotal": last["SugarConsumed"],
        "FracFermentedFinal": last["FracFermented"],
        "Dry": int(last["ResidualSugar"] < 2.0),       # <2 g/L = "dry" wine
        "FinalEthanol": last["Ethanol"],
        "EthanolYield_pct_per_gL": 100 * last["Ethanol"] / last["SugarConsumed"]
                                   if last["SugarConsumed"] > 0 else np.nan,
        "FinalGlycerol": last["Glycerol"],
        "FinalAcetate": last["Acetate"],
        "FinalSuccinate": last["Succinate"],
        "MalateConsumed": g.iloc[0]["Malate"] - last["Malate"],
        "T_total_h": last["Time"],
        "T50_h": time_to_fraction(g, 0.50),
        "T90_h": time_to_fraction(g, 0.90),
        "MaxRate_gL_h": np.nanmax(rate) if np.isfinite(rate).any() else np.nan,
        "MaxViable": g["Viable"].max(),
        "FinalViability": last["Viability"],
    })
units = pd.DataFrame(recs)
units["Strain"] = pd.Categorical(units["Strain"], df.Strain.cat.categories)
units["Temperature"] = pd.Categorical(units["Temperature"], C.TEMP_ORDER, ordered=True)
C.dump(units.set_index("Unit"), "02_unit_level_features",
       f"{len(units)} fermentation units x {units.shape[1] - 1} features")

print(f"   built {len(units)} units; {units.Dry.sum()} finished dry (<2 g/L residual)")
print("\n   fermentation kinetics by strain (mean over all 24 fermentations each):")
ks = units.groupby("Strain", observed=True)[
    ["T50_h", "T90_h", "MaxRate_gL_h", "FinalResidualSugar", "FinalEthanol", "Dry"]
].mean().round(2)
ks["Dry"] = (100 * ks["Dry"]).round(0).astype(int)
ks = ks.rename(columns={"Dry": "Pct_dry"})
print(ks.to_string())
C.dump(ks, "02_kinetics_by_strain")

print("\n   kinetics by temperature regime:")
kt = units.groupby("Temperature", observed=True)[
    ["T50_h", "T90_h", "MaxRate_gL_h", "FinalResidualSugar", "FinalEthanol"]
].mean().round(2)
print(kt.to_string())
C.dump(kt, "02_kinetics_by_temperature")

# variance decomposition: how much spread comes from strain vs temperature?
print("\n   spread of T90_h: SD between temperature means =",
      round(units.groupby("Temperature", observed=True).T90_h.mean().std(), 1), "h;",
      "SD between strain means =",
      round(units.groupby("Strain", observed=True).T90_h.mean().std(), 1), "h")


# ========================================== FIG 1 - fermentation progress
print("\n3. FIGURES")

fig, axes = plt.subplots(3, 3, figsize=(11, 9), sharex=True, sharey=True)
for ax, s in zip(axes.flat, df.Strain.cat.categories):
    sub = df[df.Strain == s]
    for temp in C.TEMP_ORDER:
        g = sub[sub.Temperature == temp]
        m = g.groupby("Time_name", observed=True).agg(
            t=("Time", "mean"), y=("ResidualSugar", "mean"))
        ax.plot(m.t, m.y, color=C.TEMP_COLORS[temp], lw=2,
                marker="o", ms=3.5, mec=C.SURFACE, mew=0.8, label=temp)
    ax.set_title(s)
    ax.set_xlim(-20, 920)
    C.despine(ax)
for ax in axes[-1]:
    ax.set_xlabel("Fermentation time (h)")
for ax in axes[:, 0]:
    ax.set_ylabel("Residual sugar (g/L)")
# Legend carries identity; the companion table 02_kinetics_by_temperature.csv is
# the relief for the two light-mode slots that sit below 3:1 contrast.
fig.legend(handles=[Line2D([], [], color=C.TEMP_COLORS[t], lw=2, label=f"{t} °C"
                           if t != "TVAR" else "TVAR (variable)")
                    for t in C.TEMP_ORDER],
           loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.015))
rect = C.titles(fig, "Sugar consumption over time, by strain and temperature regime",
                "Mean of 3 replicates x 2 initial-sugar levels. The x-axis is clock "
                "time, not sampling index: every panel ends when that strain's "
                "fermentation did.", top=0.925)
rect[1] = 0.035
fig.tight_layout(rect=rect)
C.save(fig, "fig01_sugar_curves_by_strain", "small multiples: 9 strains")


# ========================================== FIG 2 - distributions of key vars
fig, axes = plt.subplots(2, 4, figsize=(12, 5.5))
dist_vars = ["ResidualSugar", "Ethanol", "Glycerol", "Acetate",
             "Succinate", "Malate", "Viable", "Viability"]
LOGVARS = ("Viable", "Dead", "Total")
for ax, v in zip(axes.flat, dist_vars):
    x = df[v].dropna()
    if v in LOGVARS:                      # log-spaced bins, or a log axis lies
        x = x[x > 0]
        bins = np.logspace(np.log10(x.min()), np.log10(x.max()), 40)
        ax.set_xscale("log")
    else:
        bins = 40
    ax.hist(x, bins=bins, color=C.SEQ_HUE, edgecolor=C.SURFACE, linewidth=0.4)
    ax.axvline(x.median(), color=C.INK, lw=1.2, ls="--")
    ax.set_title(f"{v}", fontsize=9)
    ax.set_xlabel(C.UNITS.get(v, ""), fontsize=8)
    ax.set_ylabel("count", fontsize=8)
    ax.annotate(f"median {x.median():,.3g}\nskew {x.skew():+.1f}",
                (0.97, 0.96), xycoords="axes fraction", ha="right", va="top",
                fontsize=7.5, color=C.INK2,
                bbox=dict(fc=C.SURFACE, ec="none", alpha=0.82, pad=1.5))
    C.despine(ax)
rect = C.titles(fig, "Distributions of the main fermentation variables",
                "All 1944 samples pooled over time, so most are strongly skewed or "
                "bimodal by fermentation stage - that is a property of the sampling "
                "design, not of the strains. Dashed line = median.", top=0.885)
fig.tight_layout(rect=rect)
C.save(fig, "fig02_distributions")


# ================================= FIG 3 - endpoint distribution across strains
fig, axes = plt.subplots(1, 3, figsize=(12, 4.6))
panel = [("FinalResidualSugar", "Residual sugar at final sample (g/L)"),
         ("FinalEthanol", "Final ethanol (% v/v)"),
         ("T90_h", "Time to 90 % sugar consumption (h)")]
order = units.groupby("Strain", observed=True).T90_h.mean().sort_values().index
for ax, (v, lab) in zip(axes, panel):
    data = [units.loc[units.Strain == s, v].dropna().to_numpy() for s in order]
    bp = ax.boxplot(data, vert=False, widths=0.6, patch_artist=True,
                    medianprops=dict(color=C.INK, lw=1.6),
                    whiskerprops=dict(color=C.INK3, lw=1),
                    capprops=dict(color=C.INK3, lw=1),
                    flierprops=dict(marker="o", ms=3, mfc=C.INK3, mec="none", alpha=.7))
    for b in bp["boxes"]:
        b.set(facecolor=C.SEQ_HUE, alpha=0.30, edgecolor=C.SEQ_HUE, linewidth=1.2)
    for i, d in enumerate(data, start=1):
        ax.plot(d, np.full_like(d, i) + np.random.default_rng(0).uniform(-.13, .13, len(d)),
                "o", ms=2.6, mfc=C.SEQ_HUE, mec="none", alpha=.55)
    ax.set_yticks(range(1, len(order) + 1))
    ax.set_yticklabels(order)
    ax.set_xlabel(lab)
    ax.grid(axis="y", visible=False)
    C.despine(ax)
axes[0].set_ylabel("Strain  (ordered by mean time to 90 %)")
rect = C.titles(fig, "Endpoint and kinetic outcomes across the 9 strains",
                "One point per fermentation unit (n = 24 per strain: 4 temperature "
                "regimes x 2 sugar levels x 3 replicates). The spread within a strain "
                "is dominated by temperature, so these box plots pool very different "
                "conditions - they are a first look, not a strain comparison.",
                top=0.86)
fig.tight_layout(rect=rect)
C.save(fig, "fig03_endpoint_by_strain")


# ======================== FIG 4 - strain x temperature interaction (faceted)
# NOTE: deliberately NOT sharey - each panel is sorted independently and must
# show its own strain labels, otherwise the re-ordering is invisible.
fig, axes = plt.subplots(1, 4, figsize=(13.5, 4.4))
for ax, temp in zip(axes, C.TEMP_ORDER):
    sub = units[units.Temperature == temp]
    m = sub.groupby("Strain", observed=True).T90_h.agg(["mean", "std", "count"])
    m = m.sort_values("mean", ascending=False)
    sem = m["std"] / np.sqrt(m["count"])
    ax.barh(range(len(m)), m["mean"], xerr=sem,
            color=C.TEMP_COLORS[temp], height=0.72,
            error_kw=dict(ecolor=C.INK3, lw=1, capsize=2))
    ax.set_yticks(range(len(m)))
    ax.set_yticklabels(m.index, fontsize=8.5)
    ax.set_title(f"{temp} °C" if temp != "TVAR" else "TVAR (variable)")
    ax.set_xlabel("Time to 90 % sugar consumed (h)")
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, (m["mean"] + sem).max() * 1.26)
    for i, (v, e) in enumerate(zip(m["mean"], sem)):
        ax.annotate(f"{v:.0f}", (v + e, i), xytext=(5, 0),
                    textcoords="offset points", va="center", fontsize=7.5,
                    color=C.INK2)
    C.despine(ax)
rect = C.titles(fig, "Strain ranking is not stable across temperature regimes",
                "Mean ± SEM of 6 fermentations per strain per regime; fastest at the "
                "top. Each panel is sorted independently and has its own x-scale — "
                "compare the label orders, not the bar lengths.", top=0.88)
fig.tight_layout(rect=rect)
C.save(fig, "fig04_strain_x_temperature")


# ============================ FIG 7 - rank bump chart (the interaction, directly)
ranks = (units.pivot_table(index="Strain", columns="Temperature",
                           values="T90_h", aggfunc="mean", observed=True)
              .rank())
movers = (ranks.max(axis=1) - ranks.min(axis=1)).sort_values(ascending=False)
hilite = dict(zip(movers.index[:3], C.SERIES[:3]))   # 3 slots validate all-pairs

fig, ax = plt.subplots(figsize=(8.2, 5.2))
xs = np.arange(len(C.TEMP_ORDER))
for s in ranks.index:
    y = ranks.loc[s, C.TEMP_ORDER].to_numpy()
    col = hilite.get(s, "#c9c8c2")
    z = 3 if s in hilite else 1
    ax.plot(xs, y, color=col, lw=2.4 if s in hilite else 1.4, zorder=z,
            marker="o", ms=8 if s in hilite else 6, mec=C.SURFACE, mew=1.5,
            alpha=1.0 if s in hilite else 0.85)
    ax.annotate(s, (xs[0], y[0]), xytext=(-8, 0), textcoords="offset points",
                ha="right", va="center", fontsize=8,
                color=col if s in hilite else C.INK3,
                fontweight="bold" if s in hilite else "normal", zorder=z)
    ax.annotate(s, (xs[-1], y[-1]), xytext=(8, 0), textcoords="offset points",
                ha="left", va="center", fontsize=8,
                color=col if s in hilite else C.INK3,
                fontweight="bold" if s in hilite else "normal", zorder=z)
ax.set_xticks(xs)
ax.set_xticklabels([f"{t} °C" if t != "TVAR" else "TVAR" for t in C.TEMP_ORDER])
ax.set_yticks(range(1, 10))
ax.set_ylabel("Rank by time to 90 % sugar consumed  (1 = fastest)")
ax.invert_yaxis()
ax.set_xlim(-0.65, len(xs) - 0.35)
ax.grid(axis="x", visible=False)
C.despine(ax)
rect = C.titles(fig, "No strain is fastest everywhere",
                "Each line is one strain's speed rank across the four temperature "
                "regimes. The three strains that move most are\nhighlighted; the rest "
                "are grey. Lines crossing = strain x temperature interaction.",
                top=0.88)
fig.tight_layout(rect=rect)
C.save(fig, "fig07_rank_bump")
C.dump(ranks.round(1), "02_strain_rank_by_temperature", "rank of T90_h, 1 = fastest")
print("   rank range per strain (max-min across regimes):",
      {k: int(v) for k, v in movers.items()})
print("   Spearman between regime rankings:\n",
      ranks.corr(method="spearman").round(2).to_string())


# ======================================= FIG 5 - growth & viability over time
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
for temp in C.TEMP_ORDER:
    g = df[df.Temperature == temp].groupby("Time_name", observed=True).agg(
        t=("Time", "mean"), v=("Viable", "mean"), vi=("Viability", "mean"))
    axes[0].plot(g.t, g.v, color=C.TEMP_COLORS[temp], lw=2, marker="o", ms=4,
                 mec=C.SURFACE, mew=.8, label=temp)
    axes[1].plot(g.t, g.vi, color=C.TEMP_COLORS[temp], lw=2, marker="o", ms=4,
                 mec=C.SURFACE, mew=.8, label=temp)
    axes[0].annotate(temp, (g.t.iloc[-1], g.v.iloc[-1]), xytext=(4, 0),
                     textcoords="offset points", color=C.TEMP_COLORS[temp],
                     fontsize=7.5, fontweight="bold", va="center")
    axes[1].annotate(temp, (g.t.iloc[-1], g.vi.iloc[-1]), xytext=(4, 0),
                     textcoords="offset points", color=C.TEMP_COLORS[temp],
                     fontsize=7.5, fontweight="bold", va="center")
axes[0].set_yscale("log")
axes[0].set_ylabel("Viable cells (cells/mL, log scale)")
axes[1].set_ylabel("Viability (% of total cells)")
for ax in axes:
    ax.set_xlabel("Fermentation time (h)")
    ax.set_xlim(-20, 800)
    C.despine(ax)
axes[0].set_title("Growth")
axes[1].set_title("Viability")
rect = C.titles(fig, "Yeast population dynamics by temperature regime",
                "Mean of all 9 strains x 2 sugar levels x 3 replicates. Viability "
                "starts near 33 % because the inoculum is rehydrated active dry yeast.",
                top=0.87)
fig.tight_layout(rect=rect)
C.save(fig, "fig05_growth_viability")


# ================================================= FIG 6 - correlation heatmap
corr_vars = ["ResidualSugar", "SugarConsumed", "Ethanol", "Glycerol", "Acetate",
             "Citrate", "Malate", "Succinate", "Viable", "Dead", "Total",
             "Viability", "NH4Cl", "Arginine", "Proline", "Alanine",
             "IsoamylAlcohol", "Isobutanol", "PhenEtoh", "EthAcetate"]
corr_vars = [v for v in corr_vars if v in df.columns]
cm = df[corr_vars].corr(method="spearman")

div = LinearSegmentedColormap.from_list(
    "blue_gray_red", ["#104281", "#2a78d6", "#9ec5f4", "#f0efec",
                      "#f0a6a5", "#e34948", "#9e2423"])
fig, ax = plt.subplots(figsize=(8.6, 7.6))
im = ax.imshow(cm, cmap=div, norm=TwoSlopeNorm(vmin=-1, vcenter=0, vmax=1))
ax.set_xticks(range(len(corr_vars)))
ax.set_xticklabels(corr_vars, rotation=90, fontsize=8)
ax.set_yticks(range(len(corr_vars)))
ax.set_yticklabels(corr_vars, fontsize=8)
ax.grid(False)
for i in range(len(corr_vars)):
    for j in range(len(corr_vars)):
        v = cm.iloc[i, j]
        if abs(v) >= 0.55:
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6.2,
                    color=C.SURFACE if abs(v) > 0.8 else C.INK)
cb = fig.colorbar(im, ax=ax, shrink=0.72, pad=0.02)
cb.set_label("Spearman ρ", color=C.INK2)
cb.outline.set_visible(False)
rect = C.titles(fig, "Correlation structure of the fermentation variables",
                "Spearman ρ on all samples pooled; labels shown for |ρ| ≥ 0.55. Most "
                "of this correlation is driven by fermentation\nstage - everything "
                "moves together as sugar is consumed - not by differences between "
                "strains.", top=0.90)
fig.tight_layout(rect=rect)
C.save(fig, "fig06_correlation_heatmap")
C.dump(cm.round(3), "02_spearman_correlations")

strong = (cm.where(~np.eye(len(cm), dtype=bool)).stack()
            .sort_values(key=abs, ascending=False))
seen, top = set(), []
for (a, b), v in strong.items():
    if (b, a) in seen:
        continue
    seen.add((a, b))
    top.append((a, b, round(v, 3)))
print("\n   strongest correlations:")
for a, b, v in top[:10]:
    print(f"     {a:16s} {b:16s} rho = {v:+.3f}")

print("\nDone. Tables in outputs/tables/, figures in outputs/figures/")
