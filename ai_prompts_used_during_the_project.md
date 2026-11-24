# AI prompts used during the project

Every prompt submitted to the AI assistant during the BT3041 term project, listed chronologically across all three working sessions.

## Session 1 - inspection, cleaning decisions, EDA, the EDA report

*29 October 2026, 17:45 to 30 October 2026, 13:01*

**1.** (29 October 2026, 17:45)

> I have placed the raw experimental dataset (`C:\Users\Siva\Desktop\AIBT\Complete_DataSet.xlsx`) and the project brief (`C:\Users\Siva\Desktop\AIBT\Project Topic_ Comparative Statistical Analysis of Commercial Yeast Strains During Wine Fermentation.docx`) in the workspace. Before running any inferential tests, conduct a thorough structural audit and exploratory data analysis (EDA) aligned with the project brief:
> 1. Inspect the workbook schema, variable units, experimental design balance across commercial yeast strains, thermal regimes, initial must sugar levels (`MS`), and biological replicates, as well as the longitudinal sampling schedule ($t_0$–$t_8$).
> 2. Diagnose data-quality anomalies—specifically missingness mechanisms (structural assay schedules vs. random loss), discrepancies between nominal `MS` labels and measured initial sugar ($t_0$), non-monotonic sugar trajectories, and unaligned sampling clock times.
> 3. Propose defensible preprocessing rules and derived unit-level kinetic/endpoint features (such as interpolated $T_{50}$, $T_{90}$, peak fermentation rate, and net metabolite yields) so downstream statistical tests avoid pseudoreplication across repeated timepoints.

**2.** (29 October 2026, 20:16)

> Document the complete inspection workflow, experimental design structure, data-quality diagnostics, preprocessing decisions, and initial EDA findings in a structured Markdown work log (`ANALYSIS_LOG.md`). Map our current progress directly against the project brief's nine-step plan, clearly distinguishing reproducible exploratory outputs from the research framing, hypothesis formulation, and biological interpretation that our team will develop independently.

**3.** (30 October 2026, 10:42)

> Provide a clear mechanistic and experimental synthesis of this *Saccharomyces cerevisiae* wine fermentation study—connecting yeast sugar catabolism, primary metabolite production (ethanol, glycerol, organic acids), nitrogen/volatile dynamics, and the factorial manipulation of strain, temperature regime ($12\text{ }^\circ\text{C}$, $18\text{ }^\circ\text{C}$, $25\text{ }^\circ\text{C}$, and `TVAR`), and initial sugar concentration to the core statistical questions in our project brief.

**4.** (30 October 2026, 10:48)

> Compile the exploratory data analysis into a clean, publication-grade PDF report (`outputs/EDA_Report.pdf`) using standard black-and-white typography, a verified table of contents, structured summary tables, and all generated EDA figures with explanatory captions, avoiding decorative colour styling so the empirical distributions and kinetic trajectories remain the visual focus.

**5.** (30 October 2026, 13:01)

> Refine the layout, pagination, and prose of `outputs/EDA_Report.pdf` so it reads like a cohesive scientific monograph: eliminate forced section page breaks and excessive whitespace, bind headings to their corresponding figures and captions, tighten the table of contents to top-level numbered sections, and present the methodological rationale (such as unit-level aggregation and non-imputation of structural assay blocks) in clear, rigorous prose.

---

## Session 2 - hypothesis testing, PCA, clustering, progress report and slides

*01 November 2026, 16:59 to 01 November 2026, 22:42*

**1.** (01 November 2026, 16:59)

> Audit our current pipeline and outputs against the project brief's nine-step roadmap and the upcoming progress presentation milestone. Clarify how the ~40–50% completion threshold applies across methods, code, results, and interpretation, and outline the exact statistical workflow required on the $n = 216$ unit-level feature table—specifically comparing within-regime strain effects, pooled strain effects, and cross-regime thermal robustness given the observed strain $\times$ temperature interaction.

**2.** (01 November 2026, 17:08)

> Implement the statistical analysis scripts for Steps 5–7 on the $n = 216$ unit-level feature dataset (`02_unit_level_features.csv`):
> 1. **Hypothesis testing (`05_hypothesis_tests.py`):** Evaluate residual normality (Shapiro–Wilk) and variance homogeneity (Levene's test) across candidate outcomes, apply two-way ANOVA with the `Strain * Temperature` interaction (controlling for `MS`), run within-regime strain comparisons using Welch's ANOVA where heteroscedasticity is detected alongside classical ANOVA/Kruskal–Wallis, compute post-hoc pairwise contrasts, apply Benjamini–Hochberg FDR correction, and report partial $\eta^2$ effect sizes.
> 2. **Multivariate ordination (`06_pca.py`):** Perform standardized Principal Component Analysis (`StandardScaler`), quantify explained variance and feature loadings, and evaluate group separation by strain versus thermal regime.
> 3. **Cluster analysis (`07_clustering.py`):** Run hierarchical (Ward) and $k$-means clustering, justify $k$ via silhouette diagnostics, cross-tabulate clusters against strain and temperature regime, and evaluate cluster stability under resampling.
> 4. Compile an analytical interpretation reference document summarizing the statistical outputs so our team can critically evaluate the results and author our own biological interpretation.

**3.** (01 November 2026, 17:27)

> Generate a reproducible progress report PDF (`outputs/Progress_Report.pdf`) that dynamically reads all metrics, test statistics, variance shares, and cluster summaries directly from our output CSV tables, while leaving the biological interpretation section explicitly blank for our team to write.

**4.** (01 November 2026, 20:44)

> Clarify how the project brief evaluates the progress milestone across its four stated components (methods, code, results, and interpretation), and identify which core empirical patterns from our EDA and inferential tests require concise, defensible biological interpretation ahead of the presentation.

**5.** (01 November 2026, 20:54)

> Build a structured progress presentation deck (`outputs/BT3041_Progress_Presentation.pptx`) grounded in the assertion-evidence presentation framework—using full-sentence empirical claims as slide titles, large quantitative callouts, high-resolution figures from our pipeline, and timed speaker notes.

**6.** (01 November 2026, 21:12)

> Expand `outputs/Progress_Report.pdf` to ~15–20 pages with scholarly booktabs-style tables, running headers, full kinetic summaries, residual/variance-homogeneity diagnostics, complete PC1–PC3 feature loadings, $k = 2$–$10$ silhouette selection tables, cluster cross-tabulations, and dedicated structured pages with analytical prompts for our group's written interpretation—while auditing and rectifying any numerical discrepancies across the report and README.

**7.** (01 November 2026, 21:23)

> Verify that `outputs/BT3041_Progress_Presentation.pptx` is present, intact, and numerically consistent with the updated diagnostic counts in the CSV tables.

**8.** (01 November 2026, 21:24)

> Re-scope `outputs/BT3041_Progress_Presentation.pptx` to strictly match the project brief's 10-slide presentation cap and the ~40% milestone scope: center the main deck on our experimental design, data-quality controls, EDA findings, formal null and alternative hypotheses ($H_0 / H_1$), and statistical analysis plan, omit clustering from the primary narrative, and provide a dedicated slide for our team's interpretation.

**9.** (01 November 2026, 21:29)

> Deepen the analytical content across the scoped slides—explicitly contrasting the strain $\times$ temperature interaction $H_0$ and within-regime $H_0$, detailing the 6-step statistical testing protocol, and presenting complete quantitative summaries for kinetic rates, variance decomposition, and regime-dependent strain rank shifts—while clarifying the exact milestone scope.

**10.** (01 November 2026, 21:53)

> Refine the structure and visual design of `outputs/BT3041_Progress_Presentation.pptx` to 10 core content slides (between the title and closing slides, without separate Q&A backup slides):
> 1. Remove heavy coloured top/side accent borders so the layout relies on clean typography, subtle hairlines, and quantitative visuals.
> 2. Add a concise code and reproducibility slide highlighting our read-only data loader, $t_0$ sugar baselining, and interaction model formula, plus a single consolidated slide summarizing our ongoing downstream analyses (hypothesis testing, PCA, and clustering).
> 3. Place the Observations and Interpretation slide immediately before the closing slide, incorporating our team's structured synthesis on thermal dominance over strain choice and regime-dependent rank shifts (`VIN13` and `W12`):
>
> ## 1. Temperature has priority over strain
> Why would tank temperature be a more important parameter than yeast strain used?
>
> Observation:
> - The fermentation process was much faster at 25°C than at 12°C.
> - T90 values were much more variable due to temperature (147.9 h) than yeast strain (26.3 h).
>
> Interpretation:
> - Temperature plays a much greater role than yeast strain when considering fermentation rate.
> - Proper fermentation temperature regulation is thus essential in the control of fermentation kinetics.
> - The selection of a specific yeast strain will not save the day in inappropriate temperature conditions.
>
> ## 2. Rankings depend on temperature regime
> Why would some strains rank poorly under cold conditions yet perform near the top under a variable temperature regime?
>
> Observation:
> - VIN13 was 8th at 12°C and went up to 2nd place at TVAR.
> - W12 yeast consistently ranked among the fastest across temperature regimes.
> - Yeast strains' rankings were greatly affected by the temperature.
>
> Interpretation:
> - Various yeast strains exhibit different responses to temperature conditions.
> - A poor-performing yeast strain at low temperatures can perform great in temperature variations.
> - Yeast strain should be selected based on the fermentation conditions and not on the universal performance ranking.
>
> Key takeaway message:
> Fermentation speed is mostly determined by the temperature while the yeast performance is dependent on the temperature regime.

**11.** (01 November 2026, 22:03)

> Enrich the visual balance of the presentation by adding a clear fermentation biochemistry and factorial-design schematic to the context slide and compact quantitative figures (effect-size bars, PCA projection, and cluster structure) to the downstream-analysis slide, keeping text concise alongside key summary metrics.

**12.** (01 November 2026, 22:15)

> Add our official team metadata and canonical data citation to the presentation and report title blocks: **Team 20** (K James Bond, Avala Madhavi, Dinesh Kumar, Mohesh, Pranav Ram), Teaching Assistant **Kaviya D**, and the Zenodo source dataset (<https://zenodo.org/records/15260916>), updating any experimental medium descriptions accordingly.

**13.** (01 November 2026, 22:30)

> Audit our presentation deck against the updated logistical constraints: each team is allotted exactly **6 minutes** for presentation followed by **2 minutes** for Q&A, slides must be uploaded to Moodle by **2 November 2026 at 3:00 PM**, and TAs will project the slides from their own laptops. Assess slide pacing and cross-platform font compatibility.

**14.** (01 November 2026, 22:34)

> Resolve both the 6-minute presentation pacing constraint and the cross-platform font/rendering risks identified in the audit.

**15.** (01 November 2026, 22:35)

> Consolidate the deck structure and tighten per-slide word density so the entire talk paces comfortably within 6 minutes (~45 seconds per content slide) while preserving our experimental design, data-quality controls, variance decomposition, interaction rank-bump evidence, hypotheses/code, ongoing work summary, and observations/interpretation.

**16.** (01 November 2026, 22:42)

> Fix the remaining slide geometry defects: eliminate the excess bottom whitespace and realign the card/figure layout on Slide 4 (Data Quality), and resolve the vertical overlap between the variance-decomposition figure and the lower text block on Slide 5 (EDA).

---

## Session 3 - step-8 validation, the 8-page report, the supplementary file

*23 November 2026, 18:52 to 24 November 2026, 13:11*

**1.** (23 November 2026, 18:52)

> Review the entire repository and complete the final deliverables (Steps 8 and 9) in strict compliance with the submission instructions (deadline: **25 November 2026, 23:59**):
> 1. **Step 8 — Statistical Validation (`analysis/10_validate.py`):** Implement independent verification checks across our pipeline—including an independent re-derivation of all unit-level kinetic/endpoint features, block-restricted permutation tests (shuffling strain labels within initial must-sugar blocks `MS` to control for batch sugar variance), pseudoreplication diagnostics ($n = 1,944$ vs. $n = 216$), linear mixed-effects modeling with fermentation-unit random intercepts, leave-one-replicate-out sensitivity, flagged-artefact exclusion sensitivity, noncentral-$F$ / bootstrap effect-size intervals, and automated claim verification.
> 2. **Step 9a — Main Term Project Report (`outputs/BT3041_Final_Report.pdf`):** Build a reproducible, publication-formatted Turnitin report capped strictly at **8 pages**, reading every quantitative figure dynamically from `outputs/tables/` and documenting any methodological discrepancies uncovered during validation.
> 3. **Step 9b — Moodle Supplementary Package (`outputs/BT3041_Supplementary.pdf`):** Compile the complete supplementary archive containing the repository link placeholder (`CODE_LINK.txt`), AI-use declaration (`AI_USE_LOG.md`), exported AI prompts and chat history, literature references, and all generated figures and summary tables.

**2.** (24 November 2026, 13:10)

> Audit the repository to verify whether all nine project steps, validation checks, figures, tables, the 8-page Turnitin report, and the Moodle supplementary PDF are complete and internally consistent, and list any remaining submission prerequisites.

**3.** (24 November 2026, 13:11)

> Extract and export the complete chronological record of user prompts and session transcripts from the local session logs into clean, reproducible Markdown documentation (`ai_prompts.md` and `ai_chat_history.md`) so the supplementary package includes the exact prompt and conversation record.