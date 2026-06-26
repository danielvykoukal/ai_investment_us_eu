#!/usr/bin/env python3
"""
AI investment, EU vs US — STEP 1: data collection
==================================================

Pulls and cleans every series the project needs and writes tidy CSVs to ./data.
It produces NO plots — that is 02_make_figures.py. Run this first.

The story has two halves (the "adopt vs. fund" angle):
  - ADOPTION  : how widely EU firms USE AI         -> Eurostat, pulled LIVE
  - INVESTMENT: how much money REGIONS put into AI -> Stanford AI Index figures

Sources
-------
  - Eurostat `isoc_eb_ai` (AI by size class of enterprise). Live, keyless pull
    via the `eurostat` package. Indicator E_AI_TANY = enterprises using at least
    one AI technology; unit PC_ENT (% of enterprises); size GE10 (10+ employed).
  - Stanford HAI AI Index — private AI investment by geography (underlying data:
    Quid). These are NOT available via a free API, so the figures are read from
    the report PDFs and hardcoded below WITH their figure numbers. They are the
    one set of "verify before publishing" numbers in this project (same pattern
    as ECB CES figures in the sibling precautionary-savings project).

Outputs (./data/*.csv)
----------------------
  ai_adoption_by_country.csv     ai_adoption_trend.csv
  ai_adoption_by_firmsize.csv    ai_investment_by_geo.csv
  ai_investment_us_eu_cn.csv     ai_investment_cumulative.csv
  ai_investment_genai.csv

Run
---
    pip install -r requirements.txt
    python 01_collect_data.py

Notes
-----
- Eurostat is pulled via the `eurostat` package (keyless). Each section is
  wrapped in try/except: if a source is down or a dataset code changes, the rest
  still run and any CSV from a previous run is left untouched.
- The latest available survey year is detected automatically, so the country
  bar and firm-size split track the newest Eurostat release without edits.
"""

import os
import re
import sys
import warnings

warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np

try:
    import eurostat
except ImportError:
    sys.exit("Missing 'eurostat'. Run: pip install -r requirements.txt")

# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)

# The 27 EU member states (Eurostat geo codes; EL = Greece).
EU27 = ["BE", "BG", "CZ", "DK", "DE", "EE", "IE", "EL", "ES", "FR", "HR", "IT",
        "CY", "LV", "LT", "LU", "HU", "MT", "NL", "AT", "PL", "PT", "RO", "SI",
        "SK", "FI", "SE"]

# Lines to draw on the adoption trend chart (EU aggregate + a readable spread).
TREND_GEOS = ["EU27_2020", "DK", "SE", "DE", "ES", "FR", "IT", "PL", "RO"]

# isoc_eb_ai dimension selections
AI_INDIC = "E_AI_TANY"          # enterprises using >=1 AI technology
AI_UNIT = "PC_ENT"              # percentage of enterprises
AI_SIZE_ALL = "GE10"            # 10 persons employed or more (headline size)
AI_NACE = "C10-S951_X_K"        # all activities (the only nace value in the set)
FIRM_SIZES = ["10-49", "50-249", "GE250"]   # small / medium / large


# ----------------------------------------------------------------------------
# Eurostat helpers (shared conventions with the sibling project)
# ----------------------------------------------------------------------------
def es_long(code):
    """Fetch a Eurostat dataset and return it tidy: dimension cols + time + value."""
    df = eurostat.get_data_df(code)
    if df is None or df.empty:
        raise RuntimeError(f"Eurostat returned nothing for {code}")
    geo_col = next((c for c in df.columns if "geo" in c.lower()), None)
    if geo_col:
        df = df.rename(columns={geo_col: "geo"})
    time_cols = [c for c in df.columns if re.match(r"^\d{4}", str(c))]
    id_cols = [c for c in df.columns if c not in time_cols]
    long = df.melt(id_vars=id_cols, value_vars=time_cols,
                   var_name="time", value_name="value")
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long = long.dropna(subset=["value"])
    long["year"] = long["time"].astype(str).str.extract(r"(\d{4})").astype(int)
    return long


def show_dims(long, code, dims):
    """Print available codes for given dimensions to help debugging filters."""
    print(f"  [{code}] dimension values:")
    for d in dims:
        if d in long.columns:
            vals = sorted(str(v) for v in long[d].dropna().unique())[:25]
            print(f"    {d}: {vals}")


def _ai_base(long):
    """Restrict isoc_eb_ai to the headline AI indicator + unit (+ nace if present)."""
    sub = long[(long["indic_is"] == AI_INDIC) & (long["unit"] == AI_UNIT)].copy()
    if "nace_r2" in sub.columns and AI_NACE in set(sub["nace_r2"]):
        sub = sub[sub["nace_r2"] == AI_NACE]
    if sub.empty:
        raise RuntimeError(f"isoc_eb_ai: no rows for indic_is={AI_INDIC}, unit={AI_UNIT}")
    return sub


# ----------------------------------------------------------------------------
# 1) ADOPTION — Eurostat isoc_eb_ai (live)
# ----------------------------------------------------------------------------
def get_adoption_by_country():
    """Latest-year AI adoption (% of enterprises, 10+) for every EU member,
    plus the EU-27 and euro-area aggregates. -> ai_adoption_by_country.csv"""
    long = es_long("isoc_eb_ai")
    show_dims(long, "isoc_eb_ai", ["indic_is", "unit", "size_emp", "nace_r2"])
    sub = _ai_base(long)
    sub = sub[sub["size_emp"] == AI_SIZE_ALL]
    latest = int(sub["year"].max())
    keep = set(EU27) | {"EU27_2020", "EA"}
    out = (sub[(sub["year"] == latest) & (sub["geo"].isin(keep))]
           .groupby("geo", as_index=False)["value"].mean())
    out["year"] = latest
    out = out.sort_values("value", ascending=False)
    out.to_csv(os.path.join(DATA, "ai_adoption_by_country.csv"), index=False)
    print(f"  adoption by country: {len(out)} geos, year={latest}, "
          f"EU-27={out.loc[out['geo']=='EU27_2020','value'].squeeze():.1f}%")
    return out


def get_adoption_trend():
    """AI adoption over time for the EU-27 + a readable country spread.
    -> ai_adoption_trend.csv  (long: geo, year, value)"""
    long = es_long("isoc_eb_ai")
    sub = _ai_base(long)
    sub = sub[(sub["size_emp"] == AI_SIZE_ALL) & (sub["geo"].isin(TREND_GEOS))]
    out = (sub.groupby(["geo", "year"], as_index=False)["value"].mean()
           .sort_values(["geo", "year"]))
    out.to_csv(os.path.join(DATA, "ai_adoption_trend.csv"), index=False)
    yrs = sorted(out["year"].unique())
    print(f"  adoption trend: {out['geo'].nunique()} geos, years {yrs}")
    return out


def get_adoption_by_firmsize():
    """Latest-year EU-27 AI adoption by firm-size class (the SME gap).
    -> ai_adoption_by_firmsize.csv"""
    long = es_long("isoc_eb_ai")
    sub = _ai_base(long)
    sub = sub[(sub["geo"] == "EU27_2020") & (sub["size_emp"].isin(FIRM_SIZES))]
    latest = int(sub["year"].max())
    out = (sub[sub["year"] == latest]
           .groupby("size_emp", as_index=False)["value"].mean())
    order = {s: i for i, s in enumerate(FIRM_SIZES)}
    out = out.sort_values("size_emp", key=lambda s: s.map(order))
    out["year"] = latest
    out.to_csv(os.path.join(DATA, "ai_adoption_by_firmsize.csv"), index=False)
    print(f"  adoption by firm size (EU-27, {latest}): "
          + ", ".join(f"{r.size_emp}={r.value:.1f}%" for r in out.itertuples()))
    return out


# ----------------------------------------------------------------------------
# 2) INVESTMENT — Stanford HAI AI Index (hardcoded; VERIFY before publishing)
#    No free API exists (underlying data is Quid). Values are read from the
#    report PDFs; figure numbers given so each can be re-checked / refreshed.
#    $ = current USD billions, private investment.
# ----------------------------------------------------------------------------
# Global private AI investment by geography, 2025 (AI Index 2026, Fig 4.2.8)
INVEST_BY_GEO_2025 = {
    "United States": 285.88, "China": 12.41, "United Kingdom": 5.90,
    "France": 4.36, "Canada": 4.28, "India": 4.09, "Germany": 3.89,
    "Israel": 3.58, "Australia": 2.52, "Saudi Arabia": 2.03,
    "Singapore": 1.82, "South Korea": 1.78, "Belgium": 1.20,
    "Japan": 1.11, "Sweden": 0.97,
}

# US vs Europe vs China over time. "Europe" is the AI Index regional line and
# INCLUDES THE UK (the 2024 report labelled it "European Union and United
# Kingdom"; 2025/26 relabel it "Europe"). Each row tagged with its source
# vintage because Quid revises back-data between reports.
#   year, US, Europe, China, source
INVEST_US_EU_CN = [
    (2023, 67.22, 11.00, 7.76, "AI Index 2024, Fig 4.3.10 (line: EU+UK)"),
    (2024, 109.08, 19.42, 9.29, "AI Index 2025, Fig 4.3.10 (line: Europe)"),
    (2025, 285.88, 20.92, 12.41, "AI Index 2026, Fig 4.2.11 (line: Europe)"),
]

# Cumulative private AI investment, 2013-2025 sum (AI Index 2026, Fig 4.2.12)
INVEST_CUMULATIVE = {
    "United States": 757.27, "China": 131.83, "United Kingdom": 34.07,
    "Canada": 19.59, "Israel": 18.54, "Germany": 17.16, "France": 15.57,
    "India": 15.39,
}

# Generative-AI private investment, 2025 endpoint (AI Index 2026, Fig 4.2.10)
INVEST_GENAI_2025 = {
    "United States": 163.64, "Europe": 3.21, "China": 1.48,
}


def write_investment_csvs():
    """Materialise the AI Index figures above into tidy CSVs."""
    by_geo = (pd.DataFrame({"country": list(INVEST_BY_GEO_2025),
                            "investment_usd_bn": list(INVEST_BY_GEO_2025.values())})
              .sort_values("investment_usd_bn", ascending=False))
    by_geo["year"] = 2025
    by_geo.to_csv(os.path.join(DATA, "ai_investment_by_geo.csv"), index=False)

    trend = pd.DataFrame(INVEST_US_EU_CN,
                         columns=["year", "United States", "Europe", "China", "source"])
    trend.to_csv(os.path.join(DATA, "ai_investment_us_eu_cn.csv"), index=False)

    cum = (pd.DataFrame({"country": list(INVEST_CUMULATIVE),
                         "cumulative_usd_bn": list(INVEST_CUMULATIVE.values())})
           .sort_values("cumulative_usd_bn", ascending=False))
    cum.to_csv(os.path.join(DATA, "ai_investment_cumulative.csv"), index=False)

    genai = pd.DataFrame({"region": list(INVEST_GENAI_2025),
                          "genai_usd_bn": list(INVEST_GENAI_2025.values()),
                          "year": 2025})
    genai.to_csv(os.path.join(DATA, "ai_investment_genai.csv"), index=False)

    print("  wrote 4 investment CSVs from AI Index figures (VERIFY before publishing)")
    print(f"    2025: US ${INVEST_BY_GEO_2025['United States']:.1f}bn vs "
          f"Europe ${INVEST_US_EU_CN[-1][2]:.1f}bn vs China ${INVEST_BY_GEO_2025['China']:.1f}bn")
    return by_geo, trend, cum, genai


# ----------------------------------------------------------------------------
# 3) PRODUCTION, INFRASTRUCTURE, RESEARCH, PUBLIC MONEY & TALENT
#    All from the Stanford AI Index 2026 full report (hardcoded; VERIFY).
#    These build out the "Europe researches & uses AI but doesn't build/fund it"
#    story. Figure numbers given so each can be re-checked / refreshed.
# ----------------------------------------------------------------------------
# Notable AI models by national affiliation, 2025 (Epoch AI; Fig 1.1.1/1.1.2).
# The "Europe" regional line in Fig 1.1.2 = 2 models in 2025.
MODELS_BY_COUNTRY_2025 = {
    "United States": 59, "China": 35, "South Korea": 8, "Europe": 2,
    "Canada": 1, "Singapore": 1, "Hong Kong": 1,
}

# Notable AI models by organization, 2025 (Fig 1.1.6) -> the massive AI
# developers and where they are from. DeepMind is counted under Google.
#   (organization, models, country)
MODELS_BY_ORG_2025 = [
    ("OpenAI", 20, "United States"), ("Google", 14, "United States"),
    ("Alibaba", 11, "China"), ("Anthropic", 7, "United States"),
    ("xAI", 5, "United States"), ("DeepSeek", 4, "China"),
    ("LG AI Research", 4, "South Korea"), ("Meta", 4, "United States"),
    ("Tsinghua University", 4, "China"), ("ByteDance", 3, "China"),
    ("Moonshot", 3, "China"), ("Nvidia", 3, "United States"),
    ("University of Illinois", 3, "United States"), ("Z.ai (Zhipu AI)", 3, "China"),
    ("MiniMax", 2, "China"), ("Shanghai AI Lab", 2, "China"),
    ("Allen Institute for AI", 1, "United States"), ("Ant Group", 1, "China"),
    ("Baidu", 1, "China"), ("CUHK Shenzhen", 1, "China"),
]

# Europe's PARADOX: its share of the global AI pipeline, research -> production.
# Europe is strong in science, near-absent downstream. (stage, %, kind, source)
EUROPE_SHARE_PIPELINE = [
    ("Research citations", 19.5, "research", "Fig 1.6.7 (2024)"),
    ("Research publications", 11.1, "research", "Fig 1.6.6 (2024)"),
    ("Patent citations", 4.2, "production", "Fig 1.7.5 (2010-24)"),
    ("Patents granted", 3.0, "production", "Fig 1.7.2 (2024)"),
    ("Notable AI models", 2.0, "production", "Fig 1.1.2 (2025; 2 of 102)"),
]

# AI research output by region (supports "AI research is big in Europe").
#   region, publications %, citations %   (2024; Fig 1.6.6 / 1.6.7)
RESEARCH_BY_REGION = [
    ("China", 17.8, 20.6), ("Europe", 11.1, 19.5), ("United States", None, 12.6),
    ("India", 7.6, None),
]

# Data centers by country, 2025 (Cloudscene; Fig 1.3.2) -> infrastructure location.
DATACENTERS_2025 = {
    "United States": 5427, "Germany": 529, "United Kingdom": 523, "China": 449,
    "Canada": 337, "France": 322, "Australia": 314, "Netherlands": 298,
    "Russia": 251, "Japan": 222, "Brazil": 197, "Mexico": 173, "Italy": 168,
    "India": 153, "Poland": 144,
}

# Public (government) AI spending, cumulative 2013-24, US$bn.
# NOTE: US and Europe measured differently (US: contracts+OTAs+grants from FPDS;
# Europe: awarded contract ceilings from TED). The report presents them
# SEPARATELY; the only like-for-like comparison is contracts(+OTAs).
PUBLIC_AI_US = {"Grants": 15.9, "Contracts": 3.9, "OTAs": 0.7}          # Fig 8.5.1/8.5.3
PUBLIC_AI_EUROPE = {"United Kingdom": 1.6, "Germany": 0.505, "France": 0.320,
                    "Other Europe": 1.275}                              # Fig 8.5.8 (sum ~3.7)

# AI talent (LinkedIn, 2025). Concentration = % of members; migration = net per 10k.
TALENT_CONCENTRATION_2025 = {  # Fig 4.4.21 (top 15)
    "Israel": 2.10, "Singapore": 1.82, "Luxembourg": 1.60, "Ireland": 1.31,
    "Switzerland": 1.25, "Finland": 1.23, "Estonia": 1.15, "Germany": 1.15,
    "Netherlands": 1.10, "Lithuania": 1.05, "South Korea": 1.05, "India": 1.01,
    "Canada": 1.01, "Poland": 1.00, "Cyprus": 0.95,
}
TALENT_NET_MIGRATION_2025 = {  # Fig 4.4.23 (top 15 net inflows), per 10k members
    "Luxembourg": 5.23, "United Arab Emirates": 4.40, "Australia": 1.79,
    "Saudi Arabia": 1.77, "Switzerland": 1.72, "Singapore": 1.36, "Canada": 1.23,
    "United States": 1.22, "Hong Kong": 1.14, "United Kingdom": 1.04,
    "Austria": 0.90, "Cyprus": 0.62, "Denmark": 0.45, "Spain": 0.23, "Germany": 0.17,
}

# Organisational AI adoption by region (McKinsey via AI Index 2026, Fig 4.3.2):
# % of respondents whose organisation uses AI in >=1 business function.
# Europe leads the world at 91% in 2025. NOTE: a broad, self-reported measure of
# (mostly large) organisations -- NOT comparable to Eurostat's firm-level
# adoption (~20%); the two are cited separately.
#   region, 2023, 2024, 2025
ORG_ADOPTION_BY_REGION = [
    ("All geographies", 55, 78, 88),
    ("Asia-Pacific", 58, 72, 82),
    ("Europe", 57, 80, 91),
    ("North America", 61, 82, 90),
    ("Greater China", 48, 75, 88),
    ("Developing markets", 49, 77, 88),
]


def write_aiindex_extras():
    """Materialise the production/infrastructure/research/public/talent figures."""
    pd.DataFrame({"country": list(MODELS_BY_COUNTRY_2025),
                  "models": list(MODELS_BY_COUNTRY_2025.values()), "year": 2025}) \
      .to_csv(os.path.join(DATA, "ai_models_by_country.csv"), index=False)

    pd.DataFrame(MODELS_BY_ORG_2025, columns=["organization", "models", "country"]) \
      .to_csv(os.path.join(DATA, "ai_models_by_org.csv"), index=False)

    pd.DataFrame(EUROPE_SHARE_PIPELINE,
                 columns=["stage", "europe_share_pct", "kind", "source"]) \
      .to_csv(os.path.join(DATA, "europe_share_pipeline.csv"), index=False)

    pd.DataFrame(RESEARCH_BY_REGION,
                 columns=["region", "publications_pct", "citations_pct"]) \
      .to_csv(os.path.join(DATA, "research_by_region.csv"), index=False)

    pd.DataFrame({"country": list(DATACENTERS_2025),
                  "datacenters": list(DATACENTERS_2025.values()), "year": 2025}) \
      .to_csv(os.path.join(DATA, "datacenters_by_country.csv"), index=False)

    rows = [("United States", k, v) for k, v in PUBLIC_AI_US.items()] \
         + [("Europe", k, v) for k, v in PUBLIC_AI_EUROPE.items()]
    pd.DataFrame(rows, columns=["region", "category", "usd_bn"]) \
      .to_csv(os.path.join(DATA, "public_ai_investment.csv"), index=False)

    pd.DataFrame({"country": list(TALENT_CONCENTRATION_2025),
                  "concentration_pct": list(TALENT_CONCENTRATION_2025.values())}) \
      .to_csv(os.path.join(DATA, "talent_concentration.csv"), index=False)
    pd.DataFrame({"country": list(TALENT_NET_MIGRATION_2025),
                  "net_per_10k": list(TALENT_NET_MIGRATION_2025.values())}) \
      .to_csv(os.path.join(DATA, "talent_net_migration.csv"), index=False)

    pd.DataFrame(ORG_ADOPTION_BY_REGION, columns=["region", "2023", "2024", "2025"]) \
      .to_csv(os.path.join(DATA, "org_adoption_by_region.csv"), index=False)

    us_models = sum(v for _, v, c in MODELS_BY_ORG_2025 if c == "United States")
    cn_models = sum(v for _, v, c in MODELS_BY_ORG_2025 if c == "China")
    print("  wrote 9 AI-Index extras CSVs (VERIFY before publishing)")
    print(f"    models 2025: US 59 / China 35 / Europe 2; top-20 orgs are "
          f"{us_models} US + {cn_models} China + rest, zero EU")
    us_public = sum(PUBLIC_AI_US.values())
    eu_public = sum(PUBLIC_AI_EUROPE.values())
    print(f"    data centers: US {DATACENTERS_2025['United States']:,} vs "
          f"Germany {DATACENTERS_2025['Germany']}; "
          f"public AI: US ~${us_public:.1f}bn vs Europe ~${eu_public:.1f}bn")
    print("    org adoption 2025 (McKinsey): Europe leads at 91% (N.America 90, China 88)")


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    print("=" * 64)
    print("STEP 1 — collecting data into ./data")
    print("=" * 64)

    print("\n[1] AI adoption by country (Eurostat isoc_eb_ai) ...")
    try:
        get_adoption_by_country()
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[2] AI adoption trend (Eurostat isoc_eb_ai) ...")
    try:
        get_adoption_trend()
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[3] AI adoption by firm size (Eurostat isoc_eb_ai) ...")
    try:
        get_adoption_by_firmsize()
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[4] AI investment by geography (Stanford AI Index figures) ...")
    try:
        write_investment_csvs()
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[5] Production, infrastructure, research, public money & talent "
          "(AI Index 2026) ...")
    try:
        write_aiindex_extras()
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\nDone. CSVs written to ./data — now run 02_make_figures.py")


if __name__ == "__main__":
    main()
