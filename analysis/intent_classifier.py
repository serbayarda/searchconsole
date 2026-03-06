from __future__ import annotations


class IntentClassifier:
    # SERP features that signal specific intents
    INTENT_SIGNALS = {
        "informational": [
            "featured_snippet", "people_also_ask", "knowledge_graph",
            "knowledge_panel", "related_searches",
        ],
        "transactional": [
            "shopping", "paid", "commercial_units", "buy_on_google",
            "google_flights", "google_hotels",
        ],
        "navigational": [
            "site_links", "top_stories",
        ],
        "commercial": [
            "reviews", "local_pack", "carousel", "video",
            "images", "recipes",
        ],
    }

    def classify_with_dataforseo(
        self,
        keywords: list[str],
        dataforseo_service,
    ) -> dict[str, dict]:
        raw = dataforseo_service.get_search_intent(keywords)
        results = {}
        for kw, data in raw.items():
            results[kw] = {
                "primary_intent": data.get("primary_intent", "informational"),
                "probability": data.get("probability", 0.0),
                "secondary_intents": data.get("secondary_intents", []),
                "source": "dataforseo",
            }
        return results

    def classify_from_serp_features(
        self,
        keyword: str,
        serp_features: list[str],
    ) -> dict:
        if not serp_features:
            return {
                "intent": "informational",
                "confidence": 0.3,
                "signals": [],
            }

        scores = {"informational": 0, "transactional": 0, "navigational": 0, "commercial": 0}
        matched_signals = []

        for feature in serp_features:
            feature_lower = feature.lower()
            for intent, signal_list in self.INTENT_SIGNALS.items():
                if feature_lower in [s.lower() for s in signal_list]:
                    scores[intent] += 1
                    matched_signals.append(f"{feature}->{intent}")

        if sum(scores.values()) == 0:
            return {
                "intent": "informational",
                "confidence": 0.3,
                "signals": [],
            }

        top_intent = max(scores, key=scores.get)
        total = sum(scores.values())
        confidence = scores[top_intent] / total if total > 0 else 0.3

        return {
            "intent": top_intent,
            "confidence": confidence,
            "signals": matched_signals,
        }

    def merge_classifications(
        self,
        dataforseo_intent: dict | None,
        serp_intent: dict | None,
    ) -> dict:
        if not dataforseo_intent and not serp_intent:
            return {
                "primary_intent": "informational",
                "confidence": 0.3,
                "source": "default",
                "secondary_intents": [],
                "signals": [],
            }

        if not dataforseo_intent:
            return {
                "primary_intent": serp_intent["intent"],
                "confidence": serp_intent["confidence"],
                "source": "serp_features",
                "secondary_intents": [],
                "signals": serp_intent.get("signals", []),
            }

        if not serp_intent:
            return {
                "primary_intent": dataforseo_intent.get("primary_intent", "informational"),
                "confidence": dataforseo_intent.get("probability", 0.5),
                "source": "dataforseo",
                "secondary_intents": dataforseo_intent.get("secondary_intents", []),
                "signals": [],
            }

        dfs_intent = dataforseo_intent.get("primary_intent", "informational")
        dfs_prob = dataforseo_intent.get("probability", 0.5)
        serp_int = serp_intent.get("intent", "informational")
        serp_conf = serp_intent.get("confidence", 0.3)

        # If they agree, boost confidence
        if dfs_intent.lower() == serp_int.lower():
            return {
                "primary_intent": dfs_intent,
                "confidence": min(1.0, (dfs_prob + serp_conf) / 2 + 0.15),
                "source": "both_agree",
                "secondary_intents": dataforseo_intent.get("secondary_intents", []),
                "signals": serp_intent.get("signals", []),
            }

        # If they disagree, use the one with higher confidence
        if dfs_prob >= serp_conf:
            return {
                "primary_intent": dfs_intent,
                "confidence": dfs_prob,
                "source": "dataforseo",
                "secondary_intents": [
                    {"intent": serp_int, "confidence": serp_conf, "source": "serp_features"}
                ] + dataforseo_intent.get("secondary_intents", []),
                "signals": serp_intent.get("signals", []),
            }
        else:
            return {
                "primary_intent": serp_int,
                "confidence": serp_conf,
                "source": "serp_features",
                "secondary_intents": [
                    {"intent": dfs_intent, "confidence": dfs_prob, "source": "dataforseo"}
                ],
                "signals": serp_intent.get("signals", []),
            }

    def get_intent_description(self, intent: str) -> str:
        descriptions = {
            "informational": "User wants to learn or find information. Content should educate with guides, tutorials, FAQs.",
            "transactional": "User wants to buy or complete an action. Page should have clear CTAs, pricing, product details.",
            "navigational": "User looking for a specific website/page. Ensure strong brand presence and easy navigation.",
            "commercial": "User researching before purchase. Content should compare options, show reviews, highlight benefits.",
        }
        return descriptions.get(intent.lower(), "Unknown intent type.")

    def get_intent_recommendations(self, intent: str) -> list[str]:
        recs = {
            "informational": [
                "Add comprehensive FAQ section",
                "Include step-by-step guides with visuals",
                "Add table of contents for long content",
                "Use clear H2/H3 headings for scanability",
                "Add related internal links to deeper content",
            ],
            "transactional": [
                "Add clear, prominent CTAs above the fold",
                "Include pricing information or comparison tables",
                "Add trust signals (reviews, testimonials, badges)",
                "Simplify the conversion path (fewer clicks to action)",
                "Add urgency elements (limited time, stock levels)",
            ],
            "navigational": [
                "Ensure brand name is prominent in title and H1",
                "Add sitelinks-friendly structure with clear sections",
                "Include quick links to popular pages",
                "Optimize meta description with brand messaging",
                "Ensure fast page load for returning users",
            ],
            "commercial": [
                "Add comparison tables vs competitors",
                "Include detailed product/service reviews",
                "Add pros and cons lists",
                "Include case studies or success stories",
                "Add 'Best for...' or 'Who is this for?' sections",
            ],
        }
        return recs.get(intent.lower(), [])
