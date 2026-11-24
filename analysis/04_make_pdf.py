"""
Step 4 - Build the EDA write-up as a plain PDF.

Set like a book: a serif face, justified text, continuous flow with no forced
page breaks between sections, and figures sized so the text keeps running
beside and below them. Black on white, no colour, no rules, no decoration.

Output: outputs/EDA_Report.pdf
"""
import sys
from pathlib import Path

from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib import colors
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, Image as RLImage, PageBreak, Table,
                                TableStyle, KeepTogether, CondPageBreak)
from reportlab.platypus.tableofcontents import TableOfContents

sys.path.insert(0, str(Path(__file__).parent))
import common as C

FIG = C.FIGURES
OUT = C.ROOT / "outputs" / "EDA_Report.pdf"

PAGE_W, PAGE_H = A4
MARGIN_X = 24 * mm
MARGIN_Y = 22 * mm
CONTENT_W = PAGE_W - 2 * MARGIN_X

BLACK = colors.black
BODY = "Times-Roman"
BOLD = "Times-Bold"
ITAL = "Times-Italic"

S = {
    "title": ParagraphStyle("title", fontName=BOLD, fontSize=20, leading=25,
                            textColor=BLACK, spaceAfter=8),
    "subtitle": ParagraphStyle("subtitle", fontName=BODY, fontSize=12, leading=17,
                               textColor=BLACK, spaceAfter=4),
    "h1": ParagraphStyle("h1", fontName=BOLD, fontSize=14, leading=18,
                         textColor=BLACK, spaceBefore=20, spaceAfter=8,
                         keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName=BOLD, fontSize=11.5, leading=15,
                         textColor=BLACK, spaceBefore=13, spaceAfter=5,
                         keepWithNext=1),
    "body": ParagraphStyle("body", fontName=BODY, fontSize=11, leading=15.5,
                           textColor=BLACK, alignment=TA_JUSTIFY, spaceAfter=8),
    "bullet": ParagraphStyle("bullet", fontName=BODY, fontSize=11, leading=15.5,
                             textColor=BLACK, alignment=TA_JUSTIFY,
                             leftIndent=14, bulletIndent=3, spaceAfter=5),
    "caption": ParagraphStyle("caption", fontName=BODY, fontSize=9.5, leading=13,
                              textColor=BLACK, alignment=TA_JUSTIFY,
                              spaceBefore=6, spaceAfter=14,
                              leftIndent=8, rightIndent=8),
}

story = []


def h1(t):
    story.append(Paragraph(t, S["h1"]))


def h2(t):
    story.append(Paragraph(t, S["h2"]))


def p(t):
    story.append(Paragraph(t, S["body"]))


def bullets(items):
    for it in items:
        story.append(Paragraph(it, S["bullet"], bulletText="•"))
    story.append(Spacer(1, 5))


def table(data, widths=None, size=9.5):
    """Plain table: thin black grid, no fills, no colour."""
    rows = [[Paragraph(str(c), ParagraphStyle(
        "c", fontName=BOLD if r == 0 else BODY, fontSize=size, leading=size + 2.5,
        textColor=BLACK)) for c in row] for r, row in enumerate(data)]
    t = Table(rows, colWidths=widths, hAlign="LEFT", repeatRows=1)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, BLACK),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    story.append(KeepTogether([t, Spacer(1, 11)]))


def figure(name, *, caption, height=92 * mm, heading=None):
    """A figure sized to leave room for text on the same page.

    The heading is bound into the same KeepTogether block, so a section title
    can never be stranded at the foot of a page with its figure overleaf.
    """
    path = FIG / name
    if not path.exists():
        p(f"[missing figure: {name}]")
        return
    iw, ih = Image.open(path).size
    h = height
    w = h * iw / ih
    if w > CONTENT_W:
        w = CONTENT_W
        h = w * ih / iw
    img = RLImage(str(path), width=w, height=h)
    img.hAlign = "CENTER"
    block = [img, Paragraph(caption, S["caption"])]
    if heading:
        block.insert(0, Paragraph(heading, S["h2"]))
    story.append(KeepTogether(block))


# ============================================================== TITLE PAGE
story.append(Spacer(1, 52 * mm))
story.append(Paragraph("Yeast, Sugar and Temperature", S["title"]))
story.append(Paragraph("An exploratory analysis of 216 wine fermentations",
                       S["subtitle"]))
story.append(Spacer(1, 14 * mm))
story.append(Paragraph("BT3041 &mdash; Analysis and Interpretation of Biological Data",
                       S["subtitle"]))
story.append(Paragraph("Dataset: <i>Complete_DataSet.xlsx</i>, the Wine Fermentation "
                       "dataset published on Zenodo", S["subtitle"]))
story.append(Paragraph("30 October 2026", S["subtitle"]))
story.append(PageBreak())

# ================================================================ CONTENTS
story.append(Paragraph("Contents", S["h1"]))
contents = TableOfContents()
contents.levelStyles = [
    ParagraphStyle("toc0", fontName=BOLD, fontSize=10.5, leading=16.5,
                   textColor=BLACK, firstLineIndent=0, leftIndent=0,
                   spaceBefore=3),
    ParagraphStyle("toc1", fontName=BODY, fontSize=10.5, leading=14.5,
                   textColor=BLACK, firstLineIndent=0, leftIndent=14),
]
contents.dotsMinLevel = 0
story.append(contents)
story.append(PageBreak())

# ===================================================================== 1
h1("1. What this is about")
p("Wine is grape juice that yeast has eaten the sugar out of. Grape juice arrives "
  "with something like 210 to 250 grams of sugar in every litre, which is roughly "
  "the consistency of syrup. Add yeast, and it sets about consuming that sugar, "
  "giving off ethanol and carbon dioxide as it goes. When the sugar runs out the "
  "yeast dies back, and what is left is wine.")
p("Winemakers do not leave this to chance. They buy yeast in packets, much like "
  "bread yeast, and the packets carry brand names. Each brand is a different "
  "<i>strain</i> &mdash; genetically distinct versions of the same species, "
  "<i>Saccharomyces cerevisiae</i> &mdash; and wineries pay real money for "
  "particular ones on the understanding that they behave differently. Whether they "
  "really do, and in what way, is the question this dataset was built to answer.")
p("Somebody ran 216 small wine fermentations and followed every one from start to "
  "finish. This report describes what is in that record: how the experiment was "
  "arranged, what had to be checked and corrected before the numbers could be "
  "trusted, and what the data shows once it is cleaned up. It stops short of "
  "drawing biological conclusions, which is work for the group rather than for a "
  "piece of software.")

# ===================================================================== 2
h1("2. What is inside the file")
p("The workbook has two sheets. One, named <i>Explanation</i>, promises to describe "
  "the data but turns out to hold nothing except a list of units, so the data "
  "dictionary had to be reconstructed from the column names and some knowledge of "
  "the biology. The other, named <i>Data</i>, holds 1,950 rows across 49 columns, "
  "and that is the whole dataset.")
p("Each row is one sample drawn from one fermentation at one moment, and the columns "
  "record roughly 43 measured quantities. They fall into natural groups:")
table([
    ["Group of measurements", "How many", "Units"],
    ["Which fermentation this is (strain, temperature, and so on)", "6", "&mdash;"],
    ["Yeast cell counts: live, dead and total", "3", "cells/mL"],
    ["The sugars themselves: glucose and fructose", "2", "g/L"],
    ["The main products: ethanol and glycerol", "2", "% v/v, g/L"],
    ["Organic acids: acetate, citrate, malate, succinate", "4", "g/L"],
    ["Nitrogen the yeast feeds on: amino acids, ammonium", "22", "mg/L"],
    ["Aroma compounds produced during fermentation", "10", "mg/L"],
], widths=[CONTENT_W - 48 * mm, 20 * mm, 28 * mm])
p("The full dictionary, with a description of every variable, is saved as "
  "<i>01_data_dictionary.csv</i> and covers 55 entries once the derived columns are "
  "included.")

# ===================================================================== 3
h1("3. How the experiment was set up")
p("This is not simply nine yeasts compared side by side. Four things were varied "
  "deliberately, and every possible combination of them was run:")
table([
    ["What was varied", "The options", "Why it was varied"],
    ["Yeast strain", "9: DV10, GALA, OPA, SAI, TXL,<br/>VIN13, W12, X16, X5",
     "This is the actual question"],
    ["Temperature", "4: 12 &deg;C, 18 &deg;C, 25 &deg;C,<br/>and a varying regime (TVAR)",
     "Whites ferment cold, reds warm"],
    ["Starting sugar", "2: about 210 or 250 g/L",
     "Riper grapes mean more sugar"],
    ["Repeats", "3 independent runs of each",
     "To separate real effects from flukes"],
], widths=[30 * mm, 60 * mm, CONTENT_W - 90 * mm])
p("Multiply those out: 9 &times; 4 &times; 2 &times; 3 comes to <b>216 separate "
  "fermentations</b>. Each was sampled nine times, from inoculation through to "
  "completion, which gives <b>1,944 observations</b> in total. Nothing is missing "
  "and nothing is doubled up &mdash; there are exactly 24 fermentations per strain, "
  "54 per temperature, and 6 in every single strain-and-temperature combination. A "
  "perfectly balanced design like this is rare and makes the statistics much more "
  "straightforward than they might have been.")
p("That accounts for 1,944 of the 1,950 rows. The remaining six are extra samples "
  "labelled <i>t5bis</i>, taken for two strains only (TXL and VIN13) at one "
  "particular setting. They were dropped so the balance holds, and noted separately "
  "rather than quietly discarded.")

h2("Why the shape of the design matters")
p("Here is the point that governs everything downstream. Because each fermentation "
  "was sampled nine times, those 1,944 rows are <b>not 1,944 independent "
  "observations</b>. Nine of them describe the same vessel at different moments, the "
  "way nine photographs of one person are not nine people. Treating them as "
  "independent would multiply the apparent sample size ninefold and produce "
  "confident-looking results that mean nothing.")
p("So the analysis works from a second table, built in section 6, which condenses "
  "each fermentation down to a single row.")

# ===================================================================== 4
h1("4. Checking the data before trusting it")
p("Before any analysis, the dataset was put through a set of checks. Most of it came "
  "through clean:")
table([
    ["What was checked", "What was found"],
    ["Rows duplicated exactly", "None"],
    ["The same fermentation and time recorded twice", "None"],
    ["Negative concentrations, which are impossible", "None"],
    ["More live cells than total cells, also impossible", "1 sample"],
    ["Ethanol present at the very start", "At most 0.23 %, negligible"],
    ["Live yeast at the start", "33 % of cells, which is normal"],
    ["Fermentations that used up nearly all the sugar", "184 out of 216"],
], widths=[CONTENT_W - 52 * mm, 52 * mm])
p("That figure of 33 % deserves a word, because it looks alarming. The yeast is "
  "added as dried granules that have to be rehydrated, and a good share of the cells "
  "do not survive the process. Starting with a third of the cells alive is ordinary "
  "for this kind of inoculum, not a sign of anything wrong.")
p("Four other things did need attention, and each one would have distorted the "
  "results if it had been missed.")

h2("4.1 Some measurements are missing on purpose")
p("Large blocks of the table are empty, but not at random. Whole assays were simply "
  "not run at certain sampling points:")
table([
    ["Group of measurements", "Incomplete rows", "Where the gaps are"],
    ["Yeast cell counts", "14", "A few at t3 and t4"],
    ["Sugars", "0", "Complete"],
    ["Ethanol and glycerol", "0", "Complete"],
    ["Organic acids", "0", "Complete"],
    ["Nitrogen sources", "300", "t4 and t6"],
    ["Aroma compounds", "864", "t0, t1, t3 and t5"],
], widths=[CONTENT_W - 78 * mm, 30 * mm, 48 * mm])
p("Aroma compounds, for instance, were measured at only five of the nine sampling "
  "points. This is a gap in the laboratory schedule, not data that went astray, and "
  "the distinction matters: filling those cells in by estimating them would be "
  "inventing measurements that were never taken. <b>Nothing was imputed.</b> Each "
  "analysis simply uses the sampling points where its variables actually exist.")

h2("4.2 A label that does not match reality")
p("Each fermentation is tagged as starting with either 210 or 250 g/L of sugar. "
  "Measure what was actually in the juice at the start, though, and the numbers come "
  "out rather differently:")
table([
    ["The label says", "12 &deg;C batch", "18 &deg;C batch", "25 &deg;C batch", "TVAR batch"],
    ["210 g/L", "229.4", "206.2", "203.3", "214.2"],
    ["250 g/L", "266.6", "248.2", "242.3", "244.9"],
], widths=[34 * mm] + [(CONTENT_W - 34 * mm) / 4] * 4)
p("A juice labelled 210 actually ranged from 203 to 229 g/L depending on which batch "
  "it belonged to. Every strain within one batch shares exactly the same starting "
  "value, which tells us this is variation between batches of juice rather than "
  "sloppy measurement. The label is a target the winemaker aimed at, not a reading "
  "they took.")
p("This matters because the obvious way to calculate how much sugar a yeast consumed "
  "is to subtract what is left from what it started with. Use the label as the "
  "starting figure and <b>173 rows come out negative</b> &mdash; yeasts apparently "
  "creating sugar. Every calculation here therefore uses each fermentation's own "
  "measured starting value instead.")

h2("4.3 Readings that cannot be true")
p("Sugar cannot increase during a fermentation. Yeast consumes it; nothing in the "
  "vessel makes more. So any sample showing more sugar than the one before it is "
  "telling us something went wrong in the laboratory rather than in the fermentation. "
  "Checking every fermentation for this turned up 74 such samples, spread across 71 "
  "of the 216 runs, every one of them at an early sampling point. Of those, 63 show "
  "more sugar than the fermentation started with. The worst cases:")
table([
    ["Fermentation", "Sample", "Sugar found", "Jump", "It started at", "Ethanol"],
    ["TXL, 12 &deg;C, 250, run 3", "t1", "346.5 g/L", "+79.9", "266.6 g/L", "0.15 %"],
    ["OPA, 25 &deg;C, 250, run 2", "t1", "289.3 g/L", "+51.5", "237.8 g/L", "0.16 %"],
    ["TXL, 12 &deg;C, 250, run 2", "t2", "297.7 g/L", "+41.9", "266.7 g/L", "0.29 %"],
], widths=[40 * mm, 14 * mm] + [(CONTENT_W - 54 * mm) / 4] * 4)
p("A reading of 346 g/L is outside the range of any grape juice, and with ethanol "
  "still near zero the yeast had barely started work. These are almost certainly "
  "dilution errors made during chemical analysis.")
p("They were <b>flagged rather than deleted</b>. Removing inconvenient numbers "
  "without saying so is how analyses go quietly wrong; the full list is saved to "
  "file. They are skipped when calculating fermentation speed, and they cannot "
  "affect any result measured at the end, because all of them occur early.")

h2("4.4 Samples were not taken on a fixed schedule")
p("The nine sampling points are labelled t0 through t8, which invites the assumption "
  "that t4 means the same elapsed time everywhere. It does not:")
table([
    ["Temperature", "t0", "t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8"],
    ["12 &deg;C", "0", "53", "96", "168", "193", "251", "372", "529", "725"],
    ["18 &deg;C", "0", "28", "53", "82", "119", "162", "218", "268", "477"],
    ["25 &deg;C", "0", "7", "24", "31", "53", "76", "99", "170", "284"],
    ["TVAR", "0", "7", "26", "33", "50", "96", "167", "241", "456"],
], widths=[22 * mm] + [(CONTENT_W - 22 * mm) / 9] * 9, size=9)
p("The final sample comes at around 725 hours in the cold fermentations but 284 "
  "hours in the warm ones, and it even varies between strains at the same "
  "temperature: at 12 &deg;C, W12 was finished at 671 hours while VIN13 ran on to "
  "803. Whoever ran the experiment sampled according to how each fermentation was "
  "progressing, which is sensible laboratory practice but has consequences.")
p("Three of them. Averaging a measurement across strains at a given t-label treats "
  "different elapsed times as though they were the same, so it should not be done. "
  "How long a fermentation took is a genuine result in its own right, not an "
  "inconvenience to be controlled away. And comparing the speed of fermentations "
  "requires putting them on a common time axis first, which is what section 6 does.")

# ===================================================================== 5
h1("5. The decisions made before analysing")
p("Five choices shape everything that follows. They are written into the code so "
  "they are reproducible, and they are listed here so they can be questioned:")
bullets([
    "<b>The original file is never touched.</b> Every script reads it fresh and does "
    "its cleaning in memory, so the raw data on disk stays exactly as downloaded.",
    "<b>Temperature is treated as a category, not a number.</b> Three of the four "
    "settings are numbers, but TVAR is a regime that changes over time and has no "
    "single value, so averaging across them arithmetically would be meaningless.",
    "<b>The six t5bis rows are set aside</b> so the design stays balanced.",
    "<b>Missing values are left missing.</b> They are missing by design, as section "
    "4.1 explained, and estimating them would be fabrication.",
    "<b>Sugar consumed is measured from each fermentation's own starting point</b>, "
    "never from the 210 or 250 label.",
])

# ===================================================================== 6
h1("6. Turning 1,944 rows into 216")
p("Since the rows are not independent, the useful move is to summarise each "
  "fermentation into a single row describing how that run behaved overall. That "
  "produces a table of <b>216 rows, one per fermentation</b>, which is what "
  "hypothesis testing, PCA and clustering should be built on. It is saved as "
  "<i>02_unit_level_features.csv</i>. The columns answer practical questions:")
table([
    ["Column", "The question it answers"],
    ["InitialSugar", "How much sugar was really there at the start?"],
    ["FinalResidualSugar", "How much was left at the end?"],
    ["Dry", "Did it finish properly, below 2 g/L?"],
    ["T50_h, T90_h", "How long to get through half the sugar, and 90 % of it?"],
    ["MaxRate_gL_h", "How fast was it working at its peak?"],
    ["FinalEthanol", "How strong is the resulting wine?"],
    ["EthanolYield_pct_per_gL", "How efficiently was sugar turned into alcohol?"],
    ["FinalGlycerol, FinalAcetate, FinalSuccinate", "What else did the yeast leave behind?"],
    ["MalateConsumed", "How much malic acid did it break down?"],
    ["MaxViable, FinalViability", "How well did the population grow and survive?"],
], widths=[58 * mm, CONTENT_W - 58 * mm])
p("The two timing columns are worth explaining. Rather than take whichever sample "
  "happened to be nearest, the time to reach 50 % and 90 % is interpolated between "
  "the samples either side, so fermentations sampled on different schedules can be "
  "compared fairly. The calculation runs along the best progress achieved so far, "
  "which means the faulty readings from section 4.3 cannot drag the curve backwards.")
p("One fermentation, GALA at the varying temperature with 250 g/L, never reaches "
  "90 % at all. It stalls at 88.8 %, leaving 27.5 g/L of sugar unconsumed. Its "
  "timing is therefore genuinely undefined, so that one outcome has 215 values "
  "rather than 216 &mdash; a small point, but the sort that quietly breaks a "
  "later calculation if nobody notices it.")

# ===================================================================== 7
h1("7. What the data shows")

figure("fig01_sugar_curves_by_strain.png", heading="7.1 How a fermentation unfolds",
       caption="<b>Figure 1.</b> Sugar remaining against time, one panel per strain and one "
       "line per temperature. Each line averages three repeats at two sugar levels. "
       "The horizontal axis is real elapsed time, so each panel simply stops when "
       "that strain was done.", height=104 * mm)
p("Every one of the 36 curves has the same shape: a slow start while the yeast wakes "
  "up and multiplies, then a steep plunge as the population hits full stride, then a "
  "long tail as it works through the last stubborn grams. What changes between the "
  "lines is almost entirely how stretched out that shape is &mdash; and the "
  "stretching is set by temperature, not by which yeast is in the vessel. The "
  "panels look remarkably alike; the lines within each panel do not.")

figure("fig02_distributions.png", heading="7.2 What the individual measurements look like",
       caption="<b>Figure 2.</b> How the eight main measurements are distributed across all "
       "1,944 samples, with the median marked by the dashed line.", height=70 * mm)
p("Most of these are lopsided or have two separate humps, which would normally "
  "suggest something interesting about the strains. Here it is an artefact of when "
  "the samples were taken. Because sampling spans the whole fermentation, each "
  "distribution mixes early samples &mdash; sugar high, ethanol nil &mdash; with "
  "late ones where the reverse holds. The two humps are the beginning and the end of "
  "fermentation, not two kinds of yeast. Cell counts use a logarithmic scale because "
  "they span four orders of magnitude.")

figure("fig03_endpoint_by_strain.png", heading="7.3 Comparing the strains directly",
       caption="<b>Figure 3.</b> Sugar left over, final alcohol, and time taken, with one "
       "point for each of the 24 fermentations per strain. Strains are ordered by "
       "average speed.", height=62 * mm)
p("The spread within each strain is enormous, which is the honest message of this "
  "figure: because every strain was run at four temperatures and two sugar levels, "
  "pooling them together mixes conditions that have very little to do with one "
  "another. It is a reasonable first look and a poor basis for a conclusion. The "
  "next two figures explain why.")

figure("fig05_growth_viability.png", heading="7.4 How the yeast population behaves",
       caption="<b>Figure 4.</b> Live cell count and the percentage of cells still alive, "
       "over time, averaged across all strains and sugar levels.", height=64 * mm)
p("The population climbs by roughly a hundredfold, peaks while fermentation is at "
  "its most active, and then falls away as accumulating ethanol becomes toxic to the "
  "yeast that produced it. Viability traces the same arc, starting around a third "
  "because of the dried inoculum, recovering as the culture grows, and declining at "
  "the end. Cold fermentations take far longer to climb but hold their viability "
  "better once they get there.")

figure("fig04_strain_x_temperature.png", heading="7.5 The finding that complicates everything",
       caption="<b>Figure 5.</b> Average time to get through 90 % of the sugar, shown "
       "separately for each temperature. Each panel is sorted on its own and has its "
       "own scale, so what matters is the order of the names, not the length of the "
       "bars.", height=58 * mm)
p("Read the four lists of names from top to bottom and they are not the same list. "
  "A strain near the top in one panel can sit near the bottom in another. The next "
  "figure makes that explicit by following each strain across the four conditions:")
figure("fig07_rank_bump.png",
       caption="<b>Figure 6.</b> Each line follows one strain's speed ranking across "
       "the four temperatures, where 1 is fastest. The three that shift the most are "
       "drawn in colour; the rest are grey. Lines that cross mean the ranking changed.",
       height=80 * mm)
p("GALA finishes dead last at 12 &deg;C and third fastest at 25 &deg;C. VIN13 is "
  "last at 25 &deg;C and second in the varying regime. Measured properly, the "
  "agreement between the 12 &deg;C ranking and the TVAR ranking is only 0.32 on a "
  "scale where 1 would mean identical and 0 would mean unrelated. No strain is "
  "fastest in all four conditions, though W12 comes closest at first, third, first "
  "and first.")
table([
    ["Strain", "12 &deg;C", "18 &deg;C", "25 &deg;C", "TVAR", "How far it moves"],
    ["VIN13", "8", "9", "9", "2", "7 places"],
    ["GALA", "9", "5", "3", "6", "6 places"],
    ["X16", "4", "4", "5", "8", "4 places"],
    ["SAI", "3", "7", "6", "5", "4 places"],
    ["OPA", "5", "1", "2", "3", "4 places"],
    ["X5", "6", "8", "7", "9", "3 places"],
    ["DV10", "2", "2", "4", "4", "2 places"],
    ["TXL", "7", "6", "8", "7", "2 places"],
    ["W12", "1", "3", "1", "1", "2 places"],
], widths=[26 * mm] + [(CONTENT_W - 26 * mm) / 5] * 5)
p("Statisticians call this an interaction: the effect of one factor depends on the "
  "setting of another. In plain terms, asking which yeast is best is not a question "
  "this data can answer, because the answer changes with the thermostat. Asking "
  "which yeast is best <i>at 18 &deg;C</i>, or which is most dependable across "
  "conditions, are questions it can answer.")

figure("fig06_correlation_heatmap.png", heading="7.6 How the measurements relate to one another",
       caption="<b>Figure 7.</b> How strongly each pair of measurements moves together, "
       "across all samples. Numbers are shown where the relationship is strong.",
       height=100 * mm)
p("A great many of these are very strong &mdash; ethanol and sugar consumed sit at "
  "0.98, succinate and glycerol at 0.96. It is tempting to read deep metabolic "
  "connections into that, and mostly wrong. The common cause is time. Since the "
  "samples span whole fermentations, everything that rises as fermentation proceeds "
  "correlates with everything else that rises, and inversely with everything that "
  "falls. The heat map is largely a picture of fermentation progress wearing a "
  "disguise. Correlations worth interpreting would have to be computed within a "
  "single time point.")

figure("fig08_variance_decomposition.png", heading="7.7 Where the differences actually come from",
       caption="<b>Figure 8.</b> For each outcome, how much of the variation is associated "
       "with temperature, with strain, with starting sugar, with the interaction "
       "between strain and temperature, and how much is left unexplained.",
       height=64 * mm)
p("This is the most useful single picture in the report, because it says where it is "
  "worth looking before any formal test is run. Read a row across and it shows what "
  "drives that outcome, as a percentage:")
table([
    ["Outcome", "Temp.", "Strain", "Sugar", "Strain &times; temp.", "Unexplained"],
    ["Time to half the sugar", "87.5", "5.4", "1.7", "3.6", "1.8"],
    ["Peak fermentation rate", "75.8", "1.8", "0.1", "5.1", "17.1"],
    ["Time to 90 % of the sugar", "72.2", "2.7", "14.9", "3.3", "6.9"],
    ["Succinate at the end", "42.0", "23.8", "10.5", "8.6", "15.2"],
    ["Malic acid broken down", "25.1", "19.1", "5.9", "10.6", "39.2"],
    ["Glycerol at the end", "22.6", "4.0", "53.7", "5.0", "14.6"],
    ["Efficiency of sugar conversion", "18.7", "0.9", "23.7", "12.6", "44.2"],
    ["Peak live cell count", "16.6", "29.5", "12.6", "11.2", "30.2"],
    ["Acetate at the end", "6.5", "18.1", "60.2", "3.6", "11.6"],
    ["Sugar left unconsumed", "5.6", "12.3", "4.2", "15.6", "62.3"],
    ["Cells still alive at the end", "4.4", "9.3", "19.1", "20.4", "46.8"],
    ["Final alcohol", "1.7", "0.4", "76.7", "4.6", "16.6"],
], widths=[52 * mm] + [(CONTENT_W - 52 * mm) / 5] * 5, size=9)
p("These are descriptive figures, deliberately reported without p-values. Their job "
  "is to show where signal exists so that the group can choose its tests for "
  "reasons, rather than running everything against everything and seeing what "
  "survives.")

# ===================================================================== 8
h1("8. What it all adds up to")

h2("Temperature matters far more than brand")
table([
    ["Temperature", "To half the sugar", "To 90 % of it", "Peak rate", "Sugar left"],
    ["12 &deg;C", "216 hours", "506 hours", "0.94 g/L per hour", "2.46 g/L"],
    ["18 &deg;C", "144 hours", "338 hours", "1.44 g/L per hour", "1.39 g/L"],
    ["25 &deg;C", "64 hours", "146 hours", "2.92 g/L per hour", "0.00 g/L"],
    ["TVAR", "78 hours", "307 hours", "2.83 g/L per hour", "1.55 g/L"],
], widths=[26 * mm] + [(CONTENT_W - 26 * mm) / 4] * 4)
p("A fermentation at 12 &deg;C takes about three and a half times as long as the "
  "same one at 25 &deg;C. Set that against the gap between strains and the "
  "comparison is stark: the spread between temperature averages is 148 hours, while "
  "the spread between strain averages is 26. The thermostat moves the outcome "
  "roughly six times as much as the choice of yeast does.")

h2("The alcohol comes from the grapes, not the yeast")
p("Final alcohol is almost entirely decided by how much sugar went in: starting "
  "sugar accounts for 77 % of the variation, and strain for 0.4 %. Fermentations "
  "beginning at the 210 label finished at 11.3 % alcohol on average, those at 250 "
  "finished at 14.3 %. This makes chemical sense &mdash; alcohol is converted sugar, "
  "and nearly every strain converted it about equally well. It also means that "
  "comparing strains on alcohol content, which is the first thing most people would "
  "think to do, would mostly be measuring the juice.")

h2("Strains do differ, but in narrower ways")
p("Strain is never the single largest influence on any outcome measured here. Where "
  "it comes closest is peak cell count, at about 30 % of the variation, followed by "
  "succinate at 24 %, malic acid broken down at 19 % and acetate at 18 %. Those four "
  "are where a comparison between strains has the best prospect of finding something "
  "real &mdash; and acetate in particular matters in practice, since it is what "
  "makes a wine taste of vinegar.")

h2("Thirty-two fermentations never finished")
p("Of the 216 runs, 32 failed to consume their sugar: 14 at 12 &deg;C, 10 in the "
  "varying regime, 8 at 18 &deg;C, and none at all at 25 &deg;C. By strain, GALA "
  "accounted for 9 of them, with OPA, X16 and X5 contributing 4 each and DV10 only "
  "1. A stuck fermentation is a real and expensive problem for a winery, leaving a "
  "sweet wine that spoilage organisms are happy to finish off, so this may be more "
  "practically interesting than small differences in speed.")

h2("There is no single best strain")
p("The honest summary is that the question has no answer without a temperature "
  "attached to it. W12 is the most dependable performer across conditions, and GALA "
  "the least. Beyond that, showing <i>why</i> the obvious question is the wrong one "
  "is a more substantial finding than naming a winner would have been.")

# ===================================================================== 9
h1("9. What was produced")
p("Eight figures, all in <i>outputs/figures</i>:")
table([
    ["File", "What it shows"],
    ["fig01_sugar_curves_by_strain.png", "Sugar against time, every strain and temperature"],
    ["fig02_distributions.png", "How the main measurements are distributed"],
    ["fig03_endpoint_by_strain.png", "Final outcomes compared across strains"],
    ["fig04_strain_x_temperature.png", "Speed per strain within each temperature"],
    ["fig05_growth_viability.png", "Growth and survival of the yeast population"],
    ["fig06_correlation_heatmap.png", "How twenty measurements relate to each other"],
    ["fig07_rank_bump.png", "How strain rankings shift with temperature"],
    ["fig08_variance_decomposition.png", "What drives each outcome"],
], widths=[72 * mm, CONTENT_W - 72 * mm])
p("Fourteen tables, all in <i>outputs/tables</i>:")
table([
    ["File", "What is in it"],
    ["01_data_dictionary.csv", "Every variable, with units and description"],
    ["01_design_balance.csv", "Confirmation that the design is balanced"],
    ["01_sampling_times.csv", "When samples were actually taken"],
    ["01_missingness_by_block.csv", "Which measurements are missing where"],
    ["01_nominal_vs_measured_sugar.csv", "The label against the real starting sugar"],
    ["01_flagged_nonmonotonic_sugar.csv", "The 74 suspect readings, listed in full"],
    ["02_descriptives_all_timepoints.csv", "Averages, spreads and ranges"],
    ["02_endpoint_by_strain.csv", "Final-sample figures per strain"],
    ["02_unit_level_features.csv", "The 216-row table the analysis runs on"],
    ["02_kinetics_by_strain.csv", "Speed summary per strain"],
    ["02_kinetics_by_temperature.csv", "Speed summary per temperature"],
    ["02_strain_rank_by_temperature.csv", "Rankings behind Figures 5 and 6"],
    ["02_spearman_correlations.csv", "The full correlation matrix"],
    ["03_variance_decomposition.csv", "The figures behind Figure 8"],
], widths=[72 * mm, CONTENT_W - 72 * mm])

h2("Reproducing all of this")
p("Install the libraries, then run the four scripts in order:")
p("<font name='Courier' size='9.5'>pip install pandas numpy scipy matplotlib "
  "openpyxl reportlab pillow</font>")
p("<font name='Courier' size='9.5'>python analysis/01_inspect.py<br/>"
  "python analysis/02_eda.py<br/>python analysis/03_variance_scan.py<br/>"
  "python analysis/04_make_pdf.py</font>")
p("Deleting the outputs folder and running those four commands rebuilds every "
  "figure, every table and this report from the original spreadsheet, which is never "
  "modified.")

h2("A note on what this report does not do")
p("Everything above describes what is in the data. It does not state the group's "
  "aims or hypotheses, and it draws no biological conclusions, because the BT3041 "
  "guidelines require that work to be the group's own. The percentages in section "
  "7.7 are given as effect sizes without p-values for the same reason: which tests "
  "to run, and why, is a decision that should be made and defended by the people "
  "writing the report.")


# ================================================================== BUILD
def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont(BODY, 9.5)
    canvas.setFillColor(BLACK)
    if doc.page > 1:
        canvas.drawCentredString(PAGE_W / 2, 12 * mm, str(doc.page))
    canvas.restoreState()


class ReportDoc(BaseDocTemplate):
    """Feeds each heading to the table of contents with the page it landed on."""

    def afterFlowable(self, flowable):
        if not isinstance(flowable, Paragraph):
            return
        name = flowable.style.name
        if name not in ("h1", "h2"):
            return
        text = flowable.getPlainText()
        if text == "Contents":
            return
        # Only numbered sub-headings are navigation targets. The unnumbered ones
        # are narrative signposts inside a section, and listing them makes the
        # contents longer and harder to read, not more useful.
        if name == "h2" and not text[:1].isdigit():
            return
        self.notify("TOCEntry", (0 if name == "h1" else 1, text, self.page))


doc = ReportDoc(str(OUT), pagesize=A4,
                leftMargin=MARGIN_X, rightMargin=MARGIN_X,
                topMargin=MARGIN_Y, bottomMargin=MARGIN_Y,
                title="Yeast, Sugar and Temperature",
                author="BT3041 Term Project")
frame = Frame(MARGIN_X, MARGIN_Y, CONTENT_W, PAGE_H - 2 * MARGIN_Y, id="f")
doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=footer)])
doc.multiBuild(story)
print(f"  wrote {OUT.relative_to(C.ROOT)}")
