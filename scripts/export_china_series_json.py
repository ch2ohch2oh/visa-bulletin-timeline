from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

INPUT_CSV = Path("data/processed/employment_based_dates.csv")
OUTPUT_JSON = Path("web/src/data/china_series.json")
CATEGORY_MAP = {"1st": "EB-1", "2nd": "EB-2", "3rd": "EB-3"}
TABLE_TYPES = ["final_action", "dates_for_filing"]
LABELS = {"final_action": "final action date", "dates_for_filing": "filing date"}
REQUIRED_COLUMNS = {
    "bulletin_month",
    "bulletin_year",
    "preference_category",
    "table_type",
    "china_mainland_born",
}


def parse_cutoff(value: str, bulletin_date: pd.Timestamp):
    if pd.isna(value):
        return pd.NaT
    v = str(value).strip().upper()
    if v == "C":
        return bulletin_date
    if not v or v == "U":
        return pd.NaT
    return pd.to_datetime(v, format="%d%b%y", errors="coerce")


def clean_value(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip().upper()


def require_columns(df: pd.DataFrame) -> None:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise RuntimeError(f"Missing required columns: {', '.join(sorted(missing))}")


def main() -> None:
    df = pd.read_csv(INPUT_CSV)
    require_columns(df)
    df = df[(df["preference_category"].isin(CATEGORY_MAP)) & (df["table_type"].isin(TABLE_TYPES))].copy()
    if df.empty:
        raise RuntimeError("No China EB-1/EB-2/EB-3 rows found in parsed CSV.")
    df["bulletin_date"] = pd.to_datetime(
        df["bulletin_month"] + " " + df["bulletin_year"].astype(str),
        format="%B %Y",
        errors="coerce",
    )
    if df["bulletin_date"].isna().any():
        raise RuntimeError("Failed to parse one or more bulletin dates from the parsed CSV.")
    df["cutoff_date"] = df.apply(lambda r: parse_cutoff(r["china_mainland_born"], r["bulletin_date"]), axis=1)
    df = df.dropna(subset=["bulletin_date", "cutoff_date"]).copy()
    if df.empty:
        raise RuntimeError("No valid China cutoff dates available for frontend export.")
    df["months_to_current"] = (df["bulletin_date"] - df["cutoff_date"]).dt.days / 30.4375

    latest_bulletin_date = df["bulletin_date"].max()
    latest_rows = df[df["bulletin_date"] == latest_bulletin_date]

    out = []
    for raw, label in CATEGORY_MAP.items():
        for ttype in TABLE_TYPES:
            part = df[(df["preference_category"] == raw) & (df["table_type"] == ttype)].sort_values("bulletin_date")
            if part.empty:
                raise RuntimeError(f"Missing series data for {label} / {ttype}.")
            latest_part = latest_rows[
                (latest_rows["preference_category"] == raw) & (latest_rows["table_type"] == ttype)
            ]
            if latest_part.empty:
                raise RuntimeError(
                    f"Latest bulletin {latest_bulletin_date:%Y-%m-%d} is missing {label} / {ttype}."
                )
            out.append(
                {
                    "category": label,
                    "table_type": ttype,
                    "label": LABELS[ttype],
                    "data": [
                        [
                            bulletin_date.strftime("%Y-%m-%d"),
                            round(float(months_to_current), 3),
                            cutoff_date.strftime("%Y-%m-%d"),
                            clean_value(raw_value),
                        ]
                        for bulletin_date, months_to_current, cutoff_date, raw_value in zip(
                            part["bulletin_date"],
                            part["months_to_current"],
                            part["cutoff_date"],
                            part["china_mainland_born"],
                        )
                    ],
                }
            )

    OUTPUT_JSON.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT_JSON}")
    print(f"Latest bulletin exported: {latest_bulletin_date:%B %Y}")


if __name__ == "__main__":
    main()
