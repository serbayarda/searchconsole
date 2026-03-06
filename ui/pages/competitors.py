import streamlit as st
import pandas as pd
import plotly.express as px


def render():
    st.header("Competitor Analysis")

    gap_analyses = st.session_state.get("gap_analyses", [])
    user_page_data = st.session_state.get("user_page_data", {})

    if not gap_analyses:
        st.info("No competitor data available. Run the analysis first.")
        return

    # Summary table across all keywords
    st.subheader("Gap Summary Across All Keywords")

    summary_rows = []
    for gap in gap_analyses:
        content = gap.get("content_gap", {})
        meta = gap.get("meta_gap", {})
        kw_usage = gap.get("keyword_usage_gap", {})
        structural = gap.get("structural_gap", {})

        summary_rows.append({
            "Keyword": gap.get("keyword", ""),
            "Your Page": gap.get("user_url", "")[:60],
            "Your Words": content.get("user_word_count", 0),
            "Avg Comp Words": content.get("avg_competitor_word_count", 0),
            "Word Deficit": content.get("word_count_deficit", 0),
            "Keyword in Title": "Yes" if meta.get("title_contains_keyword") else "No",
            "Keyword in Meta": "Yes" if meta.get("meta_desc_contains_keyword") else "No",
            "Keyword in H1": "Yes" if kw_usage.get("keyword_in_h1") else "No",
            "Missing Schemas": len(structural.get("missing_schema_types", [])),
        })

    if summary_rows:
        summary_df = pd.DataFrame(summary_rows)
        st.dataframe(summary_df)

    st.markdown("---")

    # Content length comparison chart
    st.subheader("Content Length: You vs Competitors")

    chart_data = []
    for gap in gap_analyses:
        content = gap.get("content_gap", {})
        kw = gap.get("keyword", "")[:30]
        chart_data.append({"Keyword": kw, "Source": "Your Page", "Word Count": content.get("user_word_count", 0)})
        chart_data.append({"Keyword": kw, "Source": "Competitor Avg", "Word Count": content.get("avg_competitor_word_count", 0)})

    if chart_data:
        chart_df = pd.DataFrame(chart_data)
        fig = px.bar(
            chart_df,
            x="Keyword",
            y="Word Count",
            color="Source",
            barmode="group",
            color_discrete_map={"Your Page": "#4CAF50", "Competitor Avg": "#FF5722"},
        )
        fig.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # On-page SEO checklist
    st.subheader("On-Page SEO Checklist")

    checklist_rows = []
    for gap in gap_analyses:
        meta = gap.get("meta_gap", {})
        kw_usage = gap.get("keyword_usage_gap", {})
        checklist_rows.append({
            "Keyword": gap.get("keyword", ""),
            "Keyword in Title": "pass" if meta.get("title_contains_keyword") else "fail",
            "Keyword in Meta Desc": "pass" if meta.get("meta_desc_contains_keyword") else "fail",
            "Keyword in H1": "pass" if kw_usage.get("keyword_in_h1") else "fail",
            "Keyword in H2": "pass" if kw_usage.get("keyword_in_h2") else "fail",
            "Keyword in 1st Para": "pass" if kw_usage.get("keyword_in_first_paragraph") else "fail",
        })

    if checklist_rows:
        checklist_df = pd.DataFrame(checklist_rows)
        # Style pass/fail
        def color_result(val):
            if val == "pass":
                return "background-color: #C8E6C9"
            elif val == "fail":
                return "background-color: #FFCDD2"
            return ""

        styled = checklist_df.style.map(color_result)
        st.dataframe(styled)

    st.markdown("---")

    # Per-page analysis
    st.subheader("Scraped Page Data")
    if user_page_data:
        page_urls = list(user_page_data.keys())
        selected_page = st.selectbox("Select a page", page_urls, key="comp_page_select")

        if selected_page and selected_page in user_page_data:
            page = user_page_data[selected_page]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Title:** {page.get('title', 'N/A')}")
                st.markdown(f"**Word Count:** {page.get('content_length', 0)}")
                st.markdown(f"**H1 Tags:** {len(page.get('h1_tags', []))}")
            with col2:
                st.markdown(f"**H2 Tags:** {len(page.get('h2_tags', []))}")
                st.markdown(f"**H3 Tags:** {len(page.get('h3_tags', []))}")
                st.markdown(f"**Images w/o Alt:** {page.get('images_without_alt', 0)}")
            with col3:
                st.markdown(f"**Internal Links:** {len(page.get('internal_links', []))}")
                st.markdown(f"**External Links:** {len(page.get('external_links', []))}")
                st.markdown(f"**Schema Types:** {', '.join(page.get('schema_types', [])) or 'None'}")

            if page.get("h2_tags"):
                st.markdown("**H2 Headings:**")
                for h2 in page["h2_tags"]:
                    st.markdown(f"- {h2}")
