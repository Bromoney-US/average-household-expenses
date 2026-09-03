#!/usr/bin/env python3
"""Build the three published charts.

Inputs, both in this directory:
  ../bromoney_ces_cpi_crosswalk_2023-2024.csv   chart 1 (built by build_crosswalk.py)
  chart_inputs.csv                              charts 2 and 3

Every number plotted comes from one of those two files. Nothing is hard-coded here.

Run:  python build_charts.py
Out:  ../charts/*.svg and ../charts/*.png — 16:9, 4:3 and 1:1 for all three.
      Each aspect gets its own margins.

Output is deterministic: PNG and SVG are byte-identical between runs
(SVG date metadata is suppressed, hash salt is fixed).

Charts may be republished with attribution: Bromoney analysis of BLS data.
"""
import csv
import io
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__))
CROSSWALK = os.path.join(HERE, "..", "bromoney_ces_cpi_crosswalk_2023-2024.csv")
INPUTS = os.path.join(HERE, "chart_inputs.csv")
OUT = os.path.join(HERE, "..", "charts")
os.makedirs(OUT, exist_ok=True)

INK = "#1A1317"
MUTED = "#6E626A"
RULE = "#D9D2D6"
ACCENT = "#A31243"
OK = "#1D6B4C"
WARN = "#87661A"
BLOCKED = "#4E5A68"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "text.color": INK,
    "axes.labelcolor": INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.edgecolor": RULE,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "svg.hashsalt": "bromoney-ces-cpi-2023-2024",   # deterministic SVG element ids
})

QUALITY_COLOR = {"direct": ACCENT, "close": OK, "caution": WARN, "partial": BLOCKED}

# aspect -> (figsize, subplots_adjust, footer y, label font, title size, title pad, subtitle y, footer x)
ASPECT = {
    "16x9": ((10, 5.625), dict(left=0.085, right=0.975, top=0.845, bottom=0.28), 0.022, 8.5, 13.5, 22, 1.045, 0.014),
    "4x3":  ((8, 6),      dict(left=0.135, right=0.970, top=0.850, bottom=0.265), 0.020, 8.0, 12.0, 26, 1.038, 0.024),
    "1x1":  ((7.5, 7.5),  dict(left=0.130, right=0.965, top=0.855, bottom=0.215), 0.018, 8.0, 12.0, 30, 1.030, 0.024),
}


def quality_key(raw):
    head = raw.split(":")[0].strip().lower()
    if head.startswith("not comparable"):
        return "not_comparable"
    return head if head in QUALITY_COLOR else "partial"


def read_csv(path):
    with io.open(path, encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def inputs(series):
    return [r for r in read_csv(INPUTS) if r["series"] == series]


def footer(fig, note, y, x=0.012):
    """Footer sits in figure coordinates; narrow aspects need more left margin."""
    fig.text(x, y, note, fontsize=7.2, color=MUTED, ha="left", va="bottom", linespacing=1.6)


def save(fig, name):
    for ext in ("svg", "png"):
        path = os.path.join(OUT, "%s.%s" % (name, ext))
        meta = {"Date": None} if ext == "svg" else {"Software": None}
        fig.savefig(path, format=ext, dpi=200, metadata=meta)
        print("  wrote", os.path.relpath(path, HERE))
    plt.close(fig)


def suffix_for(aspect):
    return "" if aspect == "16x9" else "-" + aspect


# ---------------------------------------------------------------- chart 1
LABELS = {
    "Meats, poultry, fish and eggs": (1.1, 0.0, "left", "Meats, poultry,\nfish and eggs"),
    "Drugs": (1.0, 0.0, "left", "Drugs"),
    "Dairy products": (-0.9, 0.0, "right", "Dairy products"),
    "Gasoline": (0.0, -1.9, "center", "Gasoline"),
    "Food at home": (1.0, -0.1, "left", "Food at home"),
    "Owned dwellings": (1.0, 0.45, "left", "Owned dwellings"),
    "Rented dwellings": (1.0, -0.95, "left", "Rented dwellings"),
    "Apparel and services": (1.0, -0.1, "left", "Apparel and services"),
    "Food away from home": (1.0, -0.1, "left", "Food away from home"),
    "Vehicle insurance": (-1.0, 0.0, "right", "Vehicle insurance"),
    "Cereals and bakery products": (1.0, -0.25, "left", "Cereals and\nbakery products"),
}


def chart_scatter(aspect="16x9"):
    size, margins, fy, lfs, tfs, tpad, sy, fx = ASPECT[aspect]
    rows = [r for r in read_csv(CROSSWALK)
            if quality_key(r["crosswalk_quality"]) != "not_comparable"]

    fig, ax = plt.subplots(figsize=size)
    fig.subplots_adjust(**margins)

    hi = 23.0
    ax.plot([-8.5, hi], [-8.5, hi], color=RULE, lw=1.1, ls="--", zorder=1)
    if aspect == "16x9":
        ax.annotate("dashed line: spending and price moved together",
                    xy=(10.2, 24.4), fontsize=8, color=MUTED, ha="left", va="center")

    for r in rows:
        x = float(r["cpi_change_pct"])
        y = float(r["ces_change_pct"])
        sig = r["ces_significant_95"] == "yes"
        ax.scatter(x, y, s=200 if sig else 85, marker="*" if sig else "o",
                   color=QUALITY_COLOR[quality_key(r["crosswalk_quality"])],
                   edgecolors="white", linewidths=0.9, zorder=3)
        dx, dy, ha, text = LABELS[r["ces_category"]]
        ax.annotate(text, (x + dx, y + dy), fontsize=lfs, color=INK,
                    ha=ha, va="center", zorder=4, linespacing=1.35)

    ax.axhline(0, color=RULE, lw=1, zorder=1)
    ax.axvline(0, color=RULE, lw=1, zorder=1)
    ax.set_xlabel("CPI price change, 2023 to 2024 annual averages (%)", fontsize=9, labelpad=8)
    ax.set_ylabel("CE spending change, 2023 to 2024 (%)", fontsize=9)
    ax.set_xlim(-8.5, hi)
    ax.set_ylim(-9.5, 26)
    ax.set_title("Where household spending outran prices — and where it lagged",
                 fontsize=tfs, loc="left", pad=tpad)
    ax.text(0, sy, "Same two calendar years, categories paired one to one",
            transform=ax.transAxes, fontsize=8.5, color=MUTED)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

    handles = [
        Line2D([], [], marker="*", ls="", color=ACCENT, markersize=13, label="passed the 95% test"),
        Line2D([], [], marker="o", ls="", color=ACCENT, markersize=7, label="did not pass"),
        Line2D([], [], marker="s", ls="", color=ACCENT, markersize=7, label="direct pairing"),
        Line2D([], [], marker="s", ls="", color=OK, markersize=7, label="close pairing"),
        Line2D([], [], marker="s", ls="", color=WARN, markersize=7, label="read with caution"),
        Line2D([], [], marker="s", ls="", color=BLOCKED, markersize=7, label="partial pairing"),
    ]
    ax.legend(handles=handles, fontsize=7.5, frameon=False, loc="lower right",
              ncol=2, handletextpad=0.4, columnspacing=1.2, borderaxespad=0.5)

    footer(fig, "Above the dashed line, outlay grew faster than the index; below it, more slowly.\n"
                "The gap is arithmetic, not a measure of quantity.\n"
                "Bromoney analysis of BLS CE 2024 and CPI-U annual averages (M13).\n"
                "Housing/Shelter excluded as not comparable.", fy, fx)
    save(fig, "ces-cpi-spending-vs-prices-2023-2024" + suffix_for(aspect))


# ---------------------------------------------------------------- chart 2
def chart_quintiles(aspect="16x9"):
    size, margins, fy, _, tfs, tpad, sy, fx = ASPECT[aspect]
    rows = inputs("quintile")
    mean = float(inputs("quintile_mean")[0]["value"])
    labels = [r["label"].replace(" ", "\n") for r in rows]
    values = [float(r["value"]) for r in rows]

    fig, ax = plt.subplots(figsize=size)
    m = dict(margins)
    m["left"] = 0.155 if aspect != "16x9" else 0.095
    fig.subplots_adjust(**m)

    bars = ax.bar(labels, values, color=BLOCKED, width=0.6, zorder=3)
    bars[0].set_color(ACCENT)
    bars[-1].set_color(ACCENT)

    ax.axhline(mean, color=INK, lw=1.3, ls="--", zorder=4)
    ax.annotate("national mean  $%s" % format(int(mean), ","), xy=(-0.42, mean),
                xytext=(-0.42, mean + 440), fontsize=8.5, color=INK, ha="left")

    for b, v in zip(bars, values):
        ax.annotate("$%s" % format(int(v), ","), (b.get_x() + b.get_width() / 2, v),
                    ha="center", va="bottom", fontsize=9, color=INK,
                    xytext=(0, 4), textcoords="offset points", zorder=5)

    ax.set_ylabel("Average monthly expenses", fontsize=9, labelpad=6)
    ax.set_ylim(0, max(values) * 1.16)
    ax.set_yticks([0, 3000, 6000, 9000, 12000])
    ax.set_yticklabels(["$0", "$3,000", "$6,000", "$9,000", "$12,000"], fontsize=8.5)
    ax.tick_params(axis="x", labelsize=9, length=0)
    ax.set_title("The average describes no one in particular",
                 fontsize=tfs, loc="left", pad=tpad)
    ax.text(0, sy, "Average monthly expenses by income quintile, 2024",
            transform=ax.transAxes, fontsize=8.5, color=MUTED)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color=RULE, lw=0.8, alpha=0.8)
    ax.set_axisbelow(True)

    footer(fig, "The bottom fifth spends less than half the mean; the top fifth nearly twice it.\n"
                "Bromoney analysis of BLS CE 2024, table C. Annual totals divided by twelve.", fy, fx)
    save(fig, "average-monthly-expenses-by-quintile-2024" + suffix_for(aspect))


# ---------------------------------------------------------------- chart 3
CLOCK_WHAT = {
    "BLS CPI": "Price change for a defined market basket",
    "BEA Personal Income and Outlays": "Consumption and saving across the whole sector",
    "Federal Reserve SHED": "What people report about their own finances",
    "BLS Consumer Expenditure Survey": "What each consumer unit spent, by category",
}
CLOCK_COLOR = [ACCENT, OK, WARN, BLOCKED]
CLOCK_WRAP = {
    "BEA Personal Income and Outlays": "BEA Personal Income\nand Outlays",
    "BLS Consumer Expenditure Survey": "BLS Consumer\nExpenditure Survey",
}


def chart_clocks(aspect="16x9"):
    size, margins, fy, _, tfs, tpad, sy, fx = ASPECT[aspect]
    rows = inputs("lag_months")

    fig, ax = plt.subplots(figsize=size)
    m = dict(margins)
    m["left"] = 0.245 if aspect != "16x9" else 0.185
    fig.subplots_adjust(**m)

    ys = list(range(len(rows)))
    for y, r, color in zip(ys, rows, CLOCK_COLOR):
        lag = float(r["value"])
        ax.barh(y, lag, color=color, height=0.32, zorder=3)
        unit = "month" if lag < 1.5 else "months"
        ax.annotate("%s %s" % (("%.1f" % lag).rstrip("0").rstrip("."), unit), (lag, y),
                    xytext=(8, 0), textcoords="offset points", va="center",
                    fontsize=9, color=INK)
        ax.annotate(CLOCK_WHAT[r["label"]], (0.15, y + 0.33), fontsize=7.5,
                    color=MUTED, va="center")

    ax.set_yticks(ys)
    ax.set_yticklabels([CLOCK_WRAP.get(r["label"], r["label"]) for r in rows],
                       fontsize=9, linespacing=1.4)
    ax.invert_yaxis()
    ax.set_xlabel("Age of the newest data on 3 September 2026, from the end of the period it covers (months)",
                  fontsize=8.5, labelpad=8)
    ax.set_xlim(0, 24)
    ax.set_ylim(3.7, -0.7)
    ax.set_title("Four official sources, four different clocks",
                 fontsize=tfs, loc="left", pad=tpad)
    ax.text(0, sy, "Mixing them is where most confusion about household spending starts",
            transform=ax.transAxes, fontsize=8.5, color=MUTED)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="x", color=RULE, lw=0.8, alpha=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", labelsize=8.5)

    footer(fig, "Measured the same way for all four: from the end of the reference period, not the release date.\n"
                "Bromoney, from published release dates and reference periods.", fy, fx)
    save(fig, "four-official-sources-four-clocks" + suffix_for(aspect))


if __name__ == "__main__":
    print("chart 1 — spending vs prices")
    for a in ("16x9", "4x3", "1x1"):
        chart_scatter(a)
    print("chart 2 — quintiles")
    for a in ("16x9", "4x3", "1x1"):
        chart_quintiles(a)
    print("chart 3 — four clocks")
    for a in ("16x9", "4x3", "1x1"):
        chart_clocks(a)
    print("\ndone")
