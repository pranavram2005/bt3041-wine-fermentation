"""
BT3041 Term Project - Comparative Statistical Analysis of Commercial Yeast
Strains During Wine Fermentation.

Shared loader, data dictionary and plotting theme.
The source workbook is NEVER modified; every script reads it fresh.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

ROOT    = Path(__file__).resolve().parent.parent
XLSX    = ROOT / "Complete_DataSet.xlsx"
TABLES  = ROOT / "outputs" / "tables"
FIGURES = ROOT / "outputs" / "figures"
for d in (TABLES, FIGURES):
    d.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------------
# Variable groups (from the workbook's "Explanation" sheet)
# ----------------------------------------------------------------------------
DESIGN = ["Strain", "Rep", "Time_name", "Time", "Temperature", "MS"]

CELLS   = ["Viable", "Dead", "Total"]
SUGARS  = ["Glucose", "Fructose"]
PRIMARY = ["Glycerol", "Ethanol"]
ACIDS   = ["Acetate", "Citrate", "Malate", "Succinate"]
NITROGEN = ["Alanine", "Arginine", "Aspartate", "Cysteine", "Glutamate",
            "Glutamine", "Glycine", "Histidine", "Isoleucine", "Leucine",
            "Lysine", "Methionine", "NH4Cl", "Phenylalanine", "Proline",
            "Serine", "Threonine", "Tryptophan", "Tyrosine", "Valine",
            "Ornithine", "GABA"]
VOLATILES = ["EthAcetate", "Isobutanol", "IsoamylAcetate", "IsoamylAlcohol",
             "EthylHexanoate", "EthOctanoate", "PhenEthAcetate", "PhenEtoh",
             "OctanoicAcid", "DecanoicAcid"]

BLOCKS = {"Cell counts": CELLS, "Sugars": SUGARS,
          "Primary metabolites": PRIMARY, "Organic acids": ACIDS,
          "Nitrogen sources": NITROGEN, "Volatile aroma compounds": VOLATILES}

UNITS = {
    "ResidualSugar": "g/L", "InitialSugar": "g/L", "SugarConsumed": "g/L",
    "FracFermented": "fraction", "Viability": "%", "GlcFruRatio": "ratio",
    "Time": "h", "Temperature": "degC", "MS": "g/L",
    "Viable": "cells/mL", "Dead": "cells/mL", "Total": "cells/mL",
    "Ethanol": "% v/v",
    **{v: "g/L" for v in SUGARS + PRIMARY + ACIDS},
    **{v: "mg/L" for v in NITROGEN + VOLATILES},
}

DESCRIPTIONS = {
    "Strain": "Commercial S. cerevisiae wine yeast strain (9 levels)",
    "Rep": "Biological replicate fermentation (R1-R3)",
    "Time_name": "Nominal sampling point label (t0-t8, plus t5bis)",
    "Time": "Accumulated fermentation time at sampling",
    "Temperature": "Fermentation temperature regime: 12, 18, 25 degC, or TVAR (time-varying)",
    "MS": "Initial must sugar concentration (210 or 250 g/L)",
    "Viable": "Viable yeast cell concentration",
    "Dead": "Dead yeast cell concentration",
    "Total": "Total yeast cell concentration",
    "Glucose": "Residual glucose", "Fructose": "Residual fructose",
    "ResidualSugar": "Glucose + fructose remaining (derived)",
    "InitialSugar": "Measured glucose + fructose at t0 for that unit (derived)",
    "SugarConsumed": "InitialSugar - ResidualSugar (derived)",
    "FracFermented": "SugarConsumed / InitialSugar (derived)",
    "Viability": "100 x Viable / Total (derived)",
    "GlcFruRatio": "Glucose / Fructose (derived)",
    "Glycerol": "Glycerol, an osmolyte/by-product of glycolysis",
    "Ethanol": "Ethanol, the principal fermentation product",
    "Acetate": "Acetic acid (volatile acidity)",
    "Citrate": "Citric acid", "Malate": "L-malic acid",
    "Succinate": "Succinic acid",
    "NH4Cl": "Ammonium (inorganic assimilable nitrogen)",
    "GABA": "gamma-aminobutyric acid",
}
for v in NITROGEN:
    DESCRIPTIONS.setdefault(v, f"{v}, an assimilable nitrogen source in the must")
for v in VOLATILES:
    DESCRIPTIONS.setdefault(v, f"{v}, a fermentation-derived volatile aroma compound")

MEASURED = CELLS + SUGARS + PRIMARY + ACIDS + NITROGEN + VOLATILES

TEMP_ORDER = ["12", "18", "25", "TVAR"]
TIME_ORDER = ["t0", "t1", "t2", "t3", "t4", "t5", "t5bis", "t6", "t7", "t8"]


def load(drop_t5bis=True):
    """Load the Data sheet with ordered categoricals and derived variables.

    Cleaning decisions (documented for the report):
      1. The source file is read-only; all changes live in memory.
      2. `Temperature` is kept as an ordered *categorical*, not a number,
         because TVAR is a time-varying regime with no single numeric value.
      3. `t5bis` is an extra off-schedule sample taken only for TXL and VIN13
         at 18 degC / 250 g/L (6 rows). It breaks the balanced design, so it is
         excluded by default and reported separately.
      4. Missing values are NOT imputed: the gaps are structural (whole
         variable blocks were not assayed at certain sampling points), so each
         analysis uses only the sampling points where its variables exist.
      5. `MS` (210 / 250) is a NOMINAL target, not a measurement: the sugar
         actually measured at t0 averages 213.3 and 250.5 g/L and differs
         systematically between temperature batches (e.g. 229 vs 203 g/L
         within nominal 210). Sugar consumption is therefore baselined on each
         fermentation unit's OWN measured t0 sugar (`InitialSugar`), never on
         `MS`; using `MS` as the baseline produces 173 impossible negative
         values. `MS` is retained only as the experimental factor label.
    """
    df = pd.read_excel(XLSX, sheet_name="Data")
    df["Strain"] = pd.Categorical(df["Strain"], sorted(df["Strain"].unique()))
    df["Temperature"] = pd.Categorical(df["Temperature"], TEMP_ORDER, ordered=True)
    df["Time_name"] = pd.Categorical(df["Time_name"], TIME_ORDER, ordered=True)
    df["MS"] = df["MS"].astype(int)

    if drop_t5bis:
        df = df[df["Time_name"] != "t5bis"].copy()
        df["Time_name"] = df["Time_name"].cat.remove_unused_categories()

    # ---- derived variables -------------------------------------------------
    df["ResidualSugar"] = df["Glucose"] + df["Fructose"]
    df["Viability"] = 100 * df["Viable"] / df["Total"]
    df["GlcFruRatio"] = df["Glucose"] / df["Fructose"].replace(0, np.nan)
    df["Unit"] = (df["Strain"].astype(str) + "|" + df["Temperature"].astype(str)
                  + "|" + df["MS"].astype(str) + "|" + df["Rep"].astype(str))

    # measured initial sugar of each fermentation unit (see cleaning note 5)
    t0 = df.loc[df["Time"] == 0].set_index("Unit")["ResidualSugar"]
    df["InitialSugar"] = df["Unit"].map(t0)
    df["SugarConsumed"] = df["InitialSugar"] - df["ResidualSugar"]
    df["FracFermented"] = df["SugarConsumed"] / df["InitialSugar"]
    return df.sort_values(["Strain", "Temperature", "MS", "Rep", "Time"]).reset_index(drop=True)


# ----------------------------------------------------------------------------
# Plot theme.  Palette = validated default (dataviz skill, light mode).
# Light-mode contrast WARN on aqua/yellow -> every multi-series chart carries
# direct labels or a legend plus a companion table.
# ----------------------------------------------------------------------------
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
          "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
TEMP_COLORS = dict(zip(TEMP_ORDER, SERIES[:4]))
SEQ_HUE = "#2a78d6"           # single hue for magnitude
INK, INK2, INK3 = "#0b0b0b", "#52514e", "#8a8882"
SURFACE, GRID = "#fcfcfb", "#e6e5e0"

mpl.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "savefig.dpi": 200,
    "font.size": 9, "font.family": "DejaVu Sans",
    "axes.edgecolor": GRID, "axes.linewidth": 0.8,
    "axes.labelcolor": INK2, "axes.titlecolor": INK,
    "axes.titlesize": 10, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "axes.grid": True, "axes.axisbelow": True,
    "grid.color": GRID, "grid.linewidth": 0.6,
    "xtick.color": INK3, "ytick.color": INK3,
    "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
    "xtick.direction": "out", "ytick.direction": "out",
    "lines.linewidth": 2.0, "lines.markersize": 4,
    "legend.frameon": False, "legend.fontsize": 8,
    "figure.titlesize": 12, "figure.titleweight": "bold",
})


def despine(ax, keep=("left", "bottom")):
    for side, sp in ax.spines.items():
        sp.set_visible(side in keep)


def save(fig, name, caption=""):
    path = FIGURES / f"{name}.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  figure -> {path.relative_to(ROOT)}" + (f"  [{caption}]" if caption else ""))
    return path


def dump(df, name, note=""):
    path = TABLES / f"{name}.csv"
    df.to_csv(path, index=True)
    print(f"  table  -> {path.relative_to(ROOT)}" + (f"  [{note}]" if note else ""))
    return path


def titles(fig, title, subtitle="", top=0.90, x=0.02):
    """Left-aligned title with a subtitle *below* it, and a reserved top band.

    Returns the rect to pass to fig.tight_layout so nothing collides.
    """
    fig.suptitle(title, x=x, ha="left", y=0.985, va="top")
    if subtitle:
        fig.text(x, 0.945, subtitle, color=INK2, fontsize=8.5, ha="left", va="top")
    return [0, 0, 1, top]
