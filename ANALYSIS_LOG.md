# BT3041 Term Project — Work Log

**Project:** Comparative Statistical Analysis of Commercial Yeast Strains During Wine Fermentation
**Dataset:** `Complete_DataSet.xlsx` (Wine Fermentation dataset, Zenodo)
**Stage completed:** Steps 1–4 of the project brief — download, understand, prepare, EDA
**Date:** 30 October 2026

**Part A (sections 1–11)** records the EDA that has been done.
**Part B (sections 12–16)** maps it onto the step-by-step plan in your project
brief and sets out what to do next, by step, by person and by date.

---

## Progress against the brief's 9 steps

| # | Step in the brief | Status | Where it is |
|---|---|---|---|
| 1 | Download the dataset | **Done** | `Complete_DataSet.xlsx` in place |
| 2 | Understand the dataset | **Done** | §3–§5, `01_data_dictionary.csv`, `01_inspection_report.txt` |
| 3 | Understand and prepare the data | **Done** | §6, `common.py`, `02_unit_level_features.csv` |
| 4 | Exploratory data analysis | **Done** | §8, 8 figures, 14 tables |
| 5 | Hypothesis testing | **Done** | `05_hypothesis_tests.py`, tables `05_*.csv`, figs 9-11 |
| 6 | PCA | **Done** | `06_pca.py`, tables `06_*.csv`, figs 12-14 |
| 7 | Clustering | **Done** | `07_clustering.py`, tables `07_*.csv`, figs 15-17 |
| 8 | Validate and interpret | **Done** | §18 — `10_validate.py`, tables `10_*.csv`, figs 19–21 |
| 9 | Presentation and report | **Done** | §19 — `BT3041_Final_Report.pdf`, `BT3041_Supplementary.pdf` |

The brief asks for "at least 40 % of the methods, code, results and interpretation
work" to be complete by the progress presentation. Steps 1–4 of 9, with a
reproducible pipeline and the analysis-ready table built, clears that bar for
methods, code and results. **Interpretation is the gap** — and it is the part the
group must write itself.

---

## 0. Scope and course-policy boundary

What was done here: data inspection, cleaning decisions, exploratory data analysis,
and a descriptive variance scan.

What was deliberately **not** done, because the BT3041 guidelines prohibit AI
involvement:

- formulating the aims and hypotheses
- writing the biological interpretation and conclusions

`03_variance_scan.py` reports effect sizes **without p-values** for exactly this
reason — the choice and justification of the formal tests stays with the group.

---

## 1. Environment setup

Python 3.13.7 with `pandas 3.0.0`, `numpy`, `scipy`, `matplotlib` already present.
Installed the two missing packages:

```bash
python -m pip install openpyxl python-docx
```

Created the project structure:

```
AIBT/
├── Complete_DataSet.xlsx          # source, never modified
├── ANALYSIS_LOG.md                # this file
├── analysis/
│   ├── README.md                  # how to run the pipeline
│   ├── common.py                  # loader, cleaning decisions, plot theme
│   ├── 01_inspect.py              # structure + data quality
│   ├── 02_eda.py                  # EDA + unit-level feature table
│   └── 03_variance_scan.py        # descriptive variance decomposition
└── outputs/
    ├── 01_inspection_report.txt   # full text log
    ├── tables/                    # 14 CSVs
    └── figures/                   # 8 PNGs
```

---

## 2. Reading the project brief

Extracted the text of the `.docx` brief with `python-docx`. The key instruction is
in its section 9:

> "Your first task should be to inspect `Complete_DataSet.xlsx`, not immediately
> start writing the report or running every statistical method."

The brief also specifies the required first-session outputs: a list of all sheets
and columns, an understanding of variables/units/strains/time points/replicates,
and a preliminary set of data-quality checks. Those became `01_inspect.py`.

---

## 3. Workbook structure

| Sheet | Size | Contents |
|---|---|---|
| `Explanation` | 49 × 21 | Variable names and units only — no other metadata |
| `Data` | 1951 × 49 | 1,950 observations × 49 columns |

The `Explanation` sheet turned out to be just a units list, so the data dictionary
had to be built by hand from the column names and the biology. It is written to
`outputs/tables/01_data_dictionary.csv` (55 variables including derived ones).

### Variable blocks

| Block | N vars | Unit |
|---|---|---|
| Design factors | 6 | — |
| Cell counts (Viable, Dead, Total) | 3 | cells/mL |
| Sugars (Glucose, Fructose) | 2 | g/L |
| Primary metabolites (Glycerol, Ethanol) | 2 | g/L, % v/v |
| Organic acids (Acetate, Citrate, Malate, Succinate) | 4 | g/L |
| Nitrogen sources (20 amino acids + NH4Cl + GABA) | 22 | mg/L |
| Volatile aroma compounds | 10 | mg/L |

---

## 4. The experimental design (the key structural finding)

This is **not** a simple 9-strain comparison. It is a balanced three-way factorial
with repeated measures:

| Factor | Levels |
|---|---|
| Strain | 9 — DV10, GALA, OPA, SAI, TXL, VIN13, W12, X16, X5 |
| Temperature | 4 — 12 °C, 18 °C, 25 °C, TVAR (time-varying regime) |
| Initial sugar (`MS`) | 2 — nominal 210, 250 g/L |
| Replicate | 3 — R1, R2, R3 (biological) |

9 × 4 × 2 × 3 = **216 fermentation units**, each sampled at 9 time points
(t0–t8) = **1,944 observations**. Fully balanced, verified by cross-tabulation.

The sheet's 1,950 rows include **6 extra `t5bis` samples**, taken only for TXL and
VIN13 at 18 °C / 250 g/L. These are excluded to keep the design balanced and
reported separately.

> **Consequence:** observations within a fermentation are *not independent*. Any
> test must either collapse each unit to one summary value or model the repetition.
> This drove the decision to build a unit-level table (section 7).

---

## 5. Data-quality checks

All checks live in `01_inspect.py`; the full output is in
`outputs/01_inspection_report.txt`.

| Check | Result |
|---|---|
| Exact duplicate rows | 0 |
| Duplicate design keys | 0 |
| Negative concentrations | 0 |
| `Viable > Total` (impossible) | 1 — `SAI\|18\|250\|R3` at t6 |
| Ethanol at t0 (should be ~0) | max 0.229 % — fine |
| Mean t0 viability | 33.2 % — normal for rehydrated active dry yeast |
| Fermentations reaching <2 g/L residual sugar | 184 of 216 |

### 5a. Missingness is structural, not random

| Block | Rows incomplete | Affected sampling points |
|---|---|---|
| Cell counts | 14 | t3, t4 |
| Sugars | 0 | complete |
| Primary metabolites | 0 | complete |
| Organic acids | 0 | complete |
| Nitrogen sources | 300 | t4, t6 |
| Volatile aroma compounds | 864 | t0, t1, t3, t5 |

Volatiles were measured **only** at t2, t4, t6, t7, t8. Amino acids were not
measured at t4/t6 for 6 of the 8 temperature × sugar batches.

> **Decision: do not impute.** The gaps are whole assay blocks that were never run,
> not values lost at random. Each analysis uses only the sampling points where its
> variables exist.

### 5b. `MS` is a nominal label, not a measurement

Mean *measured* glucose + fructose at t0:

| Nominal MS | 12 °C | 18 °C | 25 °C | TVAR |
|---|---|---|---|---|
| 210 | 229.4 | 206.2 | 203.3 | 214.2 |
| 250 | 266.6 | 248.2 | 242.3 | 244.9 |

Strains within one batch share the same t0 value (same must), so this is **batch
variation, not noise**. Using the nominal `MS` as the baseline for sugar consumed
produces **173 impossible negative values**.

> **Decision:** baseline sugar consumption on each fermentation unit's own measured
> t0 (`InitialSugar`). `MS` is retained only as the experimental factor label.

### 5c. Non-monotonic sugar (analytical artefacts)

Residual sugar cannot increase during fermentation. A monotonicity check flagged:

- **74 samples** with sugar rising by >2 g/L versus the previous sample
- in **71 of the 216 fermentations**, all at **t1–t3**
- **63** of them exceed their own t0 value

Worst cases:

| Unit | Point | Sugar | Rise | Its t0 | Ethanol |
|---|---|---|---|---|---|
| `TXL\|12\|250\|R3` | t1 | 346.49 g/L | +79.9 | 266.6 | 0.15 % |
| `OPA\|25\|250\|R2` | t1 | 289.29 g/L | +51.5 | 237.8 | 0.16 % |
| `TXL\|12\|250\|R2` | t2 | 297.72 g/L | +41.9 | 266.7 | 0.29 % |

346 g/L total sugar is outside the range of grape must, and ethanol is ~0, so no
fermentation had occurred. These are analytical artefacts (likely HPLC dilution
errors), not biology.

> **Decision: flag, do not delete.** Listed in
> `outputs/tables/01_flagged_nonmonotonic_sugar.csv`. They are excluded from the
> kinetic fits via a cumulative-max/cumulative-min, and they cannot affect endpoint
> results because all of them occur at early sampling points.

### 5d. Sampling times are not aligned

Mean clock time (h) at each nominal sampling point:

| Temp | t0 | t1 | t2 | t3 | t4 | t5 | t6 | t7 | t8 |
|---|---|---|---|---|---|---|---|---|---|
| 12 | 0 | 53.2 | 95.5 | 167.5 | 192.6 | 251.1 | 372.4 | 528.5 | 724.6 |
| 18 | 0 | 28.3 | 53.4 | 82.0 | 118.9 | 162.3 | 218.4 | 267.6 | 477.0 |
| 25 | 0 | 7.3 | 23.7 | 30.8 | 53.2 | 76.4 | 98.8 | 169.6 | 283.9 |
| TVAR | 0 | 6.6 | 25.7 | 33.0 | 50.0 | 96.2 | 167.4 | 240.5 | 456.1 |

t0–t8 are **labels, not fixed clock times**. The final sample is at 725 h on
average at 12 °C but 284 h at 25 °C, and it varies *between strains within one
temperature* (at 12 °C: W12 671 h vs VIN13 803 h). Sampling was event-driven.

> **Consequences:** never average across strains at a given t-label as if the
> elapsed time were equal; time-to-completion is itself an **outcome**, not a
> nuisance; kinetic comparisons need interpolation onto a common basis.

---

## 6. The five cleaning decisions

Documented in the `common.load()` docstring so they are reproducible and defensible:

1. The source workbook is read-only — nothing is written back; all cleaning is in memory.
2. `Temperature` is an ordered **categorical**, not a number — TVAR has no single numeric value.
3. The 6 `t5bis` rows are dropped to keep the design balanced at 1,944 rows.
4. Missing values are **not imputed** — the gaps are structural.
5. Sugar consumption is baselined on each unit's own measured t0, never on nominal `MS`.

---

## 7. The unit-level feature table

Built in `02_eda.py` → `outputs/tables/02_unit_level_features.csv`.
**216 rows, one per fermentation**, 21 features. This is the analysis-ready table
for hypothesis testing, PCA and clustering.

Derived features include:

| Feature | Meaning |
|---|---|
| `InitialSugar` | measured glucose + fructose at t0 for that unit |
| `FinalResidualSugar`, `SugarConsumedTotal`, `FracFermentedFinal` | endpoint sugar |
| `Dry` | 1 if final residual sugar < 2 g/L |
| `T50_h`, `T90_h` | interpolated time to 50 % / 90 % sugar consumption |
| `MaxRate_gL_h` | peak fermentation rate |
| `FinalEthanol`, `EthanolYield_pct_per_gL`, `FinalGlycerol`, `FinalAcetate`, `FinalSuccinate` | endpoint chemistry |
| `MalateConsumed` | t0 malate − final malate |
| `MaxViable`, `FinalViability` | population dynamics |

`T50_h`/`T90_h` are interpolated on the **cumulative maximum** of the fermented
fraction, so the flagged artefacts cannot drag the curve backwards.

One unit, `GALA|TVAR|250|R1`, never reaches 90 % sugar consumption (stalls at
88.8 %, 27.5 g/L residual), so its `T90_h` is `NaN` → **n = 215 for that outcome**,
not 216.

---

## 8. EDA findings

### 8a. Temperature dominates the kinetics

| Temperature | T50 (h) | T90 (h) | Peak rate (g/L/h) | Final residual sugar (g/L) |
|---|---|---|---|---|
| 12 °C | 215.6 | 506.4 | 0.94 | 2.46 |
| 18 °C | 143.9 | 338.4 | 1.44 | 1.39 |
| 25 °C | 63.6 | 145.6 | 2.92 | 0.00 |
| TVAR | 78.2 | 306.8 | 2.83 | 1.55 |

Spread of `T90_h`: SD between temperature means = **147.9 h**; SD between strain
means = **26.3 h**. Temperature moves the outcome ~6× more than strain does.

### 8b. Kinetics by strain (pooled over all 24 fermentations each)

| Strain | T50 (h) | T90 (h) | Peak rate | Final sugar (g/L) | Final ethanol (%) | % dry |
|---|---|---|---|---|---|---|
| DV10 | 123.8 | 295.7 | 2.01 | 0.39 | 12.87 | 96 |
| GALA | 107.2 | 344.3 | 2.22 | 4.69 | 12.58 | 62 |
| OPA | 126.1 | 305.5 | 2.19 | 1.78 | 12.95 | 83 |
| SAI | 129.0 | 316.3 | 1.96 | 0.59 | 12.87 | 92 |
| TXL | 151.0 | 333.6 | 1.75 | 0.59 | 12.81 | 88 |
| VIN13 | 149.3 | 360.0 | 2.02 | 0.33 | 12.69 | 92 |
| W12 | 109.5 | 286.6 | 2.02 | 0.56 | 12.76 | 88 |
| X16 | 115.3 | 320.6 | 1.98 | 1.40 | 12.83 | 83 |
| X5 | 116.8 | 357.4 | 2.13 | 1.80 | 12.90 | 83 |

> These pooled means hide the interaction in 8d — they are a first look, not a
> strain comparison.

### 8c. Stuck and sluggish fermentations

32 of 216 did not reach <2 g/L:

- by temperature: 12 °C → 14, TVAR → 10, 18 °C → 8, 25 °C → **0**
- by strain: GALA 9, OPA 4, X16 4, X5 4, TXL 3, W12 3, SAI 2, VIN13 2, DV10 1

### 8d. Strain rankings do not transfer between regimes

Rank by mean `T90_h` (1 = fastest) within each regime:

| Strain | 12 °C | 18 °C | 25 °C | TVAR | Range |
|---|---|---|---|---|---|
| VIN13 | 8 | 9 | 9 | 2 | **7** |
| GALA | 9 | 5 | 3 | 6 | **6** |
| X16 | 4 | 4 | 5 | 8 | 4 |
| SAI | 3 | 7 | 6 | 5 | 4 |
| OPA | 5 | 1 | 2 | 3 | 4 |
| X5 | 6 | 8 | 7 | 9 | 3 |
| DV10 | 2 | 2 | 4 | 4 | 2 |
| TXL | 7 | 6 | 8 | 7 | 2 |
| W12 | 1 | 3 | 1 | 1 | 2 |

Spearman correlation between regime rankings:

| | 12 | 18 | 25 | TVAR |
|---|---|---|---|---|
| **12** | 1.00 | 0.52 | 0.48 | **0.32** |
| **18** | 0.52 | 1.00 | 0.83 | 0.30 |
| **25** | 0.48 | 0.83 | 1.00 | 0.38 |
| **TVAR** | 0.32 | 0.30 | 0.38 | 1.00 |

No strain is fastest in all four regimes (W12 is closest: ranks 1, 3, 1, 1). This
is a genuine **strain × temperature interaction** — a single pooled "best strain"
claim would not be supportable.

### 8e. Descriptive variance decomposition

Share of variance (%) per unit-level outcome. **No p-values** — this is EDA, to show
where signal exists before tests are chosen.

| Outcome | Temperature | Strain | Initial sugar | Strain×Temp | Residual |
|---|---|---|---|---|---|
| T50_h | **87.5** | 5.4 | 1.7 | 3.6 | 1.8 |
| MaxRate_gL_h | **75.8** | 1.8 | 0.1 | 5.1 | 17.1 |
| T90_h | **72.2** | 2.7 | 14.9 | 3.3 | 6.9 |
| FinalSuccinate | **42.0** | 23.8 | 10.5 | 8.6 | 15.2 |
| MalateConsumed | 25.1 | 19.1 | 5.9 | 10.6 | **39.2** |
| FinalGlycerol | 22.6 | 4.0 | **53.7** | 5.0 | 14.6 |
| EthanolYield | 18.7 | 0.9 | 23.7 | 12.6 | **44.2** |
| MaxViable | 16.6 | **29.5** | 12.6 | 11.2 | 30.2 |
| FinalAcetate | 6.5 | 18.1 | **60.2** | 3.6 | 11.6 |
| FinalResidualSugar | 5.6 | 12.3 | 4.2 | 15.6 | **62.3** |
| FinalViability | 4.4 | 9.3 | 19.1 | 20.4 | **46.8** |
| FinalEthanol | 1.7 | 0.4 | **76.7** | 4.6 | 16.6 |

Reading of this table:

- **Temperature** governs the kinetics (T50, T90, peak rate).
- **Initial sugar** governs the endpoint chemistry — final ethanol is almost
  entirely a function of how much sugar went in (210 g/L → 11.32 ± 0.82 %;
  250 g/L → 14.29 ± 0.82 %).
- **Strain** is never the largest single term. It leads only for peak viable cells
  (29.5 %), and is clearest in succinate (23.8 %), malate consumed (19.1 %) and
  acetate (18.1 %).
- The **strain × temperature** term is non-trivial for residual sugar (15.6 %) and
  final viability (20.4 %) — a warning against ranking strains on pooled data.

### 8f. Correlation structure

Strongest Spearman correlations (all samples pooled):

| Pair | ρ |
|---|---|
| Ethanol ~ SugarConsumed | +0.980 |
| Succinate ~ Glycerol | +0.963 |
| Ethanol ~ Succinate | +0.959 |
| Glycerol ~ Ethanol | +0.958 |
| SugarConsumed ~ ResidualSugar | −0.956 |
| Ethanol ~ ResidualSugar | −0.948 |

> Most of this is driven by **fermentation stage** — everything moves together as
> sugar is consumed — not by differences between strains. Correlations computed on
> pooled time-series data should not be read as metabolic coupling.

---

## 9. Outputs produced

### Figures (`outputs/figures/`)

| File | What it shows |
|---|---|
| `fig01_sugar_curves_by_strain.png` | Sugar consumption over time, 9 strains × 4 regimes (small multiples) |
| `fig02_distributions.png` | Distributions of 8 main variables, with medians and skew |
| `fig03_endpoint_by_strain.png` | Endpoint and kinetic outcomes per strain (box + strip) |
| `fig04_strain_x_temperature.png` | Strain ranking per regime, each panel sorted independently |
| `fig05_growth_viability.png` | Yeast growth and viability over time by regime |
| `fig06_correlation_heatmap.png` | Spearman correlation structure (20 variables) |
| `fig07_rank_bump.png` | Rank bump chart — the interaction, shown directly |
| `fig08_variance_decomposition.png` | Share of variance by factor, per outcome |

### Tables (`outputs/tables/`)

| File | Contents |
|---|---|
| `01_data_dictionary.csv` | 55 variables: block, unit, type, missing counts, description |
| `01_design_balance.csv` | Rows per Strain × Temperature × MS |
| `01_sampling_times.csv` | Mean clock time per Temperature × t-label |
| `01_missingness_by_block.csv` | Incomplete rows and affected points per block |
| `01_nominal_vs_measured_sugar.csv` | Nominal `MS` vs measured t0 sugar |
| `01_flagged_nonmonotonic_sugar.csv` | The 74 flagged artefact samples |
| `02_descriptives_all_timepoints.csv` | N, mean, median, SD, min, max, CV for all numeric variables |
| `02_endpoint_by_strain.csv` | Final-sample means and SDs per strain |
| `02_unit_level_features.csv` | **216 × 21 — the analysis-ready table** |
| `02_kinetics_by_strain.csv` | Kinetic summary per strain |
| `02_kinetics_by_temperature.csv` | Kinetic summary per regime |
| `02_strain_rank_by_temperature.csv` | Rank of T90 per strain per regime |
| `02_spearman_correlations.csv` | Full correlation matrix |
| `03_variance_decomposition.csv` | Variance shares per outcome |

Plus `outputs/01_inspection_report.txt` — the full inspection log.

### Shareable summary

A dashboard version of the findings:
<https://claude.ai/code/artifact/efd5fa4d-769d-4b0c-bee6-1dbc2ae0a916>

Private until shared. Note: its self-check never reported back, so it should be
opened and eyeballed before being shared; and anyone it is shared with can read the
attached CSV data files.

---

## 10. Figure design notes

Figures were built against a validated colour palette rather than matplotlib
defaults, so they hold up in print and for colour-vision-deficient readers:

- The 4-colour temperature palette was checked with a CVD validator — worst
  adjacent pair ΔE 9.1 (protan), normal-vision ΔE 22.9, both above threshold.
- Two light-mode slots fall below 3:1 contrast, so every multi-series chart carries
  a legend and a companion CSV table as relief.
- 9 strains exceeds the safe categorical limit, so strain identity is carried by
  **small multiples** (fig01) or by **axis position** (fig03, fig04) — never by 9
  cycled hues. The bump chart (fig07) greys all strains and highlights only the
  three that move most.
- No dual-axis charts. Sequential magnitude uses a single hue; the correlation
  heatmap uses a blue–grey–red diverging ramp with a neutral midpoint.

Several defects were caught by rendering and inspecting each figure rather than
trusting the code:

- colliding direct labels in fig01 (removed; legend + table carry identity)
- `sharey=True` in fig04 hid the per-panel strain labels, making the re-ordering —
  the entire point of the figure — invisible (removed)
- linear bins on a log axis in fig02's `Viable` panel produced one meaningless
  block (switched to log-spaced bins)
- subtitles rendering above their titles (fixed with a shared `titles()` helper)
- a subtitle stating "slowest at the top" when the panels showed fastest at top

---

## 11. Reproducibility

```bash
pip install pandas numpy scipy matplotlib openpyxl
python analysis/01_inspect.py
python analysis/02_eda.py
python analysis/03_variance_scan.py
```

Verified: deleting `outputs/` and re-running all three scripts regenerates
8 figures and 14 tables with no manual steps. `Complete_DataSet.xlsx` is never
modified.

---

# Part B — What to do next, per the project brief

## 12. The decision that has to come first

The brief's step 5 says: *"Use the research question agreed upon with your mentor
to decide which measurements and groups to compare."* That question is not yet
settled, and the EDA has made clear it is not a formality — **two defensible
readings of the same dataset give different answers.**

| Reading | Question | What you'd test |
|---|---|---|
| **A — within regime** | "Do strains differ at a given fermentation temperature?" | Strain effect separately at 12, 18, 25 °C and TVAR |
| **B — across regimes** | "Do strains differ overall?" | Strain main effect pooled across regimes |

Because the strain × temperature interaction is real (§8d: Spearman 0.32 between
the 12 °C and TVAR rankings), **reading B averages away the effect** and will
mostly report "no difference". Reading A is the one the data supports.

A third framing the design also supports, and which may be the strongest:

> **C — robustness.** "Which strains ferment *consistently* across temperature
> regimes, and which are temperature-sensitive?" Here the interaction is not a
> nuisance to be controlled, it *is* the finding. W12 (ranks 1, 3, 1, 1) and
> VIN13 (8, 9, 9, 2) are the two ends of that spectrum.

**Take all three to the mentor and pick one.** Everything downstream depends on it.
Do not let AI pick it — the brief prohibits AI from formulating your aims and
hypotheses, and your TA will ask why you chose it.

### Outcomes worth testing

Whatever the question, the variance scan (§8e) says where the strain signal is:

| Priority | Outcome | Strain share | Why |
|---|---|---|---|
| High | `MaxViable` | 29.5 % | largest strain term in the dataset |
| High | `FinalSuccinate` | 23.8 % | clear strain signal, low residual |
| High | `MalateConsumed` | 19.1 % | biologically interesting (malic acid degradation) |
| High | `FinalAcetate` | 18.1 % | volatile acidity — a real wine-quality variable |
| Medium | `FinalResidualSugar` | 12.3 % | noisy (62 % residual) but practically important |
| **Avoid** | `FinalEthanol` | **0.4 %** | ~entirely determined by initial sugar (76.7 %) |

Testing final ethanol across strains would be the classic mistake here: it looks
like the headline wine variable, but in this dataset it just measures how much
sugar went into the must.

---

## 13. Steps 5–7: the statistics

### Step 5 — Hypothesis testing

**Use `outputs/tables/02_unit_level_features.csv` (216 rows), not the raw sheet.**
This is the single most important methodological point in the project: the raw
1,944 rows are nine repeated samples of 216 fermentations, and treating them as
independent would inflate your sample size ninefold.

The design is balanced (24 fermentations per strain, 54 per regime), which makes
the standard tools valid:

1. **Check assumptions first**, as the brief requires. Shapiro–Wilk on model
   residuals, Levene's test for equal variance. Skew of the candidate outcomes,
   raw vs `log10`:

   | Outcome | raw skew | log10 skew |
   |---|---|---|
   | `FinalResidualSugar` | **+4.21** | −0.17 |
   | `MalateConsumed` | +1.01 | −1.85 |
   | `MaxViable` | +0.73 | −0.09 |
   | `FinalSuccinate` | +0.58 | +0.01 |
   | `FinalAcetate` | +0.14 | −0.39 |

   Only `FinalResidualSugar` is badly skewed and clearly benefits from a log
   transform (watch the zeros — use `log1p`). `MalateConsumed` gets *worse* on a
   log scale, so leave it. The rest are near-symmetric already. Decide from the
   residuals, not the raw values.
2. **Two-way ANOVA**, strain × temperature, **with the interaction term**:
   ```python
   import statsmodels.formula.api as smf
   from statsmodels.stats.anova import anova_lm
   m = smf.ols('MaxViable ~ C(Strain) * C(Temperature) + C(MS)', data=units).fit()
   anova_lm(m, typ=2)
   ```
   Use `typ=2`; include `MS` since §8e shows it matters for most endpoints.
3. **If assumptions fail**, Kruskal–Wallis on strain within each regime, with
   Dunn's post-hoc.
4. **Post-hoc**: Tukey HSD for which strain pairs differ — ANOVA alone only says
   "some strain differs".
5. **Correct for multiple comparisons.** You are testing ~6 outcomes × 4 regimes.
   Benjamini–Hochberg across the family.
6. **Report effect sizes and confidence intervals**, which the brief asks for
   explicitly — partial η² and group mean differences with 95 % CIs. With n = 216
   you will find small differences "significant"; the effect size is what says
   whether they matter.

Deliverable the brief names: *"A statistical results table showing the comparisons,
test used, sample sizes and results."*

### Step 6 — PCA

- Features: the unit-level numeric columns. **Standardise** (`StandardScaler`) —
  the columns range from 0.5 g/L acetate to 10⁸ cells/mL, so without scaling PCA
  would just describe cell count.
- **Decide on the volatile block.** It exists at only five of nine sampling points
  (§5a). Either exclude it, or use endpoint-only volatiles. Say which you did and
  why — this is exactly the kind of documented choice the brief asks for.
- Report explained variance per component and a scree plot.
- Plot PC1–PC2 twice: coloured by **strain**, then by **temperature**. Based on
  §8e, expect temperature to separate and strain not to. That is a legitimate
  result, not a failure.
- Examine the **loadings** — which variables drive each component.
- The brief's own caution: *"A separation between groups is exploratory evidence,
  not proof of statistical significance."*

### Step 7 — Clustering

- Cluster the 216 fermentations on the same standardised features.
- Hierarchical (Ward) with a dendrogram, and/or k-means with the choice of *k*
  justified (elbow or silhouette). Don't just use k = 9 because there are 9 strains.
- **The key output is a cross-tabulation**: clusters × strain, and clusters × temperature.
- Assess stability, as the brief asks — re-run on a subsample, or compare Ward vs
  k-means, and report whether cluster membership holds.

Prediction from the EDA: clusters will track **temperature regime and fermentation
stage**, not strain. If that is what you find, report it plainly — it answers
"do strains form distinct fermentation profiles?" with evidence.

---

## 14. Step 8 — Validate and interpret (your work, not AI's)

The brief is explicit that the group must write this, and that AI must not. Some
things to have ready:

**Limitations this EDA uncovered that belong in the discussion:**

- 74 samples in 71 of 216 fermentations have physically impossible sugar readings
  (§5c). You flagged rather than deleted them — justify that.
- Amino acids and volatiles were not assayed at every sampling point (§5a), so
  nitrogen and aroma conclusions rest on fewer points than sugar/ethanol ones.
- `MS` is a nominal label; actual must sugar varied 203–229 g/L within the nominal
  210 group (§5b). Strains were not all challenged with identical musts.
- Sampling was event-driven, not on a fixed clock (§5d).
- One fermentation (`GALA|TVAR|250|R1`) never completed, so n = 215 for `T90_h`.
- This is one published dataset from one laboratory — no independent replication.

**The claim to avoid**, in the brief's own words: *"Avoid claiming that one strain
is superior unless your measurements and analysis actually support that
conclusion."* Given §8d, a blanket "strain X is best" is not supportable. "W12 was
the fastest or near-fastest in all four regimes" is.

**Literature comparison** (Member 4): search for the dataset's own source
publication first, then for strain-specific work on the commercial strains named
here (VIN13, DV10, X5 are widely studied), and for temperature effects on
*S. cerevisiae* fermentation kinetics and stuck fermentations.

---

## 15. Step 9 — The progress presentation

**Due 3–6 November. Today is 30 October.** Format: ≤10 slides, 8 minutes + 2
minutes Q&A.

A slide plan that uses what already exists:

| # | Slide | Material |
|---|---|---|
| 1 | Title, team, topic | — |
| 2 | Why this topic / biological background | your own words |
| 3 | The dataset and its design | §4 — stress 216 units, balanced factorial |
| 4 | Data quality: what we found and fixed | §5 — the 4 issues |
| 5 | EDA: fermentation curves | `fig01_sugar_curves_by_strain.png` |
| 6 | EDA: where the variance is | `fig08_variance_decomposition.png` |
| 7 | The interaction | `fig07_rank_bump.png` |
| 8 | Methods plan: tests, PCA, clustering | §13 |
| 9 | Preliminary interpretation | **your own words** |
| 10 | Limitations and next steps | §14 |

Slides 3 and 4 are your strongest material and the most likely to draw TA
questions — they show you inspected the data rather than running methods blindly.
All figures have readable labels, units and legends as the brief requires.

**Be ready to explain, not recite:** why the unit-level table has 216 rows and not
1,944; why you flagged rather than deleted the bad sugar readings; why you are not
testing final ethanol across strains; what an interaction is, in one sentence.

### Final report — due 25 November

Keep for supplementary submission, as the brief instructs: the code in
`analysis/`, the AI-use declaration and prompts, and the contribution statement.

---

## 16. Work division and timeline

The brief's table assigns four roles. Mapped to current state:

| Member | Role | Status | Next |
|---|---|---|---|
| 1 | Exploration and preprocessing | Pipeline + data dictionary + cleaned table **done** — verify and take ownership | Re-run the scripts, confirm the cleaning decisions, be able to defend all five |
| 2 | Descriptive stats and hypothesis testing | Descriptives **done** | Step 5 — assumptions, two-way ANOVA, post-hoc, corrections, effect sizes |
| 3 | PCA and clustering | Not started | Steps 6–7 on the unit-level table |
| 4 | Literature and presentation | Not started | Source publication + strain literature; assemble the deck |

The brief's warning applies: *"The fourth member should not be the only person
responsible for biological interpretation. Each member should interpret and verify
the results of their own analysis."* And: *"your TA may ask any member to explain
the statistical tests, code, plots or limitations"* — so everyone should be able to
walk through §4, §5 and §8e regardless of their assigned role.

### Remaining schedule

| Dates | Brief's plan | Concretely |
|---|---|---|
| **30 Oct (today)** | — | Agree the research question (§12) with the mentor. Blocks everything else. |
| **30 Oct – 1 Nov** | "Make progress on statistical analysis" | Member 2: step 5. Member 3: steps 6–7. Member 4: literature. Member 1: verify pipeline. |
| **1–2 Nov** | — | Each member writes their own interpretation; group discusses together. |
| **2–6 Nov** | "Prepare and deliver the progress presentation" | Build the 10 slides (§15), rehearse to 8 minutes, prep Q&A. |
| **7–24 Nov** | "Complete the analysis and report" | Validate results, literature comparison, limitations, final report + supplementary. |
| **25 Nov** | Final report due | — |

---

## 17. Course-policy note

Per the BT3041 guidelines quoted in your brief, AI must not formulate your aims and
hypotheses or write the final report's interpretation and conclusions.

- **What this log contains:** description of what is in the data, data-quality
  findings, reproducible code, and a menu of standard methods with the reasons each
  fits this design.
- **What it deliberately does not contain:** your research question, your
  hypotheses, or any biological interpretation of the results.
- §12 presents three candidate framings precisely so the group chooses between
  them, rather than being handed one.
- `03_variance_scan.py` reports effect sizes with **no p-values** so that the
  choice and justification of the formal tests remains the group's.

Keep this file, the code in `analysis/`, and your AI-use declaration together for
the supplementary submission.


---

# Part C — Steps 8 and 9 (24 November 2026)

## 18. Step 8 — validation

`analysis/10_validate.py` runs ten checks. Each re-derives a number the report
claims, by a different route.

| # | Check | Result |
|---|---|---|
| V1 | Second, independent implementation of every unit-level feature | all 8 agree to machine precision (max relative difference 3 × 10⁻¹³ %) |
| V2 | Restricted permutation test, 5000 shuffles per cell | **changed 7 of 24 calls** — see below |
| V3 | Pseudoreplication: the same tests on the raw 1944 rows | verdict differs in 8 of 12 cells, in *both* directions |
| V4 | Mixed model on the raw repeated measures, random intercept per fermentation | strain ordering preserved by the collapse to 216 rows, Spearman ρ = 0.82 |
| V5 | Leave-one-replicate-out, three two-replicate subsets per cell | 19 of the 22 positive cells hold in all three |
| V6 | Re-test with the 71 flagged fermentations removed | 23 of 24 cells unchanged on n = 145 |
| V7 | Partial η² with a noncentral-F interval, plus a bootstrap interval for the largest strain gap | 18 of 24 intervals exclude zero |
| V8 | Cross-regime robustness per strain | W12 top-three in all four regimes; VIN13 spans 7 rank positions |
| V9 | PCA and clustering summary numbers recomputed from scratch | all 8 reproduce exactly |
| V10 | Every quantitative claim in the report, checked against the data | 16 of 16 pass |

### 18a. The flaw V2 found

Step 5 chooses its test from the assumption checks. The classical-ANOVA branch
fits `_y ~ C(Strain) + C(MS)`, which holds the must-sugar factor out of the
error term. The Welch and Kruskal–Wallis branches compare raw strain groups
and leave it in. Where initial sugar is a large variance component — final
acetate is 60 % — that inflates the within-group variance and costs most of
the test's power.

The fix is a restricted permutation test: shuffle strain labels only within
must-sugar blocks, 5000 times, and permute whichever statistic the cell's
assumption checks call for. No distributional assumption, and the design stays
inside the null hypothesis.

- agreement with step 5 where it used ANOVA (adjusted): **7 of 7**
- agreement where it used Welch or Kruskal–Wallis (not adjusted): **10 of 17**
- significant cells: step 5 **15 of 24** → validated **22 of 24**

Both the original and the corrected numbers are in the report; §4.1 of the main
report explains the discrepancy rather than quietly adopting the better one.

### 18b. The other finding worth keeping

V3 is a useful counter-example to have ready for the viva. Treating the 1944
raw samples as independent does not merely inflate significance — it gives the
*wrong* answer in both directions, because pooling across sampling points mixes
fermentation stage into a comparison that is supposed to be about strain. For
peak viable cells at 12 °C the naive test gives F = 2.1 where the correct
unit-level test gives F = 36.6; for final acetate at 12 °C the naive test gives
p = 0.0001 where the correct one gives p = 0.09.

## 19. Step 9 — the submission

| File | Where it goes | Built by |
|---|---|---|
| `outputs/BT3041_Final_Report.pdf` | **Turnitin** (max 8 pages — it is exactly 8) | `11_make_final_report.py` |
| `outputs/BT3041_Supplementary.pdf` | **Moodle** (27 pages) | `12_make_supplementary.py` |

The main report reads every number it prints from `outputs/tables/`, holds no
literal of its own, and asserts its own page count — the build fails if the
content grows past 8 pages. The supplementary carries the five items the
submission instructions ask for: the code link, the AI prompts, the chat
history, the references, and all 21 figures and 45 tables.

### Before submitting

1. Put the GitHub or Google Drive link on the first line of `CODE_LINK.txt`,
   then re-run `python analysis/12_make_supplementary.py`. Until that is done
   the supplementary shows an "action required" panel where the link belongs.
2. Export the AI chat transcript to `ai_chat_history.md` (or `.pdf`) in the
   project root and upload it with the supplementary; §S2 picks it up
   automatically and notes its presence.
3. Read `AI_USE_LOG.md` and correct anything in the prompt log that does not
   match what was actually asked — the entries marked **[summary]** are
   reconstructed from this work log, not transcribed.
4. Check the author list and the TA name on the title block of both PDFs.
