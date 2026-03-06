from __future__ import annotations
import pandas as pd
import json
import io


def export_to_csv(data) -> bytes:
    if isinstance(data, list):
        df = pd.DataFrame(data)
    elif isinstance(data, pd.DataFrame):
        df = data
    else:
        raise ValueError("Data must be a list of dicts or a DataFrame")

    buffer = io.BytesIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue()


def export_to_json(data) -> bytes:
    if isinstance(data, pd.DataFrame):
        data = data.to_dict(orient="records")
    return json.dumps(data, indent=2, default=str).encode("utf-8")


def export_actions_report(actions: list[dict], format: str = "csv") -> bytes:
    df = pd.DataFrame(actions)
    cols = ["priority", "category", "title", "keyword", "page_url",
            "effort", "estimated_impact", "description", "specific_suggestions"]
    existing_cols = [c for c in cols if c in df.columns]
    df = df[existing_cols]

    if format == "json":
        return export_to_json(df)
    return export_to_csv(df)
