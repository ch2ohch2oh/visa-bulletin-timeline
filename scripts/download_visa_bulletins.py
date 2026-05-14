from __future__ import annotations

import re
import time
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
RETRY_DELAYS = (1, 3)


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    last_error: Exception | None = None
    for delay in (0, *RETRY_DELAYS):
        if delay:
            time.sleep(delay)
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read()
        except Exception as exc:
            last_error = exc
    assert last_error is not None
    raise RuntimeError(f"Failed to fetch {url}") from last_error


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
    filtered = [url for url in urls if bulletin_month(url) >= MIN_BULLETIN_MONTH]
    if not filtered:
        raise RuntimeError("No visa bulletin URLs discovered from the index page.")
    return filtered


def read_existing_urls() -> set[str]:
    if not URLS_FILE.exists():
        return set()
    return {
        line.strip()
        for line in URLS_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def should_download(out_file: Path) -> bool:
    return not out_file.exists() or out_file.stat().st_size == 0


def main() -> None:
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    HTML_ROOT.mkdir(parents=True, exist_ok=True)

    existing_urls = read_existing_urls()
    index_html = fetch(INDEX_URL).decode("utf-8", errors="ignore")
    write_text(INDEX_FILE, index_html)

    urls = discover_urls(index_html)
    write_text(URLS_FILE, "\n".join(urls) + "\n")

    latest_url = max(urls, key=bulletin_month)
    new_urls = sorted(set(urls) - existing_urls, key=bulletin_month)

    downloaded = 0
    skipped = 0
    refreshed_empty = 0
    for url in urls:
        year = bulletin_year(url)
        out_dir = HTML_ROOT / year
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / Path(url).name
        had_empty_file = out_file.exists() and out_file.stat().st_size == 0
        if not should_download(out_file):
            skipped += 1
            continue
        out_file.write_bytes(fetch(url))
        if out_file.exists() and out_file.stat().st_size == 0:
            raise RuntimeError(f"Downloaded empty bulletin file: {out_file}")
        if had_empty_file:
            refreshed_empty += 1
        downloaded += 1

    print(f"Discovered bulletins: {len(urls)}")
    print(f"Latest bulletin discovered: {bulletin_month(latest_url):%B %Y}")
    print(f"New bulletin URLs added: {len(new_urls)}")
    print(f"Downloaded: {downloaded}")
    print(f"Refreshed empty files: {refreshed_empty}")
    print(f"Skipped existing: {skipped}")


if __name__ == "__main__":
    main()
