# Comparative Statistical Analysis of Commercial Yeast Strains During Wine Fermentation

BT3041 — Analysis and Interpretation of Biological Data · Team 20

**All code files are in [`analysis/`](analysis).**

Nine commercial *Saccharomyces cerevisiae* wine strains compared across **216
fermentations** of synthetic grape must, laid out as a balanced factorial of
9 strains × 4 temperature regimes × 2 initial sugar levels × 3 biological
replicates, each sampled at nine time points.

**Headline result.** Strains differ, but conditionally. A strain effect is
detectable in 22 of 24 outcome × regime comparisons after adjustment for must
sugar and for multiple comparisons, yet the strain × temperature interaction
is significant for every outcome tested, so the ranking does not transfer
between regimes (Spearman 0.30–0.83). No strain is fastest everywhere: W12 is
in the fastest three in all four regimes, while VIN13 moves across seven rank
positions. Strain is also the smallest of the three levers — temperature
governs the kinetics and initial sugar governs the endpoint chemistry.

---

## The main codes

The analysis pipeline, in the order it runs. These nine scripts produce every
number in the report.

| # | Script | What it does |
|---|---|---|
| — | [`analysis/common.py`](analysis/common.py) | Loader, the five cleaning decisions, variable groups, plot theme. Everything imports this. |
| 01 | [`analysis/01_inspect.py`](analysis/01_inspect.py) | Workbook structure, the 55-variable data dictionary, data-quality checks |
| 02 | [`analysis/02_eda.py`](analysis/02_eda.py) | Descriptive statistics, figures 1–7, and **the 216-row unit-level table** |
| 03 | [`analysis/03_variance_scan.py`](analysis/03_variance_scan.py) | Where the signal is — effect sizes deliberately without p-values |
| 05 | [`analysis/05_hypothesis_tests.py`](analysis/05_hypothesis_tests.py) | Assumption checks, two-way ANOVA with interaction, within-regime strain tests, Tukey and Dunn, Benjamini–Hochberg |
| 06 | [`analysis/06_pca.py`](analysis/06_pca.py) | PCA on 15 standardised features — 4 components, 81.8 % of variance |
| 07 | [`analysis/07_clustering.py`](analysis/07_clustering.py) | Ward and k-means, k by silhouette, stability over 100 resamples |
| 10 | [`analysis/10_validate.py`](analysis/10_validate.py) | **Step 8** — ten checks that re-derive every reported number by a different route |
| 11 | [`analysis/11_make_final_report.py`](analysis/11_make_final_report.py) | Builds the 8-page main report; fails the build if it runs past 8 pages |
| 12 | [`analysis/12_make_supplementary.py`](analysis/12_make_supplementary.py) | Builds the supplementary file |

### Two decisions that drive the results

**216 experimental units, not 1944 rows.** The nine samples of one fermentation
are repeated measures. Treating them as independent is pseudoreplication and
inflates the effective sample size ninefold; `10_validate.py` shows it gives
the wrong answer in 8 of 12 trial comparisons, in *both* directions.

**The must-sugar factor belongs out of the error term.** Step 5 did this in its
classical-ANOVA branch but not in its Welch or Kruskal–Wallis branches. For
final acetate, where must sugar is 60 % of the variance, that omission
destroyed the test's power. The restricted permutation test in `10_validate.py`
changes **7 of 24 conclusions**, and all seven lie in the unadjusted branch.
Both the original and the corrected numbers are reported — the discrepancy is
the finding.

---

## Supporting scripts

| Script | What it does |
|---|---|
| [`analysis/04_make_pdf.py`](analysis/04_make_pdf.py) | The earlier plain-text EDA report |
| [`analysis/08_make_progress_report.py`](analysis/08_make_progress_report.py) | The 22-page progress report |
| [`analysis/09_make_slides.py`](analysis/09_make_slides.py) | The 12-slide progress presentation |
| [`analysis/13_export_ai_history.py`](analysis/13_export_ai_history.py) | Exports the AI prompt log and chat history from the session transcripts |
| [`analysis/make_schematic.py`](analysis/make_schematic.py) | The design-and-pipeline schematic (figure 18) |

## Other files

| Path | What it is |
|---|---|
| `Complete_DataSet.xlsx` | The source workbook, unmodified. No script writes to it. |
| `outputs/figures/` | All 21 figures |
| `outputs/tables/` | All 45 result tables as CSV |
| `outputs/BT3041_Final_Report.pdf` | **The main report — 8 pages** |
| `outputs/BT3041_Supplementary.pdf` | **The supplementary file — 31 pages** |
| `outputs/EDA_Report.pdf`, `outputs/Progress_Report.pdf` | Earlier stage reports |
| `outputs/BT3041_Progress_Presentation.pptx` | The progress presentation |
| `ANALYSIS_LOG.md` | The working log kept through the project |
| `AI_USE_LOG.md` | The AI-use declaration |
| `ai_prompts.md` | All 24 prompts, verbatim with timestamps |
| `ai_chat_history.md` | The full conversation record |
| `analysis/README.md` | Longer notes on the pipeline and the cleaning decisions |

Course lecture slides and past question papers are **not** in this repository —
they are not ours to redistribute.

---

## Running it

```bash
pip install pandas numpy scipy statsmodels scikit-learn \
            matplotlib openpyxl reportlab pillow pypdf python-pptx

python analysis/01_inspect.py
python analysis/02_eda.py
python analysis/03_variance_scan.py
python analysis/make_schematic.py
python analysis/05_hypothesis_tests.py
python analysis/06_pca.py
python analysis/07_clustering.py
python analysis/10_validate.py
python analysis/11_make_final_report.py
python analysis/12_make_supplementary.py
```

Deleting `outputs/` and running the above regenerates all 21 figures, all 45
tables and every PDF, with no manual steps. The resampling in `10_validate.py`
is seeded, so the permutation and bootstrap figures reproduce exactly.

## Data

Minebois, R. & Querol, A. (2025) *Fermentation data set obtained from
commercial wine strains in synthetic grape must.* Zenodo,
[doi:10.5281/zenodo.15260916](https://doi.org/10.5281/zenodo.15260916).
Licensed CC BY 4.0 and redistributed here under that licence.

## AI use

Generative AI (Claude, via Claude Code) was used for the analysis code and its
debugging, the figures and typesetting, explanations of statistical methods,
and first drafts of prose including the interpretation. All 24 prompts
(`ai_prompts.md`) and the full chat history (`ai_chat_history.md`) are in this
repository; `AI_USE_LOG.md` sets out where the boundary fell.
