import streamlit as st
from auth.google_oauth import (
    handle_oauth_callback,
    get_authenticated_credentials,
    render_login_ui,
    logout,
)
from services.search_console import SearchConsoleService
from services.dataforseo import DataForSEOService, DataForSEOError
from services.scraping import ScrapingService
from analysis.keyword_analyzer import KeywordAnalyzer
from analysis.intent_classifier import IntentClassifier
from analysis.competitor_analyzer import CompetitorAnalyzer
from analysis.action_generator import ActionGenerator
from cache.cache_manager import CacheManager
from config.settings import (
    DATAFORSEO_LOGIN,
    DATAFORSEO_PASSWORD,
    SCRAPINGBEE_API_KEY,
    MAX_KEYWORDS_TO_ANALYZE,
    MAX_COMPETITOR_PAGES,
    CACHE_DIR,
    CACHE_TTL_SERP,
)


st.set_page_config(
    page_title="SEO Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    # Handle OAuth callback
    handle_oauth_callback()

    # Check authentication
    credentials = get_authenticated_credentials()
    if credentials is None:
        st.title("SEO Analyzer")
        st.markdown("Connect to Google Search Console, analyze your keywords, scrape competitors, and get actionable recommendations.")
        render_login_ui()
        return

    # Sidebar
    with st.sidebar:
        st.title("SEO Analyzer")
        st.markdown("---")

        # Property selection
        if "selected_property" not in st.session_state:
            render_property_selector(credentials)
            return

        st.success(f"Property: {st.session_state['selected_property']}")

        if st.button("Change Property"):
            for key in ["selected_property", "analysis_complete", "gsc_data",
                        "opportunities", "user_page_data", "serp_results",
                        "intent_data", "competitor_data", "gap_analyses", "actions",
                        "summary_stats", "date_series", "selected_keyword"]:
                st.session_state.pop(key, None)
            st.rerun()

        st.markdown("---")

        # Navigation
        page = st.radio(
            "Navigation",
            ["Overview", "Keywords", "Keyword Detail", "Competitors", "Actions"],
            key="nav_page",
        )

        st.markdown("---")

        # Re-run analysis
        if st.button("Re-run Analysis"):
            for key in ["analysis_complete", "gsc_data", "opportunities",
                        "user_page_data", "serp_results", "intent_data",
                        "competitor_data", "gap_analyses", "actions",
                        "summary_stats", "date_series"]:
                st.session_state.pop(key, None)
            st.rerun()

        # Analysis settings
        with st.expander("Analysis Settings"):
            st.session_state["max_keywords"] = st.slider(
                "Max keywords to analyze",
                5, 100, MAX_KEYWORDS_TO_ANALYZE, key="max_kw_slider",
            )
            st.session_state["min_impressions"] = st.number_input(
                "Min impressions filter",
                0, 10000, 100, step=50, key="min_imp_setting",
            )

        st.markdown("---")
        if st.button("Logout"):
            logout()
            st.rerun()

    # Run analysis if not done
    if "analysis_complete" not in st.session_state:
        run_full_analysis(credentials)
        return

    # Render selected page
    if page == "Overview":
        from ui.pages.overview import render
        render()
    elif page == "Keywords":
        from ui.pages.keywords import render
        render()
    elif page == "Keyword Detail":
        from ui.pages.keyword_detail import render
        render()
    elif page == "Competitors":
        from ui.pages.competitors import render
        render()
    elif page == "Actions":
        from ui.pages.actions import render
        render()


def render_property_selector(credentials):
    st.subheader("Select Property")

    try:
        service = SearchConsoleService(credentials)
        properties = service.list_properties()
    except Exception as e:
        st.error(f"Failed to fetch properties: {e}")
        return

    if not properties:
        st.warning("No Search Console properties found for this account.")
        return

    options = [p["siteUrl"] for p in properties]
    selected = st.selectbox("Choose a property", options, key="property_select")

    if st.button("Start Analysis"):
        st.session_state["selected_property"] = selected
        st.rerun()


def run_full_analysis(credentials):
    site_url = st.session_state["selected_property"]
    max_keywords = st.session_state.get("max_keywords", MAX_KEYWORDS_TO_ANALYZE)
    min_impressions = st.session_state.get("min_impressions", 100)

    st.title("Running SEO Analysis...")
    progress_text = st.empty()
    progress = st.progress(0)
    status = st.empty()
    progress_text.text("Initializing...")

    cache = CacheManager(CACHE_DIR, ttl_seconds=CACHE_TTL_SERP)

    try:
        # Phase 1: Fetch GSC data
        progress_text.text("Fetching Search Console data...")
        progress.progress(5)
        status.info("Connecting to Google Search Console API...")

        gsc_service = SearchConsoleService(credentials)
        gsc_data = gsc_service.fetch_search_analytics(site_url)
        date_series = gsc_service.fetch_date_series(site_url)

        st.session_state["gsc_data"] = gsc_data
        st.session_state["date_series"] = date_series

        if gsc_data.empty:
            progress.progress(100)
            st.warning("No search analytics data found for this property.")
            st.session_state["analysis_complete"] = True
            st.session_state["summary_stats"] = {}
            st.session_state["opportunities"] = gsc_data
            st.session_state["actions"] = []
            st.session_state["gap_analyses"] = []
            st.rerun()
            return

        # Phase 2: Identify opportunities
        progress_text.text("Identifying keyword opportunities...")
        progress.progress(15)
        status.info(f"Analyzing {len(gsc_data)} keyword-page combinations...")

        analyzer = KeywordAnalyzer(min_impressions=min_impressions)
        stats = analyzer.get_summary_stats(gsc_data)
        st.session_state["summary_stats"] = stats

        opportunities = analyzer.identify_opportunities(gsc_data)
        opportunities = opportunities.head(max_keywords)
        st.session_state["opportunities"] = opportunities

        if opportunities.empty:
            progress.progress(100)
            st.info("No keyword opportunities found with current filters. Try lowering the minimum impressions.")
            st.session_state["analysis_complete"] = True
            st.session_state["actions"] = []
            st.session_state["gap_analyses"] = []
            st.rerun()
            return

        # Phase 3: Scrape user's pages
        progress_text.text("Scraping your pages...")
        progress.progress(25)
        unique_pages = opportunities["page"].unique().tolist()
        status.info(f"Scraping {len(unique_pages)} of your landing pages...")

        scraper = ScrapingService(SCRAPINGBEE_API_KEY)
        user_pages = {}

        for i, page_url in enumerate(unique_pages):
            cache_key = cache.make_key("scrape", page_url)
            cached = cache.get(cache_key)
            if cached:
                user_pages[page_url] = cached
            else:
                page_data = scraper.scrape_page(page_url)
                user_pages[page_url] = page_data
                cache.set(cache_key, page_data)

            pct = 25 + int(10 * (i + 1) / len(unique_pages))
            progress_text.text(f"Scraping your pages ({i+1}/{len(unique_pages)})...")
            progress.progress(pct)

        st.session_state["user_page_data"] = user_pages

        # Phase 4: DataForSEO - SERP + Intent
        progress_text.text("Analyzing SERPs for top keywords...")
        progress.progress(40)

        dataforseo = DataForSEOService(DATAFORSEO_LOGIN, DATAFORSEO_PASSWORD)
        keywords = opportunities["query"].unique().tolist()

        # Get search intent (batch)
        status.info(f"Classifying search intent for {len(keywords)} keywords...")
        try:
            intent_classifier = IntentClassifier()
            raw_intents = intent_classifier.classify_with_dataforseo(keywords, dataforseo)
        except DataForSEOError as e:
            st.warning(f"Intent classification failed: {e}. Proceeding without intent data.")
            raw_intents = {}

        progress_text.text("Fetching SERP results...")
        progress.progress(45)

        # Get SERP results per keyword
        serp_results = {}
        serp_features_map = {}
        for i, kw in enumerate(keywords):
            cache_key = cache.make_key("serp", kw)
            cached = cache.get(cache_key)
            if cached:
                serp_results[kw] = cached
            else:
                try:
                    results = dataforseo.get_serp_results(kw)
                    serp_results[kw] = results
                    cache.set(cache_key, results)
                except DataForSEOError:
                    serp_results[kw] = []

            # Get SERP features for intent classification
            cache_key_feat = cache.make_key("serp_feat", kw)
            cached_feat = cache.get(cache_key_feat)
            if cached_feat:
                serp_features_map[kw] = cached_feat
            else:
                try:
                    features = dataforseo.get_serp_features(kw)
                    serp_features_map[kw] = features
                    cache.set(cache_key_feat, features)
                except DataForSEOError:
                    serp_features_map[kw] = []

            pct = 45 + int(15 * (i + 1) / len(keywords))
            progress_text.text(f"Fetching SERPs ({i+1}/{len(keywords)})...")
            progress.progress(pct)

        st.session_state["serp_results"] = serp_results

        # Merge intent classifications
        merged_intents = {}
        for kw in keywords:
            dfs_intent = raw_intents.get(kw)
            serp_features = serp_features_map.get(kw, [])
            serp_intent = intent_classifier.classify_from_serp_features(kw, serp_features)
            merged = intent_classifier.merge_classifications(dfs_intent, serp_intent)
            merged_intents[kw] = merged

        st.session_state["intent_data"] = merged_intents

        # Phase 5: Scrape competitor pages
        progress_text.text("Scraping competitor pages...")
        progress.progress(65)

        competitor_data = {}
        all_comp_urls = set()
        for kw, results in serp_results.items():
            for r in results[:MAX_COMPETITOR_PAGES]:
                comp_url = r.get("url", "")
                if comp_url:
                    all_comp_urls.add(comp_url)

        all_comp_urls = list(all_comp_urls)
        status.info(f"Scraping {len(all_comp_urls)} competitor pages...")

        comp_page_data = {}
        for i, comp_url in enumerate(all_comp_urls):
            cache_key = cache.make_key("scrape_comp", comp_url)
            cached = cache.get(cache_key)
            if cached:
                comp_page_data[comp_url] = cached
            else:
                page_data = scraper.scrape_page(comp_url)
                comp_page_data[comp_url] = page_data
                cache.set(cache_key, page_data)

            pct = 65 + int(15 * (i + 1) / len(all_comp_urls))
            progress_text.text(f"Scraping competitors ({i+1}/{len(all_comp_urls)})...")
            progress.progress(min(80, pct))

        st.session_state["competitor_data"] = comp_page_data

        # Phase 6: Gap analysis
        progress_text.text("Performing competitor gap analysis...")
        progress.progress(82)
        status.info("Comparing your pages against competitors...")

        comp_analyzer = CompetitorAnalyzer()
        gap_analyses = []

        for _, row in opportunities.iterrows():
            kw = row["query"]
            page_url = row["page"]
            user_page = user_pages.get(page_url, {"url": page_url})

            # Get competitor pages for this keyword
            kw_serp = serp_results.get(kw, [])
            comp_pages = []
            for r in kw_serp[:MAX_COMPETITOR_PAGES]:
                comp_url = r.get("url", "")
                if comp_url in comp_page_data:
                    comp_pages.append(comp_page_data[comp_url])

            gap = comp_analyzer.analyze_competitor_gap(user_page, comp_pages, kw)
            gap_analyses.append(gap)

        st.session_state["gap_analyses"] = gap_analyses

        # Phase 7: Generate actions
        progress_text.text("Generating recommendations...")
        progress.progress(90)
        status.info("Creating prioritized action items...")

        action_gen = ActionGenerator()
        actions = action_gen.generate_actions(
            keyword_opportunities=opportunities,
            intent_classifications=merged_intents,
            competitor_gaps=gap_analyses,
            user_page_data=list(user_pages.values()),
        )
        st.session_state["actions"] = actions

        progress_text.text("Analysis complete!")
        progress.progress(100)
        status.success(
            f"Analysis complete! Found {len(opportunities)} keyword opportunities "
            f"and generated {len(actions)} action items."
        )

        st.session_state["analysis_complete"] = True
        st.rerun()

    except Exception as e:
        progress.progress(100)
        st.error(f"Analysis failed: {str(e)}")
        st.exception(e)


if __name__ == "__main__":
    main()
