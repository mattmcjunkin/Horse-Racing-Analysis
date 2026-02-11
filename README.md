# Horse Racing Figure Lab (Streamlit)

This app ingests racing data and builds custom proprietary figures for winner prediction.

## Supported file types
- **BRISNET Single File** (comma-delimited PP rows)
- **DRF flat files** (CSV/TSV/pipe with headers)

## Proprietary Figure Model (BRIS-aligned scale)
The app now keeps the proprietary number on a BRIS-like figure scale:
1. Start with a **BRIS baseline speed figure** (latest BRIS speed `#846`, fallback to recent average).
2. Normalize each factor in-race.
3. Apply your weights (`0.0` to `2.0`) to generate positive/negative contribution units.
4. Convert contribution units into figure points using **Interpretation sensitivity**.
5. Final output:
   - `proprietary_speed_figure = bris_speed_figure + figure_adjustment`

This makes it easy to see exactly how your interpretation changes the baseline BRIS figure.

## What the model uses
- Speed metrics: Prime Power, best-speed slices, class speed par, recent BRIS speed.
- Pace metrics: pace par average (2f/4f/6f), recent early pace, recent late pace.
- Form metrics: days since last race, trainer/jockey meet win rates, track and distance win percentages.

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## DRF column hints
For best results, include columns like:
`horse_name, track, date/race_date, race_number, post_position, program, trainer, jockey, prime_power, speed_par, days_since_last, best_speed_life, pace_2f, pace_4f, pace_6f, late_pace, bris_speed`.
