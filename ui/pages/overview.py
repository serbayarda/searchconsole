import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ui.components import render_metric_row, render_keyword_table


def render():
    st.header("Overview Dashboard")

    gsc_data = st.session_state.get("gsc_data")
    stats = st.session_state.get("summary_stats", {})
    date_series = st.session_state.get("date_series")
    opportunities = st.session_state.get("opportunities")

    if not stats:
        st.warning("No data loaded yet. Please run the analysis first.")
        return

    # Key metrics row
    render_metric_row(stats)

    st.markdown("---")

    # Time series chart
    if date_series is not None and not date_series.empty:
        st.subheader("Performance Trend")

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Clicks", "Impressions", "CTR", "Position"),
            vertical_spacing=0.12,
        )

        fig.add_trace(
            go.Scatter(x=date_series["date"], y=date_series["clicks"],
                       mode="lines", name="Clicks", line=dict(color="#4CAF50")),
            row=1, col=1,
        )
        fig.add_trace(
            go.Scatter(x=date_series["date"], y=date_series["impressions"],
                       mode="lines", name="Impressions", line=dict(color="#2196F3")),
            row=1, col=2,
        )
        fig.add_trace(
            go.Scatter(x=date_series["date"], y=date_series["ctr"],
                       mode="lines", name="CTR", line=dict(color="#FF9800")),
            row=2, col=1,
        )
        fig.add_trace(
            go.Scatter(x=date_series["date"], y=date_series["position"],
                       mode="lines", name="Position", line=dict(color="#9C27B0")),
            row=2, col=2,
        )
        fig.update_yaxes(autorange="reversed", row=2, col=2)
        fig.update_layout(height=500, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Top keywords by impressions
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top Keywords by Impressions")
        if gsc_data is not None and not gsc_data.empty:
            top_kw = gsc_data.nlargest(15, "impressions")[
                ["query", "clicks", "impressions", "ctr", "position"]
            ]
            render_keyword_table(top_kw, key_prefix="top_kw")

    with col2:
        st.subheader("Top Pages by Clicks")
        if gsc_data is not None and not gsc_data.empty:
            page_data = gsc_data.groupby("page").agg({
                "clicks": "sum",
                "impressions": "sum",
            }).reset_index()
            page_data["ctr"] = page_data["clicks"] / page_data["impressions"].clip(lower=1)
            top_pages = page_data.nlargest(15, "clicks")
            # Shorten URLs for display
            top_pages["page"] = top_pages["page"].apply(
                lambda x: x.replace("https://", "").replace("http://", "")[:60]
            )
            render_keyword_table(top_pages, key_prefix="top_pages")

    # Opportunities summary
    if opportunities is not None and not opportunities.empty:
        st.markdown("---")
        st.subheader(f"Keyword Opportunities Found: {len(opportunities)}")
        st.caption("Keywords with high impressions but below-expected CTR. Navigate to Keywords tab for details.")
        render_keyword_table(
            opportunities.head(10)[["query", "page", "impressions", "ctr", "position", "opportunity_score"]],
            key_prefix="opp_preview",
        )
