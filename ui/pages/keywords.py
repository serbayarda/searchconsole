import streamlit as st
from ui.components import render_keyword_table
from utils.export import export_to_csv, export_to_json


def render():
    st.header("Keyword Opportunities")

    opportunities = st.session_state.get("opportunities")
    intent_data = st.session_state.get("intent_data", {})

    if opportunities is None or opportunities.empty:
        st.info("No keyword opportunities found. Run the analysis first.")
        return

    # Add intent data to opportunities if available
    df = opportunities.copy()
    if intent_data:
        df["intent"] = df["query"].map(
            lambda q: intent_data.get(q, {}).get("primary_intent", "")
        )
    else:
        df["intent"] = ""

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        intent_filter = st.multiselect(
            "Filter by Intent",
            options=sorted(df["intent"].unique()),
            default=[],
            key="intent_filter",
        )

    with col2:
        pos_range = st.slider(
            "Position Range",
            min_value=1.0,
            max_value=20.0,
            value=(1.0, 20.0),
            step=0.5,
            key="pos_range",
        )

    with col3:
        min_impressions = st.number_input(
            "Min Impressions",
            min_value=0,
            value=100,
            step=50,
            key="min_imp",
        )

    # Apply filters
    filtered = df.copy()
    if intent_filter:
        filtered = filtered[filtered["intent"].isin(intent_filter)]
    filtered = filtered[
        (filtered["position"] >= pos_range[0])
        & (filtered["position"] <= pos_range[1])
    ]
    filtered = filtered[filtered["impressions"] >= min_impressions]

    # Summary
    st.markdown(f"Showing **{len(filtered)}** of {len(df)} opportunities")

    # Display columns
    display_cols = ["query", "page", "impressions", "clicks", "ctr", "position",
                    "expected_ctr", "ctr_gap", "opportunity_score"]
    if "intent" in filtered.columns:
        display_cols.append("intent")

    existing_cols = [c for c in display_cols if c in filtered.columns]
    render_keyword_table(filtered[existing_cols], key_prefix="opp_full")

    # Export buttons
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        csv_data = export_to_csv(filtered[existing_cols])
        st.download_button(
            "Download CSV",
            data=csv_data,
            file_name="keyword_opportunities.csv",
            mime="text/csv",
        )
    with col2:
        json_data = export_to_json(filtered[existing_cols])
        st.download_button(
            "Download JSON",
            data=json_data,
            file_name="keyword_opportunities.json",
            mime="application/json",
        )

    # Quick wins section
    st.markdown("---")
    st.subheader("Quick Wins (Position 4-10, High Impressions)")
    quick_wins = filtered[
        (filtered["position"] >= 4) & (filtered["position"] <= 10)
    ].head(10)
    if not quick_wins.empty:
        render_keyword_table(quick_wins[existing_cols], key_prefix="quick_wins")
    else:
        st.info("No quick wins found with current filters.")

    # Keyword selector for drill-down
    st.markdown("---")
    st.subheader("Keyword Detail")
    selected_kw = st.selectbox(
        "Select a keyword for detailed analysis",
        options=filtered["query"].tolist(),
        key="kw_detail_select",
    )

    if selected_kw:
        st.session_state["selected_keyword"] = selected_kw
        st.info("Navigate to 'Keyword Detail' page for SERP analysis and competitor breakdown.")
