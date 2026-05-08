from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import List

from bs4 import BeautifulSoup

ROOT = Path("data/raw/visa_bulletins/html")
OUT_CSV = Path("data/processed/employment_based_dates.csv")
OUT_JSON = Path("data/processed/employment_based_dates.json")

SECTION_A = "FINAL ACTION DATES FOR EMPLOYMENT-BASED PREFERENCE CASES"
SECTION_B = "DATES FOR FILING OF EMPLOYMENT-BASED VISA APPLICATIONS"


def normalize_text(s: str) -> str:
    s = s.replace("\xa0", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def month_year_from_filename(name: str) -> tuple[str, str]:
    m = re.search(r"visa-bulletin-for-([a-z]+)-(\d{4})\.html$", name)
    if not m:
        return "", ""
    return m.group(1).capitalize(), m.group(2)


def clean_cell(cell) -> str:
    text = cell.get_text(" ", strip=True)
    return normalize_text(text)


def classify_table_label(text: str) -> str | None:
    upper = normalize_text(text).upper()
    upper = upper.replace("\u00a0", " ")
    if SECTION_A in upper:
        return "final_action"
    if SECTION_B in upper:
        return "dates_for_filing"
    return None


def find_nearest_label(table) -> str | None:
    # Walk backwards through previous nodes to find nearest A/B heading.
    for node in table.find_all_previous(limit=60):
        if getattr(node, "name", None) in {"p", "b", "u", "div", "td", "span"}:
            label = classify_table_label(node.get_text(" ", strip=True))
            if label:
                return label
    return None


def parse_file(path: Path) -> List[dict]:
    html = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "lxml")
    month, year = month_year_from_filename(path.name)

    out: List[dict] = []
    for table in soup.find_all("table"):
        label = find_nearest_label(table)
        if not label:
            continue

        rows = table.find_all("tr")
        if len(rows) < 2:
            continue

        header_cells = rows[0].find_all(["td", "th"])
        headers = [clean_cell(c) for c in header_cells]
        if len(headers) < 2:
            continue

        # Validate this is an employment-based table by first header cell.
        if "Employment" not in headers[0]:
            continue

        for tr in rows[1:]:
            cells = tr.find_all(["td", "th"])
            values = [clean_cell(c) for c in cells]
            if len(values) < 2:
                continue

            row = {
                "source_file": str(path),
                "bulletin_year": year,
                "bulletin_month": month,
                "table_type": label,
                "preference_category": values[0],
            }

            # Map country columns from header row.
            for i in range(1, min(len(headers), len(values))):
                col = headers[i]
                key = re.sub(r"[^a-z0-9]+", "_", col.lower()).strip("_")
                row[key] = values[i]

            out.append(row)

    return out


def main() -> None:
    files = sorted(ROOT.glob("*/*.html"))
    records: List[dict] = []
    for f in files:
        records.extend(parse_file(f))

    if not records:
        raise SystemExit("No employment-based table rows parsed.")

    # Stable column ordering.
    fieldnames = [
        "source_file",
        "bulletin_year",
        "bulletin_month",
        "table_type",
        "preference_category",
    ]
    dynamic = sorted({k for r in records for k in r.keys() if k not in set(fieldnames)})
    fieldnames.extend(dynamic)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in records:
            w.writerow(r)

    with OUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    print(f"Parsed records: {len(records)}")
    print(f"CSV: {OUT_CSV}")
    print(f"JSON: {OUT_JSON}")


if __name__ == "__main__":
    main()
