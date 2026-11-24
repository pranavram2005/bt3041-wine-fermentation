# BT3041 Term Project — analysis pipeline

Comparative statistical analysis of commercial yeast strains during wine
fermentation (Wine Fermentation dataset, `Complete_DataSet.xlsx`).

## Running it

```bash
pip install pandas numpy scipy matplotlib openpyxl statsmodels scikit-learn
python analysis/01_inspect.py          # workbook structure, data dictionary, QC
python analysis/02_eda.py              # descriptives, unit-level table, figs 1-7
python analysis/03_variance_scan.py    # descriptive variance decomposition, fig 8
python analysis/make_schematic.py      # the design/pipeline schematic, fig 18
python analysis/05_hypothesis_tests.py # assumptions, ANOVA, post-hoc, figs 9-11
python analysis/06_pca.py              # PCA, loadings, separation, figs 12-14
python analysis/07_clustering.py       # Ward + k-means, cross-tabs, figs 15-17
python analysis/08_make_progress_report.py  # the 13-page progress report PDF
python analysis/09_make_slides.py      # the 8-slide progress presentation (.pptx)
python analysis/10_validate.py         # step 8: the ten validation checks, figs 19-21
python analysis/11_make_final_report.py     # the 8-page main report (Turnitin)
python analysis/12_make_supplementary.py    # the supplementary file (Moodle)
```

Scripts 08-09 need `reportlab`, `pillow` and `python-pptx`; 11-12 also need
`pypdf`, which they use to assert the page count of what they produced.

**The two files that get submitted** are `outputs/BT3041_Final_Report.pdf`
(8 pages, Turnitin) and `outputs/BT3041_Supplementary.pdf` (Moodle). Before
submitting, put the GitHub or Drive link on the first line of `CODE_LINK.txt`
and re-run script 12 - until then the supplementary carries a visible
"action required" panel where the link should be.

Scripts 05-09 import `common` as `CM`, not `C` — patsy needs the name `C` for
its own categorical operator in the model formulas.

`Complete_DataSet.xlsx` is **never modified** — every script re-reads it and all
cleaning happens in memory, in `common.load()`.

## Layout

| Path | What it is |
|---|---|
| `analysis/common.py` | loader, cleaning decisions, variable groups, plot theme |
| `analysis/01_inspect.py` | structure + data-quality checks |
| `analysis/02_eda.py` | EDA + builds the unit-level feature table |
| `analysis/03_variance_scan.py` | where the signal is, descriptively |
| `analysis/04_make_pdf.py` | builds the plain PDF report (auto table of contents) |
| `analysis/05_hypothesis_tests.py` | assumption checks, two-way ANOVA with interaction, within-regime strain tests, Tukey + Dunn, BH correction, effect sizes |
| `analysis/06_pca.py` | PCA on 15 standardised unit-level features, loadings, label separation |
| `analysis/07_clustering.py` | Ward + k-means, k by silhouette, cluster x design cross-tabs, resampling stability |
| `analysis/08_make_progress_report.py` | builds `Progress_Report.pdf`; booktabs tables, running headers, ruled interpretation pages. Every number is read from the CSVs at build time |
| `analysis/09_make_slides.py` | builds the 12-slide `.pptx` (title + 10 content + close), assertion-evidence style, scoped to steps 1-4; numbers read from the CSVs |
| `outputs/tables/*.csv` | every summary table |
| `outputs/figures/*.png` | every figure |
| `outputs/01_inspection_report.txt` | the full text inspection log |
| `outputs/EDA_Report.pdf` | the EDA written up as a 16-page report |
| `outputs/Progress_Report.pdf` | steps 1-7 written up as a 22-page progress report; section 9 is ruled writing space |
| `analysis/10_validate.py` | step 8: ten checks that re-derive reported numbers by a different route - second implementation of the features, restricted permutation tests, pseudoreplication counter-example, mixed model, leave-one-replicate-out, artefact sensitivity, effect-size intervals, cross-regime robustness, multivariate re-verification, and an automated check of every claim in the report |
| `analysis/11_make_final_report.py` | builds the 8-page `BT3041_Final_Report.pdf`; reads every number from the CSVs and fails the build if the report runs past 8 pages |
| `analysis/12_make_supplementary.py` | builds `BT3041_Supplementary.pdf`: code link, AI prompt log, chat-history pointer, methods in full, all 21 figures, all 45 tables |
| `AI_USE_LOG.md` | the AI-use declaration and prompt log, rendered into section S2 of the supplementary |
| `CODE_LINK.txt` | one line: the GitHub or Drive link to the code |
| `outputs/BT3041_Progress_Presentation.pptx` | the 12-slide progress presentation, with speaker notes and timings |
| `outputs/BT3041_Final_Report.pdf` | **the main report, 8 pages, for Turnitin** |
| `outputs/BT3041_Supplementary.pdf` | **the supplementary file, for Moodle** |

## The five cleaning decisions (documented in `common.load()`)

1. The source workbook is read-only; nothing is written back.
2. `Temperature` is an ordered **categorical**, not a number — `TVAR` is a
   time-varying regime with no single numeric value.
3. The 6 `t5bis` rows (TXL and VIN13 only, 18 °C / 250 g/L) are dropped so the
   design stays balanced at 1944 rows. They are reported separately.
4. Missing values are **not imputed** — the gaps are structural (whole assay
   blocks were not run at certain sampling points).
5. `MS` (210/250) is a **nominal** label, not a measurement. Sugar consumption
   is baselined on each fermentation's own measured t0 sugar (`InitialSugar`).

## The two tables everything downstream should use

- `outputs/tables/02_unit_level_features.csv` — **216 rows, one per
  fermentation.** Use this for hypothesis testing, PCA and clustering. The raw
  sheet is repeated-measures (9 samples per fermentation) and its rows are
  *not* independent.
- `outputs/tables/01_data_dictionary.csv` — all 55 variables with units,
  types, missing counts and descriptions.

## Known data-quality flags

- 74 samples in 71 of the 216 fermentations show residual sugar *rising* over
  time (all at t1–t3); 63 exceed their own t0. Analytical artefacts, listed in
  `01_flagged_nonmonotonic_sugar.csv`. They are flagged, not deleted, and are
  excluded from the kinetic fits via a cumulative-max.
- One sample has `Viable > Total` (`SAI|18|250|R3` at t6).
- `GALA|TVAR|250|R1` never reaches 90 % sugar consumption, so its `T90_h` is
  `NaN` (n = 215 for that outcome, not 216).

## Headline results from steps 5-7

Framed as Reading A — the strain effect tested *within* each temperature regime,
because the interaction makes a pooled strain effect misleading.

- The strain x temperature **interaction is significant for all six outcomes**
  tested (BH-corrected p < 0.005).
- Strain differs significantly in **15 of 24** outcome x regime comparisons.
  Every outcome separates at 12 °C; almost none do at 25 °C.
- `MaxViable` is the only outcome significant in all four regimes.
- Levene fails in 15 of 24 cells, so **Welch's ANOVA** is used where residuals
  are normal but variances are not equal. Classical ANOVA and Welch disagree
  on `FinalAcetate` — worth reporting, not hiding.
- PCA: 4 components, 81.8 % of variance. PC1 = must loading, PC2 = fermentation
  vigour, PC3 = completion. Silhouette by **initial sugar 0.372, temperature
  0.097, strain −0.085** — strain does not separate.
- Clustering: k = 5, stable (resample ARI 0.961, Ward vs k-means 0.854).
  Cluster vs **initial sugar ARI 0.558, temperature 0.191, strain −0.013**.
  Cluster 1 (n = 11) is the stuck-fermentation group; GALA 4 and OPA 3.

## Note on course policy

These scripts cover data handling, EDA and descriptive summaries only. The
BT3041 guidelines require the group to formulate its own aims and hypotheses
and to write its own interpretation and conclusions — `03_variance_scan.py`
deliberately reports effect sizes **without p-values** so that the choice and
justification of the formal tests stays with the group.
