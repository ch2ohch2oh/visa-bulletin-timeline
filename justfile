update-data:
    UV_CACHE_DIR=.uv-cache uv run python scripts/download_visa_bulletins.py
    UV_CACHE_DIR=.uv-cache uv run python scripts/parse_eb_tables.py
    UV_CACHE_DIR=.uv-cache uv run python scripts/export_china_series_json.py

web:
    cd web && npm run dev -- --host 127.0.0.1
