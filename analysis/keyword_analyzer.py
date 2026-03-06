from __future__ import annotations
import pandas as pd
import numpy as np


# Industry-standard CTR curve by position
CTR_CURVE = {
    1: 0.317, 2: 0.247, 3: 0.187, 4: 0.136, 5: 0.095,
    6: 0.063, 7: 0.044, 8: 0.031, 9: 0.022, 10: 0.016,
    11: 0.012, 12: 0.010, 13: 0.008, 14: 0.007, 15: 0.006,
    16: 0.005, 17: 0.005, 18: 0.004, 19: 0.004, 20: 0.003,
}


class KeywordAnalyzer:
    def __init__(
        self,
        min_impressions: int = 100,
        max_position: float = 20.0,
        low_ctr_threshold: float = 0.03,
    ):
        self._min_impressions = min_impressions
        self._max_position = max_position
        self._low_ctr_threshold = low_ctr_threshold

    def identify_opportunities(self, gsc_data: pd.DataFrame) -> pd.DataFrame:
        if gsc_data.empty:
            return gsc_data

        df = gsc_data.copy()

        # Filter for meaningful data
        df = df[df["impressions"] >= self._min_impressions]
        df = df[df["position"] <= self._max_position]

        if df.empty:
            return df

        # Calculate expected CTR and gap
        df["expected_ctr"] = df["position"].apply(self.calculate_expected_ctr)
        df["ctr_gap"] = df["expected_ctr"] - df["ctr"]

        # Only keep keywords where CTR is below expected
        df = df[df["ctr_gap"] > 0]

        # Score opportunities
        df["opportunity_score"] = df.apply(self.score_opportunity, axis=1)

        # Sort by opportunity score
        df = df.sort_values("opportunity_score", ascending=False).reset_index(drop=True)

        return df

    def calculate_expected_ctr(self, position: float) -> float:
        pos_int = max(1, min(20, round(position)))
        return CTR_CURVE.get(pos_int, 0.003)

    def score_opportunity(self, row: pd.Series) -> float:
        impressions = row["impressions"]
        ctr_gap = row["ctr_gap"]

        # Position factor: keywords at 4-10 have highest improvement potential
        pos = row["position"]
        if 4 <= pos <= 10:
            position_factor = 1.5
        elif 2 <= pos < 4:
            position_factor = 1.2
        elif 10 < pos <= 15:
            position_factor = 1.0
        elif 15 < pos <= 20:
            position_factor = 0.7
        else:
            position_factor = 0.5

        return impressions * ctr_gap * position_factor

    def get_top_keywords_by_impressions(
        self, gsc_data: pd.DataFrame, n: int = 50
    ) -> pd.DataFrame:
        if gsc_data.empty:
            return gsc_data
        return gsc_data.nlargest(n, "impressions").reset_index(drop=True)

    def get_quick_wins(self, opportunities: pd.DataFrame, n: int = 10) -> pd.DataFrame:
        """Keywords at position 4-10 with high impressions - easiest to improve."""
        if opportunities.empty:
            return opportunities
        quick = opportunities[
            (opportunities["position"] >= 4) & (opportunities["position"] <= 10)
        ]
        return quick.head(n)

    def group_by_page(self, opportunities: pd.DataFrame) -> dict[str, pd.DataFrame]:
        if opportunities.empty or "page" not in opportunities.columns:
            return {}
        return {url: group for url, group in opportunities.groupby("page")}

    def get_summary_stats(self, gsc_data: pd.DataFrame) -> dict:
        if gsc_data.empty:
            return {
                "total_clicks": 0,
                "total_impressions": 0,
                "avg_ctr": 0.0,
                "avg_position": 0.0,
                "total_keywords": 0,
                "total_pages": 0,
            }
        return {
            "total_clicks": int(gsc_data["clicks"].sum()),
            "total_impressions": int(gsc_data["impressions"].sum()),
            "avg_ctr": float(gsc_data["ctr"].mean()),
            "avg_position": float(gsc_data["position"].mean()),
            "total_keywords": gsc_data["query"].nunique() if "query" in gsc_data.columns else 0,
            "total_pages": gsc_data["page"].nunique() if "page" in gsc_data.columns else 0,
        }
