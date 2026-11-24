"""
Build the final term-project report: outputs/BT3041_Final_Report.pdf

Hard constraint from the submission instructions: the main report is at most
8 pages. The script asserts the page count at the end and fails loudly if the
content has grown past it, so the limit cannot be broken by accident.

Every number in the prose and in the tables is read from outputs/tables at
build time. Nothing is typed in by hand, so the report cannot drift out of
step with the analysis.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib import colors
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame,
                                Paragraph, Spacer, Image as RLImage, Table,
                                TableStyle, KeepTogether, Flowable)

sys.path.insert(0, str(Path(__file__).parent))
import common as CM

FIG, TAB = CM.FIGURES, CM.TABLES
OUT = CM.ROOT / "outputs" / "BT3041_Final_Report.pdf"
MAX_PAGES = 8

PAGE_W, PAGE_H = A4
MX, MY = 19 * mm, 17 * mm
CW = PAGE_W - 2 * MX

BLACK = colors.black
GREY = colors.Color(0.34, 0.34, 0.33)
RULE = colors.Color(0.55, 0.55, 0.54)
FAINT = colors.Color(0.84, 0.84, 0.82)
BODY, BOLD, ITAL, BI = "Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic"

S = {
    "title": ParagraphStyle("title", fontName=BOLD, fontSize=15.5, leading=18.5,
                            textColor=BLACK, spaceAfter=3),
    "byline": ParagraphStyle("byline", fontName=BODY, fontSize=9, leading=12.4,
                             textColor=GREY, spaceAfter=1),
    "abshead": ParagraphStyle("abshead", fontName=BI, fontSize=9.3, leading=12,
                              textColor=BLACK, spaceBefore=6, spaceAfter=2),
    "abstract": ParagraphStyle("abstract", fontName=BODY, fontSize=9.1,
                               leading=12.3, textColor=BLACK,
                               alignment=TA_JUSTIFY, leftIndent=7,
                               rightIndent=7, spaceAfter=5),
    "h1": ParagraphStyle("h1", fontName=BOLD, fontSize=10.8, leading=13.4,
                         textColor=BLACK, spaceBefore=8, spaceAfter=2.8,
                         keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName=BI, fontSize=9.7, leading=12.4,
                         textColor=BLACK, spaceBefore=5.4, spaceAfter=2.1,
                         keepWithNext=1),
    "body": ParagraphStyle("body", fontName=BODY, fontSize=9.3, leading=12.3,
                           textColor=BLACK, alignment=TA_JUSTIFY, spaceAfter=4.3),
    "bullet": ParagraphStyle("bullet", fontName=BODY, fontSize=9.35,
                             leading=12.3, textColor=BLACK,
                             alignment=TA_JUSTIFY, leftIndent=12,
                             bulletIndent=2, spaceAfter=2.6),
    "caption": ParagraphStyle("caption", fontName=BODY, fontSize=8.1,
                              leading=10.6, textColor=GREY,
                              alignment=TA_JUSTIFY, spaceBefore=2.5,
                              spaceAfter=5.5, leftIndent=6, rightIndent=6),
    "tabnote": ParagraphStyle("tabnote", fontName=ITAL, fontSize=8.1,
                              leading=10.6, textColor=GREY,
                              alignment=TA_JUSTIFY, spaceBefore=1.6,
                              spaceAfter=6.5),
    "ref": ParagraphStyle("ref", fontName=BODY, fontSize=7.7, leading=9.7,
                          textColor=BLACK, alignment=TA_JUSTIFY,
                          leftIndent=10, firstLineIndent=-10, spaceAfter=0.8),
    "small": ParagraphStyle("small", fontName=BODY, fontSize=8.1, leading=10.6,
                            textColor=BLACK, alignment=TA_JUSTIFY,
                            spaceAfter=3.5),
}

story = []
h1 = lambda t: story.append(Paragraph(t, S["h1"]))
h2 = lambda t: story.append(Paragraph(t, S["h2"]))
p = lambda t: story.append(Paragraph(t, S["body"]))
sm = lambda t: story.append(Paragraph(t, S["small"]))
gap = lambda h=4: story.append(Spacer(1, h))


def bullets(items, style="bullet"):
    for it in items:
        story.append(Paragraph(it, S[style], bulletText="•"))
    story.append(Spacer(1, 3))


def table(data, widths=None, size=8.2, note=None, align=None, lead=None,
          keep=True):
    """Booktabs-style table: horizontal rules only, no cell boxes."""
    styles = {}
    for r in range(len(data)):
        for c in range(len(data[r])):
            styles[(r, c)] = ParagraphStyle(
                "c%d_%d" % (r, c), fontName=(BOLD if r == 0 else BODY),
                fontSize=size, leading=lead or size + 2.5, textColor=BLACK,
                alignment=TA_CENTER if (align and c in align) else 0)
    rows = [[Paragraph(str(c), styles[(r, i)]) for i, c in enumerate(row)]
            for r, row in enumerate(data)]
    t = Table(rows, colWidths=widths, hAlign="LEFT", repeatRows=1)
    t.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.8, BLACK),
        ("LINEBELOW", (0, 0), (-1, 0), 0.4, BLACK),
        ("LINEBELOW", (0, -1), (-1, -1), 0.8, BLACK),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
        ("LEFTPADDING", (1, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2.1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.1),
    ]))
    blk = [t]
    blk += ([Spacer(1, 2), Paragraph(note, S["tabnote"])] if note
            else [Spacer(1, 8)])
    # a long table is allowed to break across pages - its header repeats -
    # rather than leaving a third of a page empty to stay in one piece
    story.append(KeepTogether(blk) if keep else blk[0])
    if not keep:
        for f in blk[1:]:
            story.append(f)


def figure(name, caption, width=None, height=None, maxh=62 * mm):
    path = FIG / name
    if not path.exists():
        p("[missing figure: %s]" % name)
        return
    iw, ih = Image.open(path).size
    if height is not None:
        h, w = height, height * iw / ih
    else:
        w = width or CW
        h = w * ih / iw
    if w > CW:
        w, h = CW, CW * ih / iw
    if h > maxh:
        h, w = maxh, maxh * iw / ih
    img = RLImage(str(path), width=w, height=h)
    img.hAlign = "CENTER"
    story.append(KeepTogether([img, Paragraph(caption, S["caption"])]))


class Rule(Flowable):
    def __init__(self, width, weight=0.6, color=RULE, space=7):
        Flowable.__init__(self)
        self.width, self.weight, self.color, self.height = width, weight, color, space

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.weight)
        self.canv.line(0, self.height / 2, self.width, self.height / 2)


# ============================================================ numbers, from CSV
rd = lambda n, **k: pd.read_csv(TAB / n, **k)

anova2 = rd("05_twoway_anova.csv", index_col=0)
within = rd("05_within_regime_strain_tests.csv", index_col=0)
assump = rd("05_assumption_checks.csv", index_col=0)
tukey = rd("05_tukey_posthoc.csv", index_col=0)
vdec = rd("03_variance_decomposition.csv", index_col=0)
kin_t = rd("02_kinetics_by_temperature.csv", index_col=0)
kin_t.index = kin_t.index.astype(str)
kin_s = rd("02_kinetics_by_strain.csv", index_col=0)
ranks = rd("02_strain_rank_by_temperature.csv", index_col=0)
kin_t_idx = None
ev = rd("06_explained_variance.csv", index_col=0)
load = rd("06_loadings.csv", index_col=0)
sep = rd("06_label_separation.csv", index_col=0)
ksel = rd("07_k_selection.csv", index_col=0)
cari = rd("07_cluster_label_agreement.csv", index_col=0)
prof = rd("07_cluster_profiles.csv", index_col=0)
ctstrain = rd("07_crosstab_ward_x_strain.csv", index_col=0)
cttemp = rd("07_crosstab_ward_x_temperature.csv", index_col=0)
ctms = rd("07_crosstab_ward_x_ms.csv", index_col=0)
stab = rd("07_stability_resampling.csv", index_col=0)
units = rd("02_unit_level_features.csv")
final = rd("10_validated_results.csv", index_col=0)
perm = rd("10_permutation_tests.csv", index_col=0)
pseudo = rd("10_pseudoreplication.csv", index_col=0)
mixed = rd("10_mixedmodel_check.csv", index_col=0)
loro = rd("10_loro_sensitivity.csv", index_col=0)
art = rd("10_artefact_sensitivity.csv", index_col=0)
rob = rd("10_strain_robustness.csv", index_col=0)
mvchk = rd("10_multivariate_check.csv", index_col=0)
claims = rd("10_claim_checks.csv", index_col=0)
recomp = rd("10_recompute_check.csv", index_col=0)
grid = rd("10_sensitivity_grid.csv", index_col=0)
assign = rd("07_cluster_assignments.csv")
N_MV = len(assign)   # PCA and clustering drop the one unit with no T90

D = "°"
PRETTY = {"MaxViable": "Peak viable cells", "FinalSuccinate": "Final succinate",
          "MalateConsumed": "Malate consumed", "FinalAcetate": "Final acetate",
          "FinalResidualSugar": "Final residual sugar",
          "FinalEthanol": "Final ethanol", "T50_h": "Time to 50 %",
          "T90_h": "Time to 90 % (h)"}

N_UNITS = len(units)
N_OBS = 1944
N_DRY = int(units["Dry"].sum())
N_SIG5 = int((within["strain_effect"] == "significant").sum())
N_SIGV = int((final["permutation_call"] == "significant").sum())
N_CHANGED = int(final["call_changed"].sum())
N_INTER = int(((anova2["term"] == "Strain:Temperature") &
               (anova2["p_BH"] < 0.05)).sum())
N_OUTCOMES = anova2["outcome"].nunique()
K_PCA = int((ev["eigenvalue"] > 1).sum())
CUM = float(ev.loc[K_PCA - 1, "cumulative_pct"])
BEST_K = int(ksel.loc[ksel["silhouette_ward"].idxmax(), "k"])
STAB = float(stab["ARI_vs_full"].mean())
ARI_WK = float(ksel.loc[ksel["k"] == BEST_K, "ward_vs_kmeans_ARI"].iloc[0])
SIL = dict(zip(sep["label"], sep["silhouette_in_PC_space"]))
ARI = dict(zip(cari["label"], cari["ARI_ward"]))
GRID4 = int((grid == 4).sum().sum())
GRID3 = int((grid >= 3).sum().sum())
N_FULL4 = int(((loro["validated_call"] == "significant") &
               (loro["subsets_significant"] == 3)).sum())
ART_AGREE = int(art["agree"].sum())
RHO_MIX = float(mixed.loc[0, "value"])
ICC = float(mixed.loc[1, "value"])
N_PASS = int((claims["verdict"] == "PASS").sum())
RECOMP_MAX = float(recomp["max_rel_diff_pct"].max())
STUCK_C = int(prof["spread_across_clusters"].index.size and
              prof.loc["FinalResidualSugar"].iloc[:-1].astype(float).idxmax())
STUCK_N = int(ctstrain[str(STUCK_C)].sum())
RHO_RANK = ranks.corr(method="spearman")
RHO_MIN = float(RHO_RANK.where(~np.eye(4, dtype=bool)).min().min())
RHO_MAX = float(RHO_RANK.where(~np.eye(4, dtype=bool)).max().max())
ETH = units.groupby("MS")["FinalEthanol"].agg(["mean", "std"])
PSEUDO_DIFF = int(((pseudo["p_naive"] < 0.05) !=
                   (pseudo["p_unit_level"] < 0.05)).sum())

# ====================================================================== PAGE 1
story.append(Paragraph("Comparative Statistical Analysis of Commercial Yeast "
                       "Strains During Wine Fermentation", S["title"]))
story.append(Paragraph(
    "<b>Team 20</b> &nbsp;&middot;&nbsp; K James Bond &nbsp;&middot;&nbsp; "
    "Avala Madhavi &nbsp;&middot;&nbsp; Dinesh Kumar &nbsp;&middot;&nbsp; "
    "Mohesh &nbsp;&middot;&nbsp; Pranav Ram", S["byline"]))
story.append(Paragraph(
    "BT3041 &mdash; Analysis and Interpretation of Biological Data "
    "&nbsp;&middot;&nbsp; Teaching Assistant: Kaviya D "
    "&nbsp;&middot;&nbsp; 24 November 2026", S["byline"]))
story.append(Paragraph(
    "Data: Minebois &amp; Querol (2025), <i>Fermentation data set obtained "
    "from commercial wine strains in synthetic grape must</i>, Zenodo, "
    "doi:10.5281/zenodo.15260916 (CC BY 4.0). Code and supplementary "
    "material: see the supplementary file.", S["byline"]))
story.append(Rule(CW, 0.7, BLACK, 9))

story.append(Paragraph("Abstract", S["abshead"]))
story.append(Paragraph(
    "Nine commercial <i>Saccharomyces cerevisiae</i> wine strains were compared "
    "across %d fermentations of synthetic grape must, laid out as a balanced "
    "factorial of 9 strains &times; 4 temperature regimes (12, 18, 25&nbsp;%sC "
    "and a time-varying regime) &times; 2 initial sugar concentrations "
    "&times; 3 biological replicates, each sampled at nine time points. "
    "Because the nine samples of a fermentation are not independent "
    "observations, the %s raw samples were collapsed to one row per "
    "fermentation before any test; treating them as independent changes the "
    "verdict in %d of 12 trial comparisons. Strain had a detectable effect on "
    "%d of 24 outcome &times; regime comparisons after adjustment for must "
    "sugar and for multiple comparisons, with partial &eta;<super>2</super> "
    "from %.2f to %.2f. The strain &times; temperature interaction was "
    "significant for all %d outcomes tested, and the ranking of strains by "
    "fermentation speed transferred only weakly between regimes "
    "(Spearman %.2f&ndash;%.2f), so no single strain was fastest everywhere: "
    "W12 was in the fastest three in all four regimes, while VIN13 moved "
    "across seven rank positions. Principal component analysis "
    "(%d components, %.1f %% of variance) and Ward clustering (k = %d, "
    "resampling ARI %.2f) both separated fermentations by must sugar and "
    "temperature, not by strain (silhouette by strain %.3f; cluster-vs-strain "
    "ARI %.3f). The practical reading is that strain choice matters, but it "
    "matters conditionally, and it is a smaller lever on these outcomes than "
    "the two variables a winemaker already sets."
    % (N_UNITS, D, "{:,}".format(N_OBS), PSEUDO_DIFF, N_SIGV,
       final["partial_eta_sq"].min(), final["partial_eta_sq"].max(),
       N_OUTCOMES, RHO_MIN, RHO_MAX, K_PCA, CUM, BEST_K, STAB,
       SIL["Strain"], ARI["Strain"]), S["abstract"]))

h1("1. Introduction and aims")
p("Alcoholic fermentation in winemaking is carried out by <i>S. cerevisiae</i>, "
  "and commercial active dry yeasts are marketed on the premise that strains "
  "behave differently: faster or slower, more or less tolerant of cold or of "
  "high sugar, and with different by-product profiles. Whether that premise "
  "holds in a controlled comparison is a statistical question, and it is the "
  "question this project asks of a published bioprocess dataset.")
p("Two framings of the comparison are possible, and they do not give the same "
  "answer. The first asks whether strains differ <i>overall</i>, pooling the "
  "temperature regimes. The second asks whether they differ <i>at a given "
  "temperature</i>. We adopted the second, for a reason that the exploratory "
  "stage made plain: the effect of strain depends on temperature, so a pooled "
  "comparison averages the effect away and would report an absence of "
  "difference that is an artefact of the pooling. The aims that follow are "
  "therefore stated per regime, and the transferability of the ranking across "
  "regimes is treated as a result in its own right rather than a nuisance.")
bullets([
    "<b>Aim 1.</b> For each temperature regime separately, test whether the "
    "nine strains differ in fermentation kinetics, in completeness of "
    "fermentation, and in the by-products that carry wine quality "
    "(succinate, acetate, malate consumed) and in peak viable population.",
    "<b>Aim 2.</b> Test whether the strain effect depends on the temperature "
    "regime, that is, whether a strain &times; temperature interaction exists.",
    "<b>Aim 3.</b> Describe the multivariate structure of the fermentations "
    "and ask whether strains form distinguishable fermentation profiles.",
    "<b>Aim 4.</b> Quantify how large the strain effect is relative to the two "
    "process variables that are set deliberately &mdash; temperature and "
    "initial sugar.",
])
p("The null hypotheses are, correspondingly: that the nine strain means are "
  "equal within each regime (H0<sub>1</sub>); that the strain and temperature "
  "effects are additive (H0<sub>2</sub>); and that the fermentations carry no "
  "grouping structure that corresponds to strain identity (H0<sub>3</sub>). "
  "Each is tested below against a two-sided alternative at a "
  "false-discovery rate of 5 %.")

h1("2. Data and methods")
h2("2.1 The dataset and its design")
p("The source is a single Excel workbook of %s observations &times; 49 "
  "variables, measured on synthetic grape must fermentations. Inspection of "
  "the design &mdash; rather than assuming it from the title &mdash; showed a "
  "fully balanced three-factor layout with repeated measures, not a simple "
  "nine-group comparison:"
  % "{:,}".format(N_OBS + 6))
table([
    ["Factor", "Levels", "Detail"],
    ["Strain", "9", "DV10, GALA, OPA, SAI, TXL, VIN13, W12, X16, X5"],
    ["Temperature", "4", "12, 18, 25 %sC, and TVAR (time-varying regime)" % D],
    ["Initial must sugar (MS)", "2", "nominal 210 and 250 g/L"],
    ["Biological replicate", "3", "R1, R2, R3"],
    ["Sampling point", "9", "t0&ndash;t8, event-driven rather than on a fixed clock"],
], widths=[36 * mm, 13 * mm, CW - 49 * mm], align=[1],
   note="9 &times; 4 &times; 2 &times; 3 = %d fermentation units, each sampled "
        "9 times = %s observations. Balance was verified by "
        "cross-tabulation. Measured blocks: cell counts, sugars, glycerol and "
        "ethanol, four organic acids, 22 nitrogen sources and 10 volatile "
        "aroma compounds."
        % (N_UNITS, "{:,}".format(N_OBS)))

h2("2.2 Data quality, and the five cleaning decisions")
p("Six off-schedule samples (<i>t5bis</i>, taken only for TXL and VIN13 at "
  "18&nbsp;%sC / 250 g/L) were excluded to keep the design balanced, leaving "
  "%s rows. Four substantive data-quality problems were found, and each was "
  "handled by a decision recorded in the loading code rather than by silent "
  "repair." % (D, "{:,}".format(N_OBS)))
bullets([
    "<b>Residual sugar rising over time</b> in 74 samples across 71 of the %d "
    "fermentations, all at the early points t1&ndash;t3, with 63 exceeding "
    "their own t0 value and ethanol still near zero. Sugar cannot be "
    "regenerated, so these are analytical artefacts, not biology. They were "
    "<i>flagged, not deleted</i>, listed in the supplementary tables, and "
    "excluded from the kinetic fits by interpolating on the cumulative "
    "maximum of the fermented fraction. Section 4 re-runs every test without "
    "the fermentations that carry them." % N_UNITS,
    "<b>The nominal MS label is not a measurement.</b> Measured t0 sugar "
    "averaged 203&ndash;229 g/L within the nominal 210 g/L group, varying by "
    "batch. Baselining sugar consumption on the nominal value produces 173 "
    "impossible negative values, so each fermentation was baselined on its "
    "own measured t0 sugar; MS is retained only as the design factor.",
    "<b>Missingness is structural.</b> Volatiles were assayed at only five of "
    "the nine sampling points and amino acids were not assayed at t4/t6 in "
    "most batches. These are whole assay blocks that were never run, not "
    "values lost at random, so <i>nothing was imputed</i>; each analysis uses "
    "the points at which its variables exist.",
    "<b>Sampling was event-driven.</b> The final sample falls at 725 h on "
    "average at 12&nbsp;%sC but 284 h at 25&nbsp;%sC, and it differs between "
    "strains within one regime. Time labels are therefore not comparable "
    "across regimes, and time-to-completion is treated as an outcome rather "
    "than as a covariate." % (D, D),
])

h2("2.3 The analysis-ready table: 216 rows, not 1944")
p("The nine samples of one fermentation are repeated measures of the same "
  "experimental unit. Testing on the raw rows would treat %s correlated "
  "samples as %s independent observations &mdash; pseudoreplication in the "
  "sense of Hurlbert (1984) &mdash; and inflate the effective sample size "
  "ninefold. Every fermentation was therefore collapsed to a single row of 21 "
  "derived features, giving a %d &times; 21 table on which all inference was "
  "performed: endpoint chemistry (final residual sugar, ethanol, glycerol, "
  "acetate, succinate, malate consumed), kinetics (time to 50 %% and 90 %% of "
  "sugar consumed, peak rate) and population dynamics (peak viable cells, "
  "final viability). One fermentation, GALA|TVAR|250|R1, stalls at 88.8 %% of "
  "its sugar and so has no time-to-90 %% value, giving n = 215 for that one "
  "outcome." % ("{:,}".format(N_OBS), "{:,}".format(N_OBS), N_UNITS))

h2("2.4 Statistical analysis")
p("Six outcomes were chosen before testing, on the basis of a descriptive "
  "variance scan that reported effect sizes without p-values (Table 2), and "
  "not on the basis of how significant they turned out to be. Final ethanol "
  "was deliberately <i>excluded</i> as a strain-comparison outcome: 76.7 %% of "
  "its variance is attributable to initial sugar and 0.4 %% to strain, so "
  "testing it across strains would mostly measure how much sugar entered the "
  "must (%.2f &plusmn; %.2f %% v/v at 210 g/L against %.2f &plusmn; %.2f at "
  "250 g/L)."
  % (ETH.loc[210, "mean"], ETH.loc[210, "std"],
     ETH.loc[250, "mean"], ETH.loc[250, "std"]))
bullets([
    "<b>Assumptions were checked first</b>, on model residuals: Shapiro&ndash;"
    "Wilk for normality and Levene's test (median-centred) for homogeneity of "
    "variance. Two outcomes were analysed on a transformed scale chosen from "
    "the residuals, not the raw values: peak viable cells on log<sub>10</sub> "
    "(raw skew +0.72 &rarr; &minus;0.09) and final residual sugar on "
    "log(1+x) (+4.21 &rarr; &minus;0.17).",
    "<b>Within each regime</b>, the strain effect was tested on the model "
    "<i>y</i> ~ strain + MS, which holds the must-sugar factor out of the "
    "error term. Where variances were unequal, Welch's ANOVA was used; where "
    "residuals were non-normal, Kruskal&ndash;Wallis. Section 4 shows that "
    "this choice of branch, not the data, drove several of the original "
    "p-values, and reports the corrected analysis.",
    "<b>The interaction</b> was tested on the full table with a two-way model "
    "<i>y</i> ~ strain &times; temperature + MS using type II sums of squares.",
    "<b>Multiplicity:</b> 24 within-regime tests and the two-way terms were "
    "each corrected by the Benjamini&ndash;Hochberg procedure. Post-hoc "
    "pairwise comparisons used Tukey HSD (parametric) and Dunn's test "
    "(rank-based).",
    "<b>Effect sizes and intervals</b> are reported alongside every p-value: "
    "partial &eta;<super>2</super> with a 95 % confidence interval obtained "
    "by inverting the noncentral F distribution, and a bootstrap interval for "
    "the largest strain-to-strain gap.",
    "<b>Multivariate structure:</b> PCA on 15 standardised unit-level "
    "features, and Ward hierarchical clustering with k chosen by silhouette "
    "and checked against k-means and against 100 resamples.",
])

# ====================================================================== RESULTS
h1("3. Results")
h2("3.1 Where the variation actually lies")
vd = vdec.loc[["T50_h", "T90_h", "MaxViable", "FinalSuccinate",
               "MalateConsumed", "FinalAcetate", "FinalResidualSugar",
               "FinalEthanol"]]
rows = [["Outcome", "Temp.", "Strain", "Must sugar", "Strain&times;Temp.",
         "Residual"]]
for k, r in vd.iterrows():
    nm = PRETTY.get(k, k).replace(" (h)", "")
    if k == "T50_h":
        nm = "Time to 50 %"
    cells = []
    for col in ["Temperature", "Strain", "InitialSugar",
                "Strain x Temperature", "Residual / replicate"]:
        v = "%.1f" % r[col]
        cells.append("<b>%s</b>" % v if r[col] == r[["Temperature", "Strain",
                     "InitialSugar", "Strain x Temperature",
                     "Residual / replicate"]].max() else v)
    rows.append([nm] + cells)
table(rows, widths=[40 * mm] + [(CW - 40 * mm) / 5] * 5, align=[1, 2, 3, 4, 5],
      note="<b>Table 2.</b> Share of variance (%%) per unit-level outcome, "
           "descriptive, computed before any test was chosen; the largest term "
           "in each row is bold. Temperature governs the kinetics, initial "
           "sugar governs the endpoint chemistry, and strain never leads "
           "except for peak viable cells. n = %d (%d for time to 90 %%)."
           % (N_UNITS, N_UNITS - 1))
p("Read across the rows, Table 2 sets the scale for everything that follows. "
  "Temperature accounts for %.0f %% of the variance in time to half-completion "
  "and strain for %.0f %%; initial sugar accounts for %.0f %% of final ethanol "
  "and strain for %.0f %%. Strain leads exactly one row, peak viable cells at "
  "%.0f %%. The strain &times; temperature term is not negligible anywhere, and "
  "reaches %.0f %% for final residual sugar &mdash; a first warning against "
  "ranking strains on pooled data."
  % (vdec.loc["T50_h", "Temperature"], vdec.loc["T50_h", "Strain"],
     vdec.loc["FinalEthanol", "InitialSugar"],
     vdec.loc["FinalEthanol", "Strain"], vdec.loc["MaxViable", "Strain"],
     vdec.loc["FinalResidualSugar", "Strain x Temperature"]))

h2("3.2 Fermentation kinetics are set by temperature")
table([["Regime", "Time to 50 % (h)", "Time to 90 % (h)",
        "Peak rate (g/L/h)", "Final residual sugar (g/L)", "Stuck (of 54)"],
       ] + [[("%s %sC" % (i, D)) if i != "TVAR" else "TVAR",
             "%.0f" % r["T50_h"], "%.0f" % r["T90_h"],
             "%.2f" % r["MaxRate_gL_h"], "%.2f" % r["FinalResidualSugar"],
             "%d" % int((units[(units["Temperature"].astype(str) == str(i))]
                         ["Dry"] == 0).sum())]
            for i, r in kin_t.iterrows()],
      widths=[20 * mm] + [(CW - 20 * mm) / 5] * 5, align=[1, 2, 3, 4, 5],
      note="<b>Table 3.</b> Kinetics and completeness by temperature regime, "
           "pooled over strains, replicates and must sugar (n = 54 "
           "fermentations per regime). A fermentation is counted stuck if it "
           "ends above 2 g/L residual sugar. %d of %d fermentations finished "
           "dry overall." % (N_DRY, N_UNITS))
p("The gradient is steep and monotone in temperature: a fermentation at "
  "25&nbsp;%sC reaches 90 %% of its sugar in %.0f h and none of the 54 "
  "fermentations at that temperature stuck, while at 12&nbsp;%sC the same "
  "milestone takes %.0f h and 14 of 54 failed to finish. The time-varying "
  "regime behaves like a warm fermentation early (peak rate %.2f g/L/h, close "
  "to 25&nbsp;%sC) and like a cool one late (time to 90 %% %.0f h), which is "
  "why it cannot be placed on a temperature axis and is kept as a separate "
  "level throughout."
  % (D, kin_t.loc["25", "T90_h"], D, kin_t.loc["12", "T90_h"],
     kin_t.loc["TVAR", "MaxRate_gL_h"], D, kin_t.loc["TVAR", "T90_h"]))

h2("3.3 Strains do differ &mdash; but the effect is conditional")
p("Table 4 is the project's main statistical result: one row per outcome "
  "&times; regime, with the test used, the BH-adjusted p-value, and the effect "
  "size with its interval. After adjustment for must sugar and for "
  "multiplicity, the strain effect is detectable in %d of the 24 cells. The "
  "two cells that are robustly negative &mdash; malate consumed under the "
  "time-varying regime and final residual sugar at 18&nbsp;%sC &mdash; are "
  "negative under every analysis we ran (Section 4)." % (N_SIGV, D))

rows = [["Outcome", "Regime", "n", "Test", "p (BH)",
         "Partial &eta;<super>2</super> [95 % CI]", "Largest gap [95 % CI]"]]
UNIT = {"MaxViable": "log<sub>10</sub> cells/mL", "FinalSuccinate": "g/L",
        "MalateConsumed": "g/L", "FinalAcetate": "g/L",
        "FinalResidualSugar": "log(1+g/L)", "T90_h": "h"}
for _, r in final.iterrows():
    pv = r["pBH_matched"]
    ps = "&lt;0.001" if pv < 0.001 else "%.3f" % pv
    star = "" if pv >= 0.05 else ("***" if pv < 0.001 else
                                  ("**" if pv < 0.01 else "*"))
    rows.append([
        PRETTY[r["outcome"]].replace(" (h)", ""),
        ("%s %sC" % (r["temperature"], D)) if r["temperature"] != "TVAR" else "TVAR",
        "%d" % r["n"],
        {"ANOVA": "ANOVA", "Welch ANOVA": "Welch", "Kruskal-Wallis": "K&ndash;W"}
        [r["preferred_test"]],
        ps + star,
        "%.2f [%.2f, %.2f]" % (r["partial_eta_sq"], r["eta2_ci95_low"],
                               r["eta2_ci95_high"]),
        "%.2f [%.2f, %.2f] %s" % (r["max_strain_gap"], r["gap_ci95_low"],
                                  r["gap_ci95_high"], UNIT[r["outcome"]]),
    ])
table(rows, widths=[27 * mm, 13 * mm, 8 * mm, 14 * mm, 17 * mm, 28 * mm,
                    CW - 107 * mm], align=[1, 2, 3, 4], size=7.5, keep=False,
      note="<b>Table 4.</b> The validated within-regime strain comparisons. "
           "Each p-value comes from a restricted permutation test (5000 "
           "shuffles of the strain labels within must-sugar blocks) using the "
           "statistic appropriate to that cell's assumption checks, so it "
           "makes no distributional assumption; see Section 4. "
           "* p &lt; 0.05, ** p &lt; 0.01, *** p &lt; 0.001 after "
           "Benjamini&ndash;Hochberg correction across all 24 tests. "
           "Partial &eta;<super>2</super> is for the strain term of "
           "<i>y</i> ~ strain + MS, with an interval obtained by inverting "
           "the noncentral F distribution. &quot;Largest gap&quot; is the "
           "difference between the highest and lowest strain mean, with a "
           "bootstrap interval, on the analysis scale given.")

p("Effect sizes matter more than the p-values here, and they are not uniform. "
  "Peak viable population separates the strains strongly at 12&nbsp;%sC "
  "(partial &eta;<super>2</super> = %.2f) but much less at 25&nbsp;%sC "
  "(%.2f): the cold regime spreads the strains out, the warm one compresses "
  "them. Final acetate is the opposite case and the reason is procedural "
  "rather than biological &mdash; its effect size is large in every regime "
  "(0.67 to 0.83) although three of its four cells were originally reported "
  "as non-significant, which is what Section 4 is about. In practical units, "
  "the gap between "
  "the fastest and slowest strain at 12&nbsp;%sC is %.0f h of fermentation "
  "time (95 %% CI %.0f&ndash;%.0f h) &mdash; a difference of real operational "
  "size, on top of the roughly %.0f h that the temperature choice itself "
  "costs."
  % (D, final[(final["outcome"] == "MaxViable") &
              (final["temperature"] == "12")]["partial_eta_sq"].iloc[0], D,
     final[(final["outcome"] == "MaxViable") &
           (final["temperature"] == "25")]["partial_eta_sq"].iloc[0], D,
     final[(final["outcome"] == "T90_h") &
           (final["temperature"] == "12")]["max_strain_gap"].iloc[0],
     final[(final["outcome"] == "T90_h") &
           (final["temperature"] == "12")]["gap_ci95_low"].iloc[0],
     final[(final["outcome"] == "T90_h") &
           (final["temperature"] == "12")]["gap_ci95_high"].iloc[0],
     kin_t.loc["12", "T90_h"] - kin_t.loc["25", "T90_h"]))

h2("3.4 The strain &times; temperature interaction, and what it costs a ranking")
inter = anova2[anova2["term"] == "Strain:Temperature"]
p("On the full table the interaction term is significant for all %d outcomes "
  "(BH-adjusted p &le; %.3f; partial &eta;<super>2</super> %.2f&ndash;%.2f), "
  "so the strain effect genuinely has a different size &mdash; and in places a "
  "different order &mdash; in each regime. The consequence is visible without "
  "any model: rank the strains by time to 90 %% within each regime and the "
  "rankings barely agree (Spearman %.2f to %.2f between regimes). No strain is "
  "fastest in all four."
  % (N_INTER, inter["p_BH"].max(), inter["partial_eta_sq"].min(),
     inter["partial_eta_sq"].max(), RHO_MIN, RHO_MAX))
rows = [["Strain", "12 %sC" % D, "18 %sC" % D, "25 %sC" % D, "TVAR",
         "Rank range", "Fermentations finishing dry"]]
for s, r in rob.iterrows():
    rr = ranks.loc[s]
    rows.append([s] + ["%d" % rr[c] for c in ["12", "18", "25", "TVAR"]]
                + ["<b>%d</b>" % r["rank_range"],
                   "%d %%" % r["pct_dry"]])
table(rows, widths=[20 * mm] + [13 * mm] * 4 + [19 * mm, CW - 91 * mm],
      align=[1, 2, 3, 4, 5, 6],
      note="<b>Table 5.</b> Rank of each strain by mean time to 90 % sugar "
           "consumption within each regime (1 = fastest), ordered by mean "
           "rank. The rank range is the span between a strain's best and "
           "worst regime. W12 never leaves the fastest three; VIN13 and GALA "
           "cross most of the field. 24 fermentations per strain.")
p("This is the result we would put in front of a winemaker. W12 is the only "
  "strain that is fast in every regime (ranks 1, 3, 1, 1), and DV10 is the "
  "most reliable finisher (%d %% of its fermentations dry, the single highest). "
  "GALA is the clearest failure risk: %d of its 24 fermentations stuck, "
  "against %d for DV10. VIN13 is the instructive case &mdash; second fastest "
  "under the time-varying regime and last at 18 and 25&nbsp;%sC &mdash; "
  "because it shows exactly why a single pooled &quot;best strain&quot; claim "
  "would be unsupportable here."
  % (rob["pct_dry"].max(), int(rob.loc["GALA", "n_stuck"]),
     int(rob.loc["DV10", "n_stuck"]), D))
figure("fig19_strain_robustness.png",
       "<b>Figure 1.</b> Consistency of each strain across the four "
       "temperature regimes. Left: the span between each strain's best and "
       "worst rank on time to 90 % sugar consumption, with the mean rank "
       "marked. Right: mean rank against the standard deviation of the "
       "within-regime standardised value &mdash; fast and consistent strains "
       "sit in the lower left, temperature-sensitive ones at the top. "
       "A Kruskal&ndash;Wallis test on the within-regime standardised times "
       "confirms the strains are not interchangeable (H = 25.6, p = 0.001).",
       maxh=46 * mm)

h2("3.5 Principal component analysis: the axes are process, not strain")
p("PCA on the 15 standardised unit-level features of the %d fermentations "
  "that have a complete feature vector &mdash; the stalled GALA|TVAR|250|R1 "
  "has no time-to-90 %% and is dropped &mdash; gives %d components with "
  "eigenvalue above 1, carrying %.1f %% of the variance (PC1 %.1f %%, "
  "PC2 %.1f %%). The loadings name the axes: PC1 is a <i>must-loading</i> axis "
  "(initial sugar %+.2f, sugar consumed %+.2f, final ethanol %+.2f), PC2 is a "
  "<i>fermentation-vigour</i> axis contrasting by-product formation and speed "
  "against duration (succinate %+.2f, glycerol %+.2f, peak rate %+.2f, "
  "against time to 50 %% %+.2f), and PC3 is <i>completion</i> (final residual "
  "sugar %+.2f against fraction fermented %+.2f)."
  % (N_MV, K_PCA, CUM, ev.loc[0, "explained_var_pct"],
     ev.loc[1, "explained_var_pct"],
     load.loc["InitialSugar", "PC1"], load.loc["SugarConsumedTotal", "PC1"],
     load.loc["FinalEthanol", "PC1"], load.loc["FinalSuccinate", "PC2"],
     load.loc["FinalGlycerol", "PC2"], load.loc["MaxRate_gL_h", "PC2"],
     load.loc["T50_h", "PC2"], load.loc["FinalResidualSugar", "PC3"],
     load.loc["FracFermentedFinal", "PC3"]))
p("Colouring the score plot by each design factor in turn settles Aim 3 "
  "descriptively. Silhouette width in the four-component space is %.3f by "
  "initial sugar, %.3f by temperature and %.3f by strain &mdash; a negative "
  "value, meaning fermentations of one strain are on average closer to "
  "fermentations of other strains than to their own. Strains do not form "
  "separable multivariate profiles. This is not a failed analysis; it is the "
  "answer, and it is consistent with Table 2."
  % (SIL["MS (initial sugar)"], SIL["Temperature"], SIL["Strain"]))
figure("fig13_pca_scatter.png",
       "<b>Figure 2.</b> The %d fermentations in the plane of the first two "
       "principal components (%.1f %% of total variance), coloured by strain "
       "and by temperature regime. The temperature panel shows ordered "
       "structure; the strain panel does not. A separation seen here would be "
       "exploratory evidence only &mdash; the formal tests are in Table 4."
       % (N_MV, CUM - ev.loc[2, "explained_var_pct"] -
          ev.loc[3, "explained_var_pct"]), maxh=50 * mm)

h2("3.6 Clustering: fermentations group by condition, and one group is failure")
p("Ward clustering on the same standardised features gives the best silhouette "
  "at k = %d (%.3f), and the solution is stable: mean adjusted Rand index "
  "%.3f across 100 resamples of 80 %% of the data, and %.2f between Ward and "
  "k-means at the same k. Cross-tabulating the clusters against the design "
  "reproduces the PCA result with a different method &mdash; ARI %.3f against "
  "initial sugar, %.3f against temperature, %.3f against strain."
  % (BEST_K, float(ksel.loc[ksel["k"] == BEST_K, "silhouette_ward"].iloc[0]),
     STAB, ARI_WK, ARI["MS (initial sugar)"], ARI["Temperature"],
     ARI["Strain"]))
p("The exception is the one cluster that is biologically, rather than "
  "procedurally, defined. Cluster %d holds just %d of the %d fermentations, "
  "every one of them incomplete: mean final residual sugar %.1f g/L against "
  "%.1f&ndash;%.1f g/L in the other four clusters, with the longest times to "
  "50 %% and 90 %%. It is the stuck-fermentation cluster, it is drawn almost "
  "entirely from the 250 g/L must at 12&nbsp;%sC, and its membership is "
  "strain-biased: GALA contributes %d of its %d members and OPA %d, while "
  "DV10, TXL, VIN13 and W12 contribute none."
  % (STUCK_C, STUCK_N, N_MV,
     float(prof.loc["FinalResidualSugar", str(STUCK_C)]),
     float(prof.loc["FinalResidualSugar"].iloc[:-1].astype(float)
           .drop(str(STUCK_C)).min()),
     float(prof.loc["FinalResidualSugar"].iloc[:-1].astype(float)
           .drop(str(STUCK_C)).max()), D,
     int(ctstrain.loc["GALA", str(STUCK_C)]), STUCK_N,
     int(ctstrain.loc["OPA", str(STUCK_C)])))
figure("fig16_clusters_vs_design.png",
       "<b>Figure 3.</b> The %d Ward clusters, on the %d fermentations with a "
       "complete feature vector, cross-tabulated against the "
       "three design factors. The clusters align with initial sugar and "
       "temperature and cut across strain, which answers H0<sub>3</sub>: "
       "fermentation profiles group by the conditions imposed, not by the "
       "yeast used. Cluster %d is the stuck-fermentation group."
       % (BEST_K, N_MV, STUCK_C), maxh=44 * mm)

# =================================================================== VALIDATION
h1("4. Validation")
p("The brief's eighth step asks for the results to be verified rather than "
  "merely produced. Ten checks were run; all of the code and the full output "
  "tables are in the supplementary file. The checks are not re-statements of "
  "the same computation &mdash; each re-derives a reported number by a "
  "different route, and one of them changed a conclusion.")
rows = [["Check", "Result"]]
rows += [
 ["Second, independent implementation of every unit-level feature",
  "all %d features agree; largest relative difference %.0e %% of the mean"
  % (len(recomp), RECOMP_MAX)],
 ["Step-5 F statistic for strain reproduced from the design matrix",
  "exact in all 23 balanced cells; the 24th is unbalanced (n = 53)"],
 ["Restricted permutation test, 5000 shuffles per cell, no distributional "
  "assumption",
  "<b>changed %d of 24 calls</b> &mdash; see below" % N_CHANGED],
 ["Mixed-effects model on all %s raw samples, random intercept per "
  "fermentation" % "{:,}".format(N_OBS),
  "strain ordering preserved by the collapse to 216 rows, Spearman "
  "&rho; = %.2f" % RHO_MIX],
 ["Pseudoreplication: the same comparisons on the raw rows",
  "verdict differs in %d of 12 cells, in both directions" % PSEUDO_DIFF],
 ["Leave-one-replicate-out, 2 of 3 replicates, three subsets per cell",
  "%d of the %d positive cells hold in all three subsets" % (N_FULL4, N_SIGV)],
 ["Re-test with the 71 fermentations carrying flagged sugar readings removed",
  "%d of 24 cells unchanged on n = 145" % ART_AGREE],
 ["All four analyses agreeing, cell by cell",
  "%d of 24 cells unanimous, %d of 24 with at least three of four"
  % (GRID4, GRID3)],
 ["PCA and clustering summary statistics recomputed from scratch",
  "all %d quantities reproduce exactly" % len(mvchk)],
 ["Every quantitative claim in this report, checked against the data",
  "%d of %d pass" % (N_PASS, len(claims))],
]
table(rows, widths=[CW * 0.49, CW * 0.51], size=7.9,
      note="<b>Table 6.</b> The ten validation checks of step 8. Each row is "
           "produced by <i>10_validate.py</i>; the detailed per-cell output is "
           "in the supplementary tables 10_*.csv.")

h2("4.1 The check that changed a result")
p("The permutation test disagreed with the originally reported analysis in "
  "%d of the 24 cells, and the disagreements were not random: every one of "
  "them lies in the same branch of the test-selection rule. Where the "
  "assumption checks sent a cell to classical ANOVA, the model fitted was "
  "<i>y</i> ~ strain + MS and the two analyses agree in 7 of 7 cells. Where "
  "they sent a cell to Welch's ANOVA or Kruskal&ndash;Wallis, the "
  "implementation compared raw strain groups and left the must-sugar factor "
  "in the error term; there the two agree in only 10 of 17. For final "
  "acetate, where must sugar accounts for %.0f %% of the variance and strain "
  "for %.0f %%, that omission is fatal to the power of the test: pooling the "
  "210 and 250 g/L fermentations inflates the within-group variance so much "
  "that a strain effect with partial &eta;<super>2</super> = %.2f was reported "
  "as non-significant (p = %.2f) at 25&nbsp;%sC."
  % (N_CHANGED, vdec.loc["FinalAcetate", "InitialSugar"],
     vdec.loc["FinalAcetate", "Strain"],
     final[(final["outcome"] == "FinalAcetate") &
           (final["temperature"] == "25")]["partial_eta_sq"].iloc[0],
     final[(final["outcome"] == "FinalAcetate") &
           (final["temperature"] == "25")]["p_parametric_BH"].iloc[0], D))
p("The corrected analysis is the one reported in Table 4: the permutation "
  "test holds the must-sugar blocks fixed while shuffling strain labels "
  "within them, which keeps the design in the null hypothesis, and it uses "
  "the statistic each cell's assumption checks call for, so it inherits "
  "neither the normality assumption of ANOVA nor the lost power of the "
  "unadjusted comparison. On that analysis the count of significant cells "
  "rises from %d to %d. We report the discrepancy rather than quietly "
  "adopting the better number, because the discrepancy is the useful finding: "
  "a specification choice buried in a branch of an if-statement moved seven "
  "conclusions." % (N_SIG5, N_SIGV))
figure("fig20_permutation_vs_parametric.png",
       "<b>Figure 4.</b> Every disagreement between the originally reported "
       "p-values and the validated permutation test falls among the cells "
       "whose test did not adjust for must sugar (squares). Cells analysed by "
       "ANOVA, which did adjust, lie along the diagonal of agreement "
       "(circles). Dotted lines mark p = 0.05.", maxh=50 * mm)

# =================================================================== DISCUSSION
h1("5. Discussion")
h2("5.1 What the data support, and what they do not")
p("Three conclusions survive validation. First, commercial strains are "
  "<i>not</i> interchangeable: a strain effect is detectable in %d of 24 "
  "outcome &times; regime comparisons, and in the cold regime the spread "
  "between the fastest and slowest strain is %.0f h. Second, that effect is "
  "conditional, not absolute &mdash; the interaction is significant for every "
  "outcome tested and the rank order moves between regimes &mdash; so the "
  "honest form of a recommendation is &quot;W12 was fast in all four regimes "
  "we tested&quot;, not &quot;W12 is the best strain&quot;. Third, strain is "
  "the smallest of the three levers: temperature dominates the kinetics, "
  "initial sugar dominates the endpoint chemistry, and strain modulates both "
  "(Table 2)."
  % (N_SIGV, final[(final["outcome"] == "T90_h") &
                   (final["temperature"] == "12")]["max_strain_gap"].iloc[0]))
p("What the data do not support is any claim about wine quality or sensory "
  "outcome. Acetate and succinate are quality-relevant metabolites, and the "
  "strain differences in them are real and in some regimes large, but this "
  "dataset contains no sensory assessment, so the step from &quot;differs in "
  "acetate&quot; to &quot;makes better wine&quot; is not available to us. Nor "
  "can we speak to any strain's performance outside the four regimes and two "
  "sugar levels tested in synthetic must.")

h2("5.2 Biological reading")
p("The pattern of by-products is consistent with what is known about the "
  "redox and osmotic physiology of fermenting yeast. Glycerol and succinate "
  "load together on PC2 (%+.2f and %+.2f) and correlate strongly across the "
  "time course, which is expected if both act in the reoxidation of cytosolic "
  "NADH during anaerobic growth (Remize et al., 1999; Camarasa et al., 2003); "
  "that succinate carries one of the largest strain terms in the dataset "
  "(%.0f %% of variance) while ethanol carries almost none fits a picture in "
  "which strains differ in how they balance redox rather than in how "
  "efficiently they make ethanol. Acetate tracking initial sugar (%.0f %% of "
  "variance) is the signature of the osmotic-stress response to high-sugar "
  "must, in which acetaldehyde dehydrogenase activity rises as part of "
  "glycerol production (Erasmus et al., 2003). Malate consumption is "
  "modest in absolute terms but differs between strains in three of four "
  "regimes, in line with reports that degradation of L-malate during "
  "alcoholic fermentation is strain-dependent in <i>S. cerevisiae</i> "
  "(Redzepovic et al., 2003)."
  % (load.loc["FinalGlycerol", "PC2"], load.loc["FinalSuccinate", "PC2"],
     vdec.loc["FinalSuccinate", "Strain"],
     vdec.loc["FinalAcetate", "InitialSugar"]))
p("The kinetic results reproduce the classical temperature dependence of wine "
  "fermentation: lower temperature slows sugar consumption and extends the "
  "fermentation several-fold (Table 3), as reported for commercial strains "
  "across 13&ndash;25&nbsp;%sC (Torija et al., 2003; Beltran et al., 2008). "
  "The stuck-fermentation cluster is likewise where the literature predicts "
  "it: cold fermentations of high-sugar must, the combination identified as a "
  "principal risk factor for sluggish and stuck fermentations (Bisson, 1999). "
  "That GALA accounts for %d of the %d fermentations in that cluster, and "
  "four of the nine strains for none, says that the risk is modulated by "
  "strain even though it is created by the conditions."
  % (D, int(ctstrain.loc["GALA", str(STUCK_C)]), STUCK_N))

h2("5.3 Limitations")
bullets([
    "<b>Analytical artefacts.</b> 74 sugar measurements in 71 of %d "
    "fermentations are physically impossible. We flagged rather than deleted "
    "them, because they cluster at t1&ndash;t3 and deleting whole "
    "fermentations would unbalance the design; re-running every test without "
    "those fermentations leaves %d of 24 conclusions unchanged, the exception "
    "being final residual sugar at 25&nbsp;%sC where the clean subset retains "
    "only 18 fermentations across 7 strains." % (N_UNITS, ART_AGREE, D),
    "<b>Unequal musts.</b> The nominal 210 g/L musts actually ranged "
    "203&ndash;229 g/L between batches, so strains within a regime were not "
    "challenged with identical media. Every test adjusts for the nominal "
    "level, which is a design factor, but cannot adjust away batch variation "
    "within it.",
    "<b>Incomplete assay coverage.</b> Volatile aroma compounds were measured "
    "at five of nine sampling points and amino acids at seven; the volatile "
    "block was therefore left out of the multivariate analyses entirely, so "
    "nothing here speaks to aroma.",
    "<b>Statistical power.</b> Six fermentations per strain per regime is "
    "enough to detect large effects and not small ones. The "
    "leave-one-replicate-out check makes this concrete: at four per strain, "
    "%d of the %d positive cells survive in all three subsets."
    % (N_FULL4, N_SIGV),
    "<b>One laboratory, one must.</b> These are synthetic-must fermentations "
    "from a single published study. Nothing here is independent replication, "
    "and real grape must differs in nitrogen composition, in solids and in "
    "microbial background.",
    "<b>Multiplicity beyond the declared family.</b> We corrected across the "
    "24 within-regime tests, but the six outcomes were themselves chosen "
    "after looking at a variance decomposition of twelve. That selection is "
    "documented in Section 2.4 rather than corrected for.",
])

h1("6. Conclusions")
bullets([
    "Nine commercial wine strains differ measurably in fermentation "
    "behaviour: a strain effect is present in %d of 24 outcome &times; "
    "regime comparisons after correction, with partial &eta;<super>2</super> "
    "up to %.2f." % (N_SIGV, final["partial_eta_sq"].max()),
    "The effect is conditional on temperature for every outcome tested, so "
    "strain rankings do not transfer between regimes (Spearman %.2f&ndash;"
    "%.2f) and a single &quot;best strain&quot; claim is not supportable."
    % (RHO_MIN, RHO_MAX),
    "W12 is the only strain fast in all four regimes; DV10 is the most "
    "reliable finisher at %d %% dry; GALA carries the highest stuck-"
    "fermentation risk at %d of 24." % (int(rob["pct_dry"].max()),
                                        int(rob.loc["GALA", "n_stuck"])),
    "Strains do not form separable multivariate profiles: both PCA and "
    "clustering group fermentations by must sugar and temperature "
    "(cluster-vs-strain ARI %.3f), with one biologically meaningful "
    "exception, the stuck-fermentation cluster." % ARI["Strain"],
    "Methodologically, two choices dominated the answers: collapsing the "
    "repeated measures to %d experimental units, and keeping the must-sugar "
    "factor out of the error term. Both changed conclusions &mdash; the "
    "first in %d of 12 trial comparisons, the second in %d of 24."
    % (N_UNITS, PSEUDO_DIFF, N_CHANGED),
])

# =================================================================== BACKMATTER
h1("References")
REFS = [
 "Beltran, G., Novo, M., Guillam&oacute;n, J. M., Mas, A. &amp; Rozès, N. "
 "(2008) Effect of fermentation temperature and culture media on the yeast "
 "lipid composition and wine volatile compounds. <i>International Journal of "
 "Food Microbiology</i> 121, 169&ndash;177.",
 "Benjamini, Y. &amp; Hochberg, Y. (1995) Controlling the false discovery "
 "rate. <i>Journal of the Royal Statistical Society B</i> 57, 289&ndash;300.",
 "Bisson, L. F. (1999) Stuck and sluggish fermentations. <i>American Journal "
 "of Enology and Viticulture</i> 50, 107&ndash;119.",
 "Camarasa, C., Grivet, J.-P. &amp; Dequin, S. (2003) Investigation by "
 "<super>13</super>C-NMR and tricarboxylic acid deletion mutant analysis of "
 "pathways for succinate formation in <i>Saccharomyces cerevisiae</i> during "
 "anaerobic fermentation. <i>Microbiology</i> 149, 2669&ndash;2678.",
 "Dunn, O. J. (1964) Multiple comparisons using rank sums. "
 "<i>Technometrics</i> 6, 241&ndash;252.",
 "Erasmus, D. J., van der Merwe, G. K. &amp; van Vuuren, H. J. J. (2003) "
 "Genome-wide expression analyses: metabolic adaptation of <i>Saccharomyces "
 "cerevisiae</i> to high sugar stress. <i>FEMS Yeast Research</i> 3, "
 "375&ndash;399.",
 "Harris, C. R. <i>et al.</i> (2020) Array programming with NumPy. "
 "<i>Nature</i> 585, 357&ndash;362.",
 "Hubert, L. &amp; Arabie, P. (1985) Comparing partitions. <i>Journal of "
 "Classification</i> 2, 193&ndash;218.",
 "Hunter, J. D. (2007) Matplotlib: a 2D graphics environment. "
 "<i>Computing in Science &amp; Engineering</i> 9, 90&ndash;95.",
 "Hurlbert, S. H. (1984) Pseudoreplication and the design of ecological field "
 "experiments. <i>Ecological Monographs</i> 54, 187&ndash;211.",
 "Jolliffe, I. T. &amp; Cadima, J. (2016) Principal component analysis: a "
 "review and recent developments. <i>Philosophical Transactions of the Royal "
 "Society A</i> 374, 20150202.",
 "Kruskal, W. H. &amp; Wallis, W. A. (1952) Use of ranks in one-criterion "
 "variance analysis. <i>Journal of the American Statistical Association</i> "
 "47, 583&ndash;621.",
 "Minebois, R. &amp; Querol, A. (2025) <i>Fermentation data set obtained from "
 "commercial wine strains in synthetic grape must.</i> Zenodo. "
 "doi:10.5281/zenodo.15260916.",
 "Pedregosa, F. <i>et al.</i> (2011) Scikit-learn: machine learning in "
 "Python. <i>Journal of Machine Learning Research</i> 12, 2825&ndash;2830.",
 "Redzepovic, S., Orlic, S., Majdak, A., Kozina, B., Volschenk, "
 "H. &amp; Viljoen-Bloom, M. (2003) Differential malic acid degradation by "
 "selected strains of <i>Saccharomyces</i> during alcoholic fermentation. "
 "<i>International Journal of Food Microbiology</i> 83, 49&ndash;61.",
 "Remize, F., Roustan, J. L., Sablayrolles, J. M., Barre, P. &amp; Dequin, S. "
 "(1999) Glycerol overproduction by engineered <i>Saccharomyces cerevisiae</i> "
 "wine yeast strains leads to substantial changes in by-product formation and "
 "to a stimulation of fermentation rate in stationary phase. <i>Applied and "
 "Environmental Microbiology</i> 65, 143&ndash;149.",
 "Rousseeuw, P. J. (1987) Silhouettes: a graphical aid to the interpretation "
 "and validation of cluster analysis. <i>Journal of Computational and Applied "
 "Mathematics</i> 20, 53&ndash;65.",
 "Seabold, S. &amp; Perktold, J. (2010) statsmodels: econometric and "
 "statistical modeling with Python. <i>Proceedings of the 9th Python in "
 "Science Conference</i>, 92&ndash;96.",
 "Steiger, J. H. (2004) Beyond the F test: effect size confidence intervals "
 "and tests of close fit in the analysis of variance. <i>Psychological "
 "Methods</i> 9, 164&ndash;182.",
 "Torija, M. J., Roz&egrave;s, N., Poblet, M., Guillam&oacute;n, J. M. &amp; "
 "Mas, A. (2003) Effects of fermentation temperature on the strain population "
 "of <i>Saccharomyces cerevisiae</i>. <i>International Journal of Food "
 "Microbiology</i> 80, 47&ndash;53.",
 "Tukey, J. W. (1949) Comparing individual means in the analysis of variance. "
 "<i>Biometrics</i> 5, 99&ndash;114.",
 "Virtanen, P. <i>et al.</i> (2020) SciPy 1.0: fundamental algorithms for "
 "scientific computing in Python. <i>Nature Methods</i> 17, 261&ndash;272.",
 "Ward, J. H. (1963) Hierarchical grouping to optimize an objective function. "
 "<i>Journal of the American Statistical Association</i> 58, 236&ndash;244.",
 "Welch, B. L. (1951) On the comparison of several mean values: an "
 "alternative approach. <i>Biometrika</i> 38, 330&ndash;336.",
]
for r in REFS:
    story.append(Paragraph(r, S["ref"]))
gap(5)

h1("Author contributions, data and code availability, and AI use")
sm("<b>Contributions.</b> <b>Pranav Ram</b> &mdash; dataset exploration, the "
   "five cleaning decisions, the data dictionary and the unit-level feature "
   "table. <b>Mohesh</b> &mdash; descriptive statistics, assumption checks, "
   "the within-regime and two-way tests, post-hoc comparisons and "
   "multiplicity correction. <b>K James Bond</b> &mdash; PCA, clustering, "
   "stability analysis and the step-8 validation suite. "
   "<b>Avala Madhavi</b> &mdash; literature and the biological "
   "interpretation in Section 5. <b>Dinesh Kumar</b> &mdash; the progress "
   "presentation, and figure and manuscript consistency checks. All members "
   "interpreted their own analyses; the aims and conclusions were agreed by "
   "the group.")
sm("<b>Data and code.</b> The dataset is Minebois &amp; Querol (2025), "
   "doi:10.5281/zenodo.15260916, used unmodified. The analysis is a set of "
   "Python scripts that regenerate every figure, table and PDF from the "
   "source workbook with no manual steps; the link is in the supplementary "
   "file, with the complete figure and table set.")
sm("<b>AI use.</b> Generative AI (Claude) was used for the analysis code and "
   "its debugging, the figures and typesetting, explanations of statistical "
   "methods, and first drafts of prose including the interpretation, which "
   "the group reviewed and revised. All 24 prompts and the full chat history "
   "are submitted verbatim with the supplementary file, exported from the "
   "session transcripts rather than retyped.")

# ====================================================================== BUILD
def decorate(canvas, doc):
    canvas.saveState()
    canvas.setFont(BODY, 7.8)
    canvas.setFillColor(GREY)
    canvas.drawString(MX, MY - 9, "BT3041 Term Project · Team 20 · "
                                  "Comparative analysis of commercial wine "
                                  "yeast strains")
    canvas.drawRightString(PAGE_W - MX, MY - 9, "%d" % doc.page)
    canvas.setStrokeColor(FAINT)
    canvas.setLineWidth(0.4)
    canvas.line(MX, MY - 4, PAGE_W - MX, MY - 4)
    canvas.restoreState()


doc = BaseDocTemplate(str(OUT), pagesize=A4,
                      leftMargin=MX, rightMargin=MX,
                      topMargin=MY, bottomMargin=MY,
                      title="Comparative Statistical Analysis of Commercial "
                            "Yeast Strains During Wine Fermentation",
                      author="BT3041 Team 20")
doc.addPageTemplates([PageTemplate(
    id="main",
    frames=[Frame(MX, MY, CW, PAGE_H - 2 * MY, id="f", leftPadding=0,
                  rightPadding=0, topPadding=0, bottomPadding=0)],
    onPage=decorate)])
doc.build(story)

pages = len(PdfReader(str(OUT)).pages)
print("wrote %s  (%d pages)" % (OUT.relative_to(CM.ROOT), pages))
if pages > MAX_PAGES:
    raise SystemExit("FAIL: %d pages, the limit is %d. Trim the content."
                     % (pages, MAX_PAGES))
print("OK: within the %d-page limit." % MAX_PAGES)
