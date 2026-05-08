# Agent Guidance

## Web Design Language

The `web/` app uses a minimal, report-style design. Preserve this direction when making UI changes.

- Keep the page quiet and data-first: white background, restrained typography, light borders, and sparse color.
- Do not add decorative cards, gradients, shadows, hero sections, illustrations, or marketing-style layout.
- Use Tailwind utility classes for layout and presentation. Avoid adding ad hoc CSS unless a utility cannot express the needed behavior cleanly.
- Keep chart styling thin and understated. Lines should stay light, gridlines subtle, and labels compact.
- Use color sparingly. Current convention: slate for final action date, blue for filing date, with dash pattern as secondary encoding.
- Keep explanatory text concise and close to the relevant chart area. Avoid long instructional blocks in the main header.
- Preserve mobile readability. Any new chart/table element must work at narrow widths without squeezed text or overlapping controls.

## Chart Behavior

- The main visualization is a D3-rendered stacked chart with EB-1, EB-2, and EB-3 panels.
- Preserve the existing toggle pattern for switching chart metrics unless there is a strong reason to change it.
- Tooltip values and labels should use reader-friendly terminology. Avoid exposing raw Visa Bulletin shorthand such as `C` in user-facing copy.
- If a category is current, present it as current or as zero wait time depending on context.

## Data Pipeline

- Raw official bulletin HTML belongs under `data/raw/visa_bulletins/html/`.
- Parsed data belongs under `data/processed/`.
- Frontend chart data belongs under `web/src/data/`.
- Update data through scripts in `scripts/`; do not hand-edit generated CSV/JSON except for emergency correction.
- After data or frontend changes, run:

```bash
UV_CACHE_DIR=.uv-cache uv run python scripts/parse_eb_tables.py
UV_CACHE_DIR=.uv-cache uv run python scripts/export_china_series_json.py
cd web && npm run build
```

## GitHub Pages

- `web/vite.config.js` sets the GitHub Pages base path for `visa-bulletin-timeline`.
- If the repository name changes, update the Pages base path before deploying.
