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

## AI pace component
- The app classifies each selected race as **Fast**, **Moderate**, or **Slow** pace based on an AI-style heuristic over early pace and run-style pressure.
- It then builds a **pace map** with predicted start position and finish position for every horse in the race.
- The pace map combines early pace, late pace, run style, and proprietary figure strength.

## Auto-adjusted weights
- Enable **Auto-adjust weights by surface + pace** in the sidebar.
- The app reads race surface (dirt/turf/other) and a preliminary AI pace scenario (Fast/Moderate/Slow), then auto-populates sliders with a matching profile.
- You can still manually override any slider afterward.

## Track dropdown + card storage
- Select from a US track dropdown to set card context.
- Race labels include **surface and distance** for easier race identification.
- Save predictions for all races on a card (track/date) and review them later in-app.

## Learning from results
- Upload official results CSV (`track,date,race_number,winner_program` or `winner_horse`).
- The app compares outcomes vs stored predictions and updates a lightweight learning profile used by auto-weight recommendations.

## OpenAI-assisted learning (optional)
- In the results upload section, enable **Use OpenAI to refine factor multipliers**.
- Provide `OPENAI_API_KEY` via environment (or paste key in the app) and upload results.
- The app sends summarized historical prediction/results context to OpenAI and receives factor multipliers, then stores them in the local learning profile.
- If no key/package is available, the app gracefully falls back to local heuristic learning only.

## Archives + prediction/result comparison
- Use **View prediction archive for selected track** to browse all stored prediction cards by date.
- Use **View results archive for selected track** to browse all uploaded result cards by date.
- After uploading results, the app shows **Predictions vs Results** for the selected track/date card (race-by-race match flags).


- You can upload **multiple results files at once**; the app groups and displays uploaded rows by **track/date** and stores them in the results archive.

## BRIS Chart ZIP results support
- Results uploader now accepts the BRIS chart ZIP bundle (e.g., `DMR07012005c.zip`) and parses chart files to extract race winners.
- The parser prioritizes **Start file** official winners and can also fall back to ITM payoffs for winner identification.
- Parsed winner rows are stored in the same track/date archives and feed prediction-vs-results comparisons and learning.
