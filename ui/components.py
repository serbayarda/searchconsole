from __future__ import annotations
import streamlit as st
import pandas as pd


def metric_card(label: str, value, delta=None, delta_color="normal"):
    st.metric(label=label, value=value, delta=delta, delta_color=delta_color)


def render_metric_row(stats: dict):
    cols = st.columns(4)
    with cols[0]:
        st.metric("Total Clicks", f"{stats['total_clicks']:,}")
    with cols[1]:
        st.metric("Total Impressions", f"{stats['total_impressions']:,}")
    with cols[2]:
        st.metric("Avg CTR", f"{stats['avg_ctr']:.1%}")
    with cols[3]:
        st.metric("Avg Position", f"{stats['avg_position']:.1f}")


def render_keyword_table(df: pd.DataFrame, key_prefix: str = "kw"):
    if df.empty:
        st.info("No data available.")
        return

    display_df = df.copy()
    if "ctr" in display_df.columns:
        display_df["ctr"] = display_df["ctr"].apply(lambda x: f"{x:.2%}")
    if "expected_ctr" in display_df.columns:
        display_df["expected_ctr"] = display_df["expected_ctr"].apply(lambda x: f"{x:.2%}")
    if "ctr_gap" in display_df.columns:
        display_df["ctr_gap"] = display_df["ctr_gap"].apply(lambda x: f"{x:.2%}")
    if "position" in display_df.columns:
        display_df["position"] = display_df["position"].apply(lambda x: f"{x:.1f}")
    if "opportunity_score" in display_df.columns:
        display_df["opportunity_score"] = display_df["opportunity_score"].apply(lambda x: f"{x:.0f}")

    st.dataframe(display_df)


def render_action_card(action: dict):
    priority = action.get("priority", "medium")
    category = action.get("category", "")

    with st.expander(
        f"[{priority.upper()}] | {category.upper()} | {action['title']}",
        expanded=False,
    ):
        st.markdown(f"**Keyword:** `{action.get('keyword', '')}`")
        st.markdown(f"**Page:** `{action.get('page_url', '')}`")
        st.markdown(f"**Effort:** {action.get('effort', '')} | **Impact:** {action.get('estimated_impact', '')}")
        st.markdown("---")
        st.markdown(action.get("description", ""))

        suggestions = action.get("specific_suggestions", [])
        if suggestions:
            st.markdown("**Action Steps:**")
            for s in suggestions:
                st.markdown(f"- {s}")


def render_competitor_table(competitors: list[dict]):
    if not competitors:
        st.info("No competitor data available.")
        return
    df = pd.DataFrame(competitors)
    st.dataframe(df)


def priority_badge(priority: str) -> str:
    return f"[{priority.upper()}]"
