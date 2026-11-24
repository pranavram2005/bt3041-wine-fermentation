"""
Build the supplementary file: outputs/BT3041_Supplementary.pdf

The submission instructions ask the supplementary file to carry five things:
the link to the code, the AI prompts used, the AI chat history, the
references, and the figures and tables. This script assembles all five.

  S1  Code and data availability   - link, layout, how to reproduce, versions
  S2  AI use                       - declaration, prompt log, chat history
  S3  Methods in full              - the decisions the 8-page report compresses
  S4  Figures                      - all %d, at full width, with captions
  S5  Tables                       - a catalogue of all of them, and the
                                     small ones rendered in full
  S6  References

The code link is read from CODE_LINK.txt and the AI record from AI_USE_LOG.md,
both in the project root, so neither has to be edited inside this script.
"""
import re
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
                                TableStyle, KeepTogether, PageBreak, Flowable)

sys.path.insert(0, str(Path(__file__).parent))
import common as CM

FIG, TAB = CM.FIGURES, CM.TABLES
ROOT = CM.ROOT
OUT = ROOT / "outputs" / "BT3041_Supplementary.pdf"

PAGE_W, PAGE_H = A4
MX, MY = 20 * mm, 18 * mm
CW = PAGE_W - 2 * MX

BLACK = colors.black
GREY = colors.Color(0.34, 0.34, 0.33)
RULE = colors.Color(0.55, 0.55, 0.54)
FAINT = colors.Color(0.84, 0.84, 0.82)
WARN = colors.Color(0.86, 0.38, 0.16)
BODY, BOLD, ITAL, BI = "Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic"
MONO = "Courier"

S = {
    "title": ParagraphStyle("title", fontName=BOLD, fontSize=18, leading=22,
                            textColor=BLACK, spaceAfter=6),
    "subtitle": ParagraphStyle("subtitle", fontName=BODY, fontSize=10.5,
                               leading=14.5, textColor=GREY, spaceAfter=3),
    "h1": ParagraphStyle("h1", fontName=BOLD, fontSize=13, leading=16,
                         textColor=BLACK, spaceBefore=14, spaceAfter=6,
                         keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName=BOLD, fontSize=10.6, leading=13.4,
                         textColor=BLACK, spaceBefore=10, spaceAfter=4,
                         keepWithNext=1),
    "h3": ParagraphStyle("h3", fontName=BI, fontSize=9.8, leading=12.6,
                         textColor=BLACK, spaceBefore=7, spaceAfter=3,
                         keepWithNext=1),
    "body": ParagraphStyle("body", fontName=BODY, fontSize=9.6, leading=13,
                           textColor=BLACK, alignment=TA_JUSTIFY,
                           spaceAfter=5),
    "bullet": ParagraphStyle("bullet", fontName=BODY, fontSize=9.6,
                             leading=12.8, textColor=BLACK,
                             alignment=TA_JUSTIFY, leftIndent=13,
                             bulletIndent=3, spaceAfter=3),
    "quote": ParagraphStyle("quote", fontName=ITAL, fontSize=9.4, leading=12.8,
                            textColor=BLACK, alignment=TA_JUSTIFY,
                            leftIndent=16, rightIndent=12, spaceBefore=3,
                            spaceAfter=7, borderColor=WARN, borderWidth=0,
                            borderPadding=0),
    "code": ParagraphStyle("code", fontName=MONO, fontSize=8.4, leading=11.4,
                           textColor=BLACK, leftIndent=12, spaceAfter=2),
    "caption": ParagraphStyle("caption", fontName=BODY, fontSize=8.6,
                              leading=11.4, textColor=GREY,
                              alignment=TA_JUSTIFY, spaceBefore=4,
                              spaceAfter=12, leftIndent=8, rightIndent=8),
    "tabnote": ParagraphStyle("tabnote", fontName=ITAL, fontSize=8.4,
                              leading=11, textColor=GREY,
                              alignment=TA_JUSTIFY, spaceBefore=2,
                              spaceAfter=11),
    "ref": ParagraphStyle("ref", fontName=BODY, fontSize=8.6, leading=11,
                          textColor=BLACK, alignment=TA_JUSTIFY,
                          leftIndent=12, firstLineIndent=-12, spaceAfter=2.4),
    "toc": ParagraphStyle("toc", fontName=BODY, fontSize=10, leading=15,
                          textColor=BLACK, leftIndent=10),
}

story = []
h1 = lambda t: story.append(Paragraph(t, S["h1"]))
h2 = lambda t: story.append(Paragraph(t, S["h2"]))
h3 = lambda t: story.append(Paragraph(t, S["h3"]))
p = lambda t: story.append(Paragraph(t, S["body"]))
code = lambda t: story.append(Paragraph(t.replace(" ", "&nbsp;"), S["code"]))
gap = lambda h=6: story.append(Spacer(1, h))


def bullets(items):
    for it in items:
        story.append(Paragraph(it, S["bullet"], bulletText="•"))
    story.append(Spacer(1, 4))


class Rule(Flowable):
    def __init__(self, width, weight=0.7, color=RULE, space=8):
        Flowable.__init__(self)
        self.width, self.weight, self.color, self.height = width, weight, color, space

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.weight)
        self.canv.line(0, self.height / 2, self.width, self.height / 2)


class Callout(Flowable):
    """A tinted panel - used once, for the action the group must take."""

    def __init__(self, text, width, style):
        Flowable.__init__(self)
        self.para = Paragraph(text, style)
        self.width = width
        self.pad = 7

    def wrap(self, aw, ah):
        w, h = self.para.wrap(self.width - 2 * self.pad - 4, ah)
        self.height = h + 2 * self.pad
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(colors.Color(0.99, 0.95, 0.90))
        c.setStrokeColor(WARN)
        c.setLineWidth(0.8)
        c.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        c.setFillColor(WARN)
        c.rect(0, 0, 2.2, self.height, fill=1, stroke=0)
        self.para.drawOn(c, self.pad + 4, self.pad)


def table(data, widths=None, size=8.0, note=None, align=None, keep=True,
          head=True):
    styles = {}
    for r in range(len(data)):
        for c in range(len(data[r])):
            styles[(r, c)] = ParagraphStyle(
                "s%d_%d" % (r, c), fontName=(BOLD if (head and r == 0) else BODY),
                fontSize=size, leading=size + 2.6, textColor=BLACK,
                alignment=TA_CENTER if (align and c in align) else 0)
    rows = [[Paragraph(str(c), styles[(r, i)]) for i, c in enumerate(row)]
            for r, row in enumerate(data)]
    t = Table(rows, colWidths=widths, hAlign="LEFT", repeatRows=1 if head else 0)
    t.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.8, BLACK),
        ("LINEBELOW", (0, 0), (-1, 0), 0.4, BLACK),
        ("LINEBELOW", (0, -1), (-1, -1), 0.8, BLACK),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
        ("LEFTPADDING", (1, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2.0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.0),
    ]))
    blk = [t] + ([Spacer(1, 2), Paragraph(note, S["tabnote"])] if note
                 else [Spacer(1, 10)])
    if keep:
        story.append(KeepTogether(blk))
    else:
        for f in blk:
            story.append(f)


def figure(name, caption, maxh=112 * mm):
    path = FIG / name
    if not path.exists():
        p("[missing figure: %s]" % name)
        return
    iw, ih = Image.open(path).size
    w, h = CW, CW * ih / iw
    if h > maxh:
        h, w = maxh, maxh * iw / ih
    img = RLImage(str(path), width=w, height=h)
    img.hAlign = "CENTER"
    story.append(KeepTogether([img, Paragraph(caption, S["caption"])]))


def md_inline(t):
    """The small subset of Markdown the AI-use log uses."""
    t = (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
          .replace("—", "&mdash;").replace("–", "&ndash;"))
    t = re.sub(r"`([^`]+)`", r'<font face="Courier" size="8.6">\1</font>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", t)
    return t


def render_markdown(path, skip_until=None, heading_offset=0):
    """Render a Markdown file into the story, so the AI-use record lives in a
    plain-text file the group can edit without touching this script."""
    lines = path.read_text(encoding="utf-8").split("\n")
    started = skip_until is None
    buf, quote = [], []

    def flush():
        if buf:
            p(md_inline(" ".join(buf)))
            buf.clear()

    def flushq():
        if quote:
            story.append(Callout(md_inline(" ".join(quote)), CW, S["quote"]))
            story.append(Spacer(1, 10))
            quote.clear()

    for ln in lines:
        s = ln.rstrip()
        if not started:
            if skip_until in s:
                started = True
            continue
        if s.strip() in ("---", "***", "___"):
            flush(); flushq()
            continue
        if s.startswith("#"):
            flush(); flushq()
            lvl = len(s) - len(s.lstrip("#")) + heading_offset
            txt = md_inline(s.lstrip("# ").strip())
            story.append(Paragraph(txt, S["h%d" % min(max(lvl, 1), 3)]))
        elif s.startswith("> "):
            flush()
            quote.append(s[2:])
        elif s.startswith("- ") or s.startswith("* "):
            flush(); flushq()
            story.append(Paragraph(md_inline(s[2:]), S["bullet"],
                                   bulletText="•"))
        elif s.startswith("  ") and buf == [] and story and s.strip():
            # continuation of a bullet
            prev = story.pop()
            story.append(Paragraph(prev.text + " " + md_inline(s.strip()),
                                   S["bullet"], bulletText="•"))
        elif not s.strip():
            flush(); flushq()
        else:
            flushq()
            buf.append(s.strip())
    flush(); flushq()


# ======================================================================= DATA
FIG_CAPTIONS = [
 ("fig01_sugar_curves_by_strain.png",
  "Sugar consumption over time for all 216 fermentations, as small multiples: "
  "one panel per strain, one line per temperature regime. Strain identity is "
  "carried by the panel rather than by colour, because nine cycled hues "
  "cannot be told apart reliably."),
 ("fig02_distributions.png",
  "Distributions of the eight principal measured variables across all "
  "sampling points, with the median marked and the skew annotated. The "
  "viable-count panel uses log-spaced bins because the variable spans four "
  "orders of magnitude."),
 ("fig03_endpoint_by_strain.png",
  "Endpoint and kinetic outcomes by strain, pooled over regimes: box plots "
  "with the individual fermentations overlaid. Pooled views such as this one "
  "hide the interaction and are shown here only as a first look."),
 ("fig04_strain_x_temperature.png",
  "The same outcomes with each temperature regime in its own panel, sorted "
  "independently. The re-ordering between panels is the interaction, seen "
  "directly."),
 ("fig05_growth_viability.png",
  "Yeast population and viability over the time course, by temperature "
  "regime. Peak viable count is the one outcome for which strain is the "
  "largest single variance term."),
 ("fig06_correlation_heatmap.png",
  "Spearman correlation structure of 20 variables over all pooled samples. "
  "Most of the structure reflects fermentation stage - everything moves "
  "together as sugar is consumed - and should not be read as metabolic "
  "coupling between strains."),
 ("fig07_rank_bump.png",
  "Rank of each strain by time to 90 % sugar consumption, across the four "
  "regimes. All strains are greyed except the three that move most. No line "
  "stays flat across all four regimes."),
 ("fig08_variance_decomposition.png",
  "Share of variance attributable to each design factor, per unit-level "
  "outcome. Descriptive, computed before any test was selected, and the "
  "basis on which the six test outcomes were chosen."),
 ("fig09_anova_partial_eta2.png",
  "Partial eta-squared for each term of the two-way model, by outcome. The "
  "strain x temperature interaction term is non-zero for every outcome."),
 ("fig10_maxviable_by_strain_regime.png",
  "Peak viable population by strain within each temperature regime, with "
  "95 % confidence intervals. The spread between strains is widest at "
  "12 degC and narrowest at 25 degC."),
 ("fig11_succinate_by_strain_regime.png",
  "Final succinate by strain within each regime, with 95 % confidence "
  "intervals. Succinate carries one of the largest strain terms in the "
  "dataset."),
 ("fig12_pca_scree.png",
  "Scree plot and cumulative explained variance for the PCA on 15 "
  "standardised unit-level features. Four components have eigenvalue above "
  "1 and together carry 81.8 % of the variance."),
 ("fig13_pca_scatter.png",
  "The fermentations in the PC1-PC2 plane, coloured by temperature regime "
  "and by strain. Temperature shows ordered structure; strain does not."),
 ("fig14_pca_biplot.png",
  "Biplot of PC1 against PC2 with the feature loadings overlaid, which names "
  "the axes: PC1 is must loading, PC2 is fermentation vigour."),
 ("fig15_dendrogram.png",
  "Ward dendrogram of the 215 fermentations with a complete feature vector. "
  "The cut at k = 5 is the one selected by silhouette width."),
 ("fig16_clusters_vs_design.png",
  "The five Ward clusters cross-tabulated against strain, temperature and "
  "initial sugar. The clusters align with the conditions imposed, not with "
  "the yeast used."),
 ("fig17_silhouette_k.png",
  "Silhouette width against k for Ward and k-means, with the adjusted Rand "
  "index between the two methods at each k. k = 5 is the maximum for Ward "
  "and the two methods agree closely there."),
 ("fig18_fermentation_overview.png",
  "Schematic of the experimental design and the analysis pipeline, from the "
  "source workbook through the unit-level table to the four analyses."),
 ("fig19_strain_robustness.png",
  "Consistency of each strain across the four temperature regimes: the span "
  "between best and worst rank, and mean rank against the standard deviation "
  "of the within-regime standardised time to 90 %."),
 ("fig20_permutation_vs_parametric.png",
  "The validated permutation test against the originally reported p-values. "
  "Every disagreement falls among the cells whose step-5 test did not adjust "
  "for must sugar."),
 ("fig21_validation_sensitivity.png",
  "How many of four independent analyses call the strain effect significant, "
  "cell by cell: restricted permutation test, parametric ANOVA, "
  "leave-one-replicate-out, and the re-test with flagged units removed."),
]

TABLE_DESC = {
 "01_data_dictionary": "All 55 variables: block, unit, type, missing count and description.",
 "01_design_balance": "Fermentations per strain x temperature x initial sugar - the balance check.",
 "01_flagged_nonmonotonic_sugar": "The 74 samples where residual sugar rises over time; flagged, not deleted.",
 "01_missingness_by_block": "Incomplete rows and affected sampling points, per measurement block.",
 "01_nominal_vs_measured_sugar": "Nominal MS label against measured t0 sugar, by temperature batch.",
 "01_sampling_times": "Mean elapsed clock time at each nominal sampling point, per regime.",
 "02_descriptives_all_timepoints": "n, mean, median, SD, min, max and CV for every numeric variable.",
 "02_endpoint_by_strain": "Final-sample means and standard deviations per strain.",
 "02_kinetics_by_strain": "Kinetic summary per strain, pooled over regimes.",
 "02_kinetics_by_temperature": "Kinetic summary per temperature regime.",
 "02_spearman_correlations": "Full Spearman correlation matrix over the pooled samples.",
 "02_strain_rank_by_temperature": "Rank of each strain by mean time to 90 %, within each regime.",
 "02_unit_level_features": "THE ANALYSIS TABLE: one row per fermentation, 21 derived features.",
 "03_variance_decomposition": "Share of variance per factor, per outcome; descriptive, no p-values.",
 "05_assumption_checks": "Shapiro-Wilk and Levene results on model residuals, raw and transformed.",
 "05_dunn_posthoc": "Dunn's rank-based pairwise comparisons, all outcome x regime cells.",
 "05_group_means_ci": "Strain means with 95 % confidence intervals, per outcome and regime.",
 "05_results_table": "The step-5 results table: every test statistic for every cell.",
 "05_tukey_posthoc": "Tukey HSD pairwise comparisons, all outcome x regime cells.",
 "05_twoway_anova": "Two-way ANOVA, strain x temperature + MS, type II sums of squares.",
 "05_within_regime_strain_tests": "Within-regime strain tests as originally reported in step 5.",
 "06_explained_variance": "Eigenvalues and explained variance per principal component.",
 "06_label_separation": "Silhouette width in PC space by strain, temperature and initial sugar.",
 "06_loadings": "Feature loadings on PC1-PC5.",
 "06_pc_scores": "Principal component scores for every fermentation.",
 "07_cluster_assignments": "Ward and k-means cluster membership per fermentation.",
 "07_cluster_label_agreement": "Adjusted Rand index between clusters and each design factor.",
 "07_cluster_profiles": "Mean of every feature within each cluster, and the spread across clusters.",
 "07_crosstab_ward_x_ms": "Clusters against initial sugar.",
 "07_crosstab_ward_x_strain": "Clusters against strain.",
 "07_crosstab_ward_x_temperature": "Clusters against temperature regime.",
 "07_k_selection": "Silhouette and inertia against k, with Ward vs k-means agreement.",
 "07_stability_resampling": "Adjusted Rand index against the full solution, over 100 resamples.",
 "10_artefact_sensitivity": "V6: every test re-run with the flagged fermentations removed.",
 "10_bootstrap_effectsize": "V7: partial eta-squared with noncentral-F interval, and the bootstrap gap interval.",
 "10_claim_checks": "V10: every quantitative claim in the report, recomputed and checked.",
 "10_loro_sensitivity": "V5: leave-one-replicate-out, three two-replicate subsets per cell.",
 "10_mixedmodel_check": "V4: mixed-effects cross-check on the raw repeated measures.",
 "10_multivariate_check": "V9: PCA and clustering summary statistics, recomputed from scratch.",
 "10_permutation_tests": "V2: restricted permutation test, 5000 shuffles per cell, three statistics.",
 "10_pseudoreplication": "V3: the same comparisons run on the raw rows, as a counter-example.",
 "10_recompute_check": "V1: a second implementation of every unit-level feature.",
 "10_sensitivity_grid": "How many of the four analyses call each cell significant.",
 "10_strain_robustness": "V8: cross-regime consistency of each strain.",
 "10_validated_results": "THE RESULTS TABLE of the main report, as validated in step 8.",
}

RENDER_IN_FULL = [
 ("10_validated_results", "The validated results table reproduced in the main "
  "report as Table 4, with every column the build retains."),
 ("10_claim_checks", "Every quantitative claim in the main report, recomputed "
  "from the data by a second route."),
 ("10_recompute_check", "Each unit-level feature against a second, "
  "independent implementation."),
 ("10_pseudoreplication", "The same comparison treated correctly and "
  "incorrectly: 216 experimental units against 1944 correlated samples."),
 ("10_loro_sensitivity", "Leave-one-replicate-out."),
 ("10_artefact_sensitivity", "Re-test with the flagged fermentations removed."),
 ("10_strain_robustness", "Cross-regime robustness of each strain."),
 ("10_multivariate_check", "PCA and clustering numbers, recomputed."),
 ("10_mixedmodel_check", "Mixed-effects cross-check."),
 ("05_twoway_anova", "The two-way model with the interaction term."),
 ("05_assumption_checks", "Assumption checks on the residuals."),
 ("03_variance_decomposition", "Descriptive variance decomposition."),
 ("06_explained_variance", "PCA explained variance."),
 ("06_loadings", "PCA loadings on the first five components."),
 ("06_label_separation", "Silhouette by design factor in PC space."),
 ("07_k_selection", "Choice of k."),
 ("07_cluster_label_agreement", "Clusters against the design factors."),
 ("07_cluster_profiles", "Cluster profiles."),
 ("07_crosstab_ward_x_strain", "Clusters against strain."),
 ("07_crosstab_ward_x_temperature", "Clusters against temperature."),
 ("07_crosstab_ward_x_ms", "Clusters against initial sugar."),
 ("02_kinetics_by_strain", "Kinetics by strain."),
 ("02_kinetics_by_temperature", "Kinetics by temperature regime."),
 ("02_strain_rank_by_temperature", "Strain ranks within each regime."),
 ("01_design_balance", "Design balance."),
 ("01_sampling_times", "Mean elapsed time at each sampling point."),
 ("01_nominal_vs_measured_sugar", "Nominal against measured initial sugar."),
 ("01_missingness_by_block", "Missingness by measurement block."),
]

CODE_LINK_FILE = ROOT / "CODE_LINK.txt"
link_raw = (CODE_LINK_FILE.read_text(encoding="utf-8").strip()
            if CODE_LINK_FILE.exists() else "")
LINK_SET = link_raw.lower().startswith(("http://", "https://"))

# ================================================================ TITLE PAGE
story.append(Spacer(1, 32 * mm))
story.append(Paragraph("Supplementary File", S["title"]))
story.append(Paragraph("Comparative Statistical Analysis of Commercial Yeast "
                       "Strains During Wine Fermentation", S["subtitle"]))
story.append(Spacer(1, 5 * mm))
story.append(Rule(CW * 0.3, 0.9, BLACK, 10))
story.append(Spacer(1, 5 * mm))
story.append(Paragraph(
    "BT3041 &mdash; Analysis and Interpretation of Biological Data", S["subtitle"]))
story.append(Paragraph(
    "<b>Team 20</b> &mdash; K James Bond &middot; Avala Madhavi &middot; "
    "Dinesh Kumar &middot; Mohesh &middot; Pranav Ram", S["subtitle"]))
story.append(Paragraph("Teaching Assistant: Kaviya D &nbsp;&middot;&nbsp; "
                       "24 November 2026", S["subtitle"]))
story.append(Spacer(1, 10 * mm))
story.append(Paragraph(
    "This file accompanies the 8-page main report submitted through Turnitin. "
    "It carries the five items the submission instructions ask for: the link "
    "to the code, the AI prompts used during the project, the AI chat "
    "history, the references, and the complete set of figures and tables.",
    S["body"]))
gap(8)
table([["S1", "Code and data availability", "the repository, how to reproduce it, package versions"],
       ["S2", "AI use", "declaration, prompt log, chat history"],
       ["S3", "Methods in full", "the decisions the 8-page report had to compress"],
       ["S4", "Figures", "all %d, full width, with captions" % len(FIG_CAPTIONS)],
       ["S5", "Tables", "catalogue of all %d, and %d rendered in full"
        % (len(TABLE_DESC), len(RENDER_IN_FULL))],
       ["S6", "References", "every work cited, and the software used"]],
      widths=[10 * mm, 48 * mm, CW - 58 * mm], size=9.2, head=False)
story.append(PageBreak())

# =========================================================== S1 CODE AND DATA
h1("S1 &nbsp; Code and data availability")
h2("S1.1 Link to the code")
if LINK_SET:
    p("The complete analysis code, together with every figure and table it "
      "produces, is available at:")
    story.append(Paragraph("<b>%s</b>" % link_raw, S["code"]))
    gap(6)
else:
    story.append(Callout(
        "<b>Action required before submission.</b> &nbsp;Upload the "
        "<i>analysis/</i> folder and the <i>outputs/</i> folder to GitHub or "
        "Google Drive, make sure the link is readable by the course staff, "
        "and put that link on the first line of <b>CODE_LINK.txt</b> in the "
        "project root. Then re-run <font face=\"Courier\" size=\"8.6\">python "
        "analysis/12_make_supplementary.py</font> and this panel will be "
        "replaced by the link.", CW, S["quote"]))
    gap(10)
p("The repository carries the analysis code, the source workbook, the "
  "complete output set and the AI-use record, so the whole project can be "
  "inspected or re-run without downloading anything else. The dataset is "
  "Minebois &amp; Querol (2025), <i>Fermentation data set obtained from "
  "commercial wine strains in synthetic grape must</i>, Zenodo, "
  "doi:10.5281/zenodo.15260916, released under CC BY 4.0 and redistributed "
  "there under that licence with attribution; the file is "
  "<i>Complete_DataSet.xlsx</i> exactly as downloaded, and no script writes "
  "to it. The repository README presents the main pipeline scripts first, "
  "then the supporting ones, then everything else.")

h2("S1.2 What is in the repository")
rows = [["Path", "What it is"],
        ["analysis/common.py", "loader, the five cleaning decisions, variable groups, plot theme"],
        ["analysis/01_inspect.py", "workbook structure, data dictionary, data-quality checks"],
        ["analysis/02_eda.py", "descriptive statistics, figures 1-7, and the unit-level table"],
        ["analysis/03_variance_scan.py", "descriptive variance decomposition, figure 8"],
        ["analysis/make_schematic.py", "the design-and-pipeline schematic, figure 18"],
        ["analysis/05_hypothesis_tests.py", "assumptions, two-way ANOVA, within-regime tests, post-hoc, figures 9-11"],
        ["analysis/06_pca.py", "PCA, loadings, label separation, figures 12-14"],
        ["analysis/07_clustering.py", "Ward and k-means, cross-tabs, stability, figures 15-17"],
        ["analysis/10_validate.py", "the ten validation checks of step 8, figures 19-21"],
        ["analysis/11_make_final_report.py", "builds the 8-page main report"],
        ["analysis/12_make_supplementary.py", "builds this file"],
        ["analysis/13_export_ai_history.py", "exports the prompt log and chat history from the session transcripts"],
        ["analysis/README.md", "how to run the pipeline, and the decisions behind it"],
        ["README.md", "the repository front page: main codes, then supporting scripts, then everything else"],
        ["Complete_DataSet.xlsx", "the source workbook, unmodified"],
        ["outputs/figures/*.png", "every figure (%d files)" % len(FIG_CAPTIONS)],
        ["outputs/tables/*.csv", "every result table (%d files)" % len(TABLE_DESC)],
        ["outputs/*.pdf, *.pptx", "the main report, this file, and the earlier stage reports and slides"],
        ["ANALYSIS_LOG.md", "the working log kept through the project"],
        ["AI_USE_LOG.md", "the AI-use declaration, rendered as section S2 of this file"],
        ["ai_prompts.md, ai_chat_history.md", "all 24 prompts and the full conversation record"]]
table(rows, widths=[52 * mm, CW - 52 * mm], size=8.4, keep=False,
      note="Scripts 04, 08 and 09 build the earlier EDA report, the progress "
           "report and the progress presentation; they are in the repository "
           "but are not part of the final submission. Course lecture slides "
           "and past question papers are not in the repository: they are not "
           "ours to redistribute.")

h2("S1.3 Reproducing the analysis")
p("Every figure, table and PDF in this submission is regenerated from the "
  "source workbook by running the scripts in order. There are no manual "
  "steps, and no intermediate file is edited by hand.")
for c in ["pip install pandas numpy scipy statsmodels scikit-learn \\",
          "            matplotlib openpyxl reportlab pillow pypdf",
          "",
          "python analysis/01_inspect.py",
          "python analysis/02_eda.py",
          "python analysis/03_variance_scan.py",
          "python analysis/make_schematic.py",
          "python analysis/05_hypothesis_tests.py",
          "python analysis/06_pca.py",
          "python analysis/07_clustering.py",
          "python analysis/10_validate.py",
          "python analysis/11_make_final_report.py",
          "python analysis/13_export_ai_history.py",
          "python analysis/12_make_supplementary.py"]:
    code(c)
gap(6)
p("Two details make the results reproducible rather than merely repeatable. "
  "The resampling in <i>10_validate.py</i> is seeded "
  "(<font face=\"Courier\" size=\"8.6\">default_rng(20261124)</font>), so the "
  "permutation and bootstrap figures come out identical on a re-run. And "
  "<i>11_make_final_report.py</i> reads every number it prints from the CSV "
  "files rather than holding any literal of its own, so the report cannot "
  "drift away from the analysis; it also asserts its own page count and "
  "fails the build if the report exceeds eight pages.")

h2("S1.4 Environment")
import platform
import scipy
import matplotlib
import statsmodels
import sklearn
vers = [["Python", platform.python_version()], ["pandas", pd.__version__],
        ["numpy", np.__version__], ["scipy", scipy.__version__],
        ["statsmodels", statsmodels.__version__],
        ["scikit-learn", sklearn.__version__],
        ["matplotlib", matplotlib.__version__]]
table([["Package", "Version", "Package", "Version"]] +
      [[vers[i][0], vers[i][1]] + (vers[i + 4] if i + 4 < len(vers) else ["", ""])
       for i in range(4)],
      widths=[CW / 4] * 4, size=8.6, align=[1, 3],
      note="Versions used for the build that produced this submission.")
story.append(PageBreak())

# ======================================================================= S2 AI
h1("S2 &nbsp; AI use: declaration, prompts and chat history")
p("The course guidelines permit AI assistance with code, debugging and "
  "understanding statistical methods, require that it be disclosed, and "
  "prohibit it from formulating the aims and hypotheses or writing the "
  "interpretation and conclusions. What follows is the full record, "
  "reproduced from <i>AI_USE_LOG.md</i> in the repository.")
render_markdown(ROOT / "AI_USE_LOG.md", skip_until="## Declaration",
                heading_offset=1)

# The prompts are rendered from the file the exporter writes, never retyped,
# so what appears here is what was typed.
PROMPTS = ROOT / "ai_prompts.md"
if PROMPTS.exists():
    h2("S2.1 &nbsp; The prompts, verbatim")
    p("Exported from the session transcripts by "
      "<i>13_export_ai_history.py</i>. Typos are reproduced as typed.")
    render_markdown(PROMPTS, skip_until="## Session 1", heading_offset=1)
else:
    story.append(Callout(
        "<b>Action required.</b> &nbsp;Run <font face=\"Courier\" "
        "size=\"8.6\">python analysis/13_export_ai_history.py</font> to "
        "export the prompt log, then rebuild this file.", CW, S["quote"]))
    gap(10)

h2("S2.2 &nbsp; Chat history")
chat = None
for cand in ["ai_chat_history.md", "ai_chat_history.pdf", "ai_chat_history.txt"]:
    if (ROOT / cand).exists():
        chat = cand
if chat:
    p("The full conversation &mdash; every prompt, every reply, and the tools "
      "used at each turn &mdash; is submitted with this file as <b>%s</b> "
      "(%.0f kB), exported from the Claude Code session transcripts. Tool "
      "arguments and outputs are summarised rather than reproduced: the raw "
      "transcripts total about 36 MB, almost all of it file contents and "
      "command output, which is the code and the data rather than the "
      "conversation."
      % (chat, (ROOT / chat).stat().st_size / 1024))
else:
    story.append(Callout(
        "<b>Action required.</b> &nbsp;Run <font face=\"Courier\" "
        "size=\"8.6\">python analysis/13_export_ai_history.py</font> to "
        "export the chat history, then rebuild this file and upload the "
        "exported file to Moodle alongside it.", CW, S["quote"]))
    gap(10)
story.append(PageBreak())

# ================================================================== S3 METHODS
h1("S3 &nbsp; Methods in full")
h2("S3.1 The five cleaning decisions")
p("These are documented in the docstring of "
  "<font face=\"Courier\" size=\"8.6\">common.load()</font> so that they "
  "travel with the code rather than only with the report.")
bullets([
 "<b>1. The source workbook is read-only.</b> Every script re-reads it and "
 "all cleaning happens in memory; nothing is written back.",
 "<b>2. Temperature is an ordered categorical, not a number.</b> TVAR is a "
 "time-varying regime and has no single numeric value, so treating "
 "temperature as continuous would force a meaningless value on it.",
 "<b>3. The six t5bis rows are dropped.</b> They are off-schedule samples "
 "taken only for TXL and VIN13 at 18 degC / 250 g/L; keeping them would "
 "unbalance the design. They are reported separately.",
 "<b>4. Missing values are not imputed.</b> The gaps are whole assay blocks "
 "that were never run, not values lost at random, so each analysis uses only "
 "the sampling points at which its variables exist.",
 "<b>5. Sugar consumption is baselined on each unit's own measured t0.</b> "
 "The nominal MS label is a target, not a measurement: using it as the "
 "baseline produces 173 impossible negative values.",
])
h2("S3.2 How the test for each cell was chosen")
p("The branch was decided from the assumption checks, before any p-value was "
  "looked at: normal residuals with equal variances went to classical ANOVA; "
  "normal residuals with unequal variances to Welch's ANOVA; non-normal "
  "residuals to Kruskal-Wallis. Levene's test failed in %d of the 24 cells "
  "and Shapiro-Wilk in %d, which is why so many cells left the ANOVA branch."
  % (int((pd.read_csv(TAB / "05_within_regime_strain_tests.csv",
                      index_col=0)["levene_p"] <= 0.05).sum()),
     int((pd.read_csv(TAB / "05_within_regime_strain_tests.csv",
                      index_col=0)["shapiro_p"] <= 0.05).sum())))
p("Step 8 found the flaw this created. The ANOVA branch fits "
  "<i>y</i> ~ strain + MS and so holds the must-sugar factor out of the error "
  "term; the Welch and Kruskal-Wallis branches compared raw strain groups and "
  "left it in. For outcomes where must sugar is a large variance component "
  "that costs most of the power of the test. The validated analysis in the "
  "main report replaces all three branches with a restricted permutation "
  "test: strain labels are shuffled only within must-sugar blocks, 5000 "
  "times, and the statistic permuted is the one that cell's assumption checks "
  "call for. That keeps the design inside the null hypothesis, makes no "
  "distributional assumption, and recovers the lost power.")
h2("S3.3 Multiple comparisons")
p("The family corrected over is the 24 within-regime tests, by the "
  "Benjamini-Hochberg procedure at a false-discovery rate of 5 %. The two-way "
  "terms are corrected as their own family. Post-hoc pairwise comparisons "
  "carry their own correction internal to the method - Tukey HSD controls the "
  "family-wise rate across the 36 pairs within a cell, and Dunn's test is "
  "reported with Holm adjustment. The six outcomes were themselves selected "
  "from twelve on the strength of the variance scan, which is a selection "
  "step the correction does not cover; it is declared in the main report "
  "rather than adjusted for.")
story.append(PageBreak())

# ================================================================== S4 FIGURES
h1("S4 &nbsp; Figures")
p("All %d figures produced by the analysis, in the order they are generated. "
  "Figures 1-8 are exploratory, 9-11 accompany the hypothesis tests, 12-17 "
  "the multivariate analyses, 18 is the design schematic, and 19-21 the "
  "step-8 validation. Four of these appear in the main report; the rest are "
  "here." % len(FIG_CAPTIONS))
for i, (name, cap) in enumerate(FIG_CAPTIONS, start=1):
    figure(name, "<b>Figure S%d.</b> %s &nbsp;<font size='7.6'>(%s)</font>"
           % (i, cap, name))
story.append(PageBreak())

# =================================================================== S5 TABLES
h1("S5 &nbsp; Tables")
h2("S5.1 Catalogue")
p("Every table the analysis writes, with its shape. All are CSV files in "
  "<i>outputs/tables/</i> in the repository; the ones small enough to read on "
  "a page are reproduced in full in S5.2.")
rows = [["File", "Rows &times; cols", "Contents"]]
for f in sorted(TAB.glob("*.csv")):
    key = f.stem
    try:
        d = pd.read_csv(f)
        shape = "%d &times; %d" % (len(d), d.shape[1])
    except Exception:
        shape = "&mdash;"
    rows.append([f.name, shape, TABLE_DESC.get(key, "")])
table(rows, widths=[46 * mm, 18 * mm, CW - 64 * mm], size=7.6, keep=False,
      align=[1],
      note="%d tables. The two marked in capitals are the ones everything "
           "else depends on: the 216-row analysis table, and the validated "
           "results table." % (len(rows) - 1))

def _render_block(d, key, note, suffix, part=None):
    def cell(v):
        if pd.isna(v):
            return ""
        if isinstance(v, float):
            if v == 0:
                return "0"
            if abs(v) < 1e-3:
                return "%.1e" % v
            return ("%.4f" % v).rstrip("0").rstrip(".")
        return str(v)

    hdr = [str(c).replace("_", " ") for c in d.columns]
    body = [[cell(v) for v in r] for r in d.itertuples(index=False)]
    ncol = len(hdr)
    size = 7.4 if ncol <= 9 else 6.4

    # Columns are sized to their content, and never narrower than the longest
    # unbreakable word in them, so values such as "log10" or "significant" are
    # not split down the middle.
    charw = 0.52 * size
    want = [min(max([len(h)] + [len(r[i]) for r in body]), 26) + 2
            for i, h in enumerate(hdr)]
    longest = [max([len(w) for w in h.split()] +
                   [len(w) for r in body for w in r[i].split()] + [1])
               for i, h in enumerate(hdr)]
    need = [lw * charw + 9 for lw in longest]
    if sum(need) <= CW:
        spare = CW - sum(need)
        total = sum(want)
        widths = [n + spare * w / total for n, w in zip(need, want)]
    else:
        widths = [n * CW / sum(need) for n in need]

    title = note or "continued"
    h3("%s &mdash; <font face='Courier' size='8'>%s.csv</font>%s"
       % (title, key, suffix))
    table([hdr] + body, widths=widths, size=size, keep=False,
          align=list(range(1, ncol)))


def render_csv(key, note):
    """Render one result table in full, splitting a very wide one into stacked
    blocks that share its first two identifying columns rather than squeezing
    seventeen columns into the width of a portrait page."""
    f = TAB / (key + ".csv")
    if not f.exists():
        return
    d = pd.read_csv(f)
    if d.columns[0].startswith("Unnamed"):
        d = d.drop(columns=d.columns[0])
    if d.shape[1] <= 11:
        _render_block(d, key, note, "")
        return
    idc, rest = list(d.columns[:2]), list(d.columns[2:])
    half = (len(rest) + 1) // 2
    for n, cols in enumerate([rest[:half], rest[half:]], start=1):
        lo = 3 if n == 1 else 3 + half
        hi = 2 + (half if n == 1 else len(rest))
        _render_block(d[idc + cols], key, note if n == 1 else "",
                      ", columns %d&ndash;%d of %d" % (lo, hi, d.shape[1]),
                      part=n)


h2("S5.2 The tables in full")
p("Wide tables are split into stacked blocks that repeat their first two "
  "identifying columns. Values below 0.001 are shown in scientific notation; "
  "the CSV files carry full precision.")
for key, note in RENDER_IN_FULL:
    render_csv(key, note)

story.append(PageBreak())

# =============================================================== S6 REFERENCES
h1("S6 &nbsp; References")
REFS_DATA = [
 "Minebois, R. &amp; Querol, A. (2025) <i>Fermentation data set obtained from "
 "commercial wine strains in synthetic grape must.</i> Zenodo. "
 "doi:10.5281/zenodo.15260916. Licensed CC BY 4.0.",
]
REFS_BIO = [
 "Beltran, G., Novo, M., Guillam&oacute;n, J. M., Mas, A. &amp; Roz&egrave;s, "
 "N. (2008) Effect of fermentation temperature and culture media on the yeast "
 "lipid composition and wine volatile compounds. <i>International Journal of "
 "Food Microbiology</i> 121, 169&ndash;177.",
 "Bisson, L. F. (1999) Stuck and sluggish fermentations. <i>American Journal "
 "of Enology and Viticulture</i> 50, 107&ndash;119.",
 "Camarasa, C., Grivet, J.-P. &amp; Dequin, S. (2003) Investigation by "
 "<super>13</super>C-NMR and tricarboxylic acid deletion mutant analysis of "
 "pathways for succinate formation in <i>Saccharomyces cerevisiae</i> during "
 "anaerobic fermentation. <i>Microbiology</i> 149, 2669&ndash;2678.",
 "Erasmus, D. J., van der Merwe, G. K. &amp; van Vuuren, H. J. J. (2003) "
 "Genome-wide expression analyses: metabolic adaptation of <i>Saccharomyces "
 "cerevisiae</i> to high sugar stress. <i>FEMS Yeast Research</i> 3, "
 "375&ndash;399.",
 "Redzepovic, S., Orlic, S., Majdak, A., Kozina, B., Volschenk, H. &amp; "
 "Viljoen-Bloom, M. (2003) Differential malic acid degradation by selected "
 "strains of <i>Saccharomyces</i> during alcoholic fermentation. "
 "<i>International Journal of Food Microbiology</i> 83, 49&ndash;61.",
 "Remize, F., Roustan, J. L., Sablayrolles, J. M., Barre, P. &amp; Dequin, S. "
 "(1999) Glycerol overproduction by engineered <i>Saccharomyces cerevisiae</i> "
 "wine yeast strains leads to substantial changes in by-product formation and "
 "to a stimulation of fermentation rate in stationary phase. <i>Applied and "
 "Environmental Microbiology</i> 65, 143&ndash;149.",
 "Ribéreau-Gayon, P., Dubourdieu, D., Don&egrave;che, B. &amp; Lonvaud, A. "
 "(2006) <i>Handbook of Enology, Volume 1: The Microbiology of Wine and "
 "Vinifications</i>, 2nd edn. Chichester: Wiley.",
 "Torija, M. J., Roz&egrave;s, N., Poblet, M., Guillam&oacute;n, J. M. &amp; "
 "Mas, A. (2003) Effects of fermentation temperature on the strain population "
 "of <i>Saccharomyces cerevisiae</i>. <i>International Journal of Food "
 "Microbiology</i> 80, 47&ndash;53.",
]
REFS_STAT = [
 "Benjamini, Y. &amp; Hochberg, Y. (1995) Controlling the false discovery "
 "rate: a practical and powerful approach to multiple testing. <i>Journal of "
 "the Royal Statistical Society B</i> 57, 289&ndash;300.",
 "Dunn, O. J. (1964) Multiple comparisons using rank sums. "
 "<i>Technometrics</i> 6, 241&ndash;252.",
 "Hubert, L. &amp; Arabie, P. (1985) Comparing partitions. <i>Journal of "
 "Classification</i> 2, 193&ndash;218.",
 "Hurlbert, S. H. (1984) Pseudoreplication and the design of ecological field "
 "experiments. <i>Ecological Monographs</i> 54, 187&ndash;211.",
 "Jolliffe, I. T. &amp; Cadima, J. (2016) Principal component analysis: a "
 "review and recent developments. <i>Philosophical Transactions of the Royal "
 "Society A</i> 374, 20150202.",
 "Kruskal, W. H. &amp; Wallis, W. A. (1952) Use of ranks in one-criterion "
 "variance analysis. <i>Journal of the American Statistical Association</i> "
 "47, 583&ndash;621.",
 "Levene, H. (1960) Robust tests for equality of variances. In "
 "<i>Contributions to Probability and Statistics</i>, 278&ndash;292. "
 "Stanford University Press.",
 "Rousseeuw, P. J. (1987) Silhouettes: a graphical aid to the interpretation "
 "and validation of cluster analysis. <i>Journal of Computational and Applied "
 "Mathematics</i> 20, 53&ndash;65.",
 "Shapiro, S. S. &amp; Wilk, M. B. (1965) An analysis of variance test for "
 "normality (complete samples). <i>Biometrika</i> 52, 591&ndash;611.",
 "Steiger, J. H. (2004) Beyond the F test: effect size confidence intervals "
 "and tests of close fit in the analysis of variance. <i>Psychological "
 "Methods</i> 9, 164&ndash;182.",
 "Tukey, J. W. (1949) Comparing individual means in the analysis of variance. "
 "<i>Biometrics</i> 5, 99&ndash;114.",
 "Ward, J. H. (1963) Hierarchical grouping to optimize an objective function. "
 "<i>Journal of the American Statistical Association</i> 58, 236&ndash;244.",
 "Welch, B. L. (1951) On the comparison of several mean values: an "
 "alternative approach. <i>Biometrika</i> 38, 330&ndash;336.",
]
REFS_SW = [
 "Harris, C. R. <i>et al.</i> (2020) Array programming with NumPy. "
 "<i>Nature</i> 585, 357&ndash;362.",
 "Hunter, J. D. (2007) Matplotlib: a 2D graphics environment. "
 "<i>Computing in Science &amp; Engineering</i> 9, 90&ndash;95.",
 "McKinney, W. (2010) Data structures for statistical computing in Python. "
 "<i>Proceedings of the 9th Python in Science Conference</i>, 56&ndash;61.",
 "Pedregosa, F. <i>et al.</i> (2011) Scikit-learn: machine learning in "
 "Python. <i>Journal of Machine Learning Research</i> 12, 2825&ndash;2830.",
 "Seabold, S. &amp; Perktold, J. (2010) statsmodels: econometric and "
 "statistical modeling with Python. <i>Proceedings of the 9th Python in "
 "Science Conference</i>, 92&ndash;96.",
 "Virtanen, P. <i>et al.</i> (2020) SciPy 1.0: fundamental algorithms for "
 "scientific computing in Python. <i>Nature Methods</i> 17, 261&ndash;272.",
]

for title, refs in [("S6.1 Dataset", REFS_DATA),
                    ("S6.2 Subject literature", REFS_BIO),
                    ("S6.3 Statistical methods", REFS_STAT),
                    ("S6.4 Software", REFS_SW)]:
    h2(title)
    for r in refs:
        story.append(Paragraph(r, S["ref"]))

# ===================================================================== BUILD
def decorate(canvas, doc):
    canvas.saveState()
    canvas.setFont(BODY, 7.8)
    canvas.setFillColor(GREY)
    canvas.drawString(MX, MY - 9, "BT3041 Term Project · Team 20 · "
                                  "Supplementary file")
    canvas.drawRightString(PAGE_W - MX, MY - 9, "S%d" % doc.page)
    canvas.setStrokeColor(FAINT)
    canvas.setLineWidth(0.4)
    canvas.line(MX, MY - 4, PAGE_W - MX, MY - 4)
    canvas.restoreState()


doc = BaseDocTemplate(str(OUT), pagesize=A4, leftMargin=MX, rightMargin=MX,
                      topMargin=MY, bottomMargin=MY,
                      title="Supplementary file - BT3041 term project, Team 20",
                      author="BT3041 Team 20")
doc.addPageTemplates([PageTemplate(
    id="main",
    frames=[Frame(MX, MY, CW, PAGE_H - 2 * MY, id="f", leftPadding=0,
                  rightPadding=0, topPadding=0, bottomPadding=0)],
    onPage=decorate)])
doc.build(story)

pages = len(PdfReader(str(OUT)).pages)
print("wrote %s  (%d pages)" % (OUT.relative_to(ROOT), pages))
if not LINK_SET:
    print("NOTE: CODE_LINK.txt does not yet contain a URL, so the "
          "supplementary carries a visible 'action required' panel in its "
          "place. Add the link and re-run this script before submitting.")
