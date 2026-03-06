from __future__ import annotations
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import pandas as pd
from datetime import datetime, timedelta
from config.settings import DEFAULT_DATE_RANGE_DAYS


class SearchConsoleService:
    def __init__(self, credentials: Credentials):
        self._service = build("searchconsole", "v1", credentials=credentials)

    def list_properties(self) -> list[dict]:
        result = self._service.sites().list().execute()
        sites = result.get("siteEntry", [])
        return [
            {"siteUrl": s["siteUrl"], "permissionLevel": s.get("permissionLevel", "")}
            for s in sites
        ]

    def fetch_search_analytics(
        self,
        site_url: str,
        start_date: str | None = None,
        end_date: str | None = None,
        dimensions: list[str] | None = None,
        row_limit: int = 25000,
    ) -> pd.DataFrame:
        if dimensions is None:
            dimensions = ["query", "page"]

        if end_date is None:
            end_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
        if start_date is None:
            start_date = (
                datetime.now() - timedelta(days=DEFAULT_DATE_RANGE_DAYS + 3)
            ).strftime("%Y-%m-%d")

        all_rows = []
        start_row = 0

        while True:
            body = {
                "startDate": start_date,
                "endDate": end_date,
                "dimensions": dimensions,
                "rowLimit": row_limit,
                "startRow": start_row,
            }
            response = self._service.searchanalytics().query(
                siteUrl=site_url, body=body
            ).execute()

            rows = response.get("rows", [])
            if not rows:
                break

            for row in rows:
                keys = row.get("keys", [])
                entry = {
                    "clicks": row.get("clicks", 0),
                    "impressions": row.get("impressions", 0),
                    "ctr": row.get("ctr", 0.0),
                    "position": row.get("position", 0.0),
                }
                for i, dim in enumerate(dimensions):
                    entry[dim] = keys[i] if i < len(keys) else ""
                all_rows.append(entry)

            if len(rows) < row_limit:
                break
            start_row += row_limit

        df = pd.DataFrame(all_rows)
        if df.empty:
            return pd.DataFrame(columns=dimensions + ["clicks", "impressions", "ctr", "position"])

        col_order = dimensions + ["clicks", "impressions", "ctr", "position"]
        return df[col_order]

    def fetch_date_series(
        self,
        site_url: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        if end_date is None:
            end_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
        if start_date is None:
            start_date = (
                datetime.now() - timedelta(days=DEFAULT_DATE_RANGE_DAYS + 3)
            ).strftime("%Y-%m-%d")

        body = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": ["date"],
            "rowLimit": 25000,
        }
        response = self._service.searchanalytics().query(
            siteUrl=site_url, body=body
        ).execute()

        rows = response.get("rows", [])
        data = []
        for row in rows:
            data.append({
                "date": row["keys"][0],
                "clicks": row.get("clicks", 0),
                "impressions": row.get("impressions", 0),
                "ctr": row.get("ctr", 0.0),
                "position": row.get("position", 0.0),
            })

        df = pd.DataFrame(data)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        return df
