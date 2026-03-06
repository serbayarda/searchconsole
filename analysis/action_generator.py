from __future__ import annotations
import uuid
import pandas as pd
from analysis.intent_classifier import IntentClassifier


class ActionGenerator:
    def __init__(self):
        self._intent_classifier = IntentClassifier()

    def generate_actions(
        self,
        keyword_opportunities: pd.DataFrame,
        intent_classifications: dict,
        competitor_gaps: list[dict],
        user_page_data: list[dict],
    ) -> list[dict]:
        actions = []
        page_data_map = {p["url"]: p for p in user_page_data}

        for gap in competitor_gaps:
            keyword = gap.get("keyword", "")
            page_url = gap.get("user_url", "")
            intent = intent_classifications.get(keyword, {})
            page = page_data_map.get(page_url, {})

            actions.extend(self._generate_meta_actions(gap, keyword, page_url))
            actions.extend(self._generate_content_actions(gap, intent, keyword, page_url))
            actions.extend(self._generate_structure_actions(gap, keyword, page_url))
            actions.extend(self._generate_intent_actions(intent, page, keyword, page_url))
            actions.extend(self._generate_ux_actions(page, gap, keyword, page_url))

        # Sort by priority (high first), then impact
        priority_order = {"high": 0, "medium": 1, "low": 2}
        actions.sort(key=lambda a: (priority_order.get(a["priority"], 2), priority_order.get(a["estimated_impact"], 2)))

        return actions

    def _generate_meta_actions(self, gap: dict, keyword: str, page_url: str) -> list[dict]:
        actions = []
        meta = gap.get("meta_gap", {})
        if not meta:
            return actions

        if not meta.get("title_contains_keyword", True):
            actions.append({
                "id": str(uuid.uuid4())[:8],
                "category": "meta",
                "title": f"Add keyword to title tag",
                "description": f"Your title tag does not contain the target keyword '{keyword}'. Including the primary keyword in the title tag is one of the strongest on-page ranking signals.",
                "keyword": keyword,
                "page_url": page_url,
                "priority": "high",
                "effort": "low",
                "estimated_impact": "high",
                "specific_suggestions": [
                    f"Add '{keyword}' to the beginning of your title tag",
                    f"Keep title under 60 characters (current: {meta.get('user_title_length', 0)} chars)",
                    "Make the title compelling and click-worthy",
                ],
            })

        if not meta.get("meta_desc_contains_keyword", True):
            actions.append({
                "id": str(uuid.uuid4())[:8],
                "category": "meta",
                "title": f"Add keyword to meta description",
                "description": f"Meta description doesn't contain '{keyword}'. Google bolds matching keywords in search results, improving CTR.",
                "keyword": keyword,
                "page_url": page_url,
                "priority": "high",
                "effort": "low",
                "estimated_impact": "medium",
                "specific_suggestions": [
                    f"Naturally include '{keyword}' in the meta description",
                    f"Target 150-160 characters (current: {meta.get('user_meta_desc_length', 0)} chars)",
                    "Include a clear call-to-action in the description",
                ],
            })

        user_title_len = meta.get("user_title_length", 0)
        if user_title_len < 30 or user_title_len > 65:
            actions.append({
                "id": str(uuid.uuid4())[:8],
                "category": "meta",
                "title": "Optimize title tag length",
                "description": f"Title tag is {user_title_len} characters. Optimal range is 50-60 characters for full display in search results.",
                "keyword": keyword,
                "page_url": page_url,
                "priority": "medium",
                "effort": "low",
                "estimated_impact": "medium",
                "specific_suggestions": [
                    "Aim for 50-60 characters in your title tag",
                    "Front-load the most important keyword",
                    "Avoid truncation in search results",
                ],
            })

        return actions

    def _generate_content_actions(self, gap: dict, intent: dict, keyword: str, page_url: str) -> list[dict]:
        actions = []
        content = gap.get("content_gap", {})
        if not content:
            return actions

        deficit = content.get("word_count_deficit", 0)
        if deficit > 200:
            priority = "high" if deficit > 500 else "medium"
            actions.append({
                "id": str(uuid.uuid4())[:8],
                "category": "content",
                "title": f"Increase content depth (+{deficit} words)",
                "description": (
                    f"Your page has {content.get('user_word_count', 0)} words while "
                    f"top-ranking competitors average {content.get('avg_competitor_word_count', 0)} words. "
                    f"Adding ~{deficit} words of relevant content can help match competitor depth."
                ),
                "keyword": keyword,
                "page_url": page_url,
                "priority": priority,
                "effort": "high" if deficit > 800 else "medium",
                "estimated_impact": "high",
                "specific_suggestions": [
                    f"Add approximately {deficit} words of relevant content",
                    "Cover subtopics that competitors address",
                    "Add examples, case studies, or data to support points",
                    "Include related long-tail keyword variations naturally",
                ],
            })

        # Heading structure
        heading = gap.get("heading_gap", {})
        if heading:
            avg_comp_h2 = heading.get("avg_competitor_h2", 0)
            user_h2 = heading.get("user_h2_count", 0)
            if avg_comp_h2 > user_h2 + 2:
                missing = heading.get("missing_heading_topics", [])
                suggestions = [f"Add {round(avg_comp_h2 - user_h2)} more H2 subheadings"]
                if missing:
                    suggestions.append(f"Consider covering these topics: {', '.join(missing[:3])}")

                actions.append({
                    "id": str(uuid.uuid4())[:8],
                    "category": "content",
                    "title": "Improve heading structure",
                    "description": (
                        f"Your page has {user_h2} H2 headings vs competitor average of {avg_comp_h2}. "
                        f"More subheadings improve readability and help Google understand content structure."
                    ),
                    "keyword": keyword,
                    "page_url": page_url,
                    "priority": "medium",
                    "effort": "medium",
                    "estimated_impact": "medium",
                    "specific_suggestions": suggestions,
                })

        # Keyword density
        kw_gap = gap.get("keyword_usage_gap", {})
        if kw_gap:
            if not kw_gap.get("keyword_in_h1", True):
                actions.append({
                    "id": str(uuid.uuid4())[:8],
                    "category": "content",
                    "title": "Add keyword to H1 heading",
                    "description": f"The H1 heading doesn't contain '{keyword}'. The H1 is one of the most important on-page SEO elements.",
                    "keyword": keyword,
                    "page_url": page_url,
                    "priority": "high",
                    "effort": "low",
                    "estimated_impact": "high",
                    "specific_suggestions": [
                        f"Include '{keyword}' in your H1 tag naturally",
                        "Keep H1 descriptive and user-friendly",
                        "Use only one H1 per page",
                    ],
                })

            if not kw_gap.get("keyword_in_first_paragraph", True):
                actions.append({
                    "id": str(uuid.uuid4())[:8],
                    "category": "content",
                    "title": "Add keyword to first paragraph",
                    "description": f"The keyword '{keyword}' doesn't appear in the first paragraph. Early keyword placement signals topic relevance.",
                    "keyword": keyword,
                    "page_url": page_url,
                    "priority": "medium",
                    "effort": "low",
                    "estimated_impact": "medium",
                    "specific_suggestions": [
                        f"Mention '{keyword}' naturally in the opening paragraph",
                        "Set clear expectations about the page topic early",
                    ],
                })

        return actions

    def _generate_structure_actions(self, gap: dict, keyword: str, page_url: str) -> list[dict]:
        actions = []
        structural = gap.get("structural_gap", {})
        if not structural:
            return actions

        missing_schemas = structural.get("missing_schema_types", [])
        if missing_schemas:
            actions.append({
                "id": str(uuid.uuid4())[:8],
                "category": "structure",
                "title": f"Add schema markup ({', '.join(missing_schemas[:3])})",
                "description": (
                    f"Top competitors use schema types that your page is missing: {', '.join(missing_schemas)}. "
                    "Schema markup helps search engines understand your content and can enable rich results."
                ),
                "keyword": keyword,
                "page_url": page_url,
                "priority": "medium",
                "effort": "medium",
                "estimated_impact": "medium",
                "specific_suggestions": [
                    f"Add {schema} schema markup" for schema in missing_schemas[:3]
                ] + ["Use Google's Structured Data Testing Tool to validate"],
            })

        user_links = structural.get("user_internal_links", 0)
        avg_comp_links = structural.get("avg_competitor_internal_links", 0)
        if avg_comp_links > user_links + 5:
            actions.append({
                "id": str(uuid.uuid4())[:8],
                "category": "structure",
                "title": "Increase internal linking",
                "description": (
                    f"Your page has {user_links} internal links vs competitor average of {round(avg_comp_links)}. "
                    "More internal links help distribute page authority and improve crawlability."
                ),
                "keyword": keyword,
                "page_url": page_url,
                "priority": "medium",
                "effort": "low",
                "estimated_impact": "medium",
                "specific_suggestions": [
                    f"Add {round(avg_comp_links - user_links)} more relevant internal links",
                    "Link to related content pages using descriptive anchor text",
                    "Consider adding a 'Related Articles' section",
                ],
            })

        return actions

    def _generate_intent_actions(self, intent: dict, page: dict, keyword: str, page_url: str) -> list[dict]:
        actions = []
        primary_intent = intent.get("primary_intent", "").lower()
        if not primary_intent:
            return actions

        # Check if page content aligns with intent
        content = page.get("content_text", "").lower()
        title = page.get("title", "").lower()

        intent_recs = self._intent_classifier.get_intent_recommendations(primary_intent)
        intent_desc = self._intent_classifier.get_intent_description(primary_intent)

        # Check for intent misalignment signals
        misaligned = False
        if primary_intent == "transactional":
            # Transactional but no CTAs or pricing signals
            has_cta = any(w in content for w in ["buy", "order", "price", "add to cart", "sign up", "get started", "subscribe"])
            if not has_cta:
                misaligned = True
        elif primary_intent == "informational":
            # Informational but too short or salesy
            if page.get("content_length", 0) < 500:
                misaligned = True
        elif primary_intent == "commercial":
            has_comparison = any(w in content for w in ["vs", "compare", "best", "review", "top", "alternative"])
            if not has_comparison:
                misaligned = True

        if misaligned:
            actions.append({
                "id": str(uuid.uuid4())[:8],
                "category": "intent",
                "title": f"Align content with {primary_intent} intent",
                "description": (
                    f"Keyword intent is '{primary_intent}': {intent_desc} "
                    "Your page may not fully align with this intent."
                ),
                "keyword": keyword,
                "page_url": page_url,
                "priority": "high",
                "effort": "medium",
                "estimated_impact": "high",
                "specific_suggestions": intent_recs[:4],
            })
        else:
            # Still suggest intent optimization
            if intent_recs:
                actions.append({
                    "id": str(uuid.uuid4())[:8],
                    "category": "intent",
                    "title": f"Enhance {primary_intent} intent signals",
                    "description": f"Keyword intent is '{primary_intent}'. Strengthen alignment with these optimizations.",
                    "keyword": keyword,
                    "page_url": page_url,
                    "priority": "low",
                    "effort": "medium",
                    "estimated_impact": "medium",
                    "specific_suggestions": intent_recs[:3],
                })

        return actions

    def _generate_ux_actions(self, page: dict, gap: dict, keyword: str, page_url: str) -> list[dict]:
        actions = []

        # Images without alt text
        imgs_no_alt = page.get("images_without_alt", 0)
        if imgs_no_alt > 3:
            actions.append({
                "id": str(uuid.uuid4())[:8],
                "category": "ux",
                "title": f"Add alt text to {imgs_no_alt} images",
                "description": "Images without alt text hurt accessibility and miss keyword optimization opportunities.",
                "keyword": keyword,
                "page_url": page_url,
                "priority": "medium",
                "effort": "low",
                "estimated_impact": "low",
                "specific_suggestions": [
                    f"Add descriptive alt text to all {imgs_no_alt} images",
                    f"Include '{keyword}' naturally in 1-2 image alt tags",
                    "Make alt text descriptive for screen readers",
                ],
            })

        # Long content without table of contents
        content_length = page.get("content_length", 0)
        h2_count = len(page.get("h2_tags", []))
        if content_length > 1500 and h2_count >= 4:
            actions.append({
                "id": str(uuid.uuid4())[:8],
                "category": "ux",
                "title": "Add table of contents",
                "description": (
                    f"With {content_length} words and {h2_count} sections, a table of contents "
                    "improves navigation and can earn sitelinks in search results."
                ),
                "keyword": keyword,
                "page_url": page_url,
                "priority": "low",
                "effort": "low",
                "estimated_impact": "medium",
                "specific_suggestions": [
                    "Add a clickable table of contents at the top of the page",
                    "Use jump links that correspond to H2 headings",
                    "Consider a sticky/floating TOC for very long pages",
                ],
            })

        # Multiple H1 tags
        h1_count = len(page.get("h1_tags", []))
        if h1_count > 1:
            actions.append({
                "id": str(uuid.uuid4())[:8],
                "category": "ux",
                "title": f"Fix multiple H1 tags ({h1_count} found)",
                "description": "Multiple H1 tags can confuse search engines about the page's primary topic.",
                "keyword": keyword,
                "page_url": page_url,
                "priority": "medium",
                "effort": "low",
                "estimated_impact": "medium",
                "specific_suggestions": [
                    "Keep only one H1 tag per page",
                    f"Convert extra H1 tags to H2 (found: {', '.join(page.get('h1_tags', [])[:3])})",
                ],
            })
        elif h1_count == 0:
            actions.append({
                "id": str(uuid.uuid4())[:8],
                "category": "ux",
                "title": "Add H1 heading",
                "description": "Page is missing an H1 heading. Every page should have one H1 that describes the main topic.",
                "keyword": keyword,
                "page_url": page_url,
                "priority": "high",
                "effort": "low",
                "estimated_impact": "high",
                "specific_suggestions": [
                    f"Add a single H1 heading containing '{keyword}'",
                    "Make it descriptive and match the page title",
                ],
            })

        return actions
