import * as d3 from 'd3';
import './styles.css';
import data from './data/china_series.json';

const parseDate = d3.utcParse('%Y-%m-%d');
const prepared = data.map((s) => ({
  ...s,
  points: s.data.map(([bulletinDate, monthsToCurrent, cutoffDate]) => ({
    x: parseDate(bulletinDate),
    monthsToCurrent: Number(monthsToCurrent),
    cutoffDate: parseDate(cutoffDate)
  }))
}));
const latestBulletinDate = d3.max(prepared.flatMap((s) => s.points), (d) => d.x);
const latestBulletinLabel = d3.utcFormat('%B %Y')(latestBulletinDate);
let viewMode = 'wait';

const app = document.querySelector('#app');
app.innerHTML = `
  <div class="min-h-screen bg-white px-6 py-8 sm:px-10 sm:py-12 lg:px-16">
    <div class="mx-auto max-w-6xl px-3 py-4 sm:px-6 sm:py-7">
      <div class="mb-8">
        <h1 class="text-2xl font-medium tracking-tight text-neutral-900">China EB Visa Bulletin Wait Time</h1>
        <p class="mt-2 max-w-3xl text-sm leading-6 text-neutral-600">Monthly wait-time trends for EB-1, EB-2, and EB-3 China employment-based categories.</p>
      </div>
      <div class="relative bg-white py-6 sm:py-8">
        <div class="mb-6 flex flex-col gap-4 border-b border-neutral-200 pb-5 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div id="chart-title" class="text-sm font-medium text-neutral-900">Months to current</div>
            <p id="chart-description" class="mt-1 max-w-3xl text-sm leading-6 text-neutral-600">Shows how many months each cutoff date trails its bulletin month. Lower is better; zero means the category is current.</p>
          </div>
          <div class="flex shrink-0 flex-col gap-4 text-sm text-neutral-700 sm:items-end">
            <div class="inline-flex rounded-md border border-neutral-200 p-0.5 text-sm">
              <button data-view="wait" class="view-toggle rounded px-3 py-1.5 text-neutral-950">Wait time</button>
              <button data-view="cutoff" class="view-toggle rounded px-3 py-1.5 text-neutral-500">Cutoff date</button>
            </div>
            <div class="flex items-center gap-5">
              <div class="flex items-center gap-2">
                <span class="h-px w-8 bg-slate-700"></span>
                <span>action date</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="h-px w-8 border-t border-dashed border-blue-600"></span>
                <span>filing date</span>
              </div>
            </div>
          </div>
        </div>
        <div id="chart" class="w-full"></div>
      </div>
      <footer class="mt-8 border-t border-neutral-200 pt-5 text-sm leading-6 text-neutral-500">
        <p>Data source: U.S. Department of State Visa Bulletin monthly employment-based preference tables. Latest bulletin in this dataset: ${latestBulletinLabel}.</p>
        <p class="mt-2">Methodology: for each bulletin month, months to current is computed as bulletin month minus the listed China cutoff date. When a category is current, its cutoff date is treated as that bulletin month.</p>
      </footer>
    </div>
  </div>
`;

const categories = ['EB-1', 'EB-2', 'EB-3'];
const typeStyle = {
  final_action: { name: 'action date', color: '#334155', dash: null },
  dates_for_filing: { name: 'filing date', color: '#2563eb', dash: '5,4' }
};

function updateViewControls() {
  const title = document.getElementById('chart-title');
  const description = document.getElementById('chart-description');
  title.textContent = viewMode === 'wait' ? 'Months to current' : 'Actual cutoff dates';
  description.textContent = viewMode === 'wait'
    ? 'Shows how many months each cutoff date trails its bulletin month. Lower is better; zero means the category is current.'
    : 'Shows the actual China cutoff dates listed in each bulletin month. Higher dates indicate forward movement.';

  document.querySelectorAll('.view-toggle').forEach((button) => {
    const selected = button.dataset.view === viewMode;
    button.classList.toggle('bg-neutral-900', selected);
    button.classList.toggle('text-white', selected);
    button.classList.toggle('text-neutral-500', !selected);
  });
}

function draw() {
  const root = document.getElementById('chart');
  root.innerHTML = '';

  const width = Math.max(320, root.clientWidth);
  const compact = width < 720;
  const height = compact ? 860 : 990;
  const margin = compact
    ? { top: 34, right: 12, bottom: 48, left: 48 }
    : { top: 40, right: 24, bottom: 54, left: 64 };
  const panelGap = compact ? 64 : 78;
  const panelHeight = (height - margin.top - margin.bottom - panelGap * 2) / 3;
  const panelWidth = width - margin.left - margin.right;

  const svg = d3
    .select(root)
    .append('svg')
    .attr('viewBox', `0 0 ${width} ${height}`)
    .attr('width', '100%')
    .attr('height', 'auto');

  const tooltip = d3
    .select(root)
    .append('div')
    .style('position', 'absolute')
    .style('pointer-events', 'none')
    .style('opacity', 0)
    .style('background', '#ffffff')
    .style('color', '#1a1a1a')
    .style('padding', '8px 10px')
    .style('border-radius', '8px')
    .style('font-size', '12px')
    .style('font-weight', 500)
    .style('line-height', 1.4)
    .style('border', '1px solid #dddddd')
    .style('box-shadow', '0 6px 18px rgba(0, 0, 0, 0.08)');

  categories.forEach((cat, idx) => {
    const yOffset = margin.top + idx * (panelHeight + panelGap);
    const panelData = prepared.filter((d) => d.category === cat);
    const allPoints = panelData.flatMap((d) => d.points);

    const xExtent = d3.extent(allPoints, (d) => d.x);
    const x = d3.scaleUtc().domain(xExtent).range([0, panelWidth]);
    const yValue = (d) => viewMode === 'wait' ? d.monthsToCurrent : d.cutoffDate;
    const yExtent = d3.extent(allPoints, yValue);
    const y = viewMode === 'wait'
      ? d3.scaleLinear()
        .domain([0, (d3.max(allPoints, yValue) || 1) * 1.05])
        .nice()
        .range([panelHeight, 0])
      : d3.scaleUtc()
        .domain(yExtent)
        .nice()
        .range([panelHeight, 0]);
    const makeYAxis = () => viewMode === 'wait'
      ? d3.axisLeft(y).ticks(compact ? 4 : 5)
      : d3.axisLeft(y).ticks(compact ? 4 : 5).tickFormat(d3.utcFormat('%Y'));

    const g = svg.append('g').attr('transform', `translate(${margin.left}, ${yOffset})`);

    g.append('text')
      .attr('x', 0)
      .attr('y', -22)
      .attr('fill', '#1a1a1a')
      .style('font-size', '14px')
      .style('font-weight', 600)
      .text(cat);

    g.append('g')
      .attr('class', 'grid')
      .call(makeYAxis().tickSize(-panelWidth).tickFormat(() => ''))
      .selectAll('line')
      .attr('stroke', '#efefef');

    g.select('.grid').select('.domain').remove();

    g.append('g')
      .call(makeYAxis())
      .call((axis) => axis.select('.domain').attr('stroke', '#c7c7c7'))
      .call((axis) => axis.selectAll('line').attr('stroke', '#c7c7c7'))
      .call((axis) => axis.selectAll('text').attr('fill', '#757575').style('font-size', '11px'));

    const xAxis = g
      .append('g')
      .attr('transform', `translate(0, ${panelHeight})`)
      .call(d3.axisBottom(x).ticks(compact ? 4 : width > 1100 ? 8 : 6).tickFormat(d3.utcFormat('%Y')))
      .call((axis) => axis.select('.domain').attr('stroke', '#c7c7c7'))
      .call((axis) => axis.selectAll('line').attr('stroke', '#c7c7c7'))
      .call((axis) => axis.selectAll('text').attr('fill', '#757575').style('font-size', '11px'));

    if (!compact || idx === 1) {
      g.append('text')
        .attr('transform', 'rotate(-90)')
        .attr('x', -panelHeight / 2)
        .attr('y', compact ? -36 : -46)
        .attr('text-anchor', 'middle')
        .attr('fill', '#6f6f6f')
        .style('font-size', '12px')
        .style('font-weight', 500)
        .text(compact ? (viewMode === 'wait' ? 'Months' : 'Cutoff') : idx === 1 ? (viewMode === 'wait' ? 'Months to current' : 'Cutoff date') : '');
    }

    const line = d3
      .line()
      .x((d) => x(d.x))
      .y((d) => y(yValue(d)))
      .curve(d3.curveMonotoneX);

    panelData.forEach((s) => {
      const style = typeStyle[s.table_type];
      g.append('path')
        .datum(s.points)
        .attr('fill', 'none')
        .attr('stroke', style.color)
        .attr('stroke-width', 1.4)
        .attr('stroke-dasharray', style.dash || null)
        .attr('d', line);
    });

    const dateFmt = d3.utcFormat('%Y-%m');
    const cutoffFmt = d3.utcFormat('%b %Y');
    const bisect = d3.bisector((d) => d.x).center;
    const hoverLine = g
      .append('line')
      .attr('y1', 0)
      .attr('y2', panelHeight)
      .attr('stroke', '#b3b3b3')
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '4,4')
      .style('opacity', 0);
    const hoverDots = g
      .append('g')
      .style('opacity', 0);

    const overlay = g
      .append('rect')
      .attr('width', panelWidth)
      .attr('height', panelHeight)
      .attr('fill', 'transparent');

    overlay
      .on('mouseenter', () => {
        hoverLine.style('opacity', 1);
        hoverDots.style('opacity', 1);
        tooltip.style('opacity', 1);
      })
      .on('mouseleave', () => {
        hoverLine.style('opacity', 0);
        hoverDots.style('opacity', 0);
        tooltip.style('opacity', 0);
      })
      .on('mousemove', (event) => {
        const [mx] = d3.pointer(event, g.node());
        const xDate = x.invert(mx);
        const rows = panelData
          .map((s) => {
            const i = Math.max(0, Math.min(s.points.length - 1, bisect(s.points, xDate)));
            return { ...s, point: s.points[i] };
          })
          .filter((r) => r.point);
        if (!rows.length) return;

        const anchor = rows[0].point.x;
        const lineX = x(anchor);
        hoverLine.attr('x1', lineX).attr('x2', lineX);

        const body = rows
          .map((r) => {
            const c = typeStyle[r.table_type].color;
            const value = viewMode === 'wait'
              ? `<strong>${r.point.monthsToCurrent.toFixed(1)}</strong> months`
              : `<strong>${cutoffFmt(r.point.cutoffDate)}</strong>`;
            return `<div style="display:flex;align-items:center;gap:6px;margin-top:3px;">
              <span style="width:8px;height:8px;border-radius:999px;background:${c};display:inline-block;"></span>
              <span>${typeStyle[r.table_type].name}: ${value}</span>
            </div>`;
          })
          .join('');

        const dotSel = hoverDots.selectAll('circle').data(rows, (d) => d.table_type);
        dotSel
          .join('circle')
          .attr('r', 4)
          .attr('cx', (d) => x(d.point.x))
          .attr('cy', (d) => y(yValue(d.point)))
          .attr('fill', '#ffffff')
          .attr('stroke', (d) => typeStyle[d.table_type].color)
          .attr('stroke-width', 1.2);

        tooltip
          .html(`<div style="font-weight:600;color:#111;">${cat} · ${dateFmt(anchor)}</div>${body}`)
          .style('left', '0px')
          .style('top', '0px');

        const node = tooltip.node();
        const tooltipWidth = node.offsetWidth;
        const tooltipHeight = node.offsetHeight;
        const left = Math.min(event.offsetX + 18, root.clientWidth - tooltipWidth - 8);
        const top = Math.min(event.offsetY + 18, root.clientHeight - tooltipHeight - 8);
        tooltip
          .style('left', `${Math.max(8, left)}px`)
          .style('top', `${Math.max(8, top)}px`);
      });
  });

  svg
    .append('text')
    .attr('x', width / 2)
    .attr('y', height - 16)
    .attr('text-anchor', 'middle')
    .attr('fill', '#6f6f6f')
    .style('font-size', '12px')
    .style('font-weight', 500)
    .text('Bulletin Month');
}

document.querySelectorAll('.view-toggle').forEach((button) => {
  button.addEventListener('click', () => {
    viewMode = button.dataset.view;
    updateViewControls();
    draw();
  });
});

updateViewControls();
draw();
window.addEventListener('resize', draw);
