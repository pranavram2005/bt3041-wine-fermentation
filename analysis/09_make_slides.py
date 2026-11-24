"""
Build the progress presentation as a PowerPoint file.

Ten slides: a title, EIGHT content slides, and a closing slide, budgeted for
a SIX-minute talk plus two minutes of questions. Eight content slides at
roughly 45 seconds each is what actually fits; ten would be 36 seconds each,
which is a read-aloud, not a talk.

Consolidations made to reach six minutes:
  - the kinetics table and the variance scan merged into one EDA slide
  - the analysis plan and the code merged into one methods slide
Everything the brief asks for is still present: the hypotheses, the code,
the work under way, and the group's own interpretation, which comes last.

SCOPE: the brief asks for at least 40 % of the work by the progress
presentation, so the talk covers steps 1-4 - download, understand, prepare,
explore. Hypothesis testing, PCA and clustering are complete and are
summarised on one slide rather than presented in detail.

Design: assertion-evidence (Alley, Penn State) - every headline is a
full-sentence claim and the body is evidence, never a bulleted restatement.
Typographic only: no coloured bars, rules or borders. Colour appears in text
and in numbers, where it carries meaning, and nowhere as decoration.

Output: outputs/BT3041_Progress_Presentation.pptx
"""
import sys
import glob
from pathlib import Path

import pandas as pd
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

sys.path.insert(0, str(Path(__file__).parent))
import common as CM

OUT = CM.ROOT / "outputs" / "BT3041_Progress_Presentation.pptx"
FIG = CM.FIGURES
TAB = CM.TABLES

# ---- palette: the figures' own, so plots and slides are one system --------
INK = RGBColor(0x0B, 0x0B, 0x0B)
INK2 = RGBColor(0x52, 0x51, 0x4E)
INK3 = RGBColor(0x8A, 0x88, 0x82)
PAPER = RGBColor(0xFC, 0xFC, 0xFB)
TINT = RGBColor(0xF3, 0xF2, 0xEF)
CODEBG = RGBColor(0xF0, 0xEF, 0xEB)
GRID = RGBColor(0xE6, 0xE5, 0xE0)
BLUE = RGBColor(0x2A, 0x78, 0xD6)
ORANGE = RGBColor(0xC7, 0x4E, 0x1E)
FONT = "Calibri"
MONO = "Consolas"

W, H = Inches(13.333), Inches(7.5)
MX = Inches(0.78)
CW = W - 2 * MX

prs = Presentation()
prs.slide_width, prs.slide_height = W, H
BLANK = prs.slide_layouts[6]

# ======================================================= numbers from the CSVs
within = pd.read_csv(TAB / "05_within_regime_strain_tests.csv", index_col=0)
ev = pd.read_csv(TAB / "06_explained_variance.csv", index_col=0)
sep = pd.read_csv(TAB / "06_label_separation.csv", index_col=0)
ari = pd.read_csv(TAB / "07_cluster_label_agreement.csv", index_col=0)
stab = pd.read_csv(TAB / "07_stability_resampling.csv", index_col=0)
ksel = pd.read_csv(TAB / "07_k_selection.csv", index_col=0)
kin_t = pd.read_csv(TAB / "02_kinetics_by_temperature.csv")

N_SIG = int((within["strain_effect"] == "significant").sum())
N_TESTS = len(within)
LEVENE_FAIL = int((within["levene_p"] <= 0.05).sum())
K_KAISER = int((ev["eigenvalue"] > 1).sum())
CUM = ev.loc[K_KAISER - 1, "cumulative_pct"]
SIL = dict(zip(sep["label"], sep["silhouette_in_PC_space"]))
ARI = dict(zip(ari["label"], ari["ARI_ward"]))
STAB = stab["ARI_vs_full"].mean()
BEST_K = int(ksel.loc[ksel["silhouette_ward"].idxmax(), "k"])
D = "°"


# =================================================================== toolkit
def slide():
    s = prs.slides.add_slide(BLANK)
    f = s.background.fill
    f.solid()
    f.fore_color.rgb = PAPER
    return s


def block(s, x, y, w, h, color):
    """A plain filled area. Used only for tints behind text, never as a border."""
    sh = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    sh.fill.solid()
    sh.fill.fore_color.rgb = color
    sh.line.fill.background()
    sh.shadow.inherit = False
    return sh


def hairline(s, x, y, w, color=GRID):
    block(s, x, y, w, Pt(0.9), color)


def box(s, x, y, w, h):
    tb = s.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    return tf


def para(tf, text, *, size=16, color=INK, bold=False, italic=False, mono=False,
         before=0, after=6, first=False, align=PP_ALIGN.LEFT, line=1.22):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.space_before = Pt(before)
    p.space_after = Pt(after)
    p.line_spacing = line
    r = p.add_run()
    r.text = text
    r.font.size, r.font.bold, r.font.italic = Pt(size), bold, italic
    r.font.color.rgb = color
    r.font.name = MONO if mono else FONT
    return p


def head(s, kicker, title, n=None):
    """Kicker, headline, hairline. No coloured bar anywhere."""
    tf = box(s, MX, Inches(0.44), CW - Inches(1.3), Inches(0.26))
    para(tf, kicker.upper(), size=11.5, color=INK3, bold=True, first=True,
         after=0)
    if n:
        tf = box(s, W - MX - Inches(1.2), Inches(0.44), Inches(1.2), Inches(0.26))
        para(tf, n, size=11.5, color=INK3, first=True, after=0,
             align=PP_ALIGN.RIGHT)
    tf = box(s, MX, Inches(0.78), CW, Inches(0.72))
    para(tf, title, size=29, color=INK, bold=True, first=True, after=0,
         line=1.06)
    hairline(s, MX, Inches(1.60), CW)
    return Inches(1.90)


def stat(s, x, y, value, label, *, accent=BLUE, vsize=40, w=Inches(2.5),
         lsize=12):
    tf = box(s, x, y, w, Inches(vsize * 1.25 / 72))
    para(tf, value, size=vsize, color=accent, bold=True, first=True, after=0,
         line=0.98)
    tf = box(s, x, y + Inches(vsize * 1.22 / 72), w, Inches(0.56))
    para(tf, label, size=lsize, color=INK2, first=True, after=0, line=1.16)


def takeaway(s, y, text, *, size=16.5, w=None, x=None, h=0.62):
    x = MX if x is None else x
    w = w or CW
    block(s, x, y, w, Inches(h), TINT)
    tf = box(s, x + Inches(0.26), y + Inches(0.07), w - Inches(0.5), Inches(h))
    para(tf, text, size=size, color=INK, bold=True, first=True, after=0,
         line=1.18)


def tintpanel(s, x, y, w, h, title, lines, *, tsize=15, bsize=13.5):
    block(s, x, y, w, h, TINT)
    tf = box(s, x + Inches(0.26), y + Inches(0.18), w - Inches(0.5),
             h - Inches(0.26))
    para(tf, title, size=tsize, color=INK, bold=True, first=True, after=7,
         line=1.14)
    for t in lines:
        para(tf, t, size=bsize, color=INK2, after=5, line=1.24)


def picture(s, name, *, x, y, w=None, h=None):
    path = FIG / name
    if not path.exists():
        para(box(s, x, y, w or Inches(5), Inches(0.4)),
             "[missing figure: %s]" % name, size=14, color=ORANGE, first=True)
        return
    if w is not None:
        s.shapes.add_picture(str(path), x, y, width=w)
    else:
        s.shapes.add_picture(str(path), x, y, height=h)


def grid_table(s, x, y, w, data, *, col_w=None, size=12.5, head_size=12.5,
               row_h=Inches(0.34)):
    rows, cols = len(data), len(data[0])
    t = s.shapes.add_table(rows, cols, x, y, w, row_h * rows).table
    if col_w:
        for i, cwi in enumerate(col_w):
            t.columns[i].width = cwi
    for r in range(rows):
        for c in range(cols):
            cell = t.cell(r, c)
            cell.text = str(data[r][c])
            pr = cell.text_frame.paragraphs[0]
            pr.alignment = PP_ALIGN.LEFT if c == 0 else PP_ALIGN.CENTER
            f = pr.runs[0].font
            f.size = Pt(head_size if r == 0 else size)
            f.bold = (r == 0)
            f.name = FONT
            f.color.rgb = INK if (r == 0 or c == 0) else INK2
            cell.fill.solid()
            cell.fill.fore_color.rgb = TINT if r == 0 else PAPER
    return t


def notes(s, t):
    s.notes_slide.notes_text_frame.text = t


# ============================================================ 1  TITLE  0:00
s = slide()
tf = box(s, MX, Inches(1.85), Inches(11.2), Inches(3.2))
para(tf, "BT3041  ·  PROGRESS PRESENTATION", size=13, color=INK3,
     bold=True, first=True, after=22)
para(tf, "Do nine commercial wine yeasts\nactually ferment differently?",
     size=46, color=INK, bold=True, after=20, line=1.05)
para(tf, "Exploring 216 wine fermentations before testing them",
     size=21, color=INK2, after=0)

hairline(s, MX, Inches(5.26), Inches(2.4))
tf = box(s, MX, Inches(5.54), Inches(11.4), Inches(1.6))
para(tf, "Team 20", size=15, color=INK, bold=True, first=True, after=5)
para(tf, "K James Bond  ·  Avala Madhavi  ·  Dinesh Kumar  ·  "
         "Mohesh  ·  Pranav Ram", size=15, color=INK2, after=9)
para(tf, "Teaching Assistant: Kaviya D", size=13.5, color=INK2, after=9)
para(tf, "Data: Minebois & Querol (2025), “Fermentation data set obtained "
         "from commercial wine strains in synthetic grape must”, Zenodo, "
         "doi:10.5281/zenodo.15260916  ·  CC BY 4.0",
     size=11.5, color=INK3, after=0, line=1.26)
notes(s, "0:00-0:08   TOTAL BUDGET 6:00. Eight content slides, ~45 s each.\n\n"
         "Say the title question and move on. Do not introduce all five "
         "members by name - the slide does that.")

# ============================================================ 2  WHY  0:08
s = slide()
y = head(s, "Background", "Wineries pay a premium for strain. Does it pay off?",
         n="1 / 8")

tf = box(s, MX, y, Inches(5.35), Inches(3.6))
para(tf, "Wine is grape must that yeast has eaten the sugar out of.",
     size=18, color=INK, bold=True, first=True, after=13)
para(tf, "Wineries pay more for particular strains, assuming they behave "
         "differently. Do they?", size=15, color=INK2, after=18, line=1.28)
para(tf, "Our research question", size=14, color=INK3, bold=True, after=7)
para(tf, "Do strains differ at a given fermentation temperature?",
     size=18, color=BLUE, bold=True, after=16, line=1.2)
para(tf, "Why not simply rank them?", size=14, color=INK3, bold=True, after=7)
para(tf, "The ranking changes with temperature — slide 5.",
     size=14.5, color=INK2, after=0, line=1.28)

picture(s, "fig18_fermentation_overview.png", x=Inches(6.55), y=y - Inches(0.1),
        h=Inches(4.55))
notes(s, "0:08-0:50  (42 s)  Background and the question.\n\n"
         "Walk the diagram left to right in one sentence: synthetic must goes "
         "in at 210-250 g/L sugar, yeast converts it, wine comes out at "
         "12-14 % ethanol. Then the bottom row: that was run 216 times.\n\n"
         "Q: Why this topic? A: a real process, public data, and it lets us "
         "apply the whole course toolkit to one question.\n\n"
         "Q: Why not rank the strains? A: the ranking is not stable across "
         "temperatures - slide 5 is the evidence.")

# ============================================================ 3  DESIGN  0:50
s = slide()
y = head(s, "The dataset", "216 fermentations — not 1,944 rows", n="2 / 8")

tf = box(s, MX, y - Inches(0.08), Inches(4.0), Inches(1.5))
para(tf, "216", size=88, color=BLUE, bold=True, first=True, after=0, line=0.92)
tf = box(s, MX, y + Inches(1.10), Inches(4.0), Inches(0.5))
para(tf, "INDEPENDENT FERMENTATIONS", size=13.5, color=INK2, bold=True,
     first=True, after=0)
hairline(s, MX, y + Inches(1.60), Inches(3.8))

grid_table(s, MX, y + Inches(1.80), Inches(4.0), [
    ["Factor", "Levels"],
    ["Strain", "9"],
    ["Temperature regime", "4"],
    ["Initial sugar", "2"],
    ["Replicate", "3"],
], col_w=[Inches(2.75), Inches(1.25)], row_h=Inches(0.31))

tf = box(s, MX, y + Inches(3.62), Inches(4.3), Inches(0.7))
para(tf, "9 × 4 × 2 × 3 = 216, each sampled 9 times "
         "= 1,944 rows", size=13.5, color=INK3, first=True, after=0, line=1.25)

picture(s, "fig01_sugar_curves_by_strain.png", x=Inches(7.45),
        y=y - Inches(0.12), h=Inches(4.05))

takeaway(s, Inches(6.18),
         "Those 9 samples are one experiment measured repeatedly — using "
         "all 1,944 rows would claim 9× the evidence the experiment "
         "provides.", size=16)
notes(s, "0:50-1:45  (55 s)  THE KEY SLIDE. Give it the most time.\n\n"
         "Q: Why 216 and not 1,944? A: nine samples from one fermentation are "
         "repeated measures of one unit. Treating them as independent "
         "inflates n ninefold and almost everything comes out significant. "
         "This is pseudoreplication.\n\n"
         "Q: How did you collapse them? A: each fermentation becomes one row "
         "of summary features - T50, T90, peak rate, peak viable count, "
         "final concentrations. 216 rows, 22 columns.\n\n"
         "Q: Is the design balanced? A: yes, verified by cross-tabulation.")

# ============================================================ 4  QUALITY 1:45
s = slide()
y = head(s, "Data quality",
         "Four problems we found before trusting the numbers", n="3 / 8")

cols = [
    ("74 impossible readings",
     "Sugar rises over time in 71 of the 216 fermentations.",
     "Flagged, not deleted."),
    ("“210 g/L” was not 210 g/L",
     "Measured must ran 203–229 g/L inside the nominal 210 group.",
     "Baselined on each unit's own t0."),
    ("Structural missingness",
     "Amino acids and volatiles assayed at 5 of 9 sampling points.",
     "Not imputed."),
    ("One never finished",
     "GALA|TVAR|250|R1 never reached 90 % sugar consumption.",
     "Kept — n = 215."),
]
cwid, g = Inches(2.88), Inches(0.18)
for i, (ttl, prob, fix) in enumerate(cols):
    x = MX + i * (cwid + g)
    tf = box(s, x, y, cwid, Inches(0.56))
    para(tf, ttl, size=15.5, color=INK, bold=True, first=True, after=0,
         line=1.14)
    hairline(s, x, y + Inches(0.60), Inches(2.2))
    tf = box(s, x, y + Inches(0.78), cwid, Inches(1.15))
    para(tf, prob, size=13, color=INK2, first=True, after=10, line=1.26)
    para(tf, fix, size=13, color=INK, bold=True, after=0, line=1.26)

hairline(s, MX, Inches(3.98), CW)
tf = box(s, MX, Inches(4.18), Inches(6.3), Inches(0.9))
para(tf, "Five cleaning decisions, all documented in code",
     size=15, color=INK, bold=True, first=True, after=9)
para(tf, "Workbook never modified  ·  temperature categorical  ·  "
         "t5bis excluded  ·  no imputation  ·  MS is a label",
     size=13.5, color=INK2, after=0, line=1.28)

# the checks that came back clean belong here too - they fill what would
# otherwise be dead space under the decisions, and they are what lets us
# say the four problems above are the only ones
for j, (v, l) in enumerate([("0", "DUPLICATE ROWS"),
                            ("0", "NEGATIVE VALUES"),
                            ("32", "NEVER WENT DRY")]):
    stat(s, MX + j * Inches(2.15), Inches(5.35), v, l, accent=INK,
         vsize=30, w=Inches(2.05), lsize=11)

picture(s, "fig02_distributions.png", x=Inches(7.35), y=Inches(4.08),
        w=Inches(5.2))

takeaway(s, Inches(6.62),
         "Flagged, not deleted — the decision stays visible and "
         "reversible.", size=16)
notes(s, "1:45-2:30  (45 s)  Second-strongest slide, and a likely question "
         "source. Do not read all four cards aloud - point at them and "
         "narrate the first and the last.\n\n"
         "Q: Why not delete the impossible readings? A: deleting silently "
         "changes the dataset; flagging keeps it auditable. They are excluded "
         "from the kinetic fits anyway, via a cumulative maximum.\n\n"
         "Q: Does the sugar labelling problem matter? A: yes - using MS as "
         "the baseline would produce 173 impossible negative values.")

# ============================================================ 5  EDA  2:30
s = slide()
y = head(s, "Exploratory analysis",
         "Temperature drives kinetics. Sugar drives chemistry.", n="4 / 8")
picture(s, "fig08_variance_decomposition.png", x=MX, y=y, w=Inches(7.3))

bx = Inches(8.55)
stat(s, bx, y, "87.5%", "OF T50 VARIANCE IS\nTEMPERATURE", accent=BLUE,
     vsize=38, w=Inches(3.7))
stat(s, bx, y + Inches(1.30), "76.7%", "OF FINAL ETHANOL IS\nINITIAL SUGAR",
     accent=BLUE, vsize=38, w=Inches(3.7))
stat(s, bx, y + Inches(2.60), "29.5%", "STRAIN'S LARGEST\nSHARE ANYWHERE",
     accent=ORANGE, vsize=38, w=Inches(3.7))

tf = box(s, MX, Inches(5.34), Inches(7.6), Inches(1.1))
para(tf, "Fermentation at 25 %sC finishes in about a quarter of the time it "
         "takes at 12 %sC. Thirty-two of the 216 never reached 2 g/L "
         "— and none of those was at 25 %sC." % (D, D, D),
     size=14.5, color=INK, bold=True, first=True, after=9, line=1.26)
para(tf, "Strain is never the largest term for any outcome.",
     size=13.5, color=INK2, after=0, line=1.26)

takeaway(s, Inches(6.40),
         "So we will not test final ethanol across strains — it measures "
         "the must, not the yeast.", size=16)
notes(s, "2:30-3:15  (45 s)  Where the signal is. This slide now carries both "
         "the kinetics and the variance scan.\n\n"
         "Lead with the headline, then the two orange-ish facts: temperature "
         "for speed, sugar for chemistry, strain never first.\n\n"
         "The ethanol exclusion is the line worth saying slowly - strain "
         "explains 0.4 % of final ethanol against 76.7 % for initial sugar. "
         "It shows outcomes were chosen on evidence.")

# ============================================================ 6  INTERACTION 3:15
s = slide()
y = head(s, "The finding that shapes our analysis",
         "No strain is fastest in all four regimes", n="5 / 8")
picture(s, "fig07_rank_bump.png", x=MX, y=y, h=Inches(3.95))

bx = Inches(7.65)
tf = box(s, bx, y + Inches(0.05), Inches(4.9), Inches(2.4))
para(tf, "W12", size=24, color=BLUE, bold=True, first=True, after=2)
para(tf, "ranks 1, 3, 1, 1 — consistently fast", size=14.5, color=INK2,
     after=16)
para(tf, "VIN13", size=24, color=ORANGE, bold=True, after=2)
para(tf, "ranks 8, 9, 9, 2 — slowest when cold,\nnear-fastest under TVAR",
     size=14.5, color=INK2, after=0, line=1.25)

stat(s, bx, y + Inches(2.55), "0.32",
     "SPEARMAN BETWEEN THE 12 %sC AND TVAR RANKINGS" % D,
     accent=INK, vsize=38, w=Inches(4.9), lsize=12)

takeaway(s, Inches(6.18),
         "A strain × temperature interaction — so strain must be "
         "tested separately within each regime, not pooled across them.",
         size=16)
notes(s, "3:15-4:05  (50 s)  The methodological pivot. Second-most important "
         "slide after the design.\n\n"
         "ONE-SENTENCE DEFINITION to have ready: an interaction means the "
         "effect of one factor depends on the level of another - here, "
         "which strain is fastest depends on the temperature.\n\n"
         "Q: Is 0.32 low? A: yes - the strain ordering at 12 degC tells "
         "you very little about the ordering under TVAR. Adjacent constant "
         "temperatures agree far better: 18 vs 25 degC is 0.83.")

# ============================================================ 7  METHOD  4:05
s = slide()
y = head(s, "Hypotheses, method and code", "What we test next, and how",
         n="6 / 8")

tintpanel(s, MX, y, Inches(6.05), Inches(1.42), "H₀  ·  the interaction",
          ["The effect of strain does not depend on temperature.",
           "H₁: the strain effect differs between regimes."],
          tsize=14.5, bsize=13)
tintpanel(s, MX, y + Inches(1.58), Inches(6.05), Inches(1.42),
          "H₀  ·  strain, within one regime",
          ["All nine strains have equal mean outcome at a given temperature.",
           "H₁: at least one strain differs."],
          tsize=14.5, bsize=13)

tf = box(s, MX, y + Inches(3.18), Inches(6.05), Inches(1.5))
para(tf, "How each test is chosen", size=14.5, color=INK, bold=True,
     first=True, after=8)
para(tf, "Shapiro–Wilk and Levene decide: ANOVA, Welch, or "
         "Kruskal–Wallis. Then Tukey, Benjamini–Hochberg, "
         "partial η² and 95 % CIs.",
     size=13, color=INK2, after=0, line=1.27)

block(s, Inches(7.2), y, Inches(5.35), Inches(3.05), CODEBG)
tf = box(s, Inches(7.44), y + Inches(0.20), Inches(4.95), Inches(2.8))
code = [
    ("# common.py — source never written back", INK3),
    ("df = pd.read_excel(XLSX, \"Data\")", INK),
    ("t0 = df[df.Time == 0].set_index(\"Unit\")", INK),
    ("df[\"InitialSugar\"] = df.Unit.map(t0)", INK),
    ("", INK),
    ("# 05_hypothesis_tests.py — the model", INK3),
    ("m = smf.ols(\"y ~ C(Strain)*C(Temperature)\"", INK),
    ("            \" + C(MS)\", data=units).fit()", INK),
    ("anova_lm(m, typ=2)   # units = 216 rows", INK),
]
for i, (ln, col) in enumerate(code):
    para(tf, ln if ln else " ", size=11.5, color=col, mono=True,
         first=(i == 0), after=3, line=1.18)

tf = box(s, Inches(7.2), y + Inches(3.22), Inches(5.35), Inches(1.4))
para(tf, "Nine scripts, one unmodified workbook", size=14.5, color=INK,
     bold=True, first=True, after=8)
para(tf, "pandas · scipy · statsmodels · scikit-learn. "
         "Every number here is generated from them.",
     size=13, color=INK2, after=0, line=1.27)

takeaway(s, Inches(6.40),
         "The assumptions choose the test — not whichever test gives the "
         "smaller p-value.", size=16)
notes(s, "4:05-4:45  (40 s)  Hypotheses, method and code on one slide.\n\n"
         "State both null hypotheses out loud - the brief asks for them "
         "explicitly. Then point at the code box for five seconds: 'the "
         "workbook is never modified, and the model runs on the 216-row "
         "table.' Do not read the code.\n\n"
         "Q: Why Welch's ANOVA? A: Levene fails in %d of %d cells, and "
         "Kruskal-Wallis is not a remedy for unequal variance - it assumes "
         "comparable spread too.\n\n"
         "Q: Why correct for multiple comparisons? A: 24 tests at alpha .05 "
         "give about one false positive by chance alone." % (LEVENE_FAIL, N_TESTS))

# ============================================================ 8  UNDER WAY 4:45
s = slide()
y = head(s, "Work under way", "Three analyses are running beyond this talk",
         n="7 / 8")

items = [
    ("Hypothesis testing", "fig09_anova_partial_eta2.png",
     "%d / %d" % (N_SIG, N_TESTS), "TESTS SIGNIFICANT", BLUE,
     "Strain × temperature interaction holds for all six outcomes."),
    ("Principal Component Analysis", "fig13_pca_scatter.png",
     "%+.3f" % SIL["Strain"], "STRAIN SILHOUETTE", ORANGE,
     "%d components, %.1f %% of variance. Strain does not separate."
     % (K_KAISER, CUM)),
    ("Clustering", "fig16_clusters_vs_design.png",
     "%+.3f" % ARI["Strain"], "CLUSTERS vs STRAIN", ORANGE,
     "k = %d, stable at resample ARI %.2f. Clusters track sugar and speed."
     % (BEST_K, STAB)),
]
for i, (ttl, fign, num, lab, col, line) in enumerate(items):
    x = MX + i * Inches(4.07)
    wcol = Inches(3.8)
    tf = box(s, x, y, wcol, Inches(0.42))
    para(tf, ttl, size=15.5, color=INK, bold=True, first=True, after=0,
         line=1.1)
    hairline(s, x, y + Inches(0.40), Inches(3.3))
    picture(s, fign, x=x, y=y + Inches(0.56), w=wcol)
    stat(s, x, Inches(4.52), num, lab, accent=col, vsize=36, w=wcol,
         lsize=11.5)
    tf = box(s, x, Inches(5.62), wcol, Inches(0.9))
    para(tf, line, size=13, color=INK2, first=True, after=0, line=1.26)

takeaway(s, Inches(6.58),
         "All three agree with the exploratory work: temperature and must "
         "composition dominate, and strain modulates rather than drives.",
         size=16)
notes(s, "4:45-5:10  (25 s - FAST)  Do not explain all three. Say: "
         "'these are complete and being written up', give the three numbers, "
         "and move on.\n\n"
         "Be honest about status: the analyses are done and the code is in "
         "the repository. What is not finished is our own interpretation.\n\n"
         "HARDEST LIKELY Q: how can strains be significant in the tests but "
         "invisible in the PCA and clustering? A: they answer different "
         "questions. PCA and clustering sort by largest overall variance, and "
         "strain is third behind must composition and temperature. The tests "
         "hold temperature fixed and ask about one outcome at a time.")

# ============================================================ 9  OBS / INTERP 5:10
s = slide()
y = head(s, "Observations and interpretation", "What the data is telling us",
         n="8 / 8")

panels = [
    ("1.  Temperature has priority over strain",
     ["Fermentation was much faster at 25 %sC than at 12 %sC." % (D, D),
      "T90 varied far more with temperature (147.9 h) than with strain "
      "(26.3 h)."],
     ["Temperature plays a much greater role than strain in fermentation "
      "rate.",
      "Proper temperature regulation is therefore essential to control "
      "fermentation kinetics.",
      "Choosing a particular strain will not save the day under the wrong "
      "temperature."]),
    ("2.  Rankings depend on the temperature regime",
     ["VIN13 was 8th at 12 %sC and rose to 2nd under TVAR." % D,
      "W12 ranked among the fastest across every regime.",
      "Strain rankings were greatly affected by temperature."],
     ["Different strains respond differently to temperature conditions.",
      "A strain that performs poorly in the cold can perform well under a "
      "varying regime.",
      "Strain should be chosen for the fermentation conditions, not from a "
      "universal ranking."]),
]
for i, (ttl, obs, interp) in enumerate(panels):
    x = MX + i * Inches(6.12)
    wcol = Inches(5.7)
    tf = box(s, x, y, wcol, Inches(0.46))
    para(tf, ttl, size=16.5, color=INK, bold=True, first=True, after=0,
         line=1.14)
    hairline(s, x, y + Inches(0.46), Inches(5.2))

    tf = box(s, x, y + Inches(0.66), wcol, Inches(1.4))
    para(tf, "OBSERVATION", size=11, color=INK3, bold=True, first=True,
         after=7)
    for t in obs:
        para(tf, "·   " + t, size=13.5, color=INK2, after=5, line=1.26)

    tf = box(s, x, y + Inches(2.18), wcol, Inches(2.1))
    para(tf, "INTERPRETATION", size=11, color=BLUE, bold=True, first=True,
         after=7)
    for t in interp:
        para(tf, "·   " + t, size=13.5, color=INK, after=6, line=1.26)

takeaway(s, Inches(6.18),
         "Fermentation speed is mostly determined by temperature, while "
         "yeast performance depends on the temperature regime.", size=17)
notes(s, "5:10-5:55  (45 s)  YOUR interpretation. The TA will question this "
         "hardest, so leave time for it.\n\n"
         "Read the two bold headings and the closing line; let the audience "
         "read the bullets. Do not narrate all ten.\n\n"
         "Every member should be able to speak to both points - the brief "
         "warns that any member may be asked about any part.\n\n"
         "Avoid saying any strain is simply 'best': the interaction "
         "contradicts it. The defensible claim is conditional - W12 was "
         "fastest or near-fastest in all four regimes.")

# ============================================================ 10  CLOSE  5:55
s = slide()
tf = box(s, MX, Inches(2.75), Inches(11.2), Inches(1.6))
para(tf, "Thank you", size=48, color=INK, bold=True, first=True, after=18,
     line=1.05)
para(tf, "Questions welcome.", size=20, color=INK2, after=0)

hairline(s, MX, Inches(5.05), Inches(2.4))
tf = box(s, MX, Inches(5.35), Inches(11.4), Inches(1.3))
para(tf, "Team 20  ·  BT3041  ·  Comparative Statistical Analysis of "
         "Commercial Yeast Strains During Wine Fermentation",
     size=14, color=INK2, first=True, after=7)
para(tf, "Data: Minebois & Querol (2025), Zenodo, doi:10.5281/zenodo.15260916"
         "  ·  Code, figures and tables: analysis/ and outputs/",
     size=12.5, color=INK3, after=0, line=1.26)
notes(s, "5:55-6:00  Close. Stop talking and take questions.\n\n"
         "Most likely questions, in order: why 216 and not 1,944; why flag "
         "rather than delete the bad sugar readings; what an interaction is; "
         "why not just rank the strains; have you started the statistics.")

prs.save(str(OUT))
print("  wrote %s  (%d slides: title + 8 content + close, budgeted 6:00)"
      % (OUT.relative_to(CM.ROOT), len(prs.slides._sldIdLst)))
