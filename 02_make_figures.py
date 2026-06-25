#!/usr/bin/env python3
"""
AI investment, EU vs US — STEP 2: figures
=========================================

Reads the tidy CSVs written by 01_collect_data.py and draws every chart into
./figures. It does NO downloading: it only reads ./data and writes ./figures, so
it is fully reproducible offline once step 1 has run. Each chart is skipped (with
a message) if its input CSV is missing.

Charts:
  A   Private AI investment by geography, 2025 (bar)        -> the funding gap
  A2  US vs Europe vs China, 2023-2025 (lines)              -> the gap widening
  B   AI adoption by EU country, latest year (bar)          -> the adoption map
  B2  AI adoption over time, EU-27 + spread (lines)         -> rising off a low base
  B3  AI adoption by firm size, EU-27 (bar)                 -> the SME gap

Run
---
    python 02_make_figures.py
"""

import os
import warnings

warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # no display needed; we save PNGs
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
FIG = os.path.join(HERE, "figures")
os.makedirs(FIG, exist_ok=True)

# Editorial grouping for colour-coding the adoption map (refine before
# publishing). "North-West" = Nordic + Western Europe; everyone else (Southern +
# Eastern, incl. the Baltics) is the other group. Estonia sits in "other" yet
# scores high — a nice exception to point out in the text.
NORTH_WEST = {"DK", "FI", "SE", "BE", "NL", "LU", "AT", "DE", "IE", "FR"}

# Shared palette with the sibling project.
C_US = "#1f4e79"     # United States (dark blue)
C_EU = "#2e86c1"     # EU members (blue)
C_UK = "#e67e22"     # United Kingdom (orange)
C_CN = "#c0392b"     # China (red)
C_OTHER = "#bdc3c7"  # rest of world (grey)
C_KR = "#16a085"     # South Korea (teal)
C_EUR = "#8e44ad"    # "Europe" aggregate (purple, highlight)

EU_MEMBERS = {"Germany", "France", "Netherlands", "Italy", "Poland", "Spain",
              "Belgium", "Sweden", "Denmark", "Finland", "Ireland", "Austria",
              "Luxembourg", "Estonia", "Lithuania", "Cyprus", "Greece",
              "Portugal", "Czech Republic", "Hungary", "Romania", "Bulgaria",
              "Slovakia", "Slovenia", "Croatia", "Latvia", "Malta"}


def _country_color(c):
    """One consistent colour scheme for country/region across all charts."""
    if c == "United States":
        return C_US
    if c == "China":
        return C_CN
    if c == "South Korea":
        return C_KR
    if c == "United Kingdom":
        return C_UK
    if c == "Europe":
        return C_EUR
    if c in EU_MEMBERS:
        return C_EU
    return C_OTHER


plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 150, "font.size": 11,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25,
})


def _read(name):
    """Read a CSV from ./data, or None if it does not exist."""
    p = os.path.join(DATA, name)
    return pd.read_csv(p) if os.path.exists(p) else None


def _spread_labels(items, min_gap):
    """Stop end-of-line labels overlapping: given [(key, y), ...], push values
    upward so consecutive labels are at least `min_gap` apart. Returns {key: y}."""
    out, prev = {}, -1e18
    for k, y in sorted(items, key=lambda t: t[1]):
        y = max(y, prev + min_gap)
        out[k] = y
        prev = y
    return out


# ----------------------------------------------------------------------------
# A) Private AI investment by geography, 2025 (bar)
# ----------------------------------------------------------------------------
def chart_A_investment(by_geo):
    """Horizontal bar of 2025 private AI investment. The US bar runs off the
    field on purpose — that IS the story. EU members, the UK, China and the rest
    are colour-coded so the 'EU vs US vs UK' split is legible despite the scale."""
    df = by_geo.sort_values("investment_usd_bn", ascending=True)
    year = int(df["year"].iloc[0])

    def color(c):
        if c == "United States":
            return C_US
        if c == "United Kingdom":
            return C_UK
        if c == "China":
            return C_CN
        if c in {"France", "Germany", "Belgium", "Sweden", "Netherlands",
                 "Spain", "Italy", "Ireland", "Finland", "Denmark"}:
            return C_EU
        return C_OTHER

    colors = [color(c) for c in df["country"]]
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.barh(df["country"], df["investment_usd_bn"], color=colors)
    for c, v in zip(df["country"], df["investment_usd_bn"]):
        ax.text(v + 3, c, f"{v:,.1f}", va="center", ha="left", fontsize=8.5)
    ax.set_xlim(0, df["investment_usd_bn"].max() * 1.12)
    ax.set_xlabel("Private AI investment (US$ billions)")
    ax.set_title(f"The US doesn't lead AI funding — it laps the field\n"
                 f"Private AI investment by geography, {year}", fontweight="bold")
    # legend via dummy handles
    for lab, col in [("United States", C_US), ("EU member", C_EU),
                     ("United Kingdom", C_UK), ("China", C_CN), ("Other", C_OTHER)]:
        ax.scatter([], [], color=col, marker="s", s=60, label=lab)
    ax.legend(loc="lower right", frameon=True, framealpha=0.9, fontsize=9)
    fig.text(0.01, 0.005, "Source: Stanford HAI AI Index 2026 (data: Quid). "
             "US ≈ 23× China and 48× the UK.", fontsize=7.5, style="italic", color="#555")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "A_investment_by_geo.png"), bbox_inches="tight")
    plt.close(fig)
    print("  saved figures/A_investment_by_geo.png")


# ----------------------------------------------------------------------------
# A2) US vs Europe vs China over time (lines)
# ----------------------------------------------------------------------------
def chart_A2_gap(trend):
    """Three lines, 2023-2025. The US curve goes vertical while Europe and China
    stay pinned near the floor — the gap is widening, not closing."""
    t = trend.sort_values("year")
    fig, ax = plt.subplots(figsize=(8.5, 5.8))
    series = [("United States", C_US), ("Europe", C_EU), ("China", C_CN)]
    last = t["year"].iloc[-1]
    label_y = _spread_labels([(n, float(t[n].iloc[-1])) for n, _ in series],
                             min_gap=t["United States"].max() * 0.07)
    for name, col in series:
        ax.plot(t["year"], t[name], marker="o", lw=2.6, color=col, zorder=5)
        ax.text(last + 0.06, label_y[name], f"{name}\n${t[name].iloc[-1]:,.0f}bn",
                color=col, fontsize=9, va="center", ha="left", fontweight="bold")
    ax.set_xticks(list(t["year"]))
    ax.set_xlim(t["year"].min() - 0.1, t["year"].max() + 0.9)
    ax.set_ylabel("Private AI investment (US$ billions)")
    ax.set_title("The transatlantic AI-funding gap is exploding\n"
                 "Private AI investment, US vs Europe vs China", fontweight="bold")
    fig.text(0.01, -0.01, "Source: Stanford HAI AI Index (2024/25/26). "
             "'Europe' is the AI Index regional line and includes the UK; "
             "pre-2024 is an earlier report vintage.", fontsize=7.5,
             style="italic", color="#555")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "A2_investment_gap.png"), bbox_inches="tight")
    plt.close(fig)
    print("  saved figures/A2_investment_gap.png")


# ----------------------------------------------------------------------------
# B) AI adoption by EU country (bar)
# ----------------------------------------------------------------------------
def chart_B_adoption(by_country):
    """Horizontal bar of AI adoption for every EU member, coloured North-West vs
    the rest, with the EU-27 average marked."""
    df = by_country.copy()
    eu = df.loc[df["geo"] == "EU27_2020", "value"]
    eu_val = float(eu.iloc[0]) if len(eu) else None
    year = int(df["year"].iloc[0])
    df = df[df["geo"].isin(  # members only on the bars; aggregates become a line
        set(by_country["geo"]) - {"EU27_2020", "EA"})]
    df = df.sort_values("value", ascending=True)
    colors = [C_EU if g in NORTH_WEST else C_CN for g in df["geo"]]

    fig, ax = plt.subplots(figsize=(8, 8.5))
    ax.barh(df["geo"], df["value"], color=colors)
    for g, v in zip(df["geo"], df["value"]):
        ax.text(v + 0.4, g, f"{v:.0f}", va="center", ha="left", fontsize=8)
    if eu_val is not None:
        # zorder 2 keeps the reference line above the bars but BELOW the value
        # labels (text zorder 3), so it never obscures a number
        ax.axvline(eu_val, color="#34495e", ls="--", lw=1.3, zorder=2)
        # label sits in the empty space to the right of the line, low down
        # (short bars there), so it never touches a bar
        ax.text(eu_val + 0.5, 3.0, f"EU-27\navg {eu_val:.1f}%", color="#34495e",
                fontsize=8.5, va="center", ha="left", fontweight="bold")
    ax.set_xlabel(f"Enterprises using ≥1 AI technology, {year} (% of firms, 10+ employed)")
    ax.set_title(f"Who actually uses AI? A north–south, west–east split\n"
                 f"AI adoption by EU country, {year}", fontweight="bold")
    ax.scatter([], [], color=C_EU, marker="s", s=60, label="Nordic & Western Europe")
    ax.scatter([], [], color=C_CN, marker="s", s=60, label="Southern & Eastern Europe")
    ax.legend(loc="lower right", frameon=True, framealpha=0.9, fontsize=9)
    fig.text(0.01, 0.005, "Source: Eurostat isoc_eb_ai (E_AI_TANY). "
             "Estonia (EE) sits in the East yet scores high.", fontsize=7.5,
             style="italic", color="#555")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "B_adoption_by_country.png"), bbox_inches="tight")
    plt.close(fig)
    print("  saved figures/B_adoption_by_country.png")


# ----------------------------------------------------------------------------
# B2) AI adoption over time (lines)
# ----------------------------------------------------------------------------
def chart_B2_trend(trend):
    """EU-27 (thick) plus a country spread. The 2023->2024 step is partly a
    survey-definition change, so it is shaded and annotated."""
    fig, ax = plt.subplots(figsize=(9, 5.8))
    palette = {"EU27_2020": "#111111", "DK": C_US, "SE": "#16a085", "DE": C_EU,
               "ES": "#8e44ad", "FR": "#2980b9", "IT": "#d35400",
               "PL": "#c0392b", "RO": "#7f8c8d"}
    ends = []  # (geo, last_value) for decluttered end labels
    for geo, d in trend.groupby("geo"):
        d = d.sort_values("year")
        is_eu = geo == "EU27_2020"
        ax.plot(d["year"], d["value"], marker="o", ms=4,
                lw=3.2 if is_eu else 1.6,
                color=palette.get(geo, "#999"), zorder=6 if is_eu else 4)
        ends.append((geo, float(d["value"].iloc[-1])))

    last = max(trend["year"])
    label_y = _spread_labels(ends, min_gap=(trend["value"].max() * 0.032))
    for geo, _ in ends:
        is_eu = geo == "EU27_2020"
        ax.text(last + 0.08, label_y[geo], "EU-27" if is_eu else geo,
                fontsize=8.5, va="center", color=palette.get(geo, "#999"),
                fontweight="bold" if is_eu else "normal")

    # mark the 2023->2024 definition break
    ax.axvspan(2023, 2024, color="#5d6d7e", alpha=0.08, zorder=0)
    ax.text(2023.5, ax.get_ylim()[1] * 0.98, "survey definition\nbroadened",
            ha="center", va="top", fontsize=7.5, color="#5d6d7e")

    years = sorted(trend["year"].unique())
    ax.set_xticks(years)
    ax.set_xlim(min(years) - 0.1, max(years) + 0.8)
    ax.set_ylabel("Enterprises using ≥1 AI technology (% of firms, 10+)")
    ax.set_title("AI adoption is climbing fast — but off a low base\n"
                 "Share of EU enterprises using AI", fontweight="bold")
    fig.text(0.01, -0.01, "Source: Eurostat isoc_eb_ai (E_AI_TANY, 10+ employed). "
             "The 2023→2024 jump is partly a definition change; 2024→2025 is clean.",
             fontsize=7.5, style="italic", color="#555")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "B2_adoption_trend.png"), bbox_inches="tight")
    plt.close(fig)
    print("  saved figures/B2_adoption_trend.png")


# ----------------------------------------------------------------------------
# B3) AI adoption by firm size (bar)
# ----------------------------------------------------------------------------
def chart_B3_firmsize(fs):
    labels = {"10-49": "Small\n(10–49)", "50-249": "Medium\n(50–249)",
              "GE250": "Large\n(250+)"}
    fs = fs.copy()
    fs["lab"] = fs["size_emp"].map(labels).fillna(fs["size_emp"])
    year = int(fs["year"].iloc[0])
    colors = ["#aed6f1", "#5dade2", C_US]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.bar(fs["lab"], fs["value"], color=colors[:len(fs)])
    for i, v in enumerate(fs["value"]):
        ax.text(i, v + 0.7, f"{v:.0f}%", ha="center", fontsize=10, fontweight="bold")
    ratio = fs["value"].max() / fs["value"].min()
    ax.set_ylabel("Enterprises using ≥1 AI technology (%)")
    ax.set_ylim(0, fs["value"].max() * 1.15)
    ax.set_title(f"AI is still a big-firm technology\n"
                 f"EU-27 AI adoption by firm size, {year} "
                 f"(large firms ≈ {ratio:.0f}× small)", fontweight="bold")
    fig.text(0.01, -0.01, "Source: Eurostat isoc_eb_ai (E_AI_TANY).",
             fontsize=7.5, style="italic", color="#555")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "B3_adoption_by_firmsize.png"), bbox_inches="tight")
    plt.close(fig)
    print("  saved figures/B3_adoption_by_firmsize.png")


# ----------------------------------------------------------------------------
# C) The production gap: notable AI models by country
# ----------------------------------------------------------------------------
def chart_C_models(df):
    df = df.sort_values("models", ascending=True)
    year = int(df["year"].iloc[0])
    colors = [_country_color(c) for c in df["country"]]
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    ax.barh(df["country"], df["models"], color=colors)
    for c, v in zip(df["country"], df["models"]):
        ax.text(v + 0.6, c, f"{v}", va="center", ha="left", fontsize=9, fontweight="bold")
    ax.set_xlim(0, df["models"].max() * 1.10)
    ax.set_xlabel(f"Notable AI models released, {year}")
    ax.set_title("Europe barely builds frontier AI\n"
                 f"Notable AI models by country, {year}", fontweight="bold")
    # callout sits on the Europe row, well clear of the "2" value label, with a
    # left-arrow glyph instead of a drawn line (so nothing crosses the number)
    ax.text(4.5, "Europe", "←  all of Europe", color=C_EUR, fontsize=9.5,
            fontweight="bold", va="center", ha="left")
    fig.text(0.01, 0.005, "Source: Epoch AI via Stanford AI Index 2026 (Fig 1.1.1–1.1.2). "
             "US \\$286bn buys 59 models; Europe's ~\\$21bn, 2.", fontsize=7.5,
             style="italic", color="#555")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "C_models_by_country.png"), bbox_inches="tight")
    plt.close(fig)
    print("  saved figures/C_models_by_country.png")


# ----------------------------------------------------------------------------
# C2) Who builds the models: top developers by organization, coloured by origin
# ----------------------------------------------------------------------------
def chart_C2_developers(df):
    df = df.sort_values("models", ascending=True)
    colors = [_country_color(c) for c in df["country"]]
    fig, ax = plt.subplots(figsize=(8.5, 8))
    ax.barh(df["organization"], df["models"], color=colors)
    for o, v in zip(df["organization"], df["models"]):
        ax.text(v + 0.2, o, f"{v}", va="center", ha="left", fontsize=8)
    ax.set_xlim(0, df["models"].max() * 1.12)
    ax.set_xlabel("Notable AI models released, 2025")
    ax.set_title("The companies building AI are American or Chinese — none European\n"
                 "Top AI model developers by organization, 2025", fontweight="bold")
    for lab, col in [("United States", C_US), ("China", C_CN), ("South Korea", C_KR)]:
        ax.scatter([], [], color=col, marker="s", s=60, label=lab)
    ax.legend(loc="lower right", frameon=True, framealpha=0.9, fontsize=9)
    fig.text(0.01, 0.005, "Source: Epoch AI via Stanford AI Index 2026 (Fig 1.1.6). "
             "DeepMind counted under Google. No EU firm in the top 20.",
             fontsize=7.5, style="italic", color="#555")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "C2_developers_by_origin.png"), bbox_inches="tight")
    plt.close(fig)
    print("  saved figures/C2_developers_by_origin.png")


# ----------------------------------------------------------------------------
# D) Europe's paradox: strong in research, absent in production
# ----------------------------------------------------------------------------
def chart_D_paradox(df):
    df = df.sort_values("europe_share_pct", ascending=True)
    colors = [C_EU if k == "research" else C_CN for k in df["kind"]]
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    ax.barh(df["stage"], df["europe_share_pct"], color=colors)
    for s, v in zip(df["stage"], df["europe_share_pct"]):
        ax.text(v + 0.3, s, f"{v:.1f}%", va="center", ha="left", fontsize=9, fontweight="bold")
    ax.set_xlim(0, max(df["europe_share_pct"]) * 1.18)
    ax.set_xlabel("Europe's share of the global total (%)")
    ax.set_title("Europe's paradox: it does the science, not the product\n"
                 "Europe's share of the global AI pipeline", fontweight="bold")
    ax.scatter([], [], color=C_EU, marker="s", s=60, label="Research (upstream)")
    ax.scatter([], [], color=C_CN, marker="s", s=60, label="Production (downstream)")
    ax.legend(loc="lower right", frameon=True, framealpha=0.9, fontsize=9)
    fig.text(0.01, -0.01, "Source: Stanford AI Index 2026 — citations Fig 1.6.7, "
             "publications 1.6.6, patents 1.7.2/1.7.5, models 1.1.2.",
             fontsize=7.5, style="italic", color="#555")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "D_europe_paradox.png"), bbox_inches="tight")
    plt.close(fig)
    print("  saved figures/D_europe_paradox.png")


# ----------------------------------------------------------------------------
# E) AI's physical backbone: data centers by country
# ----------------------------------------------------------------------------
def chart_E_datacenters(df):
    df = df.sort_values("datacenters", ascending=True)
    year = int(df["year"].iloc[0])
    colors = [_country_color(c) for c in df["country"]]
    fig, ax = plt.subplots(figsize=(9, 6.5))
    ax.barh(df["country"], df["datacenters"], color=colors)
    for c, v in zip(df["country"], df["datacenters"]):
        ax.text(v + 50, c, f"{v:,}", va="center", ha="left", fontsize=8.5)
    ax.set_xlim(0, df["datacenters"].max() * 1.12)
    ax.set_xlabel(f"Number of data centers, {year}")
    ax.set_title("AI's physical backbone is overwhelmingly American\n"
                 f"Data centers by country, {year}", fontweight="bold")
    for lab, col in [("United States", C_US), ("EU member", C_EU),
                     ("United Kingdom", C_UK), ("China", C_CN), ("Other", C_OTHER)]:
        ax.scatter([], [], color=col, marker="s", s=55, label=lab)
    ax.legend(loc="lower right", frameon=True, framealpha=0.9, fontsize=8.5)
    fig.text(0.01, 0.005, "Source: Cloudscene via Stanford AI Index 2026 (Fig 1.3.2). "
             "Ownership of the stack is also non-European: chips designed by Nvidia (US), "
             "fabricated by TSMC (Taiwan), memory by SK Hynix/Samsung (Korea).",
             fontsize=7.0, style="italic", color="#555")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "E_datacenters_by_country.png"), bbox_inches="tight")
    plt.close(fig)
    print("  saved figures/E_datacenters_by_country.png")


# ----------------------------------------------------------------------------
# F) Public money too: government AI spending, US vs Europe
# ----------------------------------------------------------------------------
def chart_F_public(df):
    # Two stacked bars (US by instrument, Europe by country); both sum to the
    # region total. Segment labels go to the RIGHT of each bar (never on the
    # bars, never on each other) so nothing is obscured. Bars spaced wide so the
    # US labels can't reach the Europe bar.
    fig, ax = plt.subplots(figsize=(8.4, 5.8))
    specs = [
        ("United States", 0.0, [("Grants", C_US), ("Contracts", "#2e86c1"),
                                 ("OTAs", "#85c1e9")]),
        ("Europe", 2.0, [("United Kingdom", "#1e8449"), ("Germany", "#27ae60"),
                         ("France", "#52be80"), ("Other Europe", "#a9dfbf")]),
    ]
    totals = []
    for region, x, segs in specs:
        sub = df[df["region"] == region].set_index("category")["usd_bn"]
        bottom = 0.0
        centers = []
        for cat, col in segs:
            v = float(sub.get(cat, 0.0))
            ax.bar(x, v, bottom=bottom, color=col, width=0.6, zorder=3)
            centers.append((f"{cat}  {v:.2f}", bottom + v / 2))
            bottom += v
        totals.append(bottom)
        ys = _spread_labels(centers, min_gap=max(totals) * 0.052)
        for lab, y in ys.items():
            ax.text(x + 0.34, y, lab, va="center", ha="left", fontsize=8, color="#222")
        ax.text(x, bottom + max(totals) * 0.03, f"${bottom:.1f}bn",
                ha="center", va="bottom", fontsize=11, fontweight="bold")

    ax.set_xticks([0.0, 2.0])
    ax.set_xticklabels(["United States", "Europe"])
    ax.set_xlim(-0.6, 3.3)
    ax.set_ylabel("Cumulative public AI spending, 2013–24 (US$bn)")
    ax.set_ylim(0, max(totals) * 1.15)
    ax.set_title("Even public money flows mostly to US AI\n"
                 "Government AI spending, US vs Europe (2013–24)", fontweight="bold")
    fig.text(0.01, -0.02, "Source: Stanford AI Index 2026 (Fig 8.5.1/8.5.8). "
             "Measured differently (US: FPDS contracts+OTAs+grants; Europe: TED contract "
             "ceilings) — like-for-like contracts are US ~\\$4.6bn vs Europe ~\\$3.7bn.",
             fontsize=7.0, style="italic", color="#555")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "F_public_investment.png"), bbox_inches="tight")
    plt.close(fig)
    print("  saved figures/F_public_investment.png")


# ----------------------------------------------------------------------------
# G) AI talent: Europe is a weak magnet (the "brain drain" question)
# ----------------------------------------------------------------------------
def chart_G_talent(df):
    df = df.sort_values("net_per_10k", ascending=True)
    colors = [_country_color(c) for c in df["country"]]
    fig, ax = plt.subplots(figsize=(8.5, 6.5))
    ax.barh(df["country"], df["net_per_10k"], color=colors)
    for c, v in zip(df["country"], df["net_per_10k"]):
        ax.text(v + 0.06, c, f"+{v:.2f}", va="center", ha="left", fontsize=8)
    ax.set_xlim(0, df["net_per_10k"].max() * 1.15)
    ax.set_xlabel("Net AI talent migration, 2025 (per 10,000 LinkedIn members)")
    ax.set_title("Europe's big economies barely attract AI talent\n"
                 "Net AI talent inflow, 2025 (top 15)", fontweight="bold")
    # callout in clear space beside the bottom (big-EU) bars; no drawn line, so
    # it never crosses a value label
    ax.text(1.5, "Denmark", "major EU economies (DE, ES)\nbarely attract talent",
            color="#c0392b", fontsize=8.5, va="center", ha="left")
    fig.text(0.01, 0.005, "Source: LinkedIn via Stanford AI Index 2026 (Fig 4.4.23). "
             "The US still imports talent but its inflow fell 89% since 2017; Europe holds "
             "talent (Ireland, Finland, Estonia, Germany rank high on concentration) yet attracts little.",
             fontsize=7.0, style="italic", color="#555")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "G_talent_migration.png"), bbox_inches="tight")
    plt.close(fig)
    print("  saved figures/G_talent_migration.png")


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    print("=" * 64)
    print("STEP 2 — drawing figures into ./figures (reads ./data)")
    print("=" * 64)

    print("\n[A] Private AI investment by geography (bar) ...")
    try:
        by_geo = _read("ai_investment_by_geo.csv")
        if by_geo is None:
            print("  SKIPPED: ai_investment_by_geo.csv missing.")
        else:
            chart_A_investment(by_geo)
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[A2] US vs Europe vs China over time (lines) ...")
    try:
        trend = _read("ai_investment_us_eu_cn.csv")
        if trend is None:
            print("  SKIPPED: ai_investment_us_eu_cn.csv missing.")
        else:
            chart_A2_gap(trend)
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[B] AI adoption by EU country (bar) ...")
    try:
        by_country = _read("ai_adoption_by_country.csv")
        if by_country is None:
            print("  SKIPPED: ai_adoption_by_country.csv missing.")
        else:
            chart_B_adoption(by_country)
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[B2] AI adoption over time (lines) ...")
    try:
        trend = _read("ai_adoption_trend.csv")
        if trend is None:
            print("  SKIPPED: ai_adoption_trend.csv missing.")
        else:
            chart_B2_trend(trend)
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[B3] AI adoption by firm size (bar) ...")
    try:
        fs = _read("ai_adoption_by_firmsize.csv")
        if fs is None:
            print("  SKIPPED: ai_adoption_by_firmsize.csv missing.")
        else:
            chart_B3_firmsize(fs)
    except Exception as e:
        print(f"  FAILED: {e}")

    for tag, fname, fn in [
        ("C", "ai_models_by_country.csv", chart_C_models),
        ("C2", "ai_models_by_org.csv", chart_C2_developers),
        ("D", "europe_share_pipeline.csv", chart_D_paradox),
        ("E", "datacenters_by_country.csv", chart_E_datacenters),
        ("F", "public_ai_investment.csv", chart_F_public),
        ("G", "talent_net_migration.csv", chart_G_talent),
    ]:
        print(f"\n[{tag}] {fn.__name__} ...")
        try:
            d = _read(fname)
            if d is None:
                print(f"  SKIPPED: {fname} missing.")
            else:
                fn(d)
        except Exception as e:
            print(f"  FAILED: {e}")

    print("\nDone. See ./figures")


if __name__ == "__main__":
    main()
