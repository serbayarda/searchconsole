from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv()

# Google OAuth 2.0
GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8501")
GOOGLE_SCOPES: list[str] = ["https://www.googleapis.com/auth/webmasters.readonly"]

# DataForSEO
DATAFORSEO_LOGIN: str = os.getenv("DATAFORSEO_LOGIN", "")
DATAFORSEO_PASSWORD: str = os.getenv("DATAFORSEO_PASSWORD", "")

# ScrapingBee
SCRAPINGBEE_API_KEY: str = os.getenv("SCRAPINGBEE_API_KEY", "")

# Analysis defaults
DEFAULT_DATE_RANGE_DAYS: int = int(os.getenv("DEFAULT_DATE_RANGE_DAYS", "28"))
MAX_KEYWORDS_TO_ANALYZE: int = int(os.getenv("MAX_KEYWORDS_TO_ANALYZE", "50"))
MAX_COMPETITOR_PAGES: int = int(os.getenv("MAX_COMPETITOR_PAGES", "10"))

# Cache
CACHE_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache")
CACHE_TTL_GSC: int = 3600        # 1 hour
CACHE_TTL_SERP: int = 86400      # 24 hours
CACHE_TTL_INTENT: int = 604800   # 7 days
CACHE_TTL_SCRAPE: int = 21600    # 6 hours
