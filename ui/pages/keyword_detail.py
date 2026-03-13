import streamlit as st
import pandas as pd
from ui.components import render_action_card, render_competitor_table


def render():
    st.header("Keyword Detail & SERP Analysis")

    selected_kw = st.session_state.get("selected_keyword")
    opportunities = st.session_state.get("opportunities")
    serp_results = st.session_state.get("serp_results", {})
    intent_data = st.session_state.get("intent_data", {})
    gap_analyses = st.session_state.get("gap_analyses", [])
    actions = st.session_state.get("actions", [])

    if not selected_kw:
        # Let user pick a keyword
        if opportunities is not None and not opportunities.empty:
            selected_kw = st.selectbox(
                "Select a keyword to analyze",
                options=opportunities["query"].tolist(),
                key="detail_kw_select",
            )
            if selected_kw:
                st.session_state["selected_keyword"] = selected_kw
        else:
            st.info("No keywords available. Run the analysis first.")
            return

    if not selected_kw:
        return

    st.subheader(f"Keyword: `{selected_kw}`")

    # Keyword metrics from opportunities
    if opportunities is not None and not opportunities.empty:
        kw_row = opportunities[opportunities["query"] == selected_kw]
        if not kw_row.empty:
            row = kw_row.iloc[0]
            cols = st.columns(5)
            with cols[0]:
                st.metric("Impressions", f"{int(row['impressions']):,}")
            with cols[1]:
                st.metric("Clicks", f"{int(row['clicks']):,}")
            with cols[2]:
                st.metric("CTR", f"{row['ctr']:.2%}")
            with cols[3]:
                st.metric("Position", f"{row['position']:.1f}")
            with cols[4]:
                st.metric("Opportunity Score", f"{row.get('opportunity_score', 0):.0f}")

    st.markdown("---")

    # Intent classification
    intent = intent_data.get(selected_kw, {})
    if intent:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Search Intent:** `{intent.get('primary_intent', 'N/A')}`")
            st.markdown(f"**Confidence:** {intent.get('confidence', 0):.0%}")
        with col2:
            signals = intent.get("signals", [])
            if signals:
                st.markdown(f"**Signals:** {', '.join(signals[:5])}")
            secondary = intent.get("secondary_intents", [])
            if secondary:
                sec_labels = [s.get("intent", "") for s in secondary if isinstance(s, dict)]
                if sec_labels:
                    st.markdown(f"**Secondary Intents:** {', '.join(sec_labels)}")

    st.markdown("---")

    # SERP Results
    st.subheader("Top 10 SERP Results")
    serp = serp_results.get(selected_kw, [])
    if serp:
        serp_df = pd.DataFrame(serp)
        display_cols = ["rank", "title", "domain", "url"]
        existing = [c for c in display_cols if c in serp_df.columns]
        st.dataframe(serp_df[existing], use_container_width=True)
    else:
        st.info("SERP data not available for this keyword.")

    st.markdown("---")

    # Competitor gap analysis
    st.subheader("Competitor Gap Analysis")
    kw_gap = None
    for gap in gap_analyses:
        if gap.get("keyword") == selected_kw:
            kw_gap = gap
            break

    if kw_gap:
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Content", "Headings", "Meta Tags", "Keyword Usage", "Structure"
        ])

        with tab1:
            content = kw_gap.get("content_gap", {})
            if content:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Your Word Count", content.get("user_word_count", 0))
                with col2:
                    st.metric("Avg Competitor", content.get("avg_competitor_word_count", 0))
                with col3:
                    deficit = content.get("word_count_deficit", 0)
                    st.metric("Word Deficit", deficit, delta=f"-{deficit}" if deficit > 0 else "0")

        with tab2:
            heading = kw_gap.get("heading_gap", {})
            if heading:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Your H2s:** {heading.get('user_h2_count', 0)}")
                    st.markdown(f"**Your H3s:** {heading.get('user_h3_count', 0)}")
                with col2:
                    st.markdown(f"**Avg Competitor H2s:** {heading.get('avg_competitor_h2', 0)}")
                    st.markdown(f"**Avg Competitor H3s:** {heading.get('avg_competitor_h3', 0)}")

                missing = heading.get("missing_heading_topics", [])
                if missing:
                    st.markdown("**Missing Topics (from competitors):**")
                    for topic in missing:
                        st.markdown(f"- {topic}")

        with tab3:
            meta = kw_gap.get("meta_gap", {})
            if meta:
                st.markdown(f"**Title contains keyword:** {'Yes' if meta.get('title_contains_keyword') else 'No'}")
                st.markdown(f"**Meta desc contains keyword:** {'Yes' if meta.get('meta_desc_contains_keyword') else 'No'}")
                st.markdown(f"**Your title length:** {meta.get('user_title_length', 0)} chars")
                st.markdown(f"**Avg competitor title:** {meta.get('avg_competitor_title_length', 0)} chars")
                st.markdown(f"**Your meta desc length:** {meta.get('user_meta_desc_length', 0)} chars")
                st.markdown(f"**Avg competitor meta desc:** {meta.get('avg_competitor_meta_desc_length', 0)} chars")

        with tab4:
            kw_usage = kw_gap.get("keyword_usage_gap", {})
            if kw_usage:
                st.markdown(f"**Your keyword density:** {kw_usage.get('user_keyword_density', 0):.3f}%")
                st.markdown(f"**Avg competitor density:** {kw_usage.get('avg_competitor_keyword_density', 0):.3f}%")
                st.markdown(f"**Keyword in H1:** {'Yes' if kw_usage.get('keyword_in_h1') else 'No'}")
                st.markdown(f"**Keyword in H2:** {'Yes' if kw_usage.get('keyword_in_h2') else 'No'}")
                st.markdown(f"**Keyword in 1st paragraph:** {'Yes' if kw_usage.get('keyword_in_first_paragraph') else 'No'}")

        with tab5:
            structural = kw_gap.get("structural_gap", {})
            if structural:
                st.markdown(f"**Your schemas:** {', '.join(structural.get('user_schema_types', [])) or 'None'}")
                st.markdown(f"**Competitor schemas:** {', '.join(structural.get('common_competitor_schema_types', [])) or 'None'}")
                missing_schemas = structural.get("missing_schema_types", [])
                if missing_schemas:
                    st.markdown(f"**Missing schemas:** {', '.join(missing_schemas)}")
                st.markdown(f"**Your internal links:** {structural.get('user_internal_links', 0)}")
                st.markdown(f"**Avg competitor internal links:** {structural.get('avg_competitor_internal_links', 0)}")

        # Top competitors
        st.markdown("---")
        st.subheader("Top Competitors")
        render_competitor_table(kw_gap.get("top_competitors", []))
    else:
        st.info("Gap analysis not available for this keyword.")

    # Actions for this keyword
    st.markdown("---")
    st.subheader("Action Items for This Keyword")
    kw_actions = [a for a in actions if a.get("keyword") == selected_kw]
    if kw_actions:
        for action in kw_actions:
            render_action_card(action)
    else:
        st.info("No specific actions generated for this keyword.")
