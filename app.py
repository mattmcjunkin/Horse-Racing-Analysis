from __future__ import annotations

import streamlit as st

from brisnet_parser import group_by_race, parse_content
from scoring import DEFAULT_FACTORS, compute_scores

st.set_page_config(page_title="Horse Racing Figure Lab", page_icon="🏇", layout="wide")

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.2rem;}
    .hero {padding: 1rem 1.2rem; border-radius: 12px; background: linear-gradient(90deg,#1f2937,#334155); color: white; margin-bottom: 1rem;}
    .small-note {color: #6b7280; font-size: 0.9rem;}
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
race_labels = [f"{k[0]} | {k[1]} | Race {k[2]} ({len(v)} horses)" for k in race_keys]

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

weights: dict[str, float] = {}
for factor in DEFAULT_FACTORS:
    weights[factor.key] = st.sidebar.slider(
        factor.label,
        min_value=0.0,
        max_value=2.0,
        value=1.0,
        step=0.05,
    )

result = compute_scores(selected_records, weights, adjustment_scale=adjustment_scale)
if not result:
    st.warning("No rows returned for selected race.")
    st.stop()

leader = result[0]
st.success(
    f"Projected Winner: **{leader['horse']}** | Program {leader['program']} | Post {leader['post']} | "
    f"Proprietary Figure {leader['proprietary_speed_figure']:.1f} (BRIS {leader['bris_speed_figure']:.1f}, Δ {leader['figure_delta_vs_bris']:+.1f})"
)

st.subheader("Ranked Field (BRIS Scale + Proprietary Adjustment)")
display_columns = [
    "horse",
    "program",
    "post",
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
