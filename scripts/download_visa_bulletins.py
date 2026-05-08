from __future__ import annotations

import re
import urllib.request
from datetime import date
from pathlib import Path

INDEX_URL = "https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin.html"
RAW_ROOT = Path("data/raw/visa_bulletins")
HTML_ROOT = RAW_ROOT / "html"
INDEX_FILE = RAW_ROOT / "visa_bulletin_main.html"
URLS_FILE = RAW_ROOT / "urls.txt"

LINK_RE = re.compile(
    r"/content/travel/en/legal/visa-law0/visa-bulletin/\d{4}/visa-bulletin-for-[a-z]+-\d{4}\.html"
)
MIN_BULLETIN_MONTH = date(2016, 5, 1)
MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read()


def bulletin_year(url: str) -> str:
    match = re.search(r"visa-bulletin-for-[a-z]+-(\d{4})\.html$", url)
    if not match:
        raise ValueError(f"Could not parse bulletin year from {url}")
    return match.group(1)


def bulletin_month(url: str) -> date:
    match = re.search(r"visa-bulletin-for-([a-z]+)-(\d{4})\.html$", url)
    if not match:
        raise ValueError(f"Could not parse bulletin month from {url}")
    return date(int(match.group(2)), MONTHS[match.group(1)], 1)


def discover_urls(index_html: str) -> list[str]:
    paths = sorted(set(LINK_RE.findall(index_html)))
    urls = [f"https://travel.state.gov{path}" for path in paths]
    return [url for url in urls if bulletin_month(url) >= MIN_BULLETIN_MONTH]


def main() -> None:
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    HTML_ROOT.mkdir(parents=True, exist_ok=True)

    index_html = fetch(INDEX_URL).decode("utf-8", errors="ignore")
    INDEX_FILE.write_text(index_html, encoding="utf-8")

    urls = discover_urls(index_html)
    URLS_FILE.write_text("\n".join(urls) + "\n", encoding="utf-8")

    downloaded = 0
    skipped = 0
    for url in urls:
        year = bulletin_year(url)
        out_dir = HTML_ROOT / year
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / Path(url).name
        if out_file.exists():
            skipped += 1
            continue
        out_file.write_bytes(fetch(url))
        downloaded += 1

    print(f"Discovered bulletins: {len(urls)}")
    print(f"Downloaded: {downloaded}")
    print(f"Skipped existing: {skipped}")


if __name__ == "__main__":
    main()
