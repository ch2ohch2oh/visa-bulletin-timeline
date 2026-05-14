# Visa Bulletin Timeline

Static site for tracking China EB-1, EB-2, and EB-3 employment-based visa bulletin trends over time.

Live site: https://ch2ohch2oh.github.io/visa-bulletin-timeline/

## Set up locally

```bash
UV_CACHE_DIR=.uv-cache uv sync
cd web
npm install
```

## Just targets

```bash
just update
just update-data
just web
```

- `just update` runs the full data refresh pipeline. It is an alias for `just update-data`.
- `just update-data` downloads missing visa bulletins, parses employment-based tables, and exports `web/src/data/china_series.json`.
- `just web` starts the Vite dev server on `127.0.0.1`.

## Deploy

GitHub Actions workflow `.github/workflows/update-data-and-deploy.yml` refreshes data monthly and deploys `web/dist` to GitHub Pages.
