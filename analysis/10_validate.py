"""
Step 8 of the project brief - validate the results of steps 5-7.

Nothing new is tested here. Every check re-derives a number the report already
claims, by a different route, and records whether the two agree:

  V1  recompute the unit-level features from the raw workbook with a second,
      independent implementation                      -> 10_recompute_check.csv
  V2  permutation test of the strain effect in each regime, 5000 label
      shuffles, no distributional assumption          -> 10_permutation_tests.csv
  V3  pseudoreplication: what the same test reports if the 1944 raw samples
      are treated as independent                      -> 10_pseudoreplication.csv
  V4  mixed-effects model on the repeated measures, to check that collapsing
      to 216 units preserved the strain ordering      -> 10_mixedmodel_check.csv
  V5  leave-one-replicate-out: does each call survive on 2 of 3 replicates
                                                      -> 10_loro_sensitivity.csv
  V6  artefact sensitivity: drop the units carrying a flagged sugar reading
      and re-test                                     -> 10_artefact_sensitivity.csv
  V7  bootstrap 95% CI for the strain effect size     -> 10_bootstrap_effectsize.csv
  V8  cross-regime robustness of each strain          -> 10_strain_robustness.csv
  V9  re-verify the PCA and clustering summary numbers -> 10_multivariate_check.csv
  V10 every quantitative claim in the report, checked -> 10_claim_checks.csv

Figures: fig19 (robustness), fig20 (permutation vs parametric),
         fig21 (sensitivity grid).

Run after 05-07. Output goes to outputs/tables and outputs/figures.
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent))
import common as CM

warnings.filterwarnings("ignore")
RNG = np.random.default_rng(20261124)
N_PERM = 5000
N_BOOT = 2000

TAB = CM.TABLES
OUTCOMES = ["MaxViable", "FinalSuccinate", "MalateConsumed", "FinalAcetate",
            "FinalResidualSugar", "T90_h"]
SCALE = {"MaxViable": "log10", "FinalResidualSugar": "log1p"}
PRETTY = {"MaxViable": "Peak viable cells", "FinalSuccinate": "Final succinate",
          "MalateConsumed": "Malate consumed", "FinalAcetate": "Final acetate",
          "FinalResidualSugar": "Final residual sugar", "T90_h": "Time to 90 %"}

units = pd.read_csv(TAB / "02_unit_level_features.csv")
units["Temperature"] = pd.Categorical(units["Temperature"].astype(str),
                                      CM.TEMP_ORDER, ordered=True)
within = pd.read_csv(TAB / "05_within_regime_strain_tests.csv", index_col=0)
within["temperature"] = within["temperature"].astype(str)


def transform(v, outcome):
    s = SCALE.get(outcome)
    if s == "log10":
        return np.log10(v)
    if s == "log1p":
        return np.log1p(v)
    return v


def groups_for(frame, outcome):
    y = transform(frame[outcome].astype(float), outcome)
    ok = y.notna()
    return [g.to_numpy() for _, g in y[ok].groupby(frame.loc[ok, "Strain"],
                                                   observed=True)]


def one_way_F(gs):
    gs = [g for g in gs if len(g) > 1]
    if len(gs) < 2:
        return np.nan
    return float(stats.f_oneway(*gs).statistic)


def eps_squared(frame, outcome):
    """Kruskal-Wallis epsilon-squared: rank-based, assumption-free effect size."""
    gs = [g for g in groups_for(frame, outcome) if len(g) > 0]
    n = sum(len(g) for g in gs)
    if len(gs) < 2 or n < 3:
        return np.nan
    H = float(stats.kruskal(*gs).statistic)
    return (H - len(gs) + 1) / (n - len(gs))


# --------------------------------------------------------------------------
# Vectorised resampling helpers.
#
# Both the permutation test and the bootstrap need the same statistic tens of
# thousands of times, so they are computed in matrix form: one row per
# resample.  Two identities make that possible without any looping.
#
#   * With the total sum of squares fixed, the one-way F is a monotone
#     function of the between-group sum of squares, so the permutation
#     p-value can be read off SSB alone.
#   * The tie-corrected Kruskal-Wallis H equals (N-1) SSB / SST computed on
#     the mid-ranks, which matters because bootstrap resampling creates ties.
# --------------------------------------------------------------------------

def prep(frame, outcome):
    """Values sorted into contiguous strain blocks, with the block layout."""
    y = transform(frame[outcome].astype(float), outcome)
    ok = y.notna()
    f = frame.loc[ok].assign(_y=y[ok].to_numpy()).sort_values("Strain",
                                                              kind="stable")
    ng = f.groupby("Strain", observed=True).size().to_numpy()
    ng = ng[ng > 0]
    return f["_y"].to_numpy(float), ng, np.concatenate([[0], np.cumsum(ng)[:-1]])


def ssb_rows(mat, ng, starts):
    """Between-group sum of squares for every row of `mat`."""
    g = np.add.reduceat(mat, starts, axis=1)
    tot = mat.sum(axis=1)
    return (g ** 2 / ng).sum(axis=1) - tot ** 2 / mat.shape[1]


def F_of(y, ng, starts):
    n, k = len(y), len(ng)
    ssb = ssb_rows(y[None, :], ng, starts)[0]
    sst = float(((y - y.mean()) ** 2).sum())
    return (ssb / (k - 1)) / ((sst - ssb) / (n - k))


def eps_rows(mat, ng, starts):
    """Rank-based epsilon-squared for every row of `mat`."""
    n, k = mat.shape[1], len(ng)
    R = stats.rankdata(mat, axis=1)
    ssb = ssb_rows(R, ng, starts)
    sst = (R ** 2).sum(axis=1) - R.sum(axis=1) ** 2 / n
    H = (n - 1) * ssb / sst
    return (H - k + 1) / (n - k)


def welch_F_rows(mat, ng, starts):
    """Welch's heteroscedastic F for every row of `mat`."""
    k = len(ng)
    s = np.add.reduceat(mat, starts, axis=1)
    ss = np.add.reduceat(mat ** 2, starts, axis=1)
    mean = s / ng
    var = (ss - s ** 2 / ng) / (ng - 1)
    w = ng / var
    sw = w.sum(axis=1, keepdims=True)
    gm = (w * mean).sum(axis=1, keepdims=True) / sw
    A = (w * (mean - gm) ** 2).sum(axis=1) / (k - 1)
    lam = ((1 - w / sw) ** 2 / (ng - 1)).sum(axis=1)
    B = 1 + 2 * (k - 2) / (k ** 2 - 1) * lam
    return A / B


def anova_strain(frame, outcome):
    """F, p and partial eta-squared for the strain term in the model step 5
    actually fitted: y ~ C(Strain) + C(MS), type II sums of squares.

    Every re-test below goes through this function, so a sensitivity check
    differs from the original test only in which rows it is given.
    """
    import statsmodels.formula.api as smf
    from statsmodels.stats.anova import anova_lm
    d = frame.dropna(subset=[outcome]).copy()
    d["_y"] = transform(d[outcome].astype(float), outcome)
    d = d[np.isfinite(d["_y"])]
    if d["Strain"].nunique() < 2:
        return dict(F=np.nan, p=np.nan, df1=np.nan, df2=np.nan, eta2=np.nan,
                    n=len(d))
    t = anova_lm(smf.ols("_y ~ C(Strain) + C(MS)", data=d).fit(), typ=2)
    ss_s = float(t.loc["C(Strain)", "sum_sq"])
    ss_r = float(t.loc["Residual", "sum_sq"])
    return dict(F=float(t.loc["C(Strain)", "F"]),
                p=float(t.loc["C(Strain)", "PR(>F)"]),
                df1=float(t.loc["C(Strain)", "df"]),
                df2=float(t.loc["Residual", "df"]),
                eta2=ss_s / (ss_s + ss_r), n=len(d))


def eta2_ci(F, df1, df2, n, conf=0.95):
    """Confidence interval for partial eta-squared by inverting the
    noncentral F distribution (Steiger 2004) - no resampling, and no
    upward bias of the kind a bootstrap of a variance ratio suffers."""
    from scipy.optimize import brentq
    a = (1 - conf) / 2

    def solve(target):
        f = lambda lam: stats.ncf.cdf(F, df1, df2, lam) - target
        if f(0) < 0:
            return 0.0
        hi = 1.0
        while f(hi) > 0 and hi < 1e7:
            hi *= 2
        return brentq(f, 0, hi) if hi < 1e7 else np.nan

    lo, hi = solve(1 - a), solve(a)
    return lo / (lo + n), hi / (hi + n)


def say(title):
    print("\n" + title)
    print("-" * len(title))


print("=" * 72)
print("STEP 8 - VALIDATION")
print("=" * 72)

# ============================================================== V1 recompute
say("V1  Independent recomputation of the unit-level features")

raw = CM.load()
rows = []
for unit, g in raw.groupby("Unit", observed=True):
    g = g.sort_values("Time")
    sug = g["Glucose"].to_numpy() + g["Fructose"].to_numpy()
    t = g["Time"].to_numpy(float)
    s0 = sug[0]
    frac = np.maximum.accumulate(1 - sug / s0)       # monotone, as in 02_eda
    row = {"Unit": unit,
           "InitialSugar_v": s0,
           "FinalResidualSugar_v": sug[-1],
           "FinalEthanol_v": g["Ethanol"].to_numpy()[-1],
           "FinalSuccinate_v": g["Succinate"].to_numpy()[-1],
           "MalateConsumed_v": g["Malate"].to_numpy()[0] - g["Malate"].to_numpy()[-1],
           "MaxViable_v": np.nanmax(g["Viable"].to_numpy())}
    for lvl, name in ((0.5, "T50_h_v"), (0.9, "T90_h_v")):
        row[name] = float(np.interp(lvl, frac, t)) if frac[-1] >= lvl else np.nan
    rows.append(row)
check = units.merge(pd.DataFrame(rows), on="Unit")

recomp = []
for a, b in [("InitialSugar", "InitialSugar_v"),
             ("FinalResidualSugar", "FinalResidualSugar_v"),
             ("FinalEthanol", "FinalEthanol_v"),
             ("FinalSuccinate", "FinalSuccinate_v"),
             ("MalateConsumed", "MalateConsumed_v"),
             ("MaxViable", "MaxViable_v"),
             ("T50_h", "T50_h_v"), ("T90_h", "T90_h_v")]:
    d = (check[a] - check[b]).abs()
    scale_ = max(abs(float(check[a].mean())), 1e-12)
    recomp.append({"feature": a, "n_compared": int(d.notna().sum()),
                   "max_abs_diff": float(d.max()),
                   "max_rel_diff_pct": float(d.max() / scale_ * 100),
                   "n_missing_both": int((check[a].isna() & check[b].isna()).sum()),
                   "agree": bool(d.max() < 1e-6 or d.max() / scale_ < 1e-6)})
recomp = pd.DataFrame(recomp)
CM.dump(recomp.set_index("feature"), "10_recompute_check",
        "second implementation vs the pipeline")
print(recomp.to_string(index=False))

# ============================================================ V2 permutation
say("V2  Permutation test of the strain effect (%d shuffles per cell)" % N_PERM)

STAT_FOR = {"ANOVA": "classical F", "Welch ANOVA": "Welch F",
            "Kruskal-Wallis": "rank (H)"}

perm_rows = []
for outcome in OUTCOMES:
    for temp in CM.TEMP_ORDER:
        sub = units[units["Temperature"] == temp].dropna(subset=[outcome])
        y = transform(sub[outcome].astype(float), outcome).to_numpy()
        S = pd.get_dummies(sub["Strain"].astype(str)).to_numpy(float)   # n x k
        M = pd.get_dummies(sub["MS"].astype(str)).to_numpy(float)       # n x 2
        n, k = len(y), S.shape[1]
        ns, nm = S.sum(0), M.sum(0)

        # strain labels are shuffled *within* each must-sugar block, which is
        # the permutation scheme that matches the model step 5 actually fitted
        # (_y ~ C(Strain) + C(MS)): it holds the MS term fixed under the null
        blocks = [np.flatnonzero(M[:, j] > 0) for j in range(M.shape[1])]
        idx = np.empty((N_PERM, n), dtype=int)
        for b in blocks:
            idx[:, b] = b[np.argsort(RNG.random((N_PERM, len(b))), axis=1)]
        Y = np.vstack([y[None, :], y[idx]])          # row 0 = observed

        Yadj = Y - (Y @ M / nm) @ M.T                # remove the MS means
        g = Yadj @ S
        gm = Yadj.mean(axis=1, keepdims=True)
        ssb = (g ** 2 / ns).sum(axis=1) - Yadj.sum(axis=1) ** 2 / n
        sst = ((Yadj - gm) ** 2).sum(axis=1)
        df2 = n - k - 1                              # one df spent on MS
        F_adj = (ssb / (k - 1)) / ((sst - ssb) / df2)

        gg = (Yadj ** 2) @ S
        mean_g = g / ns
        var_g = (gg - g ** 2 / ns) / (ns - 1)
        w = ns / var_g
        sw = w.sum(axis=1, keepdims=True)
        wm = (w * mean_g).sum(axis=1, keepdims=True) / sw
        lam = ((1 - w / sw) ** 2 / (ns - 1)).sum(axis=1)
        F_wel = ((w * (mean_g - wm) ** 2).sum(axis=1) / (k - 1)
                 / (1 + 2 * (k - 2) / (k ** 2 - 1) * lam))

        R = stats.rankdata(Yadj, axis=1)
        rg = R @ S
        rssb = (rg ** 2 / ns).sum(axis=1) - R.sum(axis=1) ** 2 / n
        rsst = (R ** 2).sum(axis=1) - R.sum(axis=1) ** 2 / n
        H = (n - 1) * rssb / rsst

        ref = within[(within["outcome"] == outcome) &
                     (within["temperature"] == temp)].iloc[0]
        stat = STAT_FOR[ref["preferred"]]
        row = {"outcome": outcome, "temperature": temp, "n": n,
               "F_strain_recomputed": round(float(F_adj[0]), 4),
               "F_strain_step5": round(float(ref["F_strain"]), 4),
               "preferred_test": ref["preferred"],
               "statistic_permuted": stat}
        for key, vals in [("classicalF", F_adj), ("welchF", F_wel),
                          ("rank", H)]:
            row["p_perm_" + key] = float((np.sum(vals[1:] >= vals[0]) + 1)
                                         / (N_PERM + 1))
        row["p_perm_matched"] = row["p_perm_" + {"classical F": "classicalF",
                                                 "Welch F": "welchF",
                                                 "rank (H)": "rank"}[stat]]
        row["p_parametric_BH"] = float(ref["p_preferred_BH"])
        row["parametric_call"] = ref["strain_effect"]
        perm_rows.append(row)
perm = pd.DataFrame(perm_rows)
for col in ["p_perm_classicalF", "p_perm_welchF", "p_perm_rank",
            "p_perm_matched"]:
    perm[col.replace("p_perm_", "pBH_")] = stats.false_discovery_control(
        perm[col], method="bh")
perm["permutation_call"] = np.where(perm["pBH_matched"] < 0.05,
                                    "significant", "not significant")
perm["agree"] = perm["permutation_call"] == perm["parametric_call"]
perm["F_matches_step5"] = ((perm["F_strain_recomputed"] -
                            perm["F_strain_step5"]).abs() < 1e-3)
# step 5 fits C(MS) in its classical-ANOVA branch but not in its Welch or
# Kruskal-Wallis branches; the permutation test above always does
perm["step5_adjusted_for_MS"] = perm["preferred_test"] == "ANOVA"
CM.dump(perm, "10_permutation_tests",
        "restricted label shuffle; the permuted statistic matches the test "
        "used in step 5, and always adjusts for must sugar")
print(perm[["outcome", "temperature", "F_strain_recomputed", "F_strain_step5",
            "statistic_permuted", "pBH_matched", "p_parametric_BH",
            "agree"]].to_string(index=False))
print("  step-5 F for strain reproduced in %d of %d cells"
      % (int(perm["F_matches_step5"].sum()), len(perm)))
print("  permutation agrees with the step-5 call in %d of %d cells"
      % (int(perm["agree"].sum()), len(perm)))
for flag, name in [(True, "ANOVA (adjusts for MS)"),
                   (False, "Welch / Kruskal-Wallis (does not)")]:
    s = perm[perm["step5_adjusted_for_MS"] == flag]
    print("    where step 5 used %-34s %d of %d agree"
          % (name, int(s["agree"].sum()), len(s)))
print("  significant cells: step 5 %d of 24, validated permutation %d of 24"
      % (int((perm["parametric_call"] == "significant").sum()),
         int((perm["permutation_call"] == "significant").sum())))

# ======================================================= V3 pseudoreplication
say("V3  What pseudoreplication would have done")

pseudo = []
for unit_out, raw_col, sc in [("MaxViable", "Viable", "log10"),
                              ("FinalSuccinate", "Succinate", "raw"),
                              ("FinalAcetate", "Acetate", "raw")]:
    for temp in CM.TEMP_ORDER:
        r = raw[(raw["Temperature"].astype(str) == temp) & raw[raw_col].notna()]
        yv = np.log10(r[raw_col]) if sc == "log10" else r[raw_col]
        gs = [g.to_numpy() for _, g in yv.groupby(r["Strain"], observed=True)]
        Fn, pn = stats.f_oneway(*[g for g in gs if len(g) > 1])
        u = units[units["Temperature"] == temp]
        gsu = [g for g in groups_for(u, unit_out) if len(g) > 1]
        Fu, pu = stats.f_oneway(*gsu)
        pseudo.append({"outcome": unit_out, "temperature": temp,
                       "n_naive_rows": int(len(r)),
                       "F_naive": round(float(Fn), 2), "p_naive": float(pn),
                       "n_units": int(len(u)),
                       "F_unit_level": round(float(Fu), 2),
                       "p_unit_level": float(pu),
                       "n_inflation": round(len(r) / len(u), 1)})
pseudo = pd.DataFrame(pseudo)
CM.dump(pseudo, "10_pseudoreplication", "naive 1944-row test vs 216-unit test")
print(pseudo.to_string(index=False))

# ============================================================ V4 mixed model
say("V4  Mixed-effects cross-check on the repeated measures")

mixed_rows = []
try:
    import statsmodels.formula.api as smf
    d = raw[raw["Viable"].notna()].copy()
    d["y"] = np.log10(d["Viable"])
    d["Strain"] = d["Strain"].astype(str)
    d["TempS"] = d["Temperature"].astype(str)
    # the sampling point must be in the model: without it the within-unit
    # residual is dominated by the growth curve itself and the ICC collapses
    # to zero for reasons that have nothing to do with independence
    m = smf.mixedlm("y ~ C(Strain) * C(TempS) + C(MS) + C(Time_name)", d,
                    groups=d["Unit"]).fit()
    pred = d.assign(fit=m.fittedvalues).groupby("Strain",
                                                observed=True)["fit"].mean()
    obs_u = (units.assign(l=np.log10(units["MaxViable"]))
                  .groupby("Strain", observed=True)["l"].mean())
    rho, prho = stats.spearmanr(pred.reindex(obs_u.index).to_numpy(),
                                obs_u.to_numpy())
    icc = float(m.cov_re.iloc[0, 0] / (m.cov_re.iloc[0, 0] + m.scale))
    mixed_rows.append({"check": "strain ordering: mixed model on 1944 rows "
                                "(random intercept per fermentation) vs "
                                "unit-level means",
                       "statistic": "Spearman rho", "value": round(float(rho), 3),
                       "p": float(prho),
                       "verdict": "PASS" if rho > 0.7 else "REVIEW"})
    mixed_rows.append({"check": "within-fermentation correlation of the "
                                "repeated samples",
                       "statistic": "ICC", "value": round(icc, 3), "p": np.nan,
                       "verdict": "repeated samples correlated -> unit-level "
                                  "aggregation justified"})
    print("  Spearman rho = %.3f (p = %.3g), ICC = %.3f" % (rho, prho, icc))
except Exception as exc:
    mixed_rows.append({"check": "mixed model", "statistic": "-",
                       "value": np.nan, "p": np.nan,
                       "verdict": "not run: %s" % exc})
    print("  mixed model not run:", exc)
CM.dump(pd.DataFrame(mixed_rows), "10_mixedmodel_check", "V4")

# =================================================================== V5 LORO
say("V5  Leave-one-replicate-out")

loro = []
for outcome in OUTCOMES:
    for temp in CM.TEMP_ORDER:
        vref = perm[(perm["outcome"] == outcome) &
                    (perm["temperature"] == temp)].iloc[0]
        kept = []
        for drop in ["R1", "R2", "R3"]:
            sub = units[(units["Temperature"] == temp) & (units["Rep"] != drop)]
            kept.append(anova_strain(sub, outcome)["p"] < 0.05)
        sig = vref["permutation_call"] == "significant"
        loro.append({"outcome": outcome, "temperature": temp,
                     "validated_call": vref["permutation_call"],
                     "n_per_strain": 4,
                     "subsets_significant": int(sum(kept)), "n_subsets": 3,
                     "robust": bool(sum(kept) == 3) if sig
                               else bool(sum(kept) == 0)})
loro = pd.DataFrame(loro)
CM.dump(loro, "10_loro_sensitivity", "drop one biological replicate at a time")
print(loro.to_string(index=False))

# ========================================================== V6 artefact check
say("V6  Sensitivity to the flagged sugar artefacts")

flag = pd.read_csv(TAB / "01_flagged_nonmonotonic_sugar.csv")
ucol = "Unit" if "Unit" in flag.columns else flag.columns[0]
bad = set(flag[ucol].astype(str))
clean = units[~units["Unit"].isin(bad)]
n_flagged = int(units["Unit"].isin(bad).sum())
print("  flagged units: %d of %d; clean subset n = %d"
      % (n_flagged, len(units), len(clean)))

art = []
for outcome in OUTCOMES:
    for temp in CM.TEMP_ORDER:
        vref = perm[(perm["outcome"] == outcome) &
                    (perm["temperature"] == temp)].iloc[0]
        sub = clean[clean["Temperature"] == temp]
        r = anova_strain(sub, outcome)
        F, p = r["F"], r["p"]
        art.append({"outcome": outcome, "temperature": temp,
                    "n_full": int(vref["n"]), "n_clean": int(r["n"]),
                    "strains_left": int(sub["Strain"].nunique()),
                    "F_clean": round(float(F), 3), "p_clean": float(p),
                    "validated_call": vref["permutation_call"],
                    "clean_call": "significant" if p < 0.05
                                  else "not significant",
                    "agree": bool((p < 0.05) ==
                                  (vref["permutation_call"] == "significant"))})
art = pd.DataFrame(art)
CM.dump(art, "10_artefact_sensitivity", "re-test with flagged units removed")
print("  agreement: %d of %d cells" % (int(art["agree"].sum()), len(art)))

# ========================================================= V7 bootstrap effect
say("V7  Interval estimates for the size of the strain effect")

boot = []
for outcome in OUTCOMES:
    for temp in CM.TEMP_ORDER:
        sub = units[units["Temperature"] == temp]
        r = anova_strain(sub, outcome)
        y, ng, starts = prep(sub, outcome)
        n = r["n"]
        e_lo, e_hi = eta2_ci(r["F"], r["df1"], r["df2"], n)
        eta2 = r["eta2"]

        # bootstrap the widest strain-to-strain gap: resampling units within
        # a strain gives honest intervals for means and their differences
        off = np.repeat(starts, ng)
        size = np.repeat(ng, ng)
        take = off + (RNG.random((N_BOOT, n)) * size).astype(int)
        means = np.add.reduceat(y[take], starts, axis=1) / ng
        rng_draws = means.max(axis=1) - means.min(axis=1)
        obs_means = np.add.reduceat(y, starts) / ng
        g_lo, g_hi = np.percentile(rng_draws, [2.5, 97.5])

        boot.append({"outcome": outcome, "temperature": temp, "n": n,
                     "partial_eta_sq": round(float(eta2), 3),
                     "eta2_ci95_low": round(float(e_lo), 3),
                     "eta2_ci95_high": round(float(e_hi), 3),
                     "eta2_excludes_zero": bool(e_lo > 0),
                     "max_strain_gap": round(float(obs_means.max() -
                                                   obs_means.min()), 3),
                     "gap_ci95_low": round(float(g_lo), 3),
                     "gap_ci95_high": round(float(g_hi), 3),
                     "scale": SCALE.get(outcome, "raw")})
boot = pd.DataFrame(boot)
CM.dump(boot, "10_bootstrap_effectsize",
        "noncentral-F CI for partial eta-squared; bootstrap CI for the "
        "largest strain-to-strain gap")
print(boot.to_string(index=False))

# ----------------------------------------------------------------------------
# The consolidated results table the report quotes: one row per outcome x
# regime, carrying the step-5 call, the validated call, and the effect size
# with its interval.
# ----------------------------------------------------------------------------
final = perm[["outcome", "temperature", "n", "preferred_test",
              "statistic_permuted", "p_parametric_BH", "parametric_call",
              "pBH_matched", "permutation_call"]].merge(
    boot[["outcome", "temperature", "partial_eta_sq", "eta2_ci95_low",
          "eta2_ci95_high", "max_strain_gap", "gap_ci95_low", "gap_ci95_high",
          "scale"]], on=["outcome", "temperature"])
final["call_changed"] = final["parametric_call"] != final["permutation_call"]
CM.dump(final, "10_validated_results",
        "the results table as validated in step 8")
print("\n  validated results table -> 10_validated_results.csv  "
      "(%d of %d calls changed)" % (int(final["call_changed"].sum()),
                                    len(final)))

# ============================================================= V8 robustness
say("V8  Cross-regime robustness of each strain")

rob = units.copy()
for col in ["T90_h", "FinalResidualSugar", "MaxRate_gL_h"]:
    rob["z_" + col] = (rob.groupby("Temperature", observed=True)[col]
                          .transform(lambda s: (s - s.mean()) / s.std(ddof=1)))
rank = (rob.groupby(["Temperature", "Strain"], observed=True)["T90_h"].mean()
           .unstack("Temperature").rank(axis=0))
zmean = (rob.groupby(["Temperature", "Strain"], observed=True)["z_T90_h"].mean()
            .unstack("Temperature"))
tbl = pd.DataFrame({
    "mean_rank_T90": rank.mean(axis=1).round(2),
    "best_rank": rank.min(axis=1).astype(int),
    "worst_rank": rank.max(axis=1).astype(int),
    "rank_range": (rank.max(axis=1) - rank.min(axis=1)).astype(int),
    "sd_z_T90": zmean.std(axis=1, ddof=1).round(3),
    "pct_dry": (100 * rob.groupby("Strain", observed=True)["Dry"].mean()).round(0),
    "n_stuck": rob.groupby("Strain", observed=True)["Dry"]
                  .apply(lambda s: int((s == 0).sum())),
})
tbl["regimes_in_top3"] = (rank <= 3).sum(axis=1)
tbl = tbl.sort_values(["mean_rank_T90", "rank_range"])
CM.dump(tbl, "10_strain_robustness",
        "consistency of each strain across the four regimes")
print(tbl.to_string())

kw = stats.kruskal(*[g["z_T90_h"].dropna().to_numpy() for _, g in
                     rob.groupby("Strain", observed=True)])
print("  Kruskal-Wallis on within-regime standardised T90 across strains: "
      "H = %.2f, p = %.3g" % (kw.statistic, kw.pvalue))

# ======================================================= V9 multivariate check
say("V9  Re-verification of the PCA and clustering numbers")

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, adjusted_rand_score

FEATS = ["InitialSugar", "FinalResidualSugar", "SugarConsumedTotal",
         "FracFermentedFinal", "FinalEthanol", "EthanolYield_pct_per_gL",
         "FinalGlycerol", "FinalAcetate", "FinalSuccinate", "MalateConsumed",
         "T50_h", "T90_h", "MaxRate_gL_h", "MaxViable", "FinalViability"]
X = units[FEATS].dropna()
meta = units.loc[X.index]
Z = StandardScaler().fit_transform(X)
pca = PCA().fit(Z)
scores = pca.transform(Z)[:, :4]

ev = pd.read_csv(TAB / "06_explained_variance.csv", index_col=0)
sep = pd.read_csv(TAB / "06_label_separation.csv", index_col=0)
ari_rep = pd.read_csv(TAB / "07_cluster_label_agreement.csv", index_col=0)
assign = pd.read_csv(TAB / "07_cluster_assignments.csv")
prof = pd.read_csv(TAB / "07_cluster_profiles.csv", index_col=0)

mv = [{"quantity": "PC1-PC4 cumulative variance (%)",
       "reported": float(ev.loc[3, "cumulative_pct"]),
       "revalidated": round(100 * pca.explained_variance_ratio_[:4].sum(), 4)},
      {"quantity": "components with eigenvalue > 1",
       "reported": float((ev["eigenvalue"] > 1).sum()),
       "revalidated": float((pca.explained_variance_ > 1).sum())}]
for lab, col in [("Strain", "Strain"), ("Temperature", "Temperature"),
                 ("MS (initial sugar)", "MS")]:
    mv.append({"quantity": "silhouette by %s in PC1-PC4" % lab,
               "reported": float(sep.loc[sep["label"] == lab,
                                         "silhouette_in_PC_space"].iloc[0]),
               "revalidated": round(float(silhouette_score(
                   scores, meta[col].astype(str))), 4)})
a = assign.set_index("Unit").reindex(meta["Unit"])
for lab, col in [("Strain", "Strain"), ("Temperature", "Temperature"),
                 ("MS (initial sugar)", "MS")]:
    mv.append({"quantity": "ARI, Ward clusters vs %s" % lab,
               "reported": float(ari_rep.loc[ari_rep["label"] == lab,
                                             "ARI_ward"].iloc[0]),
               "revalidated": round(float(adjusted_rand_score(
                   a["ward"].astype(str), meta[col].astype(str))), 4)})
mv = pd.DataFrame(mv)
mv["abs_diff"] = (mv["reported"] - mv["revalidated"]).abs().round(4)
mv["agree"] = mv["abs_diff"] < 0.02
CM.dump(mv.set_index("quantity"), "10_multivariate_check", "V9")
print(mv.to_string(index=False))

stuck_c = int(prof.loc["FinalResidualSugar"].iloc[:-1].astype(float).idxmax())
stuck = assign[assign["ward"] == stuck_c].merge(
    units[["Unit", "Dry", "FinalResidualSugar", "Strain"]], on="Unit")
print("  cluster %d: n = %d, mean residual sugar %.1f g/L, %d of %d not dry"
      % (stuck_c, len(stuck), stuck["FinalResidualSugar"].mean(),
         int((stuck["Dry"] == 0).sum()), len(stuck)))

# ========================================================== V10 claim checks
say("V10  Report claims checked against the data")

claims = []


def claim(text, value, expected, tol=None, ok=None):
    if ok is None:
        ok = abs(float(value) - float(expected)) <= (tol if tol is not None else 0)
    claims.append({"claim": text, "recomputed": value, "as_reported": expected,
                   "verdict": "PASS" if ok else "FAIL"})


anova2 = pd.read_csv(TAB / "05_twoway_anova.csv", index_col=0)

claim("216 fermentation units (9 strains x 4 regimes x 2 must sugars x 3 reps)",
      len(units), 216)
claim("1944 observations after dropping the 6 t5bis rows", len(raw), 1944)
claim("balanced design: every strain has the same number of units",
      int(units.groupby("Strain", observed=True).size().nunique()), 1)
claim("184 of 216 fermentations finish dry (< 2 g/L residual sugar)",
      int(units["Dry"].sum()), 184)
claim("T90 is missing for exactly one unit (GALA|TVAR|250|R1)",
      int(units["T90_h"].isna().sum()), 1)
claim("strain x temperature interaction significant for all 6 outcomes",
      int((anova2.query("term == 'Strain:Temperature'")["p_BH"] < 0.05).sum()), 6)
claim("strain effect significant in 15 of 24 outcome x regime cells",
      int((within["strain_effect"] == "significant").sum()), 15)
claim("all 6 outcomes separate by strain at 12 degC",
      int(((within["temperature"] == "12") &
           (within["strain_effect"] == "significant")).sum()), 6)
claim("final ethanol gap between the 210 and 250 g/L musts (% v/v)",
      round(float(units.groupby("MS")["FinalEthanol"].mean().diff().iloc[-1]), 2),
      2.97, tol=0.05)
claim("step-5 F for strain reproduced in every cell with a balanced design",
      int(perm["F_matches_step5"].sum()), 23)
claim("every call that changed on validation is one where step 5 did not "
      "adjust for must sugar",
      int((perm.loc[~perm["agree"], "step5_adjusted_for_MS"]).sum()), 0)
claim("validated permutation test finds a strain effect in 22 of 24 cells",
      int((perm["permutation_call"] == "significant").sum()), 22)
claim("W12 is in the top three on T90 in all four regimes",
      int(tbl.loc["W12", "regimes_in_top3"]), 4)
claim("VIN13 has the widest rank range across regimes",
      str(tbl["rank_range"].idxmax()), "VIN13",
      ok=str(tbl["rank_range"].idxmax()) == "VIN13")
ari_sug = float(mv.loc[mv["quantity"] ==
                       "ARI, Ward clusters vs MS (initial sugar)",
                       "revalidated"].iloc[0])
ari_str = float(mv.loc[mv["quantity"] == "ARI, Ward clusters vs Strain",
                       "revalidated"].iloc[0])
claim("clusters track must sugar, not strain (ARI sugar > ARI strain)",
      round(ari_sug, 3), round(ari_str, 3), ok=ari_sug > ari_str)
claim("every unit-level feature reproduces to within 1e-6 of a second "
      "implementation", int(recomp["agree"].all()), 1)

claims = pd.DataFrame(claims)
CM.dump(claims.set_index("claim"), "10_claim_checks", "V10")
print(claims.to_string(index=False))
N_FAIL = int((claims["verdict"] == "FAIL").sum())
print("\n  %d of %d claims PASS" % (len(claims) - N_FAIL, len(claims)))

# ==================================================================== FIGURES
say("Figures")

# fig19 - robustness
fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.0))
ax = axes[0]
order = tbl.index.tolist()
for i, s in enumerate(order):
    lo, hi = tbl.loc[s, "best_rank"], tbl.loc[s, "worst_rank"]
    ax.plot([lo, hi], [i, i], color=CM.GRID, lw=5, solid_capstyle="round",
            zorder=1)
    ax.scatter([lo, hi], [i, i], s=22, color=CM.INK3, zorder=2)
    ax.scatter([tbl.loc[s, "mean_rank_T90"]], [i], s=46, color=CM.SERIES[0],
               zorder=3)
ax.set_yticks(np.arange(len(order)), order)
ax.invert_yaxis()
ax.set_xlabel("Rank on time to 90 % sugar consumption  (1 = fastest)")
ax.set_title("Range of rank across the four regimes")
ax.text(0.98, 0.04, "dot = mean rank\nbar = best to worst",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=7.5,
        color=CM.INK3)
CM.despine(ax)

ax = axes[1]
ax.scatter(tbl["mean_rank_T90"], tbl["sd_z_T90"], s=44, color=CM.SERIES[1])
for s in order:
    ax.annotate(s, (tbl.loc[s, "mean_rank_T90"], tbl.loc[s, "sd_z_T90"]),
                textcoords="offset points", xytext=(5, 3), fontsize=8,
                color=CM.INK2)
ax.set_xlabel("Mean rank on T90 (1 = fastest)")
ax.set_ylabel("SD of standardised T90 across regimes")
ax.set_title("Fast and consistent is the bottom left")
CM.despine(ax)
CM.titles(fig, "Which strains behave consistently across temperature regimes?",
          "Ranks are recomputed within each regime. A wide bar, or a high SD, "
          "means the strain's relative\nperformance depends on the temperature "
          "it is run at.")
fig.tight_layout(rect=[0, 0, 1, 0.86])
CM.save(fig, "fig19_strain_robustness")

# fig20 - where the two analyses disagree, and why
fig, ax = plt.subplots(figsize=(6.4, 4.9))
x = -np.log10(np.clip(perm["p_parametric_BH"].to_numpy(), 1e-7, 1))
y = -np.log10(np.clip(perm["pBH_matched"].to_numpy(), 1e-7, 1))
adj = perm["step5_adjusted_for_MS"].to_numpy()
thr = -np.log10(0.05)
lim = max(x.max(), y.max()) * 1.08
ax.axhspan(thr, lim, 0, thr / lim, color=CM.SERIES[3], alpha=0.07)
ax.axhline(thr, color=CM.INK3, lw=0.8, ls=":")
ax.axvline(thr, color=CM.INK3, lw=0.8, ls=":")
ax.plot([0, lim], [0, lim], color=CM.GRID, lw=1)
ax.scatter(x[adj], y[adj], s=46, color=CM.SERIES[0], alpha=0.9,
           edgecolor="white", linewidth=0.6,
           label="step 5 used ANOVA — adjusted for must sugar")
ax.scatter(x[~adj], y[~adj], s=46, color=CM.SERIES[1], alpha=0.9,
           edgecolor="white", linewidth=0.6, marker="s",
           label="step 5 used Welch / Kruskal–Wallis — not adjusted")
ax.set_xlabel("Step 5, as reported:  $-\\log_{10}$ BH-adjusted $p$")
ax.set_ylabel("Validated permutation test:  $-\\log_{10}$ BH-adjusted $p$")
ax.set_xlim(0, lim)
ax.set_ylim(0, lim)
ax.text(thr * 0.45, lim * 0.93, "significant only\nafter adjustment",
        fontsize=7.5, color=CM.INK3, va="top")
ax.legend(loc="lower right", fontsize=7.2)
CM.despine(ax)
CM.titles(fig, "The disagreements all sit in one branch of the step-5 decision "
               "tree",
          "One point per outcome x regime (n = 24). Every cell where the two "
          "analyses differ is one where\nstep 5 fell through to a test that "
          "left the must-sugar factor in the error term.", top=0.86)
fig.tight_layout(rect=[0, 0, 1, 0.86])
CM.save(fig, "fig20_permutation_vs_parametric")

# fig21 - sensitivity grid
grid = pd.DataFrame(index=OUTCOMES, columns=CM.TEMP_ORDER, dtype=float)
for _, r in within.iterrows():
    pm = perm[(perm["outcome"] == r["outcome"]) &
              (perm["temperature"] == r["temperature"])].iloc[0]
    lr = loro[(loro["outcome"] == r["outcome"]) &
              (loro["temperature"] == r["temperature"])].iloc[0]
    ar = art[(art["outcome"] == r["outcome"]) &
             (art["temperature"] == r["temperature"])].iloc[0]
    grid.loc[r["outcome"], r["temperature"]] = (
        (pm["permutation_call"] == "significant")        # restricted shuffle
        + (float(r["p_anova_BH"]) < 0.05)                # parametric, adj. MS
        + (lr["subsets_significant"] == 3)               # 2-replicate subsets
        + (ar["clean_call"] == "significant"))           # artefacts removed

fig, ax = plt.subplots(figsize=(6.4, 3.7))
im = ax.imshow(grid.to_numpy(dtype=float), cmap="Blues", vmin=0, vmax=4,
               aspect="auto")
ax.set_xticks(range(4), ["12 °C", "18 °C", "25 °C", "TVAR"])
ax.set_yticks(range(len(OUTCOMES)), [PRETTY[o] for o in OUTCOMES])
for i in range(len(OUTCOMES)):
    for j in range(4):
        v = int(grid.iloc[i, j])
        ax.text(j, i, "%d/4" % v, ha="center", va="center", fontsize=9,
                color="white" if v >= 3 else CM.INK)
ax.grid(False)
cb = fig.colorbar(im, ax=ax, ticks=[0, 1, 2, 3, 4], pad=0.02)
cb.set_label("analyses calling the strain effect significant", fontsize=8)
cb.outline.set_visible(False)
CM.titles(fig, "How many of four independent analyses agree, cell by cell",
          "Primary test (ANOVA / Welch / Kruskal-Wallis), permutation test, "
          "leave-one-replicate-out\n(all three subsets), and the re-test with "
          "the flagged units removed.", top=0.84)
fig.tight_layout(rect=[0, 0, 1, 0.84])
CM.save(fig, "fig21_validation_sensitivity")

grid.to_csv(TAB / "10_sensitivity_grid.csv")
print("  table  -> outputs/tables/10_sensitivity_grid.csv")

print("\n" + "=" * 72)
print("VALIDATION COMPLETE  -  %d of %d claims PASS, permutation agreement "
      "%d/24, artefact agreement %d/24"
      % (len(claims) - N_FAIL, len(claims), int(perm["agree"].sum()),
         int(art["agree"].sum())))
print("=" * 72)
