# AI investment, EU vs US

Data + charts for the blog post **"Europe adopts AI but doesn't fund it."**
Two halves, one argument: EU firms increasingly *use* AI, but almost none of the
money *building* it is European.

Mirrors the layout of the sibling `precautionary_savings_eu` project: a
`01 → 02` pipeline, tidy CSVs in `data/`, PNGs in `figures/`. There is **no
econometrics step** — per the brief, the charts carry the argument.

## Run

```bash
bash run_all.sh                 # install deps, collect data, draw figures
# or, step by step:
pip install -r requirements.txt
python 01_collect_data.py        # writes data/*.csv
python 02_make_figures.py        # writes figures/*.png
```

## Pipeline

- **`01_collect_data.py`** — collects everything into `data/`.
  - *Adoption* (Eurostat `isoc_eb_ai`, pulled **live**, keyless): share of
    enterprises using ≥1 AI technology (`E_AI_TANY`, 10+ employed). By country,
    over time, and by firm size. The latest survey year is detected
    automatically.
  - *Investment* (Stanford HAI **AI Index**): private AI investment by region.
    No free API exists (underlying data is Quid), so the figures are **hardcoded
    from the report PDFs with their figure numbers** and must be re-verified /
    refreshed each report cycle. See the `INVEST_*` tables in the script.
- **`02_make_figures.py`** — reads `data/` and draws `figures/`. No network.

## Figures

| File | What |
|---|---|
| `A_investment_by_geo.png`   | Private AI investment by country, 2025 (US laps the field) |
| `A2_investment_gap.png`     | US vs Europe vs China, 2023–25 (the gap exploding) |
| `B_adoption_by_country.png` | AI adoption by EU country (north-west vs south-east) |
| `B2_adoption_trend.png`     | AI adoption over time, EU-27 + spread |
| `B3_adoption_by_firmsize.png` | AI adoption by firm size (the SME gap) |

## Two caveats baked into the captions

1. **Eurostat series break.** The AI-technology definition was broadened between
   the 2023 and 2024 surveys, so part of the 8→13.5% EU jump is definitional.
   2024→2025 is clean. The trend chart shades the break.
2. **"Europe" includes the UK.** The AI Index regional investment line bundles
   the UK with the EU, and there is no clean EU-27 investment aggregate. For an
   EU-vs-UK split, use the single-country bars in `A_investment_by_geo.png`.
   Also: China's private figure excludes large state "guidance funds."

## Data sources

- Eurostat `isoc_eb_ai`: <https://ec.europa.eu/eurostat/databrowser/view/isoc_eb_ai>
- Stanford HAI AI Index (2024 / 2025 / 2026): <https://hai.stanford.edu/ai-index>

Underlying figures and provenance are also written up in `../ai-project-data.md`.
