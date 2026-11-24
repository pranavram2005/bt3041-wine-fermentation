"""
Step 5 - Hypothesis testing.

Research question framing: READING A - "do strains differ at a given
fermentation temperature?"  The EDA (log section 8d) found a real
strain x temperature interaction, so a pooled strain main effect averages the
effect away.  This script therefore does three things, in order:

  1. Assumption checks on model residuals (Shapiro-Wilk, Levene), raw vs log.
  2. A two-way ANOVA, Strain x Temperature + MS, WITH the interaction term -
     to test and report the interaction that justifies Reading A.
  3. The strain effect tested SEPARATELY within each temperature regime,
     parametric (ANOVA + Tukey HSD) and non-parametric (Kruskal-Wallis +
     Dunn), with Benjamini-Hochberg correction across the whole family and
     partial eta^2 / epsilon^2 effect sizes plus 95% CIs on group means.

Everything runs on the 216-row unit-level table.  The raw sheet's 1,944 rows
are 9 repeated samples of each fermentation and are NOT independent.
"""
import sys
import itertools
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.multitest import multipletests

sys.path.insert(0, str(Path(__file__).parent))
import common as CM

units = pd.read_csv(CM.TABLES / "02_unit_level_features.csv")
units["Temperature"] = pd.Categorical(units["Temperature"], CM.TEMP_ORDER, ordered=True)
units["MS"] = units["MS"].astype(int)

# ---------------------------------------------------------------------------
# The outcomes to test, and why.  Chosen from the descriptive variance scan
# (log section 8e): these are where a strain term actually exists.
# FinalEthanol is deliberately EXCLUDED - 0.4% strain, 76.7% initial sugar,
# so testing it across strains would just be testing the must, not the yeast.
# ---------------------------------------------------------------------------
OUTCOMES = {
    "MaxViable":          ("Peak viable cells (cells/mL)",             "log10"),
    "FinalSuccinate":     ("Final succinate (g/L)",                     None),
    "MalateConsumed":     ("Malate consumed (g/L)",                     None),
    "FinalAcetate":       ("Final acetate / volatile acidity (g/L)",    None),
    "FinalResidualSugar": ("Final residual sugar (g/L)",               "log1p"),
    "T90_h":              ("Time to 90% sugar consumption (h)",         None),
}

SCALE = {y: tr for y, (_, tr) in OUTCOMES.items()}


def transform(s, how):
    if how == "log10":
        return np.log10(s)
    if how == "log1p":
        return np.log1p(s)
    return s


def partial_eta_sq(tbl):
    """partial eta^2 = SS_effect / (SS_effect + SS_residual)."""
    ssr = tbl.loc["Residual", "sum_sq"]
    return {ix: tbl.loc[ix, "sum_sq"] / (tbl.loc[ix, "sum_sq"] + ssr)
            for ix in tbl.index if ix != "Residual"}


def welch_anova(groups):
    """Welch one-way ANOVA - the correct parametric test when group variances
    are unequal but residuals are normal.  Levene fails in most strain x temp
    cells here, and Kruskal-Wallis is NOT a remedy for heteroscedasticity
    (it assumes equal shape/spread too), so this is the test that actually
    fits those cells.  Returns (F, df1, df2, p).
    """
    n = np.array([len(g) for g in groups], float)
    m = np.array([g.mean() for g in groups], float)
    v = np.array([g.var(ddof=1) for g in groups], float)
    if np.any(v <= 0) or np.any(n < 2):
        # a group with zero variance makes the Welch weights infinite - this
        # really happens here (every 25 degC fermentation of some strains ends
        # at exactly 0 g/L residual sugar), so the test is undefined and the
        # caller falls back to Kruskal-Wallis.
        return np.nan, np.nan, np.nan, np.nan
    w = n / v
    sw = w.sum()
    mw = (w * m).sum() / sw
    k = len(groups)
    lam = ((1 - w / sw) ** 2 / (n - 1)).sum()
    A = (w * (m - mw) ** 2).sum() / (k - 1)
    B = 1 + (2 * (k - 2) / (k ** 2 - 1)) * lam
    F = A / B
    df2 = 1.0 / (3 * lam / (k ** 2 - 1))
    return F, k - 1, df2, stats.f.sf(F, k - 1, df2)


def dunn(d, group, value):
    """Dunn post-hoc after Kruskal-Wallis, with tie correction.

    Returns raw two-sided p-values; the correction is applied by the caller so
    these join the same Benjamini-Hochberg family as everything else.
    """
    d = d.dropna(subset=[value])
    N = len(d)
    r = stats.rankdata(d[value].to_numpy())
    _, counts = np.unique(d[value].to_numpy(), return_counts=True)
    ties = (counts ** 3 - counts).sum()
    sigma2 = (N * (N + 1) / 12.0) - ties / (12.0 * (N - 1))
    g = pd.DataFrame({"g": d[group].to_numpy(), "r": r}).groupby("g", observed=True)["r"]
    mean_r, n = g.mean(), g.count()
    out = []
    for a, b in itertools.combinations(list(mean_r.index), 2):
        se = np.sqrt(sigma2 * (1.0 / n[a] + 1.0 / n[b]))
        z = (mean_r[a] - mean_r[b]) / se
        out.append({"group1": a, "group2": b, "z": z,
                    "p_raw": 2 * stats.norm.sf(abs(z))})
    return pd.DataFrame(out)


# ===========================================================================
# 1. ASSUMPTION CHECKS - on the residuals of the full model, not raw values
# ===========================================================================
print("=" * 78)
print("1. ASSUMPTION CHECKS  (residuals of y ~ C(Strain)*C(Temperature) + C(MS))")
print("=" * 78)

assump = []
for y, (label, tr) in OUTCOMES.items():
    scales = [None] if tr is None else [None, tr]
    for how in scales:
        d = units.dropna(subset=[y]).copy()
        d["_y"] = transform(d[y], how)
        d = d[np.isfinite(d["_y"])]
        m = smf.ols("_y ~ C(Strain) * C(Temperature) + C(MS)", data=d).fit()
        sw_W, sw_p = stats.shapiro(m.resid)
        cells = [g["_y"].to_numpy() for _, g in
                 d.groupby(["Strain", "Temperature"], observed=True)]
        lv_W, lv_p = stats.levene(*cells, center="median")
        assump.append({
            "outcome": y, "scale": how or "raw", "n": len(d),
            "skew": stats.skew(d["_y"]), "resid_skew": stats.skew(m.resid),
            "shapiro_W": sw_W, "shapiro_p": sw_p,
            "levene_W": lv_W, "levene_p": lv_p,
            "normal_ok": sw_p > 0.05, "equalvar_ok": lv_p > 0.05,
        })
assump = pd.DataFrame(assump)
print(assump.round(4).to_string(index=False))
CM.dump(assump.round(6), "05_assumption_checks",
       "Shapiro-Wilk on residuals + Levene on strain x temp cells")
print("\nScale used downstream:", {k: (v or "raw") for k, v in SCALE.items()})

# ===========================================================================
# 2. TWO-WAY ANOVA with the interaction term
# ===========================================================================
print("\n" + "=" * 78)
print("2. TWO-WAY ANOVA   y ~ C(Strain)*C(Temperature) + C(MS),   type II SS")
print("=" * 78)

rows = []
for y, (label, _) in OUTCOMES.items():
    d = units.dropna(subset=[y]).copy()
    d["_y"] = transform(d[y], SCALE[y])
    d = d[np.isfinite(d["_y"])]
    m = smf.ols("_y ~ C(Strain) * C(Temperature) + C(MS)", data=d).fit()
    tbl = anova_lm(m, typ=2)
    eta = partial_eta_sq(tbl)
    for term in tbl.index:
        if term == "Residual":
            continue
        rows.append({
            "outcome": y, "scale": SCALE[y] or "raw", "n": len(d),
            "term": term.replace("C(", "").replace(")", ""),
            "df": tbl.loc[term, "df"], "F": tbl.loc[term, "F"],
            "p_raw": tbl.loc[term, "PR(>F)"], "partial_eta_sq": eta[term],
            "model_adj_R2": m.rsquared_adj,
        })
anova2 = pd.DataFrame(rows)
anova2["p_BH"] = multipletests(anova2["p_raw"], method="fdr_bh")[1]
anova2["signif"] = np.where(anova2["p_BH"] < 0.001, "***",
                   np.where(anova2["p_BH"] < 0.01, "**",
                   np.where(anova2["p_BH"] < 0.05, "*", "ns")))
print(anova2.round(4).to_string(index=False))
CM.dump(anova2.round(6), "05_twoway_anova",
       "type II SS, interaction included, BH-corrected")

inter = anova2[anova2["term"] == "Strain:Temperature"]
print("\nInteraction significant in %d of %d outcomes -> justifies Reading A "
      "(test strain WITHIN regime)." % ((inter["p_BH"] < 0.05).sum(), len(inter)))

# ===========================================================================
# 3. STRAIN EFFECT WITHIN EACH TEMPERATURE REGIME  (Reading A)
# ===========================================================================
print("\n" + "=" * 78)
print("3. STRAIN EFFECT WITHIN EACH REGIME  (parametric + non-parametric)")
print("=" * 78)

within, tukey_rows, dunn_rows = [], [], []
for y, (label, _) in OUTCOMES.items():
    for temp in CM.TEMP_ORDER:
        d = units[units["Temperature"] == temp].dropna(subset=[y]).copy()
        d["_y"] = transform(d[y], SCALE[y])
        d = d[np.isfinite(d["_y"])]
        if d["Strain"].nunique() < 2:
            continue

        # parametric: strain effect adjusted for initial sugar
        m = smf.ols("_y ~ C(Strain) + C(MS)", data=d).fit()
        tbl = anova_lm(m, typ=2)
        F = tbl.loc["C(Strain)", "F"]
        p_anova = tbl.loc["C(Strain)", "PR(>F)"]
        eta = partial_eta_sq(tbl)["C(Strain)"]

        # non-parametric: Kruskal-Wallis on strain (ignores MS - noted)
        groups = [g["_y"].to_numpy() for _, g in d.groupby("Strain", observed=True)]
        H, p_kw = stats.kruskal(*groups)
        k, N = len(groups), len(d)
        eps2 = (H - k + 1) / (N - k)          # epsilon^2 effect size

        # Welch one-way ANOVA - for normal residuals with unequal variances
        Fw, dfw1, dfw2, p_welch = welch_anova(groups)

        sw_p = stats.shapiro(m.resid)[1]
        lv_p = stats.levene(*groups, center="median")[1]

        # Test choice, decided from the assumptions, not from the p-values:
        #   normal + equal variance   -> classical ANOVA (and it adjusts for MS)
        #   normal + unequal variance -> Welch ANOVA
        #   non-normal                -> Kruskal-Wallis
        if sw_p <= 0.05:
            preferred = "Kruskal-Wallis"
        elif lv_p > 0.05:
            preferred = "ANOVA"
        elif np.isfinite(p_welch):
            preferred = "Welch ANOVA"
        else:
            preferred = "Kruskal-Wallis"   # Welch undefined (zero-variance group)

        within.append({
            "outcome": y, "temperature": temp, "n": N, "k_strains": k,
            "scale": SCALE[y] or "raw",
            "shapiro_p": sw_p, "levene_p": lv_p,
            "F_strain": F, "p_anova_raw": p_anova, "partial_eta_sq": eta,
            "F_welch": Fw, "df2_welch": dfw2, "p_welch_raw": p_welch,
            "H_kruskal": H, "p_kruskal_raw": p_kw, "epsilon_sq": eps2,
            "preferred": preferred,
        })

        th = pairwise_tukeyhsd(d["_y"], d["Strain"])
        tk = pd.DataFrame(th.summary().data[1:], columns=th.summary().data[0])
        tk.insert(0, "temperature", temp)
        tk.insert(0, "outcome", y)
        tukey_rows.append(tk)

        dn = dunn(d, "Strain", "_y")
        dn.insert(0, "temperature", temp)
        dn.insert(0, "outcome", y)
        dunn_rows.append(dn)

within = pd.DataFrame(within)
# ---- Benjamini-Hochberg across the whole family of 6 outcomes x 4 regimes
def bh(p):
    """Benjamini-Hochberg over the finite p-values only; NaN stays NaN.
    (One Welch test is undefined, and a single NaN would otherwise propagate
    through multipletests and blank the entire column.)"""
    p = pd.Series(p).astype(float)
    ok = p.notna()
    out = pd.Series(np.nan, index=p.index)
    out[ok] = multipletests(p[ok], method="fdr_bh")[1]
    return out.to_numpy()


within["p_anova_BH"] = bh(within["p_anova_raw"])
within["p_welch_BH"] = bh(within["p_welch_raw"])
within["p_kruskal_BH"] = bh(within["p_kruskal_raw"])
within["p_preferred_BH"] = np.select(
    [within["preferred"] == "ANOVA", within["preferred"] == "Welch ANOVA"],
    [within["p_anova_BH"], within["p_welch_BH"]],
    default=within["p_kruskal_BH"])
within["strain_effect"] = np.where(within["p_preferred_BH"] < 0.05,
                                   "significant", "not significant")
print("\nFamily size for BH correction: %d tests (%d outcomes x 4 regimes)\n"
      % (len(within), len(OUTCOMES)))
print(within.round(4).to_string(index=False))
CM.dump(within.round(6), "05_within_regime_strain_tests",
       "Reading A: strain effect per regime, BH-corrected, with effect sizes")

tukey = pd.concat(tukey_rows, ignore_index=True)
tukey.columns = [str(c) for c in tukey.columns]
CM.dump(tukey, "05_tukey_posthoc", "Tukey HSD, all strain pairs within regime")

dunn_all = pd.concat(dunn_rows, ignore_index=True)
dunn_all["p_BH"] = multipletests(dunn_all["p_raw"], method="fdr_bh")[1]
CM.dump(dunn_all.round(6), "05_dunn_posthoc",
       "Dunn post-hoc, BH-corrected across all pairs")

npairs = (tukey.assign(sig=lambda t: t["reject"].astype(bool))
          .groupby(["outcome", "temperature"], observed=True)["sig"].sum()
          .rename("tukey_pairs_sig").reset_index())
print("\nSignificant strain pairs (Tukey, of 36 possible per cell):")
print(npairs.pivot(index="outcome", columns="temperature",
                   values="tukey_pairs_sig").reindex(columns=CM.TEMP_ORDER).to_string())

summary = within.merge(npairs, on=["outcome", "temperature"], how="left")
CM.dump(summary.round(6), "05_results_table",
       "THE statistical results table the brief asks for")

# ===========================================================================
# 4. GROUP MEANS WITH 95% CONFIDENCE INTERVALS
# ===========================================================================
ci_rows = []
for y in OUTCOMES:
    for temp in CM.TEMP_ORDER:
        d = units[units["Temperature"] == temp].dropna(subset=[y])
        for strain, g in d.groupby("Strain", observed=True):
            v = g[y].to_numpy()
            n = len(v)
            se = v.std(ddof=1) / np.sqrt(n) if n > 1 else np.nan
            h = se * stats.t.ppf(0.975, n - 1) if n > 1 else np.nan
            ci_rows.append({"outcome": y, "temperature": temp, "strain": strain,
                            "n": n, "mean": v.mean(), "sd": v.std(ddof=1),
                            "ci95_low": v.mean() - h, "ci95_high": v.mean() + h})
ci = pd.DataFrame(ci_rows)
CM.dump(ci.round(4), "05_group_means_ci",
       "strain means with 95% CI, per outcome per regime")

# ===========================================================================
# FIGURES
# ===========================================================================
piv = (anova2.pivot(index="outcome", columns="term", values="partial_eta_sq")
       .reindex(columns=["Temperature", "Strain", "MS", "Strain:Temperature"])
       .rename(columns={"MS": "Initial sugar", "Strain:Temperature": "Strain x Temp"}))
piv = piv.loc[piv["Strain"].sort_values().index] * 100
fig, ax = plt.subplots(figsize=(8.2, 4.4))
ypos = np.arange(len(piv))
hh = 0.2
for i, col in enumerate(piv.columns):
    ax.barh(ypos + (1.5 - i) * hh, piv[col], height=hh, label=col,
            color=CM.SERIES[i], edgecolor="none")
ax.set_yticks(ypos, piv.index)
ax.set_xlabel("partial $\\eta^2$  (%)")
ax.set_xlim(0, piv.to_numpy().max() * 1.04)
# legend below the axes - at "lower right" it sat on top of the shortest bars
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=4)
CM.despine(ax)
rect = CM.titles(fig, "Two-way ANOVA: variance explained by each term",
                "Type II SS, y ~ Strain x Temperature + initial sugar, n = 216 fermentations",
                top=0.88)
fig.tight_layout(rect=rect)
CM.save(fig, "fig09_anova_partial_eta2", "partial eta^2 per ANOVA term")

for y, tag in [("MaxViable", "fig10_maxviable_by_strain_regime"),
               ("FinalSuccinate", "fig11_succinate_by_strain_regime")]:
    sub = ci[ci["outcome"] == y]
    fig, axes = plt.subplots(1, 4, figsize=(11.5, 3.8))
    for ax, temp in zip(axes, CM.TEMP_ORDER):
        s = sub[sub["temperature"] == temp].sort_values("mean")
        ax.errorbar(s["mean"], np.arange(len(s)),
                    xerr=[s["mean"] - s["ci95_low"], s["ci95_high"] - s["mean"]],
                    fmt="o", color=CM.TEMP_COLORS[temp], ecolor=CM.INK3,
                    elinewidth=1.0, capsize=2.5)
        ax.set_yticks(np.arange(len(s)), s["strain"])
        ax.set_title("12 degC" if temp == "12" else
                     ("TVAR" if temp == "TVAR" else temp + " degC"))
        ax.set_xlabel(OUTCOMES[y][0])
        CM.despine(ax)
    rect = CM.titles(fig, y + ": strain means with 95% CI, within each regime",
                    "Strains are re-sorted in every panel - the re-ordering IS the interaction",
                    top=0.84)
    fig.tight_layout(rect=rect)
    CM.save(fig, tag, y + " strain means per regime")

print("\nDone. Tables 05_*.csv and figures fig09-fig11 written.")
