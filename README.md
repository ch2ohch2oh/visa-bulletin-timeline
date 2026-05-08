## Visa Bulletin Timeline

This repository builds a static web page for China EB-1/EB-2/EB-3 visa bulletin wait-time trends.

### Structure

```text
data/
  raw/visa_bulletins/html/      Official DOS bulletin HTML files
  processed/                    Parsed CSV/JSON outputs
scripts/
  download_visa_bulletins.py    Downloads only missing bulletin HTML files
  parse_eb_tables.py            Parses employment-based preference tables
  export_china_series_json.py   Exports chart-ready JSON for the web app
web/
  src/                          Vite + Tailwind + D3 single-page app
```

### Update data locally

```bash
UV_CACHE_DIR=.uv-cache uv sync
UV_CACHE_DIR=.uv-cache uv run python scripts/download_visa_bulletins.py
UV_CACHE_DIR=.uv-cache uv run python scripts/parse_eb_tables.py
UV_CACHE_DIR=.uv-cache uv run python scripts/export_china_series_json.py
```

### Run the web app

```bash
cd web
npm install
npm run dev
```

### Deploy

GitHub Actions workflow `.github/workflows/update-data-and-deploy.yml` refreshes data monthly and deploys `web/dist` to GitHub Pages.
