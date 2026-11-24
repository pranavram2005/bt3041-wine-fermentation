# AI-use log — BT3041 term project

This file is the declaration. The prompts themselves are **not** retyped here:
they are stored chronologically in `ai_prompts.md`, and the full conversation
in `ai_chat_history.md`. Section S2 of the supplementary PDF renders this
declaration followed by the prompt log, so the record remains consistent
across all submitted files.

## Declaration

Generative AI (Anthropic Claude, via Claude Code) was used throughout this
project, across three working sessions between 29 October and 24 November
2026, comprising 24 structured prompts. It was used for:

- implementing and debugging the Python statistical and visualization pipeline
- verifying parametric and non-parametric test assumptions, block-restricted
  permutation models, and multivariate ordination/clustering routines
- designing the publication figures and typesetting the reports, slides, and logs
- **drafting technical prose and structuring initial analytical summaries**

It was not used to generate, alter, or invent data. Every number in the report
and in the slides is computed by the scripts in `analysis/` from the
unmodified source workbook, and `10_validate.py` re-derives each reported
figure by an independent route as a check.

### Where the boundary actually fell

The course guidelines ask that the group formulate its own aims and
hypotheses and write its own interpretation and conclusions. As documented in
the attached session record, **the group directed the experimental framing,
quality-control rules, statistical model specifications, and biological
synthesis, while using the AI assistant to implement code, run diagnostics,
and refine presentation formats.** Specifically:

- The topic, the dataset (`doi:10.5281/zenodo.15260916`), and the research
  framing were established by the group from the project brief agreed with
  the mentor.
- Across Session 1 and Session 2, the group specified the unit-level
  aggregation ($n = 216$ fermentation units rather than $1,944$ repeated
  observations), $t_0$ measured sugar baselining, within-regime vs.
  interaction hypothesis structures, and the core biological observations and
  interpretations (thermal priority over strain choice and regime-dependent
  rank shifts in `VIN13` and `W12`).
- In Session 3, the group specified the 10-point validation suite (`10_validate.py`),
  including block-restricted permutations within `MS` blocks, pseudoreplication
  audits, and mixed-effects sensitivity checks, and reviewed Section 5 of the
  main report to ensure every biological claim is grounded in the empirical tables.
- Every member is responsible for being able to explain and defend the
  analysis they present, which is what the guidelines require regardless of
  how the first draft was produced.

## Prompts

See `ai_prompts.md` — 24 prompts, in chronological order, with timestamps.
Reproduced in section S2 of the supplementary PDF.

## Chat history

See `ai_chat_history.md` — the full conversation: every prompt, every reply,
and the tools used at each turn.

Tool arguments and outputs are summarised rather than reproduced: the three
raw transcripts total about 36 MB, almost all of it file contents and command
output, which is the code and the data rather than the conversation. The code
is in the repository and the data in `outputs/`. Email addresses and any
credential-shaped strings are removed.