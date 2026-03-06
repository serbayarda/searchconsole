from __future__ import annotations
import statistics
from utils.text_analysis import keyword_density, keyword_in_text


class CompetitorAnalyzer:
    def analyze_competitor_gap(
        self,
        user_page: dict,
        competitor_pages: list[dict],
        keyword: str,
    ) -> dict:
        if not competitor_pages:
            return self._empty_gap(keyword, user_page.get("url", ""))

        valid_competitors = [p for p in competitor_pages if p.get("content_length", 0) > 0]
        if not valid_competitors:
            return self._empty_gap(keyword, user_page.get("url", ""))

        # Content gap
        comp_word_counts = [p.get("content_length", 0) for p in valid_competitors]
        avg_comp_wc = statistics.mean(comp_word_counts) if comp_word_counts else 0
        median_comp_wc = statistics.median(comp_word_counts) if comp_word_counts else 0
        user_wc = user_page.get("content_length", 0)

        content_gap = {
            "user_word_count": user_wc,
            "avg_competitor_word_count": round(avg_comp_wc),
            "median_competitor_word_count": round(median_comp_wc),
            "word_count_deficit": max(0, round(avg_comp_wc - user_wc)),
        }

        # Heading gap
        user_h1 = len(user_page.get("h1_tags", []))
        user_h2 = len(user_page.get("h2_tags", []))
        user_h3 = len(user_page.get("h3_tags", []))

        comp_h2_counts = [len(p.get("h2_tags", [])) for p in valid_competitors]
        comp_h3_counts = [len(p.get("h3_tags", [])) for p in valid_competitors]

        # Find heading topics competitors cover that user doesn't
        user_h2_topics = set(h.lower() for h in user_page.get("h2_tags", []))
        all_comp_h2s = []
        for p in valid_competitors:
            all_comp_h2s.extend(h.lower() for h in p.get("h2_tags", []))
        # Topics that appear in 2+ competitors but not in user's page
        from collections import Counter
        h2_counter = Counter(all_comp_h2s)
        missing_topics = [
            topic for topic, count in h2_counter.most_common(10)
            if count >= 2 and topic not in user_h2_topics
        ]

        heading_gap = {
            "user_h1_count": user_h1,
            "user_h2_count": user_h2,
            "user_h3_count": user_h3,
            "avg_competitor_h2": round(statistics.mean(comp_h2_counts), 1) if comp_h2_counts else 0,
            "avg_competitor_h3": round(statistics.mean(comp_h3_counts), 1) if comp_h3_counts else 0,
            "missing_heading_topics": missing_topics[:5],
        }

        # Meta gap
        user_title = user_page.get("title", "")
        user_meta = user_page.get("meta_description", "")
        comp_title_lens = [len(p.get("title", "")) for p in valid_competitors]
        comp_meta_lens = [len(p.get("meta_description", "")) for p in valid_competitors]

        meta_gap = {
            "user_title_length": len(user_title),
            "avg_competitor_title_length": round(statistics.mean(comp_title_lens)) if comp_title_lens else 0,
            "user_meta_desc_length": len(user_meta),
            "avg_competitor_meta_desc_length": round(statistics.mean(comp_meta_lens)) if comp_meta_lens else 0,
            "title_contains_keyword": keyword_in_text(user_title, keyword),
            "meta_desc_contains_keyword": keyword_in_text(user_meta, keyword),
        }

        # Keyword usage gap
        user_density = keyword_density(user_page.get("content_text", ""), keyword)
        comp_densities = [
            keyword_density(p.get("content_text", ""), keyword) for p in valid_competitors
        ]
        user_h1_texts = " ".join(user_page.get("h1_tags", []))
        user_h2_texts = " ".join(user_page.get("h2_tags", []))
        first_para = user_page.get("content_text", "")[:500]

        keyword_usage_gap = {
            "user_keyword_density": round(user_density, 3),
            "avg_competitor_keyword_density": round(statistics.mean(comp_densities), 3) if comp_densities else 0,
            "keyword_in_h1": keyword_in_text(user_h1_texts, keyword),
            "keyword_in_h2": keyword_in_text(user_h2_texts, keyword),
            "keyword_in_first_paragraph": keyword_in_text(first_para, keyword),
        }

        # Structural gap
        user_schema = user_page.get("schema_types", [])
        comp_schemas = []
        for p in valid_competitors:
            comp_schemas.extend(p.get("schema_types", []))
        schema_counter = Counter(comp_schemas)
        common_schemas = [s for s, c in schema_counter.most_common(5) if c >= 2]
        missing_schemas = [s for s in common_schemas if s not in user_schema]

        user_internal = len(user_page.get("internal_links", []))
        comp_internals = [len(p.get("internal_links", [])) for p in valid_competitors]

        structural_gap = {
            "user_schema_types": user_schema,
            "common_competitor_schema_types": common_schemas,
            "missing_schema_types": missing_schemas,
            "user_internal_links": user_internal,
            "avg_competitor_internal_links": round(statistics.mean(comp_internals), 1) if comp_internals else 0,
        }

        # Top competitors summary
        top_competitors = []
        for p in valid_competitors[:5]:
            top_competitors.append({
                "url": p.get("url", ""),
                "domain": p.get("url", "").split("/")[2] if "://" in p.get("url", "") else "",
                "word_count": p.get("content_length", 0),
                "h2_count": len(p.get("h2_tags", [])),
                "title": p.get("title", ""),
            })

        return {
            "keyword": keyword,
            "user_url": user_page.get("url", ""),
            "content_gap": content_gap,
            "heading_gap": heading_gap,
            "meta_gap": meta_gap,
            "keyword_usage_gap": keyword_usage_gap,
            "structural_gap": structural_gap,
            "top_competitors": top_competitors,
        }

    def _empty_gap(self, keyword: str, user_url: str) -> dict:
        return {
            "keyword": keyword,
            "user_url": user_url,
            "content_gap": {},
            "heading_gap": {},
            "meta_gap": {},
            "keyword_usage_gap": {},
            "structural_gap": {},
            "top_competitors": [],
        }
