from __future__ import annotations
import requests
from requests.auth import HTTPBasicAuth
import time


class DataForSEOError(Exception):
    pass


class DataForSEOService:
    BASE_URL = "https://api.dataforseo.com/v3"

    def __init__(self, login: str, password: str):
        self._auth = HTTPBasicAuth(login, password)
        self._session = requests.Session()
        self._session.auth = self._auth
        self._session.headers.update({"Content-Type": "application/json"})

    def get_serp_results(
        self,
        keyword: str,
        location_code: int = 2840,
        language_code: str = "en",
        depth: int = 10,
    ) -> list[dict]:
        endpoint = f"{self.BASE_URL}/serp/google/organic/live/advanced"
        payload = [
            {
                "keyword": keyword,
                "location_code": location_code,
                "language_code": language_code,
                "depth": depth,
            }
        ]
        response = self._post(endpoint, payload)
        results = []
        tasks = response.get("tasks", [])
        if not tasks:
            return results

        task = tasks[0]
        task_result = task.get("result", [])
        if not task_result:
            return results

        items = task_result[0].get("items", [])
        rank = 0
        for item in items:
            if item.get("type") == "organic":
                rank += 1
                results.append({
                    "rank": rank,
                    "url": item.get("url", ""),
                    "domain": item.get("domain", ""),
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "breadcrumb": item.get("breadcrumb", ""),
                })
                if rank >= depth:
                    break

        return results

    def get_serp_features(
        self,
        keyword: str,
        location_code: int = 2840,
        language_code: str = "en",
    ) -> list[str]:
        endpoint = f"{self.BASE_URL}/serp/google/organic/live/advanced"
        payload = [
            {
                "keyword": keyword,
                "location_code": location_code,
                "language_code": language_code,
                "depth": 10,
            }
        ]
        response = self._post(endpoint, payload)
        features = set()
        tasks = response.get("tasks", [])
        if not tasks:
            return list(features)

        task_result = tasks[0].get("result", [])
        if not task_result:
            return list(features)

        items = task_result[0].get("items", [])
        for item in items:
            item_type = item.get("type", "")
            if item_type and item_type != "organic":
                features.add(item_type)

        return list(features)

    def get_search_intent(
        self,
        keywords: list[str],
        language_name: str = "English",
    ) -> dict[str, dict]:
        endpoint = f"{self.BASE_URL}/dataforseo_labs/google/search_intent/live"
        # Batch in chunks of 1000
        all_results = {}
        for i in range(0, len(keywords), 1000):
            chunk = keywords[i:i + 1000]
            payload = [
                {
                    "keywords": chunk,
                    "language_name": language_name,
                }
            ]
            response = self._post(endpoint, payload)
            tasks = response.get("tasks", [])
            if not tasks:
                continue

            task_result = tasks[0].get("result", [])
            if not task_result:
                continue

            items = task_result[0].get("items", [])
            for item in items:
                kw = item.get("keyword", "")
                intent_info = item.get("keyword_intent", {})
                if isinstance(intent_info, str):
                    all_results[kw] = {
                        "primary_intent": intent_info,
                        "probability": 1.0,
                        "secondary_intents": [],
                    }
                elif isinstance(intent_info, dict):
                    all_results[kw] = {
                        "primary_intent": intent_info.get("label", "informational"),
                        "probability": intent_info.get("probability", 0.0),
                        "secondary_intents": intent_info.get("secondary", []),
                    }
                else:
                    # Handle the case where intent is returned as a direct string field
                    intent_label = item.get("keyword_intent_label", "")
                    if not intent_label:
                        intent_label = str(intent_info) if intent_info else "informational"
                    all_results[kw] = {
                        "primary_intent": intent_label,
                        "probability": item.get("keyword_intent_probability", 0.0),
                        "secondary_intents": [],
                    }

        return all_results

    def get_keyword_data(
        self,
        keywords: list[str],
        location_code: int = 2840,
        language_name: str = "English",
    ) -> dict[str, dict]:
        endpoint = f"{self.BASE_URL}/dataforseo_labs/google/keyword_suggestions/live"
        payload = [
            {
                "keywords": keywords,
                "location_code": location_code,
                "language_name": language_name,
                "limit": len(keywords),
            }
        ]
        try:
            response = self._post(endpoint, payload)
            results = {}
            tasks = response.get("tasks", [])
            if not tasks:
                return results

            task_result = tasks[0].get("result", [])
            if not task_result:
                return results

            items = task_result[0].get("items", [])
            for item in items:
                kw = item.get("keyword", "")
                results[kw] = {
                    "search_volume": item.get("search_volume", 0),
                    "cpc": item.get("cpc", 0.0),
                    "competition": item.get("competition", 0.0),
                    "competition_level": item.get("competition_level", ""),
                }
            return results
        except DataForSEOError:
            return {}

    def _post(self, endpoint: str, data: list[dict], retries: int = 3) -> dict:
        for attempt in range(retries):
            try:
                resp = self._session.post(endpoint, json=data)
                if resp.status_code == 429:
                    wait = 2 ** attempt
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                result = resp.json()
                if result.get("status_code", 0) != 20000:
                    status_msg = result.get("status_message", "Unknown error")
                    raise DataForSEOError(
                        f"DataForSEO API error: {status_msg}"
                    )
                return result
            except requests.exceptions.HTTPError as e:
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise DataForSEOError(f"HTTP error: {e}") from e
            except requests.exceptions.RequestException as e:
                raise DataForSEOError(f"Request failed: {e}") from e
        raise DataForSEOError("Max retries exceeded")
