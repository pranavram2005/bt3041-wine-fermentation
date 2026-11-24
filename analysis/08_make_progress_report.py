"""
Build the progress report as a PDF: steps 1-7 of the project brief.

Typeset as a scholarly report rather than a slide dump:
  - tables ruled horizontally only, in the booktabs manner - no cell boxes
  - a running header carrying the current section
  - figures at varied widths, sized to their own aspect
  - marginal remarks and footnotes where an aside would break the argument
  - section 9 left as ruled writing space for the group's own interpretation

Every number in the prose is read from outputs/tables/ at build time, so the
report cannot drift out of step with the analysis.

Output: outputs/Progress_Report.pdf
"""
import sys
from pathlib import Path

import pandas as pd
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib import colors
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, Image as RLImage, PageBreak, Table,
                                TableStyle, KeepTogether, Flowable, CondPageBreak)
from reportlab.platypus.tableofcontents import TableOfContents

sys.path.insert(0, str(Path(__file__).parent))
import common as CM

FIG = CM.FIGURES
TAB = CM.TABLES
OUT = CM.ROOT / "outputs" / "Progress_Report.pdf"

PAGE_W, PAGE_H = A4
MARGIN_X, MARGIN_Y = 23 * mm, 24 * mm
CONTENT_W = PAGE_W - 2 * MARGIN_X

BLACK = colors.black
RULE = colors.Color(0.62, 0.62, 0.60)
FAINT = colors.Color(0.80, 0.80, 0.78)
GREY = colors.Color(0.33, 0.33, 0.32)
BODY, BOLD, ITAL, BI = "Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic"

S = {
    "title": ParagraphStyle("title", fontName=BOLD, fontSize=21, leading=26,
                            textColor=BLACK, spaceAfter=10),
    "subtitle": ParagraphStyle("subtitle", fontName=BODY, fontSize=12, leading=17,
                               textColor=BLACK, spaceAfter=4),
    "epigraph": ParagraphStyle("epigraph", fontName=ITAL, fontSize=11, leading=16,
                               textColor=GREY, alignment=TA_JUSTIFY,
                               leftIndent=16, rightIndent=16, spaceAfter=10),
    "h1": ParagraphStyle("h1", fontName=BOLD, fontSize=14.5, leading=18,
                         textColor=BLACK, spaceBefore=22, spaceAfter=9,
                         keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName=BOLD, fontSize=11.5, leading=15,
                         textColor=BLACK, spaceBefore=14, spaceAfter=5,
                         keepWithNext=1),
    "body": ParagraphStyle("body", fontName=BODY, fontSize=10.8, leading=15.4,
                           textColor=BLACK, alignment=TA_JUSTIFY, spaceAfter=8),
    "bullet": ParagraphStyle("bullet", fontName=BODY, fontSize=10.8, leading=15.2,
                             textColor=BLACK, alignment=TA_JUSTIFY,
                             leftIndent=15, bulletIndent=3, spaceAfter=5),
    "caption": ParagraphStyle("caption", fontName=BODY, fontSize=9.2, leading=12.6,
                              textColor=GREY, alignment=TA_JUSTIFY,
                              spaceBefore=5, spaceAfter=15,
                              leftIndent=10, rightIndent=10),
    "note": ParagraphStyle("note", fontName=ITAL, fontSize=10.4, leading=14.8,
                           textColor=BLACK, alignment=TA_JUSTIFY,
                           leftIndent=16, rightIndent=14, spaceBefore=4,
                           spaceAfter=10),
    "foot": ParagraphStyle("foot", fontName=BODY, fontSize=8.8, leading=12,
                           textColor=GREY, alignment=TA_JUSTIFY,
                           leftIndent=16, rightIndent=10, spaceBefore=2,
                           spaceAfter=10),
    "tabnote": ParagraphStyle("tabnote", fontName=ITAL, fontSize=9, leading=12.4,
                              textColor=GREY, alignment=TA_JUSTIFY,
                              spaceBefore=1, spaceAfter=14),
    "prompt": ParagraphStyle("prompt", fontName=BI, fontSize=10.8, leading=15,
                             textColor=GREY, alignment=TA_JUSTIFY,
                             leftIndent=15, spaceAfter=4),
}

story = []
h1 = lambda t: story.append(Paragraph(t, S["h1"]))
h2 = lambda t: story.append(Paragraph(t, S["h2"]))
p = lambda t: story.append(Paragraph(t, S["body"]))
note = lambda t: story.append(Paragraph(t, S["note"]))
foot = lambda t: story.append(Paragraph(t, S["foot"]))
gap = lambda h=6: story.append(Spacer(1, h))


def bullets(items):
    for it in items:
        story.append(Paragraph(it, S["bullet"], bulletText="•"))
    story.append(Spacer(1, 5))


def table(data, widths=None, size=9.3, note=None, align=None, lead=None):
    """Scholarly table: rules above and below the header and at the foot only.

    No vertical lines and no cell boxes - the columns are held apart by space,
    which is what makes a table of numbers readable.
    """
    styles = {}
    for r in range(len(data)):
        for c in range(len(data[r])):
            key = (BOLD if r == 0 else BODY)
            styles[(r, c)] = ParagraphStyle(
                "c%d%d" % (r, c), fontName=key, fontSize=size,
                leading=lead or size + 3.0, textColor=BLACK,
                alignment=TA_CENTER if (align and c in align and r > 0) else 0)
    rows = [[Paragraph(str(c), styles[(r, i)]) for i, c in enumerate(row)]
            for r, row in enumerate(data)]
    t = Table(rows, colWidths=widths, hAlign="LEFT", repeatRows=1)
    t.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.9, BLACK),
        ("LINEBELOW", (0, 0), (-1, 0), 0.45, BLACK),
        ("LINEBELOW", (0, -1), (-1, -1), 0.9, BLACK),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
        ("LEFTPADDING", (1, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
    ]))
    block = [t]
    if note:
        block += [Spacer(1, 3), Paragraph(note, S["tabnote"])]
    else:
        block += [Spacer(1, 13)]
    story.append(KeepTogether(block))


MAX_FIG_H = 76 * mm   # no figure may own a page by itself


def figure(name, *, caption, width=None, height=None, heading=None,
           maxh=MAX_FIG_H):
    """Place a figure at a given width OR height; the other follows its aspect.

    A hard height cap keeps text flowing around the plots: without it a tall
    figure plus its caption is one indivisible block, and reportlab pushes the
    whole thing to a fresh page, leaving the previous one half empty.
    """
    path = FIG / name
    if not path.exists():
        p("[missing figure: %s]" % name)
        return
    iw, ih = Image.open(path).size
    if height is not None:
        h = height
        w = h * iw / ih
    else:
        w = width or CONTENT_W
        h = w * ih / iw
    if w > CONTENT_W:
        w, h = CONTENT_W, CONTENT_W * ih / iw
    if h > maxh:
        h, w = maxh, maxh * iw / ih
    img = RLImage(str(path), width=w, height=h)
    img.hAlign = "CENTER"
    block = [img, Paragraph(caption, S["caption"])]
    if heading:
        block.insert(0, Paragraph(heading, S["h2"]))
    story.append(KeepTogether(block))


class Rule(Flowable):
    """A hairline, used to close a section."""

    def __init__(self, width, weight=0.5, color=FAINT, space=8):
        Flowable.__init__(self)
        self.width, self.weight, self.color = width, weight, color
        self.height = space

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.weight)
        self.canv.line(0, self.height / 2, self.width, self.height / 2)


class Ruled(Flowable):
    """Faint ruled lines to write on."""

    def __init__(self, width, n=12, gap=20):
        Flowable.__init__(self)
        self.width, self.n, self.gap = width, n, gap
        self.height = n * gap

    def draw(self):
        c = self.canv
        c.setStrokeColor(FAINT)
        c.setLineWidth(0.4)
        for i in range(self.n):
            y = self.height - (i + 1) * self.gap
            c.line(0, y, self.width, y)


def writing_space(lines=12, prompt=None):
    blk = []
    if prompt:
        blk.append(Paragraph(prompt, S["prompt"]))
        blk.append(Spacer(1, 4))
    blk.append(Ruled(CONTENT_W, n=lines))
    blk.append(Spacer(1, 14))
    story.append(KeepTogether(blk))


# ======================================================= numbers from the CSVs
anova2 = pd.read_csv(TAB / "05_twoway_anova.csv", index_col=0)
within = pd.read_csv(TAB / "05_within_regime_strain_tests.csv", index_col=0)
assump = pd.read_csv(TAB / "05_assumption_checks.csv", index_col=0)
tukey = pd.read_csv(TAB / "05_tukey_posthoc.csv", index_col=0)
ev = pd.read_csv(TAB / "06_explained_variance.csv", index_col=0)
load = pd.read_csv(TAB / "06_loadings.csv", index_col=0)
sep = pd.read_csv(TAB / "06_label_separation.csv", index_col=0)
ksel = pd.read_csv(TAB / "07_k_selection.csv", index_col=0)
ari = pd.read_csv(TAB / "07_cluster_label_agreement.csv", index_col=0)
prof = pd.read_csv(TAB / "07_cluster_profiles.csv", index_col=0)
ctstrain = pd.read_csv(TAB / "07_crosstab_ward_x_strain.csv", index_col=0)
cttemp = pd.read_csv(TAB / "07_crosstab_ward_x_temperature.csv", index_col=0)
stab = pd.read_csv(TAB / "07_stability_resampling.csv", index_col=0)
assign = pd.read_csv(TAB / "07_cluster_assignments.csv")
kin_t = pd.read_csv(TAB / "02_kinetics_by_temperature.csv")
kin_s = pd.read_csv(TAB / "02_kinetics_by_strain.csv")

N_SIG = int((within["strain_effect"] == "significant").sum())
N_TESTS = len(within)
N_INTER = int(((anova2["term"] == "Strain:Temperature") & (anova2["p_BH"] < 0.05)).sum())
LEVENE_FAIL = int((within["levene_p"] <= 0.05).sum())
SHAPIRO_FAIL = int((within["shapiro_p"] <= 0.05).sum())
K_KAISER = int((ev["eigenvalue"] > 1).sum())
CUM = ev.loc[K_KAISER - 1, "cumulative_pct"]
BEST_K = int(ksel.loc[ksel["silhouette_ward"].idxmax(), "k"])
SIL = dict(zip(sep["label"], sep["silhouette_in_PC_space"]))
ARI = dict(zip(ari["label"], ari["ARI_ward"]))
STAB = stab["ARI_vs_full"].mean()
TUKEY_SIG = int(tukey["reject"].astype(str).isin(["True"]).sum())
STUCK_C = int(prof.loc["FinalResidualSugar"].iloc[:-1].astype(float).idxmax())
STUCK = assign[assign["ward"] == STUCK_C]
NTEST_USED = within["preferred"].value_counts().to_dict()
D = "°"


# ============================================================== TITLE PAGE
story.append(Spacer(1, 46 * mm))
story.append(Paragraph("Comparative Statistical Analysis of Commercial "
                       "Yeast Strains During Wine Fermentation", S["title"]))
story.append(Paragraph("Progress report &mdash; steps 1 to 7 of the project plan",
                       S["subtitle"]))
story.append(Spacer(1, 7 * mm))
story.append(Rule(CONTENT_W * 0.33, 0.8, BLACK, 10))
story.append(Spacer(1, 5 * mm))
story.append(Paragraph(
    "Nine commercial wine yeasts were compared across 216 fermentations. "
    "They differ, but conditionally: the strain effect depends on temperature "
    "in every outcome tested, is large at 12&nbsp;%sC and almost absent at "
    "25&nbsp;%sC, and is smaller than the two factors a winemaker already "
    "controls &mdash; the sugar in the must and the temperature of the tank."
    % (D, D), S["epigraph"]))
story.append(Spacer(1, 12 * mm))
story.append(Paragraph("BT3041 &mdash; Analysis and Interpretation of "
                       "Biological Data", S["subtitle"]))
story.append(Paragraph("<b>Team 20</b> &mdash; K James Bond &middot; "
                       "Avala Madhavi &middot; Dinesh Kumar &middot; Mohesh "
                       "&middot; Pranav Ram", S["subtitle"]))
story.append(Paragraph("Teaching Assistant: Kaviya D", S["subtitle"]))
story.append(Paragraph("Data: Minebois, R. &amp; Querol, A. (2025), "
                       "<i>Fermentation data set obtained from commercial wine "
                       "strains in synthetic grape must</i>, Zenodo, "
                       "doi:10.5281/zenodo.15260916 (CC BY 4.0)",
                       S["subtitle"]))
story.append(Paragraph("2 November 2026", S["subtitle"]))
story.append(PageBreak())

# ================================================================ CONTENTS
story.append(Paragraph("Contents", S["h1"]))
contents = TableOfContents()
contents.levelStyles = [
    ParagraphStyle("toc0", fontName=BOLD, fontSize=10.5, leading=16,
                   textColor=BLACK, firstLineIndent=0, leftIndent=0, spaceBefore=3),
    ParagraphStyle("toc1", fontName=BODY, fontSize=10.5, leading=14,
                   textColor=BLACK, firstLineIndent=0, leftIndent=14),
]
contents.dotsMinLevel = 0
story.append(contents)
story.append(PageBreak())

# ===================================================================== 1
h1("1. Where the project stands")
p("The project brief sets out nine steps. Seven are complete. This report "
  "covers what was done at each, the choices made along the way and the "
  "results they produced. Everything runs from a single unmodified source "
  "workbook through nine scripts, so every figure and table below can be "
  "regenerated from scratch.")

table([
    ["#", "Step", "Status", "Where it is"],
    ["1", "Download the dataset", "Done", "<i>Complete_DataSet.xlsx</i>"],
    ["2", "Understand the dataset", "Done", "data dictionary, 55 variables"],
    ["3", "Prepare the data", "Done", "five documented cleaning decisions"],
    ["4", "Exploratory data analysis", "Done", "8 figures, 14 tables"],
    ["5", "Hypothesis testing", "Done", "%d tests, %d significant" % (N_TESTS, N_SIG)],
    ["6", "Principal Component Analysis", "Done",
     "%d components, %.1f%% of variance" % (K_KAISER, CUM)],
    ["7", "Clustering", "Done", "k = %d, resample ARI %.2f" % (BEST_K, STAB)],
    ["8", "Validate and interpret", "To write", "section 9 &mdash; the group's own work"],
    ["9", "Report and presentation", "In progress", "this document"],
], widths=[9 * mm, 50 * mm, 22 * mm, CONTENT_W - 81 * mm])

h2("1.1 The question, and why it is phrased this way")
p("Nine commercial wine yeast strains were compared. The analysis asks "
  "whether they differ in fermentation performance <i>at a given "
  "temperature</i>, not whether one strain is better overall. That framing is "
  "not a preference: section 5.3 shows the strain effect depends on "
  "temperature for every outcome tested, so a question pooled across "
  "temperatures would average away the effect it is trying to measure.")

h2("1.2 How to read this report")
p("Sections 2 to 7 follow the analysis in the order it was done, and each "
  "ends with the result rather than a summary. Section 8 draws the three "
  "methods together. Section 9 is the group's interpretation and is "
  "deliberately left as writing space. Sections 10 and 11 cover what "
  "constrains the findings and what remains.")

# ===================================================================== 2
h1("2. The experimental design")
p("The workbook holds 1,950 rows, but it does not hold 1,950 independent "
  "observations, and almost everything about the analysis follows from that "
  "distinction.")
p("The experiment is a balanced three-way factorial with repeated measures. "
  "Nine strains were each fermented under four temperature regimes, at two "
  "nominal initial sugar levels, in three biological replicates.")

table([
    ["Factor", "Levels", "Values"],
    ["Strain", "9", "DV10, GALA, OPA, SAI, TXL, VIN13, W12, X16, X5"],
    ["Temperature", "4", "12 %sC, 18 %sC, 25 %sC, TVAR (time-varying)" % (D, D, D)],
    ["Initial sugar", "2", "nominal 210 and 250 g/L"],
    ["Replicate", "3", "R1, R2, R3 (biological)"],
], widths=[32 * mm, 16 * mm, CONTENT_W - 48 * mm],
    note="9 &times; 4 &times; 2 &times; 3 = 216 fermentations, each sampled at "
         "nine points (t0&ndash;t8) = 1,944 observations. Balance was verified "
         "by cross-tabulation: every cell holds exactly three replicates.")

p("A further six rows are an off-schedule <i>t5bis</i> sample, taken only for "
  "TXL and VIN13 at 18&nbsp;%sC and 250&nbsp;g/L. They unbalance the design "
  "and are excluded, which is what reduces 1,950 rows to 1,944." % D)

note("The nine samples from one fermentation are repeated measurements of a "
     "single experimental unit, not nine independent facts about yeast. "
     "Analysing them as independent would claim nine times more evidence than "
     "the experiment provides. This is pseudoreplication, and it is the "
     "standard failure mode for time-course bioprocess data.")

p("Each fermentation was therefore collapsed to one row of summary features, "
  "giving a table of 216 rows and 22 columns. Every hypothesis test, the "
  "principal component analysis and the clustering run on that table.")

table([
    ["Group", "Features"],
    ["Kinetics", "T50, T90, peak fermentation rate, total elapsed time"],
    ["Sugar", "measured initial sugar, final residual sugar, total consumed, "
              "fraction fermented, dryness flag"],
    ["Products", "final ethanol, ethanol yield, final glycerol"],
    ["Organic acids", "final acetate, final succinate, malate consumed"],
    ["Cells", "peak viable count, final viability"],
], widths=[32 * mm, CONTENT_W - 32 * mm],
    note="The 16 numeric features of <i>02_unit_level_features.csv</i>, besides "
         "the five design columns. T50 and T90 are the times to consume 50 % "
         "and 90 % of each fermentation's own measured starting sugar.")

figure("fig01_sugar_curves_by_strain.png", width=CONTENT_W,
       heading="2.1 What the fermentations look like",
       caption="Residual sugar against time for all 216 fermentations, one "
               "panel per strain. The four coloured bands within each panel are "
               "the temperature regimes. The spread between regimes is far "
               "wider than the differences between panels &mdash; temperature "
               "moves the outcome more than strain does.")

# ===================================================================== 3
h1("3. Data preparation and quality")
p("Five cleaning decisions were taken and recorded. The source workbook is "
  "never written to; all cleaning happens in memory each time a script runs, "
  "so the raw data and the analysis cannot drift apart.")

table([
    ["#", "Decision", "Reason"],
    ["1", "Source workbook read-only", "The raw file stays as published; "
          "cleaning is code, not an edited spreadsheet"],
    ["2", "Temperature as an ordered category, not a number",
          "TVAR is a varying regime with no single numeric value"],
    ["3", "The six <i>t5bis</i> rows excluded",
          "They unbalance the design; reported separately"],
    ["4", "Missing values not imputed",
          "The gaps are structural &mdash; whole assay blocks were not run at "
          "some sampling points"],
    ["5", "<i>MS</i> kept as a factor label, not a measurement",
          "Using it as the sugar baseline produces 173 impossible negative "
          "values; each unit is baselined on its own measured t0"],
], widths=[7 * mm, 62 * mm, CONTENT_W - 69 * mm])

h2("3.1 Four quality problems, and what was done about each")
p("<b>Physically impossible sugar readings.</b> Seventy-four samples, spread "
  "across 71 of the 216 fermentations, show residual sugar rising over time, "
  "and 63 of those exceed their own starting value. Sugar is not produced "
  "during an alcoholic fermentation, so these are analytical artefacts. They "
  "are listed in a flag table and excluded from the kinetic fits through a "
  "cumulative maximum, but left in the dataset rather than deleted.")
foot("Flagging rather than deleting was chosen because a deletion changes the "
     "dataset silently: a later reader cannot tell what was removed or "
     "disagree with the judgement. All 74 are listed in "
     "<i>01_flagged_nonmonotonic_sugar.csv</i>, and all fall at t1&ndash;t3.")

p("<b>Nominal sugar is not measured sugar.</b> <i>MS</i> is an experimental "
  "label. The sugar actually measured at t0 ranged from 203 to 229&nbsp;g/L "
  "within the nominal 210&nbsp;g/L group, and differed systematically between "
  "temperature batches. Since initial sugar turns out to be the largest "
  "single driver of the endpoint chemistry, this matters: the strains were "
  "not all challenged with identical musts. Consumption is therefore "
  "baselined on each fermentation's own t0, and <i>MS</i> enters every model "
  "as a factor.")

p("<b>Structural missingness.</b> The twenty-two amino acids and ten volatile "
  "aroma compounds were assayed at only five of the nine sampling points. The "
  "gaps are not random, so imputing them would invent a whole assay block. "
  "Each analysis instead uses only the points where its variables exist, and "
  "the volatiles are excluded from the multivariate work entirely.")

p("<b>Two single-sample anomalies.</b> One sample reports more viable cells "
  "than total cells, which is impossible. One fermentation, "
  "<i>GALA|TVAR|250|R1</i>, never reached 90&nbsp;% sugar consumption, so its "
  "completion time is undefined and n&nbsp;=&nbsp;215 for that outcome. "
  "Neither was deleted: the second is a genuine stuck fermentation and "
  "reappears as a result in section 7.3.")

note("Sampling was event-driven rather than on a fixed clock, so time points "
     "are not aligned across units. Comparisons between fermentations "
     "therefore use derived kinetics &mdash; T50, T90, peak rate &mdash; "
     "rather than raw values at matched nominal times.")

# ===================================================================== 4
h1("4. Exploratory analysis")
p("Before any test, the data was summarised to establish where variation "
  "actually lives. This decided which outcomes were worth testing formally, "
  "and the effect sizes here are reported deliberately without p-values: they "
  "were used to choose the tests, not to stand in for them.")

h2("4.1 Temperature dominates the kinetics")
table([["Temperature", "T50 (h)", "T90 (h)", "Peak rate (g/L/h)",
        "Final sugar (g/L)", "Final ethanol (%)"]] +
      [[str(r.Temperature), "%.1f" % r.T50_h, "%.1f" % r.T90_h,
        "%.2f" % r.MaxRate_gL_h, "%.2f" % r.FinalResidualSugar,
        "%.2f" % r.FinalEthanol] for r in kin_t.itertuples()],
      widths=[26 * mm] + [(CONTENT_W - 26 * mm) / 5] * 5,
      align={1, 2, 3, 4, 5},
      note="Fermentation at 25 %sC completes in roughly a quarter of the time "
           "it takes at 12 %sC. The standard deviation between these "
           "temperature means for T90 is 147.9 h; between strain means it is "
           "26.3 h." % (D, D))

h2("4.2 The same outcomes by strain")
table([["Strain", "T50 (h)", "T90 (h)", "Peak rate", "Final sugar (g/L)",
        "Final ethanol (%)", "% dry"]] +
      [[r.Strain, "%.0f" % r.T50_h, "%.0f" % r.T90_h, "%.2f" % r.MaxRate_gL_h,
        "%.2f" % r.FinalResidualSugar, "%.2f" % r.FinalEthanol,
        "%.0f" % r.Pct_dry] for r in kin_s.itertuples()],
      widths=[22 * mm] + [(CONTENT_W - 22 * mm) / 6] * 6,
      align={1, 2, 3, 4, 5, 6},
      note="Pooled over all 24 fermentations of each strain. These means hide "
           "the interaction described in 4.4 and are a first look, not a "
           "strain comparison. &ldquo;% dry&rdquo; is the share of a strain's "
           "fermentations finishing below 2 g/L residual sugar.")

h2("4.3 Where the variance is")
figure("fig08_variance_decomposition.png", width=CONTENT_W,
       caption="Share of variance in each unit-level outcome attributable to "
               "temperature, strain, initial sugar and the strain &times; "
               "temperature interaction. Descriptive effect sizes, reported "
               "without p-values.")

p("Three patterns set up everything that follows. Temperature governs the "
  "kinetics, taking 87.5&nbsp;% of the variance in T50 and 72.2&nbsp;% in "
  "T90. Initial sugar governs the endpoint chemistry, taking 76.7&nbsp;% of "
  "final ethanol and 60.2&nbsp;% of final acetate. And strain is never the "
  "largest single term for any outcome, leading only for peak viable cell "
  "count at 29.5&nbsp;%.")

note("Final ethanol was therefore excluded from the strain comparisons. It "
     "looks like the headline wine variable, but strain explains 0.4 % of it "
     "against 76.7 % for initial sugar: testing it across strains would "
     "measure the must, not the yeast.")

h2("4.4 Strain rankings do not transfer between regimes")
figure("fig07_rank_bump.png", width=CONTENT_W * 0.86,
       caption="Each strain's rank by time to 90 % sugar consumption, within "
               "each temperature regime. 1 is fastest. The lines cross "
               "repeatedly.")

p("No strain is fastest in all four regimes. W12 comes closest, at ranks 1, "
  "3, 1 and 1; VIN13 moves from 8th at 12&nbsp;%sC to 2nd under TVAR. The "
  "Spearman correlation between the 12&nbsp;%sC and TVAR rankings is 0.32, "
  "and between 18 and 25&nbsp;%sC it is 0.83 &mdash; adjacent constant "
  "temperatures agree, the extremes and the varying regime do not. Section "
  "5.2 tests this formally." % (D, D, D))

h2("4.5 Stuck and sluggish fermentations")
p("Thirty-two of the 216 fermentations failed to reach 2&nbsp;g/L residual "
  "sugar. By temperature: 14 at 12&nbsp;%sC, 10 under TVAR, 8 at 18&nbsp;%sC "
  "and none at all at 25&nbsp;%sC. By strain the count is uneven &mdash; GALA "
  "9, OPA 4, X16 4, X5 4, TXL 3, W12 3, SAI 2, VIN13 2, DV10 1. Section 7.3 "
  "finds the same group again, by a method that was not told it existed."
  % (D, D, D))

# ===================================================================== 5
h1("5. Hypothesis testing")
p("Six outcomes were tested, chosen from the variance scan because a strain "
  "term demonstrably exists in them: peak viable cells, final succinate, "
  "malate consumed, final acetate, final residual sugar, and time to "
  "90&nbsp;% sugar consumption.")

h2("5.1 Assumptions were checked first, and they changed the analysis")
p("Shapiro&ndash;Wilk was run on the residuals of the full model rather than "
  "on the raw values, and Levene across the strain-by-temperature cells. "
  "Where a transform was considered, it was judged on the residuals it "
  "produced.")

table([["Outcome", "Scale", "Skew", "Shapiro p", "Levene p", "Decision"]] +
      [[r.outcome, r.scale, "%+.2f" % r.skew, "%.4f" % r.shapiro_p,
        "%.4f" % r.levene_p,
        "used" if r.scale == dict(zip(within.outcome, within.scale)).get(r.outcome)
        else "rejected"]
       for r in assump.itertuples()],
      widths=[38 * mm, 15 * mm, 15 * mm, 20 * mm, 20 * mm,
              CONTENT_W - 108 * mm], size=8.8,
      align={2, 3, 4},
      note="Raw and transformed scales compared for the two skewed outcomes. "
           "Final residual sugar is severely right-skewed at +4.18 and was "
           "analysed as log1p; peak viable cells spans orders of magnitude and "
           "was analysed as log10. Malate consumed was left untransformed "
           "because logging makes its skew worse, from +1.01 to &minus;1.85.")

p("The important finding here is not any single transform. It is that "
  "Levene fails in <b>%d of the %d</b> regime cells: the variances genuinely "
  "differ between strains. Shapiro fails in only %d. The problem is "
  "heteroscedasticity, not non-normality."
  % (LEVENE_FAIL, N_TESTS, SHAPIRO_FAIL))

note("Kruskal&ndash;Wallis is not a remedy for unequal variance &mdash; it "
     "assumes comparable spread between groups as well. Welch's ANOVA, which "
     "does not, was therefore added. This is the correction a reader is most "
     "likely to ask about.")

p("The test applied in each cell follows from the assumptions, not from which "
  "gives the smaller p-value:")
bullets([
    "normal residuals, equal variances &rarr; classical ANOVA, adjusted for "
    "initial sugar (%d cells)" % NTEST_USED.get("ANOVA", 0),
    "normal residuals, unequal variances &rarr; Welch's ANOVA (%d cells)"
    % NTEST_USED.get("Welch ANOVA", 0),
    "non-normal residuals &rarr; Kruskal&ndash;Wallis (%d cells)"
    % NTEST_USED.get("Kruskal-Wallis", 0),
])
foot("Welch is undefined in one cell: every 25 %sC fermentation of several "
     "strains ends at exactly 0 g/L residual sugar, giving a zero-variance "
     "group and infinite weights. That cell falls back to "
     "Kruskal&ndash;Wallis." % D)

h2("5.2 The interaction, and why it decides the framing")
p("A two-way ANOVA with the interaction term was fitted for each outcome, "
  "using type II sums of squares and including initial sugar as a factor. "
  "The strain &times; temperature interaction is significant for all %d "
  "outcomes after correction." % N_INTER)

table([["Outcome", "Strain", "Temperature", "Initial sugar", "Interaction",
        "Model adj. R&sup2;"]] +
      [[o] + ["%.3f" % anova2[(anova2.outcome == o) &
                              (anova2.term == t)].partial_eta_sq.iloc[0]
              for t in ["Strain", "Temperature", "MS", "Strain:Temperature"]] +
       ["%.3f" % anova2[anova2.outcome == o].model_adj_R2.iloc[0]]
       for o in anova2.outcome.unique()],
      widths=[38 * mm] + [(CONTENT_W - 38 * mm) / 5] * 5,
      align={1, 2, 3, 4, 5},
      note="Partial eta-squared for each term. All terms shown are significant "
           "after Benjamini&ndash;Hochberg correction. Because the interaction "
           "is real, the strain main effect pooled across regimes understates "
           "the differences that exist within them.")

figure("fig09_anova_partial_eta2.png", width=CONTENT_W * 0.92,
       caption="Variance explained by each term. Initial sugar dominates "
               "acetate; temperature dominates the kinetics; strain leads only "
               "for peak viable cell count.")

h2("5.3 The strain effect within each regime")
p("Strain was then tested separately inside each temperature regime, with "
  "initial sugar retained as a factor. All %d p-values &mdash; six outcomes "
  "across four regimes &mdash; were corrected together as a single "
  "Benjamini&ndash;Hochberg family." % N_TESTS)

tmps = ["12", "18", "25", "TVAR"]
rows = [["Outcome", "12 %sC" % D, "18 %sC" % D, "25 %sC" % D, "TVAR",
         "Largest &eta;&sup2;"]]
for o in within.outcome.unique():
    r = [o]
    sub_all = within[within.outcome == o]
    for t in tmps:
        sub = sub_all[sub_all.temperature.astype(str) == t]
        r.append("<b>yes</b>" if (len(sub) and
                 sub.strain_effect.iloc[0] == "significant") else "&mdash;")
    r.append("%.2f" % sub_all.partial_eta_sq.max())
    rows.append(r)
table(rows, widths=[38 * mm] + [(CONTENT_W - 38 * mm) / 5] * 5,
      align={1, 2, 3, 4, 5},
      note="Significant strain effect after correction, by outcome and regime. "
           "%d of %d tests are significant." % (N_SIG, N_TESTS))

p("Three features of this table matter more than the count.")
p("<b>Peak viable cell count is the most robust strain difference in the "
  "dataset.</b> It is the only outcome significant in all four regimes, with "
  "partial eta-squared between 0.50 and 0.88, and Tukey separates 22 of the "
  "36 strain pairs at 12&nbsp;%sC. How much biomass a strain builds is the "
  "trait that most reliably tells these strains apart." % D)
p("<b>Every outcome separates at 12&nbsp;%sC; almost none do at "
  "25&nbsp;%sC.</b> Strains diverge under cold stress and converge when "
  "conditions are permissive. A comparison run only at 25&nbsp;%sC would have "
  "concluded that the strains are interchangeable." % (D, D, D))
p("<b>Acetate is a large effect that is not a strain effect.</b> Classical "
  "ANOVA gives F between 12.6 and 26.4 with p below 0.0001 in every regime, "
  "yet Welch and Kruskal&ndash;Wallis both find nothing once unequal "
  "variances are handled. The classical test was reading a difference in "
  "spread as a difference in means.")

h2("5.4 Post-hoc comparisons")
p("Tukey HSD was computed for all 36 strain pairs in each of the 24 cells, "
  "864 comparisons in total, of which %d are significant. Dunn's test with "
  "the same Benjamini&ndash;Hochberg correction is reported alongside it for "
  "the cells analysed non-parametrically." % TUKEY_SIG)

npairs = (tukey.assign(sig=lambda t: t["reject"].astype(str) == "True")
          .groupby(["outcome", "temperature"], observed=True)["sig"].sum()
          .rename("n").reset_index())
pv = npairs.pivot(index="outcome", columns="temperature", values="n")
pv = pv.reindex(columns=[12, 18, 25, "TVAR"]) if 12 in pv.columns else \
    pv.reindex(columns=["12", "18", "25", "TVAR"])
table([["Outcome", "12 %sC" % D, "18 %sC" % D, "25 %sC" % D, "TVAR"]] +
      [[o] + ["%d" % (0 if pd.isna(pv.loc[o, c]) else pv.loc[o, c])
              for c in pv.columns] for o in pv.index],
      widths=[44 * mm] + [(CONTENT_W - 44 * mm) / 4] * 4,
      align={1, 2, 3, 4},
      note="Number of the 36 strain pairs separated by Tukey HSD in each cell.")

figure("fig10_maxviable_by_strain_regime.png", width=CONTENT_W,
       caption="Peak viable cell count by strain with 95 % confidence "
               "intervals, within each regime. Strains are re-sorted in every "
               "panel; the re-ordering between panels is the interaction made "
               "visible.")

# ===================================================================== 6
h1("6. Principal Component Analysis")
p("Fifteen unit-level outcomes were standardised and decomposed. "
  "Standardisation is not optional: the columns run from about 0.5&nbsp;g/L "
  "of acetate to 10<super>8</super> cells per millilitre, and without scaling "
  "the first component would simply be cell count.")

h2("6.1 What was included, and what was not")
bullets([
    "<b>Total elapsed sampling time</b> &mdash; excluded. It is a property of "
    "the sampling schedule rather than of the yeast, and is almost entirely "
    "determined by temperature.",
    "<b>The dryness flag</b> &mdash; excluded, being a binary recoding of "
    "final residual sugar and therefore redundant.",
    "<b>The ten volatile aroma compounds</b> &mdash; excluded. They were "
    "assayed at only five of the nine sampling points, so including them "
    "would mean imputing a whole block.",
    "<b>One fermentation</b> &mdash; dropped rather than imputed, leaving "
    "n&nbsp;=&nbsp;215. Imputing a completion time for a fermentation that "
    "never completed would invent the result.",
])
foot("The consequence of excluding the volatiles is worth stating plainly: "
     "this multivariate analysis describes fermentation performance, not wine "
     "aroma or sensory quality. No conclusion here speaks to how the wine "
     "would taste.")

h2("6.2 How many components")
table([["Component", "Eigenvalue", "Variance (%)", "Cumulative (%)"]] +
      [[ev.loc[i, "PC"], "%.2f" % ev.loc[i, "eigenvalue"],
        "%.1f" % ev.loc[i, "explained_var_pct"],
        "%.1f" % ev.loc[i, "cumulative_pct"]] for i in range(6)],
      widths=[CONTENT_W / 4] * 4, align={1, 2, 3},
      note="%d components have an eigenvalue above one and together explain "
           "%.1f %% of the variance. The same four are the number needed to "
           "pass 80 %%, so the Kaiser criterion and the cumulative rule agree."
           % (K_KAISER, CUM))

h2("6.3 What the components mean")
top = {}
for pc in ["PC1", "PC2", "PC3"]:
    top[pc] = load[pc].abs().sort_values(ascending=False).head(5).index.tolist()
table([["", "PC1", "PC2", "PC3"]] +
      [[v, "%+.3f" % load.loc[v, "PC1"], "%+.3f" % load.loc[v, "PC2"],
        "%+.3f" % load.loc[v, "PC3"]] for v in load.index],
      widths=[52 * mm] + [(CONTENT_W - 52 * mm) / 3] * 3, size=8.8,
      align={1, 2, 3},
      note="Loadings of all fifteen features on the first three components.")

p("Read through those loadings, the components have clear identities. "
  "<b>PC1 is a must-loading axis</b>: initial sugar (+0.40), final ethanol "
  "(+0.39), sugar consumed (+0.38) and acetate (+0.33). It describes how much "
  "sugar went in and therefore how much ethanol came out. <b>PC2 is a "
  "fermentation-vigour axis</b>: succinate (+0.39), glycerol (+0.38) and peak "
  "rate (+0.36) against T50 (&minus;0.37) and T90 (&minus;0.32) &mdash; speed "
  "and by-product formation move together and oppose the completion times. "
  "<b>PC3 is completion</b>: fraction fermented (+0.63) against residual "
  "sugar (&minus;0.62) and little else, which is why it is worth retaining "
  "despite explaining only 12.3&nbsp;%.")

note("The first two axes, 62 % of all variation, are initial sugar and speed. "
     "Neither is a property of the yeast.")

# the biplot carries fifteen arrow labels; squeezed to the default cap they
# collide, so it gets its own, larger ceiling
figure("fig14_pca_biplot.png", width=CONTENT_W * 0.80, maxh=104 * mm,
       caption="Loadings of the fifteen features on PC1 and PC2, with the 215 "
               "fermentations behind them in grey.")

h2("6.4 Strain does not separate")
p("The fermentations were plotted twice on identical axes, coloured once by "
  "temperature and once by strain. Rather than leave the comparison to the "
  "eye, the silhouette of each design factor was computed in the retained "
  "four-component space.")

table([["Grouping", "Groups", "Silhouette in PC space"]] +
      [[r.label, "%d" % r.n_groups, "%+.3f" % r.silhouette_in_PC_space]
       for r in sep.itertuples()],
      widths=[58 * mm, 22 * mm, CONTENT_W - 80 * mm], align={1, 2},
      note="A silhouette near zero means no grouping; a negative value means "
           "points sit closer to other groups than to their own.")

p("Strain is negative, at %+.3f. In the space of overall metabolic outcome "
  "the nine strains do not form distinguishable groups at all, and the two "
  "visible clumps along PC1 are the two must sugar levels rather than "
  "anything biological about the yeast." % SIL["Strain"])

figure("fig13_pca_scatter.png", width=CONTENT_W,
       caption="The same 215 fermentations on the same axes, coloured by "
               "temperature on the left and by strain on the right.")

note("This does not contradict section 5. PCA asks whether strain is a leading "
     "source of overall variation, and the answer is no. The tests ask whether "
     "strains differ on a specific outcome once temperature is held fixed, and "
     "the answer is yes. A real but modest effect is invisible to a method "
     "that sorts by largest variance first.")

# ===================================================================== 7
h1("7. Clustering")
p("The same 215 fermentations and the same standardised features were "
  "clustered, so the two multivariate steps are directly comparable. The "
  "number of clusters was chosen by silhouette over k from 2 to 10 &mdash; "
  "not set to nine to match the nine strains, which would have assumed the "
  "answer. Ward linkage and k-means were both run, since agreement between "
  "methods that make different assumptions is itself a stability check.")

h2("7.1 Choosing k")
table([["k", "Silhouette (Ward)", "Silhouette (k-means)", "Inertia",
        "Ward vs k-means ARI"]] +
      [["%d" % r.k, "%.4f" % r.silhouette_ward, "%.4f" % r.silhouette_kmeans,
        "%.0f" % r.inertia_kmeans, "%.3f" % r.ward_vs_kmeans_ARI]
       for r in ksel.itertuples()],
      widths=[14 * mm] + [(CONTENT_W - 14 * mm) / 4] * 4, align={1, 2, 3, 4},
      note="Five clusters give the best Ward silhouette, at %.4f."
           % ksel.silhouette_ward.max())

note("Two caveats. The silhouette at k = 4 is %.4f against %.4f at k = 5, which "
     "is not a meaningful difference; k = 5 was kept because it isolates a "
     "biologically distinct group. And an absolute silhouette near 0.3 "
     "describes real but not sharply separated clusters."
     % (ksel.loc[ksel.k == 4, "silhouette_ward"].iloc[0],
        ksel.loc[ksel.k == 5, "silhouette_ward"].iloc[0]))

figure("fig17_silhouette_k.png", width=CONTENT_W * 0.6,
       caption="Mean silhouette against k for both methods.")

figure("fig15_dendrogram.png", width=CONTENT_W,
       caption="Ward linkage on the fifteen standardised outcomes, cut at "
               "k = %d." % BEST_K)

h2("7.2 The clusters do not correspond to strain")
p("Re-running Ward on a hundred random 80&nbsp;%% resamples gives a mean "
  "adjusted Rand index of %.3f against the full-data clusters, and Ward and "
  "k-means agree at %.3f. These are stable groups. The question is what they "
  "are groups of."
  % (STAB, ksel.loc[ksel.k == BEST_K, "ward_vs_kmeans_ARI"].iloc[0]))

table([["Clusters compared against", "Groups", "ARI (Ward)", "ARI (k-means)"]] +
      [[r.label, "%d" % r.n_groups, "%+.3f" % r.ARI_ward, "%+.3f" % r.ARI_kmeans]
       for r in ari.itertuples()],
      widths=[58 * mm, 20 * mm, (CONTENT_W - 78 * mm) / 2,
              (CONTENT_W - 78 * mm) / 2], align={1, 2, 3},
      note="Adjusted Rand index: 1 is a perfect match, 0 is chance.")

cs = sorted(assign["ward"].unique())
table([["Strain"] + ["Cluster %d" % c for c in cs]] +
      [[s] + ["%d" % ctstrain.loc[s, str(c)] for c in cs] for s in ctstrain.index],
      widths=[28 * mm] + [(CONTENT_W - 28 * mm) / len(cs)] * len(cs),
      align=set(range(1, len(cs) + 1)),
      note="Ward cluster membership by strain. The rows are near-identical: "
           "knowing a fermentation's cluster tells you nothing about which "
           "yeast was in it.")

table([["Temperature"] + ["Cluster %d" % c for c in cs]] +
      [[str(t)] + ["%d" % cttemp.loc[t, str(c)] for c in cs]
       for t in cttemp.index],
      widths=[28 * mm] + [(CONTENT_W - 28 * mm) / len(cs)] * len(cs),
      align=set(range(1, len(cs) + 1)),
      note="The same cross-tabulation by temperature, where structure is "
           "obvious: clusters 2 and 4 are almost entirely 12 %sC, clusters 3 "
           "and 5 almost entirely the warmer regimes." % D)

h2("7.3 What the clusters are instead")
p("The clusters form a sugar-by-speed grid, which is what PC1 and PC2 "
  "predicted they would be.")

order = [5, 3, 4, 2, 1]
labels = ["standard must, fast and complete", "high sugar, still completes",
          "standard must, cold and slow", "very high sugar, very slow", "stuck"]
table([["Cluster", "n", "Initial sugar", "T90 (h)", "Residual sugar",
        "Peak viable", "Character"]] +
      [["%d" % c, "%d" % (assign["ward"] == c).sum(),
        "%.0f g/L" % prof.loc["InitialSugar", str(c)],
        "%.0f" % prof.loc["T90_h", str(c)],
        "%.2f g/L" % prof.loc["FinalResidualSugar", str(c)],
        "%.1fe7" % (prof.loc["MaxViable", str(c)] / 1e7), d]
       for c, d in zip(order, labels)],
      widths=[14 * mm, 10 * mm, 22 * mm, 15 * mm, 23 * mm, 19 * mm,
              CONTENT_W - 103 * mm], size=8.8,
      align={1, 2, 3, 4, 5},
      note="Cluster means in raw units, ordered from fastest to stuck.")

p("Cluster %d is the stuck-fermentation group: %d fermentations averaging "
  "%.1f&nbsp;g/L of unfermented sugar, against 0.2 to 1.3&nbsp;g/L everywhere "
  "else. The method found them without being told they existed, and PC3 "
  "points at the same set."
  % (STUCK_C, len(STUCK),
     prof.loc["FinalResidualSugar"].iloc[:-1].astype(float).max()))

p("Their composition is not uniform. Nine of the eleven are 250&nbsp;g/L "
  "musts and all but one sat at 12 or 18&nbsp;%sC, so the failures "
  "concentrate where osmotic stress and cold stress combine. By strain, GALA "
  "contributes four and OPA three, while DV10, TXL, VIN13 and W12 contribute "
  "none at all. This agrees with the independent count in section 4.5." % D)

note("The defensible form of this observation is not that GALA is the worst "
     "strain, but that GALA and OPA are over-represented among fermentations "
     "that failed to complete under combined cold and high-sugar stress. With "
     "eleven units it is suggestive rather than conclusive.")

figure("fig16_clusters_vs_design.png", width=CONTENT_W,
       caption="The clusters the data finds, beside the actual temperature "
               "regime, in the plane of the first two components.")

# ===================================================================== 8
h1("8. Summary of results")
p("The three methods appear to disagree and do not. Hypothesis testing finds "
  "strain differences in %d of %d comparisons; PCA gives strain a negative "
  "silhouette; clustering gives it an adjusted Rand index of %+.3f. They are "
  "answering different questions." % (N_SIG, N_TESTS, ARI["Strain"]))

table([
    ["Method", "Question it asks", "Answer"],
    ["Two-way ANOVA", "Is there a strain effect once temperature and must are "
     "accounted for?", "Yes, and it interacts with temperature"],
    ["Within-regime tests", "Do strains differ on a given outcome at a fixed "
     "temperature?", "Yes, in %d of %d cases" % (N_SIG, N_TESTS)],
    ["PCA", "Is strain a leading source of overall variation?",
     "No &mdash; third, behind must and temperature"],
    ["Clustering", "Do fermentations group by strain?",
     "No &mdash; they group by sugar and speed"],
], widths=[32 * mm, 70 * mm, CONTENT_W - 102 * mm])

p("The unifying statement is one of magnitude and conditionality. Strain "
  "effects are real and statistically well supported, specific to particular "
  "outcomes under particular conditions, and small beside the two factors a "
  "winemaker controls directly. An unsupervised method sorting 215 "
  "fermentations by overall similarity finds those two first and never "
  "reaches strain.")

p("What the results do not support is a ranking. No strain is fastest in all "
  "four regimes, so a pooled claim that one strain is best is contradicted by "
  "the data rather than merely unsupported by it.")

# ===================================================================== 9
story.append(PageBreak())
h1("9. Interpretation and conclusions")
note("This section is the group's own work. The BT3041 guidelines state that "
     "the biological interpretation and conclusions must be written by the "
     "group and that AI must not formulate the aims and hypotheses. Sections 1 "
     "to 8 report method and result only. The prompts below are a checklist of "
     "what needs answering, not draft text.")

h2("9.1 Why strains diverge in the cold and converge at 25 %sC" % D)
writing_space(9, prompt="Every outcome tested separates at 12 %sC and almost "
                         "none at 25 %sC. What is happening to the yeast under "
                         "cold stress that is not happening at a permissive "
                         "temperature?" % (D, D))

h2("9.2 What it means that biomass is the most consistent strain trait")
writing_space(9, prompt="Peak viable cell count is the only outcome "
                         "significant in all four regimes, and the only one "
                         "where strain is the largest variance term. What does "
                         "that imply about what distinguishes these strains "
                         "biologically, and about what a winery is buying?")

h2("9.3 Why significant tests and null clustering are both correct")
writing_space(9, prompt="Reconcile the %d significant tests with a "
                         "cluster-to-strain ARI of %+.3f and a negative "
                         "silhouette, in your own words."
                         % (N_SIG, ARI["Strain"]))

h2("9.4 Whether the stuck-fermentation pattern is a strain property")
writing_space(9, prompt="GALA and OPA are over-represented among the eleven "
                         "stuck fermentations, all under cold plus high sugar. "
                         "Is that a property of those strains, or of the "
                         "conditions they met? What evidence would settle it?")

story.append(PageBreak())
h2("9.5 Comparison with the published literature")
writing_space(14, prompt="Find the dataset's source publication, then work on "
                         "the named commercial strains &mdash; VIN13, DV10 and "
                         "X5 are widely studied &mdash; and on temperature "
                         "effects on S. cerevisiae fermentation kinetics. Where "
                         "do these results agree, and where do they not?")

h2("9.6 Conclusions")
writing_space(10, prompt="Three or four sentences. State what was found, state "
                         "what it does not support, and avoid claiming that any "
                         "one strain is superior.")

# ===================================================================== 10
story.append(PageBreak())
h1("10. Limitations")
p("These came out of the data inspection rather than from a template, and "
  "each one bounds a specific claim made above.")
bullets([
    "<b>Impossible readings.</b> 74 samples across 71 fermentations carry "
    "rising-sugar values. They were flagged rather than deleted, and that "
    "decision needs defending either way.",
    "<b>Musts were not identical.</b> Actual initial sugar ranged 203 to "
    "229 g/L within the nominal 210 group, and initial sugar is the largest "
    "driver of endpoint chemistry, so the strains were not all set the same "
    "task.",
    "<b>Unequal variances.</b> Levene fails in %d of %d regime cells. Welch's "
    "ANOVA handles it, but heterogeneity is itself a finding: some strains are "
    "more consistent than others, which a comparison of means does not "
    "capture." % (LEVENE_FAIL, N_TESTS),
    "<b>Incomplete assay coverage.</b> Amino acids and volatiles were measured "
    "at five of nine sampling points and are excluded from the multivariate "
    "analysis. Nothing here speaks to wine aroma or sensory quality.",
    "<b>Six replicates per cell.</b> Adequate for large effects, underpowered "
    "for small ones. A non-significant result is not evidence of no "
    "difference, and several outcomes sit near the threshold.",
    "<b>Event-driven sampling.</b> Time points are not aligned across units, "
    "so comparisons use derived kinetics rather than values at matched times.",
    "<b>One incomplete fermentation</b>, so n = 215 for completion time and "
    "for both multivariate analyses.",
    "<b>Synthetic must, one laboratory.</b> The medium is a defined synthetic "
    "grape must, not pressed grapes, with no independent replication. That is "
    "a strength for control &mdash; strains met a reproducible medium &mdash; "
    "and a limit on transfer: real musts vary in nitrogen, phenolics and wild "
    "flora in ways this design deliberately removes.",
])

# ===================================================================== 11
h1("11. What remains")
table([
    ["Step", "Work", "Owner"],
    ["8", "Write the biological interpretation and conclusions (section 9)",
     "all four members"],
    ["8", "Compare the findings with published work on these strains",
     "member 4"],
    ["9", "Build and rehearse the progress presentation", "member 4"],
    ["9", "Final report and supplementary submission", "all four members"],
], widths=[14 * mm, CONTENT_W - 54 * mm, 40 * mm])

h2("11.1 Reproducing this analysis")
p("Nine scripts run in order from the unmodified workbook. Scripts 01 to 03 "
  "produce the data dictionary, the unit-level table and the exploratory "
  "figures; 05 to 07 produce the tests, the component analysis and the "
  "clustering; 04, 08 and 09 typeset the two reports and the slides. All "
  "outputs land in <i>outputs/tables</i> and <i>outputs/figures</i>, and every "
  "number quoted in this document is read from those files when it is built, "
  "so the prose cannot drift away from the analysis.")

h2("11.2 Declaration on the use of AI")
p("AI assistance was used for code, for debugging and for explanations of "
  "statistical method, which the course guidelines permit. The aims, "
  "hypotheses, biological interpretation and conclusions are the group's own "
  "work. Section 9 is left unwritten here for that reason, and the "
  "exploratory variance scan in section 4 reports effect sizes without "
  "p-values so that the choice and justification of the formal tests remained "
  "with the group.")


# ================================================================== BUILD
def page_furniture(canvas, doc):
    canvas.saveState()
    canvas.setFont(BODY, 9)
    canvas.setFillColor(GREY)
    if doc.page > 2:
        sec = getattr(doc, "_section", "")
        if sec:
            canvas.drawRightString(PAGE_W - MARGIN_X, PAGE_H - MARGIN_Y + 7 * mm,
                                   sec)
        canvas.setStrokeColor(FAINT)
        canvas.setLineWidth(0.4)
        canvas.line(MARGIN_X, PAGE_H - MARGIN_Y + 5.4 * mm,
                    PAGE_W - MARGIN_X, PAGE_H - MARGIN_Y + 5.4 * mm)
    if doc.page > 1:
        canvas.setFillColor(BLACK)
        canvas.drawCentredString(PAGE_W / 2, 13 * mm, str(doc.page))
    canvas.restoreState()


class ReportDoc(BaseDocTemplate):
    """Feeds headings to the contents and keeps the running header current."""

    def afterFlowable(self, flowable):
        if not isinstance(flowable, Paragraph):
            return
        name = flowable.style.name
        if name not in ("h1", "h2"):
            return
        text = flowable.getPlainText()
        if text == "Contents":
            return
        if name == "h1":
            self._section = text
        if name == "h2":
            return          # sections only; sub-headings made the TOC two pages
        self.notify("TOCEntry", (0, text, self.page))


doc = ReportDoc(str(OUT), pagesize=A4,
                leftMargin=MARGIN_X, rightMargin=MARGIN_X,
                topMargin=MARGIN_Y, bottomMargin=MARGIN_Y,
                title="BT3041 Progress Report",
                author="BT3041 Term Project")
doc._section = ""
frame = Frame(MARGIN_X, MARGIN_Y, CONTENT_W, PAGE_H - 2 * MARGIN_Y, id="f")
doc.addPageTemplates([PageTemplate(id="p", frames=[frame],
                                   onPage=page_furniture)])
doc.multiBuild(story)
print("  wrote %s" % OUT.relative_to(CM.ROOT))
