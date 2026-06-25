# AI investment, EU vs US

Data + charts for the blog post **"Europe researches and uses AI — but doesn't
build, patent, or fund it."** One argument across the whole AI value chain:
Europe is strong in research and heavy in *use*, yet the money, the companies,
the models, and the infrastructure that *own* AI are American or Chinese.

Mirrors the layout of the sibling `precautionary_savings_eu` project: a
`01 → 02` pipeline, tidy CSVs in `data/`, PNGs in `figures/`. There is **no
econometrics step** — these are directly measured magnitudes, so the charts
carry the argument.

## Run

```bash
bash run_all.sh                 # install deps, collect data, draw figures
# or, step by step:
pip install -r requirements.txt
python 01_collect_data.py        # writes data/*.csv
python 02_make_figures.py        # writes figures/*.png
```

## Pipeline

- **`01_collect_data.py`** — collects everything into `data/` (15 CSVs).
  - *Adoption* (Eurostat `isoc_eb_ai`, pulled **live**, keyless): share of
    enterprises using ≥1 AI technology (`E_AI_TANY`, 10+ employed), by country,
    over time, and by firm size. Latest survey year auto-detected.
  - *Everything else* (Stanford **AI Index 2026**): private + public investment,
    notable models & developers, research shares, data centres, talent. No free
    API exists (Quid/Epoch AI), so figures are **hardcoded from the report with
    their figure numbers** and must be re-verified/refreshed each report cycle.
- **`02_make_figures.py`** — reads `data/` and draws `figures/` (11 charts). No
  network.

## Figures

| File | What |
|---|---|
| `A_investment_by_geo.png`     | Private AI investment by country, 2025 (US laps the field) |
| `A2_investment_gap.png`       | US vs Europe vs China, 2023–25 (the gap exploding) |
| `C_models_by_country.png`     | Notable AI models, 2025 (US 59 / China 35 / **Europe 2**) |
| `C2_developers_by_origin.png` | Top model developers by origin (zero EU in the top 20) |
| `D_europe_paradox.png`        | Europe's share of the pipeline (research high, production low) |
| `E_datacenters_by_country.png`| Data centres by country (+ chip-stack ownership note) |
| `F_public_investment.png`     | Government AI spending, US vs Europe |
| `B_adoption_by_country.png`   | AI adoption by EU country (north-west vs south-east) |
| `B2_adoption_trend.png`       | AI adoption over time, EU-27 + spread |
| `B3_adoption_by_firmsize.png` | AI adoption by firm size (the SME gap) |
| `G_talent_migration.png`      | Net AI talent migration (Europe's big economies attract little) |

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
