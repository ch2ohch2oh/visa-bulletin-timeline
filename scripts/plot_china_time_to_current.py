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
TYPE_LABEL = {
    "final_action": "action date",
    "dates_for_filing": "filing date",
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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plot time-to-current (months) for China EB cutoff dates."
    )
    parser.add_argument(
        "--input",
        default="data/processed/employment_based_dates.csv",
        help="Input parsed CSV.",
    )
    parser.add_argument(
        "--output",
        default="artifacts/plots_china_only/eb_123_china_time_to_current_months.png",
        help="Output PNG path.",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    df = df[
        (df["preference_category"].isin(CATEGORY_MAP.keys()))
        & (df["table_type"].isin(TYPE_STYLE.keys()))
    ].copy()

    df["bulletin_date"] = pd.to_datetime(
        df["bulletin_month"] + " " + df["bulletin_year"].astype(str),
        format="%B %Y",
        errors="coerce",
    )

    col = "china_mainland_born"
    if col not in df.columns:
        raise SystemExit(f"Missing column: {col}")

    df["cutoff_date"] = df.apply(
        lambda r: parse_cutoff(r[col], r["bulletin_date"]), axis=1
    )
    df = df.dropna(subset=["bulletin_date", "cutoff_date"]).copy()

    # Approximate wait in months as day-difference / 30.4375.
    df["months_to_current"] = (
        (df["bulletin_date"] - df["cutoff_date"]).dt.days / 30.4375
    )

    fig, axes = plt.subplots(3, 1, figsize=(12, 11), sharex=True)
    for ax, (cat_raw, cat_label) in zip(axes, CATEGORY_MAP.items()):
        for ttype, style in TYPE_STYLE.items():
            part = df[
                (df["preference_category"] == cat_raw)
                & (df["table_type"] == ttype)
            ].sort_values("bulletin_date")
            if part.empty:
                continue
            ax.plot(
                part["bulletin_date"],
                part["months_to_current"],
                linestyle=style,
                marker="o",
                markersize=3,
                linewidth=1.4,
                label=TYPE_LABEL[ttype],
            )
        ax.set_title(f"{cat_label}")
        ax.set_ylabel("Months")
        ax.grid(True, alpha=0.25)
        ax.legend(loc="upper right", fontsize=10, frameon=True)

    axes[-1].set_xlabel("Bulletin Month")
    fig.suptitle("China EB-1/2/3: Time for Cutoff Date to Be Current", y=0.995)
    plt.tight_layout()

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out, dpi=160)
    plt.close()

    print(f"Wrote: {out}")


if __name__ == "__main__":
    main()
