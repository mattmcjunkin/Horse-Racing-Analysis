from __future__ import annotations

import csv
from io import StringIO

import streamlit as st

from auto_weights import detect_surface, recommended_weights
from brisnet_parser import group_by_race, parse_content
from learning_store import (
    get_card_predictions,
    learn_from_results,
    load_learning_profile,
    load_predictions,
    record_card_predictions,
    save_learning_profile,
)
from openai_learning import suggest_learning_multipliers
from pace_ai import build_pace_map, classify_race_pace
from scoring import DEFAULT_FACTORS, compute_scores
from us_tracks import track_options

st.set_page_config(page_title="Horse Racing Figure Lab", page_icon="🏇", layout="wide")

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.2rem;}
    .hero {padding: 1rem 1.2rem; border-radius: 12px; background: linear-gradient(90deg,#1f2937,#334155); color: white; margin-bottom: 1rem;}
    .small-note {color: #6b7280; font-size: 0.9rem;}
    .pill {display:inline-block; padding:0.3rem 0.7rem; border-radius:999px; background:#e2e8f0; margin-right:0.4rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
    <h2 style="margin:0;">🏇 Horse Racing Figure Lab</h2>
    <p style="margin:0.25rem 0 0 0;">Interpret BRISNET/DRF, auto-tune by surface+pace, store card predictions, and learn from results.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([2, 1])
with left:
    selected_track_menu = st.selectbox("US Track card context", track_options(), index=track_options().index("GP") if "GP" in track_options() else 0)
    source_format = st.selectbox("File type", ["auto", "brisnet", "drf"], index=0)
    uploaded = st.file_uploader("Upload data file", type=["txt", "csv", "dat", "drf"])
    manual = st.text_area("Or paste raw lines", height=140)
with right:
    st.markdown("### Notes")
    st.markdown(
        """
- Auto-weight profile uses **surface + pace scenario**.
- Race description now includes **surface + distance**.
- Save a full card's predictions by track/date.
- Upload results CSV to let model learn from outcomes.
        """
    )

if not uploaded and not manual.strip():
    st.info("Provide a file upload or paste content to begin.")
    st.stop()

content = uploaded.read().decode("utf-8", errors="ignore") if uploaded else manual
records = parse_content(content, source_format=source_format)
if not records:
    st.error("No parsable records found for selected format.")
    st.stop()

race_map = group_by_race(records)
race_keys = [k for k in race_map.keys() if (k[0] == selected_track_menu or selected_track_menu == "UNK")] or list(race_map.keys())
race_labels = []
for k in race_keys:
    sample = race_map[k][0]
    surface_code = sample.get_text(7)
    distance_yards = sample.get_text(6)
    race_labels.append(
        f"{k[0]} | {k[1]} | Race {k[2]} | Surface {surface_code or '?'} | Dist {distance_yards or '?'}y ({len(race_map[k])} horses)"
    )

c1, c2, c3 = st.columns([1, 1, 1])
c1.metric("Records Loaded", len(records))
c2.metric("Races Found", len(race_keys))
c3.metric("Factors in Model", len(DEFAULT_FACTORS))

selected_label = st.selectbox("Select race", race_labels)
selected_key = race_keys[race_labels.index(selected_label)]
selected_records = race_map[selected_key]

st.sidebar.header("Factor Weights (0.0 to 2.0)")
st.sidebar.caption("Set 0 to ignore a factor, 2 to double its influence.")
adjustment_scale = st.sidebar.slider("Interpretation sensitivity (figure points)", 1.0, 30.0, 12.0, 1.0)

neutral_weights = {f.key: 1.0 for f in DEFAULT_FACTORS}
prelim = compute_scores(selected_records, neutral_weights, adjustment_scale=adjustment_scale)
prelim_pace = classify_race_pace(prelim)
surface = detect_surface(selected_records[0].get_text(7)) if selected_records else "unknown"
learning_profile = load_learning_profile()

auto_mode = st.sidebar.toggle("Auto-adjust weights by surface + pace", value=False)
if auto_mode:
    rec = recommended_weights([f.key for f in DEFAULT_FACTORS], surface, prelim_pace.label, learning_profile=learning_profile)
    fingerprint = f"{selected_key}|{surface}|{prelim_pace.label}|{learning_profile}"
    if st.session_state.get("_auto_fp") != fingerprint:
        for factor in DEFAULT_FACTORS:
            st.session_state[f"weight_{factor.key}"] = rec.get(factor.key, 1.0)
        st.session_state["_auto_fp"] = fingerprint
    st.sidebar.caption(f"Auto profile: surface={surface}, projected pace={prelim_pace.label}")

weights: dict[str, float] = {}
for factor in DEFAULT_FACTORS:
    key = f"weight_{factor.key}"
    if key not in st.session_state:
        st.session_state[key] = 1.0
    weights[factor.key] = st.sidebar.slider(factor.label, 0.0, 2.0, float(st.session_state[key]), 0.05, key=key)

result = compute_scores(selected_records, weights, adjustment_scale=adjustment_scale)
if not result:
    st.warning("No rows returned for selected race.")
    st.stop()

pace_scenario = classify_race_pace(result)
pace_map = build_pace_map(result, top_n=len(result))
leader = result[0]

st.success(
    f"Projected Winner: **{leader['horse']}** | Program {leader['program']} | Post {leader['post']} | "
    f"Proprietary Figure {leader['proprietary_speed_figure']:.1f} (BRIS {leader['bris_speed_figure']:.1f}, Δ {leader['figure_delta_vs_bris']:+.1f})"
)

st.markdown(
    f"<span class='pill'><b>AI Pace Scenario:</b> {pace_scenario.label}</span>"
    f"<span class='pill'><b>Confidence:</b> {pace_scenario.confidence:.0%}</span>"
    f"<span class='pill'>{pace_scenario.reason}</span>",
    unsafe_allow_html=True,
)

st.subheader("Ranked Field (BRIS Scale + Proprietary Adjustment)")
display_columns = ["horse", "program", "post", "run_style", "trainer", "jockey", "bris_speed_figure", "figure_delta_vs_bris", "proprietary_speed_figure", "prime_power", "recent_early_pace", "recent_late_pace", "recent_speed_avg"]
table_rows = [{k: row.get(k, "") for k in display_columns} for row in result]
st.dataframe(table_rows, use_container_width=True, hide_index=True)

st.subheader("AI Pace Map (Predicted Start vs Finish)")
st.dataframe(pace_map, use_container_width=True, hide_index=True)

st.subheader("Store card predictions for track")
card_track, card_date, _ = selected_key
if st.button("Save all race predictions for this track/date"):
    card_predictions = []
    for key in race_keys:
        if key[0] != card_track or key[1] != card_date:
            continue
        race_result = compute_scores(race_map[key], weights, adjustment_scale=adjustment_scale)
        if not race_result:
            continue
        top = race_result[0]
        card_predictions.append(
            {
                "track": key[0],
                "date": key[1],
                "race_number": key[2],
                "predicted_winner_horse": top.get("horse", ""),
                "predicted_winner_program": top.get("program", ""),
                "predicted_figure": top.get("proprietary_speed_figure", 0.0),
            }
        )
    record_card_predictions(card_track, card_date, card_predictions)
    st.success(f"Saved {len(card_predictions)} race predictions for {card_track} {card_date}.")

saved = get_card_predictions(card_track, card_date)
if saved:
    st.caption(f"Stored predictions for {card_track} {card_date}")
    st.dataframe(saved, use_container_width=True, hide_index=True)

st.subheader("Upload official results to learn")
st.caption("Upload CSV with columns: track,date,race_number,winner_program or winner_horse")
use_openai_learning = st.checkbox("Use OpenAI to refine factor multipliers from accumulated cards", value=False)
openai_key = st.text_input("OpenAI API key (optional if OPENAI_API_KEY env is set)", type="password") if use_openai_learning else ""
results_file = st.file_uploader("Upload results CSV", type=["csv"], key="results_upload")
if results_file is not None:
    text = results_file.read().decode("utf-8", errors="ignore")
    reader = csv.DictReader(StringIO(text))
    rows = [r for r in reader]

    profile = learn_from_results(rows)

    if use_openai_learning:
        factor_keys = [f.key for f in DEFAULT_FACTORS]
        multipliers, status = suggest_learning_multipliers(
            factor_keys=factor_keys,
            stored_predictions=load_predictions(),
            recent_results=rows,
            api_key=openai_key or None,
        )
        if multipliers:
            profile.update(multipliers)
            save_learning_profile(profile)
            st.success("OpenAI learning multipliers applied.")
        else:
            st.warning(f"OpenAI learning skipped: {status}")

    st.success(f"Learning update applied. Latest hit rate: {profile.get('last_hit_rate', 'n/a')}")
    st.json(profile)

st.subheader("How your weights changed the BRIS figure")
horse_names = [row["horse"] for row in result]
focus = st.selectbox("Inspect horse", horse_names)
focus_row = next(row for row in result if row["horse"] == focus)

m1, m2, m3 = st.columns(3)
m1.metric("BRIS Baseline", f"{focus_row['bris_speed_figure']:.1f}")
m2.metric("Adjustment", f"{focus_row['figure_delta_vs_bris']:+.1f}")
m3.metric("Proprietary Figure", f"{focus_row['proprietary_speed_figure']:.1f}")

contrib_rows = []
for factor in DEFAULT_FACTORS:
    contrib = focus_row["factor_contributions"].get(factor.key, 0.0)
    contrib_rows.append({"factor": factor.label, "weight": weights.get(factor.key, 0.0), "contribution_units": contrib, "figure_points_impact": contrib * adjustment_scale})
contrib_rows.sort(key=lambda x: abs(x["figure_points_impact"]), reverse=True)
st.dataframe(contrib_rows, use_container_width=True, hide_index=True)

with st.expander("Raw field-number explorer"):
    rec_names = [r.horse_name for r in selected_records]
    picked = st.selectbox("Horse", rec_names)
    rec = selected_records[rec_names.index(picked)]
    field_num = st.number_input("Field #", min_value=1, max_value=1435, value=251)
    st.code(rec.get_raw(int(field_num)) or "<blank>")
