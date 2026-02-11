from __future__ import annotations

import streamlit as st

from brisnet_parser import group_by_race, parse_single_file_content
from scoring import DEFAULT_FACTORS, compute_scores

st.set_page_config(page_title="BRISNET PP Interpreter", layout="wide")
st.title("BRISNET Single File Interpreter + Proprietary Speed Figure Builder")

st.markdown(
    """
Upload a BRISNET **Single File** (comma-delimited PP) and tune factor weights to create
custom proprietary speed figures and a projected winner.
"""
)

uploaded = st.file_uploader("Upload BRISNET single-file data", type=["txt", "csv", "dat"])
manual = st.text_area("Or paste raw BRISNET lines", height=180)

if not uploaded and not manual.strip():
    st.info("Provide a file or paste at least one BRISNET record line to begin.")
    st.stop()

if uploaded:
    content = uploaded.read().decode("utf-8", errors="ignore")
else:
    content = manual

records = parse_single_file_content(content)
if not records:
    st.error("No parsable records found.")
    st.stop()

race_map = group_by_race(records)
race_labels = [f"{k[0]} | {k[1]} | Race {k[2]} ({len(v)} horses)" for k, v in race_map.items()]
race_keys = list(race_map.keys())
selected_label = st.selectbox("Select race", race_labels)
selected_key = race_keys[race_labels.index(selected_label)]
selected_records = race_map[selected_key]

st.sidebar.header("Factor Weights")
weights: dict[str, float] = {}
for factor in DEFAULT_FACTORS:
    weights[factor.key] = st.sidebar.slider(
        factor.label,
        min_value=-2.0,
        max_value=5.0,
        value=1.0,
        step=0.1,
    )

result = compute_scores(selected_records, weights)

if not result:
    st.warning("No rows returned for selected race.")
    st.stop()

leader = result[0]
st.subheader("Predicted Winner")
st.success(
    f"{leader['horse']} (Program {leader['program']} / Post {leader['post']}) "
    f"with score {leader['proprietary_score']:.2f}"
)

st.subheader("Ranked Field")
display_columns = [
    "horse",
    "program",
    "post",
    "trainer",
    "jockey",
    "proprietary_score",
] + [factor.key for factor in DEFAULT_FACTORS]
table_rows = [{k: row.get(k, "") for k in display_columns} for row in result]
st.dataframe(table_rows, use_container_width=True)

with st.expander("Raw field-number explorer"):
    horse_names = [r.horse_name for r in selected_records]
    picked = st.selectbox("Horse", horse_names)
    rec = selected_records[horse_names.index(picked)]
    field_num = st.number_input("Field #", min_value=1, max_value=1435, value=251)
    st.code(rec.get_raw(int(field_num)) or "<blank>")
