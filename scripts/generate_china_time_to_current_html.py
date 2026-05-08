from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

INPUT_CSV = Path("data/processed/employment_based_dates.csv")
OUTPUT_HTML = Path("artifacts/plots_china_only/eb_123_china_time_to_current_months.html")

CATEGORY_MAP = {
    "1st": "EB-1",
    "2nd": "EB-2",
    "3rd": "EB-3",
}
TABLE_TYPES = ["final_action", "dates_for_filing"]
LABELS = {"final_action": "action date", "dates_for_filing": "filing date"}


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
    df = df[
        (df["preference_category"].isin(CATEGORY_MAP.keys()))
        & (df["table_type"].isin(TABLE_TYPES))
    ].copy()

    df["bulletin_date"] = pd.to_datetime(
        df["bulletin_month"] + " " + df["bulletin_year"].astype(str),
        format="%B %Y",
        errors="coerce",
    )

    col = "china_mainland_born"
    df["cutoff_date"] = df.apply(lambda r: parse_cutoff(r[col], r["bulletin_date"]), axis=1)
    df = df.dropna(subset=["bulletin_date", "cutoff_date"]).copy()
    df["months_to_current"] = (df["bulletin_date"] - df["cutoff_date"]).dt.days / 30.4375

    series = []
    for cat_raw, cat_label in CATEGORY_MAP.items():
        for ttype in TABLE_TYPES:
            part = df[
                (df["preference_category"] == cat_raw)
                & (df["table_type"] == ttype)
            ].sort_values("bulletin_date")
            series.append(
                {
                    "category": cat_label,
                    "table_type": ttype,
                    "label": LABELS[ttype],
                    "data": [
                        [d.strftime("%Y-%m-%d"), round(float(v), 3)]
                        for d, v in zip(part["bulletin_date"], part["months_to_current"])
                    ],
                }
            )

    data_json = json.dumps(series)

    html = f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>China EB-1/2/3 Time to Current</title>
  <script src=\"https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js\"></script>
  <style>
    :root {{
      --bg: #f3f6fb;
      --ink: #16243b;
      --muted: #60708f;
      --card: #ffffff;
      --border: #d6dfec;
      --shadow: 0 10px 30px rgba(16, 35, 69, 0.06);
      --accent: #e8eef8;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: "IBM Plex Sans", "Segoe UI", -apple-system, sans-serif; background: radial-gradient(1200px 500px at 20% -5%, #ffffff, var(--bg)); color: var(--ink); }}
    .wrap {{ max-width: 1240px; margin: 26px auto; padding: 0 18px; }}
    .header {{ padding: 6px 2px 16px; }}
    h1 {{ margin: 0; font-size: 26px; font-weight: 700; letter-spacing: 0.2px; }}
    p {{ margin: 8px 0 0; color: var(--muted); font-size: 14px; line-height: 1.5; }}
    .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 16px 14px 8px; box-shadow: var(--shadow); }}
    #chart {{ width: 100%; height: 1020px; }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <div class=\"header\">
      <h1>China EB-1/2/3: Time for Cutoff Date to Be Current</h1>
      <p>Y-axis shows months to current (bulletin month minus cutoff date). Values marked C are plotted as current in that bulletin month.</p>
    </div>
    <div class=\"card\"><div id=\"chart\"></div></div>
  </div>

  <script>
    const rows = {data_json};
    const chart = echarts.init(document.getElementById('chart'));

    const cats = ['EB-1', 'EB-2', 'EB-3'];
    const typeStyle = {{
      final_action: {{name: 'action date', color: '#0f4c5c', lineType: 'solid'}},
      dates_for_filing: {{name: 'filing date', color: '#d66853', lineType: 'dashed'}}
    }};

    const grids = [
      {{left: 84, right: 36, top: 84, height: 245}},
      {{left: 84, right: 36, top: 408, height: 245}},
      {{left: 84, right: 36, top: 732, height: 235}},
    ];

    const xAxis = grids.map((g, i) => ({{
      type: 'time',
      gridIndex: i,
      axisLabel: {{ color: '#5b6b88' }},
      axisLine: {{ lineStyle: {{ color: '#8593ad' }} }},
      axisTick: {{ show: false }},
      splitLine: {{ lineStyle: {{ color: '#edf2fa' }} }},
      name: i === 2 ? 'Bulletin Month' : '',
      nameLocation: 'middle',
      nameGap: 36,
      nameTextStyle: {{ color: '#4f5f7a', fontWeight: 600, fontSize: 12 }}
    }}));

    const yAxis = cats.map((_, i) => ({{
      type: 'value',
      gridIndex: i,
      name: 'Months',
      nameTextStyle: {{ color: '#4f5f7a', fontWeight: 600, fontSize: 12 }},
      axisLabel: {{ color: '#5b6b88' }},
      axisLine: {{ lineStyle: {{ color: '#8593ad' }} }},
      axisTick: {{ show: false }},
      splitLine: {{ lineStyle: {{ color: '#edf2fa' }} }}
    }}));

    const series = [];
    cats.forEach((cat, idx) => {{
      ['final_action', 'dates_for_filing'].forEach((tt) => {{
        const row = rows.find(r => r.category === cat && r.table_type === tt);
        if (!row) return;
        series.push({{
          name: typeStyle[tt].name,
          type: 'line',
          xAxisIndex: idx,
          yAxisIndex: idx,
          data: row.data,
          showSymbol: false,
          smooth: 0.15,
          lineStyle: {{ width: 2.4, type: typeStyle[tt].lineType, color: typeStyle[tt].color }},
          itemStyle: {{ color: typeStyle[tt].color }},
          legendHoverLink: true,
          emphasis: {{ focus: 'series' }}
        }});
      }});
    }});

    const option = {{
      animation: false,
      title: cats.map((c, i) => ({{ text: c, left: 84, top: grids[i].top - 34, textStyle: {{ fontSize: 15, fontWeight: 700, color: '#1d2a44' }} }})),
      legend: {{
        data: ['action date', 'filing date'],
        right: 40,
        top: 28,
        itemWidth: 30,
        itemHeight: 10,
        icon: 'roundRect',
        textStyle: {{ color: '#2e3a52', fontSize: 13, fontWeight: 600 }},
        backgroundColor: '#ffffff',
        borderColor: '#d6dfec',
        borderWidth: 1,
        padding: [8, 10]
      }},
      grid: grids,
      xAxis,
      yAxis,
      series,
      tooltip: {{
        trigger: 'axis',
        axisPointer: {{ type: 'line' }}
      }}
    }};

    chart.setOption(option);
    window.addEventListener('resize', () => chart.resize());
  </script>
</body>
</html>
"""

    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"Wrote: {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
