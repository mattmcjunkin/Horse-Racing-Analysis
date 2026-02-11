# BRISNET Single File Interpreter (Streamlit)

This app ingests BRISNET comma-delimited **Single File** past performances, interprets key fields, and lets you assign custom weights to produce a proprietary speed figure and predicted winner for each race.

## Features
- Parse BRISNET Single File records up to field `#1435`.
- Group horses by `(Track, Date, Race #)`.
- Adjustable weighted model for key handicapping factors:
  - Prime Power, best speed slices, class speed par, trainer/jockey form, recency, and more.
- Ranked output and projected winner.
- Raw field explorer by field number for any selected horse.

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Input expectations
- One horse per line.
- Comma-delimited BRISNET Single File format.
- Quoted fields supported.

If a record has fewer than 1435 fields, missing fields are padded as blank. If it has more, extras are truncated.
