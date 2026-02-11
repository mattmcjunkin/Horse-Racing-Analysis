from __future__ import annotations

import streamlit as st

from auto_weights import detect_surface, recommended_weights
from brisnet_parser import group_by_race, parse_content
from pace_ai import build_pace_map, classify_race_pace
from scoring import DEFAULT_FACTORS, compute_scores

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
    <p style="margin:0.25rem 0 0 0;">Interpret BRISNET or DRF files, weight handicapping factors (0.0-2.0), and project winners on a BRIS-like speed figure scale.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([2, 1])
with left:
    source_format = st.selectbox("File type", ["auto", "brisnet", "drf"], index=0)
    uploaded = st.file_uploader("Upload data file", type=["txt", "csv", "dat", "drf"])
    manual = st.text_area("Or paste raw lines", height=160)
with right:
    st.markdown("### Notes")
    st.markdown(
        """
- **BRISNET:** single-file comma-delimited rows.
- **DRF:** CSV/TSV/pipe with headers (ex: `horse_name`, `track`, `race_number`, `pace_2f`).
- Proprietary figure = BRIS baseline ± weighted interpretation adjustment.
- AI pace engine classifies race shape and creates a pace map.
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
race_keys = list(race_map.keys())
race_labels = [
    f"{k[0]} | {k[1]} | Race {k[2]} ({len(race_map[k])} horses)"
    for k in race_keys
]

c1, c2, c3 = st.columns([1, 1, 1])
c1.metric("Records Loaded", len(records))
c2.metric("Races Found", len(race_keys))
c3.metric("Factors in Model", len(DEFAULT_FACTORS))

selected_label = st.selectbox("Select race", race_labels)
selected_key = race_keys[race_labels.index(selected_label)]
selected_records = race_map[selected_key]

st.sidebar.header("Factor Weights (0.0 to 2.0)")
st.sidebar.caption("Set 0 to ignore a factor, 2 to double its influence.")
adjustment_scale = st.sidebar.slider(
    "Interpretation sensitivity (figure points)",
    min_value=1.0,
    max_value=30.0,
    value=12.0,
    step=1.0,
)

# Preliminary pace read on neutral settings for auto-weight guidance
neutral_weights = {f.key: 1.0 for f in DEFAULT_FACTORS}
prelim = compute_scores(selected_records, neutral_weights, adjustment_scale=adjustment_scale)
prelim_pace = classify_race_pace(prelim)
surface = detect_surface(selected_records[0].get_text(7)) if selected_records else "unknown"

auto_mode = st.sidebar.toggle("Auto-adjust weights by surface + pace", value=False)
if auto_mode:
    rec = recommended_weights([f.key for f in DEFAULT_FACTORS], surface, prelim_pace.label)
    fingerprint = f"{selected_key}|{surface}|{prelim_pace.label}"
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
    weights[factor.key] = st.sidebar.slider(
        factor.label,
        min_value=0.0,
        max_value=2.0,
        value=float(st.session_state[key]),
        step=0.05,
        key=key,
    )

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
display_columns = [
    "horse",
    "program",
    "post",
    "run_style",
    "trainer",
    "jockey",
    "bris_speed_figure",
    "figure_delta_vs_bris",
    "proprietary_speed_figure",
    "prime_power",
    "recent_early_pace",
    "recent_late_pace",
    "recent_speed_avg",
]

table_rows = [{k: row.get(k, "") for k in display_columns} for row in result]
st.dataframe(table_rows, use_container_width=True, hide_index=True)

st.subheader("AI Pace Map (Predicted Start vs Finish)")
st.dataframe(pace_map, use_container_width=True, hide_index=True)

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
    contrib_rows.append(
        {
            "factor": factor.label,
            "weight": weights.get(factor.key, 0.0),
            "contribution_units": contrib,
            "figure_points_impact": contrib * adjustment_scale,
        }
    )
contrib_rows.sort(key=lambda x: abs(x["figure_points_impact"]), reverse=True)
st.dataframe(contrib_rows, use_container_width=True, hide_index=True)

st.markdown(
    "<div class='small-note'>Positive contribution values push the proprietary figure above BRIS baseline; negative values pull it down based on your weights and race-relative rankings.</div>",
    unsafe_allow_html=True,
)

with st.expander("Raw field-number explorer"):
    rec_names = [r.horse_name for r in selected_records]
    picked = st.selectbox("Horse", rec_names)
    rec = selected_records[rec_names.index(picked)]
    field_num = st.number_input("Field #", min_value=1, max_value=1435, value=251)
    st.code(rec.get_raw(int(field_num)) or "<blank>")
