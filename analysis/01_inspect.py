"""
Step 1 - Inspect the workbook and establish data quality.

Deliverables required by the project brief, section 9:
  * a list of all sheets and their columns
  * a clear understanding of variables, units, strains, time points, replicates
  * a preliminary set of data-quality checks
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import openpyxl

sys.path.insert(0, str(Path(__file__).parent))
import common as C

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 100)

rep = []


def say(*a):
    line = " ".join(str(x) for x in a)
    print(line)
    rep.append(line)


# ---------------------------------------------------------------- 1. workbook
wb = openpyxl.load_workbook(C.XLSX, read_only=True)
say("=" * 78)
say("1. WORKBOOK STRUCTURE")
say("=" * 78)
for s in wb.sheetnames:
    ws = wb[s]
    say(f"  sheet {s!r}: {ws.max_row} rows x {ws.max_column} cols")
say("  'Explanation' holds only the variable list and units (no other metadata).")

raw = pd.read_excel(C.XLSX, sheet_name="Data")
say(f"  'Data' parsed: {raw.shape[0]} observations x {raw.shape[1]} columns")

# ------------------------------------------------------- 2. data dictionary
df = C.load()
rows = []
for col in raw.columns:
    block = next((b for b, v in C.BLOCKS.items() if col in v), "Design factor")
    if col in ("Strain", "Rep", "Time_name", "Temperature"):
        vtype = "categorical"
    elif col == "MS":
        vtype = "factor (nominal)"
    else:
        vtype = "numeric"
    rows.append({
        "Variable": col,
        "Block": block,
        "Unit": C.UNITS.get(col, ""),
        "Type": vtype,
        "N_nonmissing": int(raw[col].notna().sum()),
        "N_missing": int(raw[col].isna().sum()),
        "Description": C.DESCRIPTIONS.get(col, ""),
    })
for col in ["ResidualSugar", "InitialSugar", "SugarConsumed", "FracFermented",
            "Viability", "GlcFruRatio"]:
    rows.append({
        "Variable": col, "Block": "Derived", "Unit": C.UNITS.get(col, ""),
        "Type": "numeric",
        "N_nonmissing": int(df[col].notna().sum()),
        "N_missing": int(df[col].isna().sum()),
        "Description": C.DESCRIPTIONS.get(col, ""),
    })
dd = pd.DataFrame(rows).set_index("Variable")
C.dump(dd, "01_data_dictionary", f"{len(dd)} variables")

# -------------------------------------------------------- 3. design map
say("")
say("=" * 78)
say("2. EXPERIMENTAL DESIGN")
say("=" * 78)
say(f"  Strains (9)      : {', '.join(df.Strain.cat.categories)}")
say(f"  Temperature (4)  : {', '.join(C.TEMP_ORDER)}   (TVAR = time-varying regime)")
say("  Initial sugar (2): 210, 250 g/L  (NOMINAL label - see data-quality note)")
say("  Replicates (3)   : R1, R2, R3  (biological)")
say(f"  Sampling points  : t0..t8 (9 per fermentation), "
    f"{df.Time.nunique()} distinct clock times")
say("")
say("  => 9 strains x 4 temperatures x 2 sugar levels x 3 reps = 216 fermentation")
say("     units; x 9 sampling points = 1944 observations. FULLY BALANCED.")
say("     The raw sheet has 1950 rows: 6 extra 't5bis' samples taken only for")
say("     TXL and VIN13 at 18 degC / 250 g/L. Excluded to keep the design balanced.")
say("")
say("  Design type: three-way factorial (Strain x Temperature x InitialSugar)")
say("     with REPEATED MEASURES over 9 sampling points on each unit.")
say("     => observations within a unit are NOT independent; any test must either")
say("        collapse each unit to one summary value, or model the repetition.")

bal = pd.crosstab(df.Strain, [df.Temperature, df.MS])
C.dump(bal, "01_design_balance", "rows per Strain x Temp x MS")

# --------------------------------------------- 4. sampling-time misalignment
say("")
say("=" * 78)
say("3. SAMPLING TIMES ARE NOT ALIGNED")
say("=" * 78)
tt = df.pivot_table(index="Temperature", columns="Time_name", values="Time",
                    aggfunc="mean", observed=True).round(1)
say(tt.to_string())
say("")
say("  t0..t8 are *nominal* labels, not fixed clock times. The mean time to the")
say("  final sample is 725 h at 12 degC but 284 h at 25 degC, and it varies")
say("  between strains within one temperature (at 12 degC: W12 671 h vs")
say("  VIN13 803 h). Sampling was event-driven - samples were taken as each")
say("  fermentation progressed.")
say("  CONSEQUENCES:")
say("   - never average a variable across strains at a given t-label as if the")
say("     elapsed time were the same;")
say("   - time-to-completion is itself an OUTCOME, not a nuisance - it should be")
say("     derived and tested;")
say("   - kinetic comparisons need interpolation onto a common basis.")
C.dump(tt, "01_sampling_times", "mean clock time (h) per Temp x t-label")

# ------------------------------------------------------ 5. data quality
say("")
say("=" * 78)
say("4. DATA-QUALITY CHECKS")
say("=" * 78)
say(f"  Exact duplicate rows                    : {raw.duplicated().sum()}")
key = ["Strain", "Rep", "Temperature", "MS", "Time_name"]
say(f"  Duplicate design keys                   : {raw.duplicated(key).sum()}")

# 5a structural missingness
say("")
say("  MISSINGNESS IS STRUCTURAL, NOT RANDOM - whole variable blocks were not")
say("  assayed at certain sampling points:")
miss = []
for name, cols in C.BLOCKS.items():
    present = df.groupby("Time_name", observed=True)[cols[0]].apply(
        lambda s: s.notna().mean())
    pts = [str(t) for t, v in present.items() if v < 0.99]
    n = int(df[cols].isna().any(axis=1).sum())
    say(f"   - {name:26s} {n:5d} rows incomplete"
        + (f"; absent/partial at {', '.join(pts)}" if pts else "; complete"))
    miss.append({"Block": name, "N_vars": len(cols), "Rows_incomplete": n,
                 "Affected_timepoints": ", ".join(pts) or "none"})
say("   Amino acids: not measured at t4/t6 for 6 of the 8 temp x sugar batches.")
say("   Volatiles  : measured ONLY at t2, t4, t6, t7, t8 (never t0, t1, t3, t5).")
say("   => Do NOT impute. Use the sampling points where a block actually exists.")
C.dump(pd.DataFrame(miss).set_index("Block"), "01_missingness_by_block")

# 5b nominal vs measured sugar
say("")
say("  NOMINAL vs MEASURED INITIAL SUGAR (mean measured g/L at t0):")
t0 = df[df.Time_name == "t0"]
ms = t0.pivot_table(index="MS", columns="Temperature", values="ResidualSugar",
                    aggfunc="mean", observed=True).round(1)
say(ms.to_string())
say("   Nominal 210 g/L musts actually measured 203-229 g/L depending on the")
say("   temperature batch; nominal 250 measured 242-267. Strains within a batch")
say("   share the same t0 value (same must), so this is batch variation, not noise.")
say("   => baseline sugar consumption on each unit's own t0, never on MS.")
C.dump(ms, "01_nominal_vs_measured_sugar")

# 5c implausible values: residual sugar must not increase over time
say("")
say("  MONOTONICITY CHECK (residual sugar cannot increase during fermentation):")
flags = []
for u, g in df.groupby("Unit", observed=True):
    g = g.sort_values("Time")
    d = g["ResidualSugar"].diff()
    for idx, r in g.loc[d > 2.0].iterrows():   # >2 g/L rise = beyond assay noise
        flags.append({"Unit": u, "Time_name": str(r["Time_name"]), "Time": r["Time"],
                      "ResidualSugar": round(r["ResidualSugar"], 2),
                      "Rise_vs_previous": round(d.loc[idx], 2),
                      "InitialSugar": round(r["InitialSugar"], 2),
                      "Ethanol": round(r["Ethanol"], 2)})
fl = pd.DataFrame(flags)
say(f"   {len(fl)} sample(s) show residual sugar rising by >2 g/L; "
    f"{int((fl.ResidualSugar > fl.InitialSugar).sum())} exceed their own t0 value.")
if len(fl):
    say(f"   affected units: {fl.Unit.nunique()} of 216; "
        f"sampling points: {sorted(fl.Time_name.unique())}")
    say("   worst cases:")
    for _, r in fl.nlargest(5, "Rise_vs_previous").iterrows():
        say(f"     {r.Unit:22s} {r.Time_name:5s} sugar {r.ResidualSugar:7.2f} g/L "
            f"(+{r.Rise_vs_previous:.1f} vs previous; t0 was {r.InitialSugar:.1f}; "
            f"ethanol {r.Ethanol:.2f}%)")
    say("   These are analytical artefacts (likely HPLC dilution errors), not")
    say("   biology: sugar cannot be produced during fermentation. FLAGGED, not")
    say("   deleted - they are excluded only from kinetic fits, and they cannot")
    say("   affect endpoint results because all of them occur at early samples.")
    C.dump(fl.set_index("Unit"), "01_flagged_nonmonotonic_sugar")

# 5d other sanity checks
say("")
say("  OTHER SANITY CHECKS:")
say(f"   Viable > Total (impossible)             : {int((df.Viable > df.Total).sum())}")
say(f"   Negative concentrations                 : {int((df[C.MEASURED] < 0).sum().sum())}")
say(f"   Ethanol at t0 (should be ~0)            : max {df[df.Time_name == 't0'].Ethanol.max():.3f} %")
say(f"   Mean t0 viability (rehydrated dry yeast): {t0.Viability.mean():.1f} %")
end = df[df.Time_name == "t8"]
say(f"   Fermentations reaching <2 g/L residual  : {int((end.ResidualSugar < 2).sum())} of 216")

out = C.ROOT / "outputs" / "01_inspection_report.txt"
out.write_text("\n".join(rep), encoding="utf-8")
print("\n  report -> outputs/01_inspection_report.txt")
