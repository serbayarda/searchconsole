import streamlit as st
from ui.components import render_action_card
from utils.export import export_actions_report


def render():
    st.header("Action Items & Recommendations")

    actions = st.session_state.get("actions", [])

    if not actions:
        st.info("No action items available. Run the full analysis first.")
        return

    # Summary
    high = sum(1 for a in actions if a["priority"] == "high")
    medium = sum(1 for a in actions if a["priority"] == "medium")
    low = sum(1 for a in actions if a["priority"] == "low")

    cols = st.columns(4)
    with cols[0]:
        st.metric("Total Actions", len(actions))
    with cols[1]:
        st.metric("High Priority", high)
    with cols[2]:
        st.metric("Medium Priority", medium)
    with cols[3]:
        st.metric("Low Priority", low)

    st.markdown("---")

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        categories = sorted(set(a["category"] for a in actions))
        cat_filter = st.multiselect(
            "Filter by Category",
            options=categories,
            default=[],
            key="action_cat_filter",
        )

    with col2:
        priority_filter = st.multiselect(
            "Filter by Priority",
            options=["high", "medium", "low"],
            default=[],
            key="action_priority_filter",
        )

    with col3:
        effort_filter = st.multiselect(
            "Filter by Effort",
            options=["low", "medium", "high"],
            default=[],
            key="action_effort_filter",
        )

    # Apply filters
    filtered = actions
    if cat_filter:
        filtered = [a for a in filtered if a["category"] in cat_filter]
    if priority_filter:
        filtered = [a for a in filtered if a["priority"] in priority_filter]
    if effort_filter:
        filtered = [a for a in filtered if a["effort"] in effort_filter]

    st.markdown(f"Showing **{len(filtered)}** of {len(actions)} actions")

    # Export
    col1, col2 = st.columns(2)
    with col1:
        csv_data = export_actions_report(filtered, "csv")
        st.download_button(
            "Download Actions CSV",
            data=csv_data,
            file_name="seo_actions.csv",
            mime="text/csv",
        )
    with col2:
        json_data = export_actions_report(filtered, "json")
        st.download_button(
            "Download Actions JSON",
            data=json_data,
            file_name="seo_actions.json",
            mime="application/json",
        )

    st.markdown("---")

    # Quick wins first (high priority + low effort)
    quick_wins = [a for a in filtered if a["priority"] == "high" and a["effort"] == "low"]
    if quick_wins:
        st.subheader("Quick Wins (High Priority + Low Effort)")
        for action in quick_wins:
            render_action_card(action)
        st.markdown("---")

    # All actions grouped by category
    st.subheader("All Actions")

    # Group by category
    category_labels = {
        "meta": "Meta Tag Optimizations",
        "content": "Content Improvements",
        "structure": "Structural & Technical",
        "intent": "Search Intent Alignment",
        "ux": "UX Improvements",
    }

    for cat, label in category_labels.items():
        cat_actions = [a for a in filtered if a["category"] == cat]
        if cat_actions:
            st.subheader(label)
            for action in cat_actions:
                render_action_card(action)
