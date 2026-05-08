from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

CATEGORY_MAP = {
    "1st": "EB-1",
    "2nd": "EB-2",
    "3rd": "EB-3",
}

TYPE_STYLE = {
    "final_action": "-",
    "dates_for_filing": "--",
}


def parse_cutoff(value: str, bulletin_date: pd.Timestamp):
    if pd.isna(value):
        return pd.NaT
    v = str(value).strip().upper()
    if v == "C":
        return bulletin_date
    if not v or v == "U":
        return pd.NaT
    try:
        return pd.to_datetime(v, format="%d%b%y", errors="coerce")
    except Exception:
        return pd.NaT


def sanitize_filename(name: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in name).strip("_").lower()


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot EB action/filing date trends over bulletin month.")
    parser.add_argument(
        "--input",
        default="data/processed/employment_based_dates.csv",
        help="Input parsed CSV.",
    )
    parser.add_argument(
        "--output-dir",
        default="artifacts/plots",
        help="Output directory for PNG files.",
    )
    parser.add_argument(
        "--countries",
        default="",
        help="Comma-separated parsed country column names to plot (e.g. china_mainland_born).",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_path)
    df = df[df["preference_category"].isin(CATEGORY_MAP.keys())].copy()

    # Build bulletin month axis from year+month in source data.
    df["bulletin_date"] = pd.to_datetime(
        df["bulletin_month"] + " " + df["bulletin_year"].astype(str),
        format="%B %Y",
        errors="coerce",
    )

    # Candidate country columns from parser output.
    meta_cols = {
        "source_file",
        "bulletin_year",
        "bulletin_month",
        "bulletin_date",
        "table_type",
        "preference_category",
    }
    country_cols = [c for c in df.columns if c not in meta_cols]
    if args.countries.strip():
        requested = [c.strip() for c in args.countries.split(",") if c.strip()]
        country_cols = [c for c in country_cols if c in requested]

    for col in country_cols:
        subset = df[["bulletin_date", "table_type", "preference_category", col]].copy()
        subset["cutoff_date"] = subset.apply(
            lambda r: parse_cutoff(r[col], r["bulletin_date"]), axis=1
        )
        subset = subset.dropna(subset=["bulletin_date"])

        if subset["cutoff_date"].notna().sum() == 0:
            continue

        plt.figure(figsize=(12, 7))
        for cat_raw, cat_label in CATEGORY_MAP.items():
            for ttype, style in TYPE_STYLE.items():
                part = subset[
                    (subset["preference_category"] == cat_raw)
                    & (subset["table_type"] == ttype)
                ].sort_values("bulletin_date")
                if part["cutoff_date"].notna().sum() == 0:
                    continue
                plt.plot(
                    part["bulletin_date"],
                    part["cutoff_date"],
                    linestyle=style,
                    marker="o",
                    markersize=3,
                    linewidth=1.4,
                    label=f"{cat_label} - {ttype}",
                )

        plt.title(f"Employment-Based Cutoff Trends ({col})")
        plt.xlabel("Bulletin Month")
        plt.ylabel("Cutoff Date")
        plt.grid(True, alpha=0.25)
        plt.legend(fontsize=8)
        plt.tight_layout()

        out_file = out_dir / f"eb_123_{sanitize_filename(col)}.png"
        plt.savefig(out_file, dpi=160)
        plt.close()

    print(f"Plots written to: {out_dir}")


if __name__ == "__main__":
    main()
