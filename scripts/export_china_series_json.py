from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

INPUT_CSV = Path("data/processed/employment_based_dates.csv")
OUTPUT_JSON = Path("web/src/data/china_series.json")
CATEGORY_MAP = {"1st": "EB-1", "2nd": "EB-2", "3rd": "EB-3"}
TABLE_TYPES = ["final_action", "dates_for_filing"]
LABELS = {"final_action": "final action date", "dates_for_filing": "filing date"}


def parse_cutoff(value: str, bulletin_date: pd.Timestamp):
    if pd.isna(value):
        return pd.NaT
    v = str(value).strip().upper()
    if v == "C":
        return bulletin_date
    if not v or v == "U":
        return pd.NaT
    return pd.to_datetime(v, format="%d%b%y", errors="coerce")


def main() -> None:
    df = pd.read_csv(INPUT_CSV)
    df = df[(df["preference_category"].isin(CATEGORY_MAP)) & (df["table_type"].isin(TABLE_TYPES))].copy()
    df["bulletin_date"] = pd.to_datetime(
        df["bulletin_month"] + " " + df["bulletin_year"].astype(str),
        format="%B %Y",
        errors="coerce",
    )
    df["cutoff_date"] = df.apply(lambda r: parse_cutoff(r["china_mainland_born"], r["bulletin_date"]), axis=1)
    df = df.dropna(subset=["bulletin_date", "cutoff_date"]).copy()
    df["months_to_current"] = (df["bulletin_date"] - df["cutoff_date"]).dt.days / 30.4375

    out = []
    for raw, label in CATEGORY_MAP.items():
        for ttype in TABLE_TYPES:
            part = df[(df["preference_category"] == raw) & (df["table_type"] == ttype)].sort_values("bulletin_date")
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
                        ]
                        for bulletin_date, months_to_current, cutoff_date in zip(
                            part["bulletin_date"],
                            part["months_to_current"],
                            part["cutoff_date"],
                        )
                    ],
                }
            )

    OUTPUT_JSON.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
