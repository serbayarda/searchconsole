from __future__ import annotations
from scrapingbee import ScrapingBeeClient
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import json
import re


class ScrapingError(Exception):
    pass


class ScrapingService:
    def __init__(self, api_key: str):
        self._client = ScrapingBeeClient(api_key=api_key)

    def scrape_page(self, url: str, render_js: bool = True) -> dict:
        try:
            response = self._client.get(
                url,
                params={
                    "render_js": str(render_js).lower(),
                    "premium_proxy": "true",
                },
            )
            if response.status_code != 200:
                return self._empty_page_data(url, response.status_code)

            html = response.text
            return self._parse_html(html, url)

        except Exception as e:
            return self._empty_page_data(url, error=str(e))

    def scrape_pages_batch(
        self,
        urls: list[str],
        render_js: bool = True,
        progress_callback=None,
    ) -> list[dict]:
        results = []
        total = len(urls)
        for i, url in enumerate(urls):
            result = self.scrape_page(url, render_js)
            results.append(result)
            if progress_callback:
                progress_callback(i + 1, total)
        return results

    def _parse_html(self, html: str, url: str) -> dict:
        soup = BeautifulSoup(html, "html.parser")
        parsed_url = urlparse(url)
        base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"

        # Title
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""

        # Meta description
        meta_desc = ""
        meta_tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
        if meta_tag:
            meta_desc = meta_tag.get("content", "")

        # Meta robots
        meta_robots = ""
        robots_tag = soup.find("meta", attrs={"name": re.compile(r"robots", re.I)})
        if robots_tag:
            meta_robots = robots_tag.get("content", "")

        # Canonical
        canonical = ""
        canonical_tag = soup.find("link", attrs={"rel": "canonical"})
        if canonical_tag:
            canonical = canonical_tag.get("href", "")

        # Headings
        h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1")]
        h2_tags = [h.get_text(strip=True) for h in soup.find_all("h2")]
        h3_tags = [h.get_text(strip=True) for h in soup.find_all("h3")]

        # Remove script/style for content extraction
        for tag in soup.find_all(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        # Body text
        body = soup.find("body")
        content_text = body.get_text(separator=" ", strip=True) if body else ""
        content_text = re.sub(r"\s+", " ", content_text)

        # Links
        internal_links = []
        external_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            full_url = urljoin(url, href)
            parsed_link = urlparse(full_url)
            if parsed_link.netloc == parsed_url.netloc:
                internal_links.append(full_url)
            elif parsed_link.scheme in ("http", "https"):
                external_links.append(full_url)

        # Images without alt
        images = soup.find_all("img")
        images_without_alt = sum(
            1 for img in images if not img.get("alt", "").strip()
        )

        # Schema/JSON-LD
        schema_types = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                if isinstance(data, dict):
                    if "@type" in data:
                        schema_types.append(data["@type"])
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "@type" in item:
                            schema_types.append(item["@type"])
            except (json.JSONDecodeError, TypeError):
                continue

        return {
            "url": url,
            "status_code": 200,
            "title": title,
            "meta_description": meta_desc,
            "meta_robots": meta_robots,
            "canonical_url": canonical,
            "h1_tags": h1_tags,
            "h2_tags": h2_tags,
            "h3_tags": h3_tags,
            "content_text": content_text,
            "content_length": len(content_text.split()),
            "internal_links": list(set(internal_links)),
            "external_links": list(set(external_links)),
            "images_without_alt": images_without_alt,
            "schema_types": schema_types,
        }

    def _empty_page_data(self, url: str, status_code: int = 0, error: str = "") -> dict:
        return {
            "url": url,
            "status_code": status_code,
            "title": "",
            "meta_description": "",
            "meta_robots": "",
            "canonical_url": "",
            "h1_tags": [],
            "h2_tags": [],
            "h3_tags": [],
            "content_text": "",
            "content_length": 0,
            "internal_links": [],
            "external_links": [],
            "images_without_alt": 0,
            "schema_types": [],
            "error": error,
        }
