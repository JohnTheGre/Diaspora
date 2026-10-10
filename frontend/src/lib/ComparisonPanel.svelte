<script>
  import { onMount } from 'svelte';
  import { Chart, registerables } from 'chart.js';
  import { comparisonOpen } from './stores.js';
  import ChipPicker from './ChipPicker.svelte';
  import { API_BASE } from './config.js';

  Chart.register(...registerables);
  Chart.defaults.color = 'rgba(255,255,255,0.7)';
  Chart.defaults.borderColor = 'rgba(255,255,255,0.08)';
  Chart.defaults.font.family = 'system-ui, -apple-system, "Segoe UI", sans-serif';

  const ACCENT = '#4f9eff';
  const PALETTE = ['#4f9eff', '#ff7a59', '#4ade80', '#f5c542', '#c084fc', '#22d3ee', '#fb7185', '#a3e635', '#f97316', '#818cf8'];

  const METRICS = [
    { id: 'height',   label: 'Height',   title: 'Average height',    unit: 'cm' },
    { id: 'weight',   label: 'Weight',   title: 'Average weight',    unit: 'kg' },
    { id: 'language', label: 'Language', title: 'Language spoken',   unit: '% of population' },
    { id: 'diaspora', label: 'Diaspora', title: 'Diaspora abroad',   unit: 'people' }
  ];
  const CHARTS = [
    { id: 'bar', label: 'Bar' },
    { id: 'pie', label: 'Pie' },
    { id: 'histogram', label: 'Histogram' }
  ];
  const SUGGESTED = ['USA', 'GBR', 'NLD', 'DEU', 'NGA', 'IND', 'CHN', 'JPN'];

  let countries = $state.raw([]);   // [{ iso, name }]
  let languages = $state.raw([]);   // [{ language, countries }]
  let origins = $state.raw([]);     // [{ iso, name }]

  let picked = $state.raw(new Set(['USA', 'GBR', 'NLD', 'NGA', 'JPN']));
  let metric = $state('height');
  let chartType = $state('bar');
  let language = $state('English');
  let origin = $state('NGA');

  let values = $state.raw({});      // iso -> value, for the current metric (all countries)
  let loading = $state(false);
  let error = $state('');
  let canvas = $state();

  const metricInfo = $derived(METRICS.find((m) => m.id === metric));
  const options = $derived(countries.map((c) => ({ key: c.iso, label: c.name, hint: c.iso })));
  const nameOf = $derived(new Map(countries.map((c) => [c.iso, c.name])));

  const rows = $derived([...picked].map((iso) => ({ iso, name: nameOf.get(iso) ?? iso, value: values[iso] })));
  const withData = $derived(rows.filter((r) => typeof r.value === 'number').sort((a, b) => b.value - a.value));
  const missing = $derived(rows.filter((r) => typeof r.value !== 'number'));

  const unitLabel = $derived(
    metric === 'language' ? `% who speak ${language}` :
    metric === 'diaspora' ? `${origins.find((o) => o.iso === origin)?.name ?? origin} diaspora (people)` :
    `${metricInfo.title} (${metricInfo.unit})`
  );

  function fmt(v) {
    return new Intl.NumberFormat('en', {
      maximumFractionDigits: 1,
      notation: metric === 'diaspora' && Math.abs(v) >= 100000 ? 'compact' : 'standard'
    }).format(v);
  }

  onMount(async () => {
    try {
      const [c, l, o] = await Promise.all([
        fetch(`${API_BASE}/api/countries`).then((r) => r.json()),
        fetch(`${API_BASE}/api/languages`).then((r) => r.json()),
        fetch(`${API_BASE}/api/diaspora-origins`).then((r) => r.json())
      ]);
      countries = c; languages = l; origins = o;
    } catch (err) {
      console.error('Comparison: could not load options', err);
      error = 'Could not load countries. Is the backend running?';
    }
  });

  // Load the numbers for the chosen metric (all countries, so the histogram has a full distribution)
  let token = 0;
  $effect(() => {
    if (!$comparisonOpen) return;
    const m = metric, lang = language, org = origin;
    const url =
      m === 'height' ? `${API_BASE}/api/height` :
      m === 'weight' ? `${API_BASE}/api/weight` :
      m === 'language' ? `${API_BASE}/api/language/${encodeURIComponent(lang)}?min_percent=0` :
      `${API_BASE}/api/diaspora/${encodeURIComponent(org)}?include_candidates=true`;

    const mine = ++token;
    loading = true;
    error = '';
    fetch(url)
      .then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then((data) => {
        if (mine !== token) return;
        values = Object.fromEntries(data.map((d) => [d.iso_code, d.value]));
      })
      .catch((err) => {
        if (mine !== token) return;
        console.error(err);
        values = {};
        error = 'Could not load data for this comparison.';
      })
      .finally(() => { if (mine === token) loading = false; });
  });

  const chartConfig = $derived.by(() => {
    const base = { responsive: true, maintainAspectRatio: false };

    if (chartType === 'bar') {
      if (!withData.length) return null;
      const horizontal = withData.length > 6;
      return {
        type: 'bar',
        data: {
          labels: withData.map((r) => r.name),
          datasets: [{
            data: withData.map((r) => r.value),
            backgroundColor: withData.map((_, i) => PALETTE[i % PALETTE.length]),
            borderRadius: 6
          }]
        },
        options: {
          ...base,
          indexAxis: horizontal ? 'y' : 'x',
          plugins: { legend: { display: false }, tooltip: { callbacks: { label: (c) => ` ${fmt(c.parsed[horizontal ? 'x' : 'y'])} ${metricInfo.unit}` } } },
          scales: {
            [horizontal ? 'x' : 'y']: {
              beginAtZero: metric === 'language' || metric === 'diaspora',
              title: { display: true, text: unitLabel }
            }
          }
        }
      };
    }

    if (chartType === 'pie') {
      if (!withData.length) return null;
      const total = withData.reduce((s, r) => s + r.value, 0) || 1;
      return {
        type: 'pie',
        data: {
          labels: withData.map((r) => r.name),
          datasets: [{
            data: withData.map((r) => r.value),
            backgroundColor: withData.map((_, i) => PALETTE[i % PALETTE.length]),
            borderColor: '#14151c',
            borderWidth: 2
          }]
        },
        options: {
          ...base,
          plugins: {
            legend: { position: 'bottom', labels: { boxWidth: 12 } },
            tooltip: { callbacks: { label: (c) => ` ${c.label}: ${fmt(c.parsed)} (${((c.parsed / total) * 100).toFixed(1)}%)` } }
          }
        }
      };
    }

    // Histogram: distribution across ALL countries, with the picked ones highlighted
    const all = Object.values(values).filter((v) => typeof v === 'number');
    if (all.length < 2) return null;
    const BINS = 10;
    const lo = Math.min(...all), hi = Math.max(...all);
    const step = (hi - lo) / BINS || 1;
    const idx = (v) => Math.min(BINS - 1, Math.floor((v - lo) / step));
    const counts = Array(BINS).fill(0);
    const picks = Array.from({ length: BINS }, () => []);
    all.forEach((v) => counts[idx(v)]++);
    withData.forEach((r) => picks[idx(r.value)].push(r.name));

    return {
      type: 'bar',
      data: {
        labels: counts.map((_, i) => `${fmt(lo + i * step)}–${fmt(lo + (i + 1) * step)}`),
        datasets: [{
          data: counts,
          backgroundColor: counts.map((_, i) => (picks[i].length ? ACCENT : 'rgba(255,255,255,0.18)')),
          borderRadius: 4,
          barPercentage: 0.98,
          categoryPercentage: 1
        }]
      },
      options: {
        ...base,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (c) => ` ${c.parsed.y} ${c.parsed.y === 1 ? 'country' : 'countries'}`,
              afterBody: (items) => (picks[items[0].dataIndex].length ? ['', 'Selected:', ...picks[items[0].dataIndex]] : [])
            }
          }
        },
        scales: {
          x: { title: { display: true, text: unitLabel }, ticks: { maxRotation: 45, autoSkip: true } },
          y: { beginAtZero: true, ticks: { precision: 0 }, title: { display: true, text: 'Number of countries' } }
        }
      }
    };
  });

  // (Re)build the chart whenever the config changes
  $effect(() => {
    const cfg = chartConfig;
    const el = canvas;
    if (!el || !cfg) return;
    const chart = new Chart(el, cfg);
    return () => chart.destroy();
  });

  const add = (iso) => (picked = new Set(picked).add(iso));
  const remove = (iso) => { const n = new Set(picked); n.delete(iso); picked = n; };
  const clear = () => (picked = new Set());
  const close = () => comparisonOpen.set(false);
</script>

<svelte:window onkeydown={(e) => e.key === 'Escape' && $comparisonOpen && close()} />

{#if $comparisonOpen}
  <div class="backdrop" role="presentation" onclick={close}>
    <div class="modal" role="dialog" aria-modal="true" aria-label="Compare countries" tabindex="-1"
      onclick={(e) => e.stopPropagation()} onkeydown={() => {}}>

      <header>
        <h2>Compare countries</h2>
        <button class="close" aria-label="Close" onclick={close}>×</button>
      </header>

      <div class="layout">
        <!-- Controls -->
        <div class="controls">
          <section>
            <h3><span class="step">1</span> Countries <small>{picked.size} selected</small></h3>
            <ChipPicker
              {options}
              selected={picked}
              suggested={SUGGESTED}
              placeholder="Add a country…"
              onadd={add}
              onremove={remove}
              onclear={clear}
            />
          </section>

          <section>
            <h3><span class="step">2</span> Compare on</h3>
            <div class="seg">
              {#each METRICS as m (m.id)}
                <button class:on={metric === m.id} onclick={() => (metric = m.id)}>{m.label}</button>
              {/each}
            </div>

            {#if metric === 'language'}
              <label class="field">
                Language
                <select bind:value={language}>
                  {#each languages as l (l.language)}<option value={l.language}>{l.language}</option>{/each}
                  {#if !languages.length}<option value="English">English</option>{/if}
                </select>
              </label>
            {:else if metric === 'diaspora'}
              <label class="field">
                Diaspora from
                <select bind:value={origin}>
                  {#each origins as o (o.iso)}<option value={o.iso}>{o.name}</option>{/each}
                  {#if !origins.length}<option value="NGA">Nigeria</option>{/if}
                </select>
              </label>
            {/if}
          </section>

          <section>
            <h3><span class="step">3</span> Chart</h3>
            <div class="seg">
              {#each CHARTS as c (c.id)}
                <button class:on={chartType === c.id} onclick={() => (chartType = c.id)}>{c.label}</button>
              {/each}
            </div>
            {#if chartType === 'pie' && metric !== 'diaspora'}
              <p class="note">Pie shows each country's share of the total, which suits population counts best.</p>
            {/if}
            {#if chartType === 'histogram'}
              <p class="note">Shows all countries in the dataset. Bins holding your selection are highlighted.</p>
            {/if}
          </section>
        </div>

        <!-- Results -->
        <div class="results">
          <div class="chart-wrap">
            <canvas bind:this={canvas}></canvas>
            {#if loading}
              <div class="overlay">Loading…</div>
            {:else if error}
              <div class="overlay">{error}</div>
            {:else if !chartConfig}
              <div class="overlay">{picked.size ? 'No data for these countries.' : 'Add a country to start comparing.'}</div>
            {/if}
          </div>

          {#if withData.length}
            <ol class="table">
              {#each withData as r, i (r.iso)}
                <li>
                  <span class="dot" style="background:{PALETTE[i % PALETTE.length]}"></span>
                  <span class="name">{r.name}</span>
                  <span class="val">{fmt(r.value)} <small>{metricInfo.unit}</small></span>
                </li>
              {/each}
            </ol>
          {/if}
          {#if missing.length}
            <p class="note">No data for: {missing.map((r) => r.name).join(', ')}</p>
          {/if}
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  .backdrop {
    position: fixed; inset: 0; z-index: 30; display: grid; place-items: center;
    background: rgba(0, 0, 0, 0.55); -webkit-backdrop-filter: blur(4px); backdrop-filter: blur(4px);
    padding: 20px;
  }
  .modal {
    --accent: #4f9eff;
    width: min(1040px, 100%); max-height: calc(100dvh - 40px);
    display: flex; flex-direction: column; overflow: hidden; color: #fff;
    font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
    background: linear-gradient(160deg, rgba(30, 32, 44, 0.96), rgba(14, 15, 22, 0.96));
    border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 18px;
    box-shadow: 0 24px 80px rgba(0, 0, 0, 0.6);
  }
  header { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid rgba(255,255,255,0.08); }
  h2 { margin: 0; font-size: 17px; font-weight: 600; }
  .close { width: 32px; height: 32px; border-radius: 50%; border: none; background: rgba(255,255,255,0.08); color: #fff; font-size: 20px; line-height: 1; cursor: pointer; }
  .close:hover { background: rgba(255,255,255,0.16); }

  .layout { display: grid; grid-template-columns: 330px 1fr; min-height: 0; overflow: hidden; }
  .controls { padding: 18px 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 22px; border-right: 1px solid rgba(255,255,255,0.08); }
  .results { padding: 18px 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; min-width: 0; }

  h3 { margin: 0 0 10px; font-size: 13px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
  h3 small { margin-left: auto; font-weight: 400; color: rgba(255,255,255,0.45); font-size: 11px; }
  .step { width: 20px; height: 20px; border-radius: 50%; background: var(--accent); display: grid; place-items: center; font-size: 11px; }

  .seg { display: grid; grid-auto-flow: column; grid-auto-columns: 1fr; gap: 4px; padding: 4px; background: rgba(255,255,255,0.06); border-radius: 10px; }
  .seg button { border: none; background: none; color: rgba(255,255,255,0.7); font-size: 12px; padding: 8px 4px; border-radius: 7px; cursor: pointer; transition: all .15s ease; }
  .seg button:hover { color: #fff; }
  .seg button.on { background: var(--accent); color: #fff; font-weight: 600; }

  .field { display: flex; flex-direction: column; gap: 6px; margin-top: 12px; font-size: 12px; color: rgba(255,255,255,0.6); }
  select { padding: 9px 10px; border-radius: 10px; font-size: 13px; color: #fff; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.14); outline: none; }
  select:focus { border-color: var(--accent); }
  select option { color: #111; }

  .note { margin: 10px 0 0; font-size: 12px; line-height: 1.4; color: rgba(255,255,255,0.5); }

  .chart-wrap { position: relative; height: 380px; }
  .overlay { position: absolute; inset: 0; display: grid; place-items: center; text-align: center; padding: 20px;
    font-size: 13px; color: rgba(255,255,255,0.6); background: rgba(14,15,22,0.72); border-radius: 12px; }

  .table { list-style: none; margin: 0; padding: 0; display: grid; gap: 4px; }
  .table li { display: flex; align-items: center; gap: 10px; padding: 9px 12px; border-radius: 10px; background: rgba(255,255,255,0.04); font-size: 13px; }
  .dot { width: 10px; height: 10px; border-radius: 50%; flex: none; }
  .name { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .val { font-variant-numeric: tabular-nums; font-weight: 600; }
  .val small { font-weight: 400; color: rgba(255,255,255,0.45); }

  /* Phones: full-screen sheet, controls stacked above the chart */
  @media (max-width: 760px) {
    .backdrop { padding: 0; place-items: stretch; }
    .modal { width: 100%; max-height: 100dvh; height: 100dvh; border-radius: 0; border: none; }
    .layout { grid-template-columns: 1fr; overflow-y: auto; }
    .controls { border-right: none; border-bottom: 1px solid rgba(255,255,255,0.08); overflow: visible; }
    .results { overflow: visible; }
    .chart-wrap { height: 300px; }
  }
</style>