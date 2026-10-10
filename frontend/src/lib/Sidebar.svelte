<script>
  import { onMount } from 'svelte';
  import { activeFilterType, heightValue, weightValue, selectedLanguages, selectedDiasporas, comparisonOpen } from './stores.js';
  import ChipPicker from './ChipPicker.svelte';

  const API_BASE = 'http://localhost:8000';

  const HEIGHT_MIN = 140, HEIGHT_MAX = 200;
  const WEIGHT_MIN = 40,  WEIGHT_MAX = 100;

  const POPULAR_LANGUAGES = ['English', 'Spanish', 'French', 'Arabic', 'Mandarin', 'Portuguese', 'German', 'Hindi'];
  const POPULAR_ORIGINS = ['NGA', 'IND', 'CHN', 'IRL', 'ITA', 'LBN', 'JAM', 'PHL', 'TUR', 'POL'];

  // Fallback options so the sidebar works even if the API call fails
  const FALLBACK_ORIGINS = [
    ['NGA', 'Nigeria'], ['IND', 'India'], ['CHN', 'China'], ['IRL', 'Ireland'], ['ITA', 'Italy'],
    ['LBN', 'Lebanon'], ['JAM', 'Jamaica'], ['PHL', 'Philippines'], ['TUR', 'Turkey'], ['POL', 'Poland']
  ].map(([key, label]) => ({ key, label, hint: key }));

  let activePanel = $state(null);
  let collapsed = $state(typeof window !== 'undefined' && window.innerWidth < 640);
  let languageOptions = $state(POPULAR_LANGUAGES.map((l) => ({ key: l, label: l })));
  let originOptions = $state(FALLBACK_ORIGINS);

  async function getJson(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`${url} -> ${res.status}`);
    return res.json();
  }

  onMount(async () => {
    try {
      const [langs, origins] = await Promise.all([
        getJson(`${API_BASE}/api/languages`),
        getJson(`${API_BASE}/api/diaspora-origins`)
      ]);
      languageOptions = langs.map((l) => ({
        key: l.language,
        label: l.language,
        hint: `${l.countries} ${l.countries === 1 ? 'country' : 'countries'}`
      }));
      originOptions = origins.map((o) => ({ key: o.iso, label: o.name, hint: o.iso }));
    } catch (err) {
      console.error('Could not load filter options, using defaults', err);
    }
  });

  function togglePanel(name) {
    activePanel = activePanel === name ? null : name;
    activeFilterType.set(activePanel); // the globe reacts to this
  }

  const addTo = (store, key) => store.update((s) => new Set(s).add(key));
  const removeFrom = (store, key) =>
    store.update((s) => {
      const next = new Set(s);
      next.delete(key);
      return next;
    });
  const clearStore = (store) => store.set(new Set());

  const pct = (v, min, max) => ((v - min) / (max - min)) * 100;
</script>

<aside class="sidebar" class:collapsed>
  <button class="head" onclick={() => (collapsed = !collapsed)} aria-expanded={!collapsed}>
    <span class="title"><span class="dot"></span>Explore the globe</span>
    <svg class="chev" class:flip={collapsed} width="18" height="18" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <polyline points="6 9 12 15 18 9" />
    </svg>
  </button>

  {#if !collapsed}
    <div class="body">
      <!-- Height -->
      <section class="group" class:active={activePanel === 'height'}>
        <button class="filter-header" onclick={() => togglePanel('height')} aria-expanded={activePanel === 'height'}>
          <span class="label">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.3 15.3a2.4 2.4 0 0 1 0 3.4l-2.6 2.6a2.4 2.4 0 0 1-3.4 0L2.7 8.7a2.41 2.41 0 0 1 0-3.4l2.6-2.6a2.41 2.41 0 0 1 3.4 0Z"/><path d="m14.5 12.5 2-2"/><path d="m11.5 9.5 2-2"/><path d="m8.5 6.5 2-2"/><path d="m17.5 15.5 2-2"/></svg>
            Height
          </span>
          <span class="chevron" class:open={activePanel === 'height'}>›</span>
        </button>
        <div class="panel" class:open={activePanel === 'height'}>
          <div class="panel-inner" inert={activePanel !== 'height'}>
            <div class="readout"><strong>{$heightValue}</strong> cm</div>
            <input type="range" min={HEIGHT_MIN} max={HEIGHT_MAX} bind:value={$heightValue}
              style="--pct:{pct($heightValue, HEIGHT_MIN, HEIGHT_MAX)}%" aria-label="Average height in centimetres" />
            <p class="hint">Countries whose average is closest to this value glow brightest.</p>
          </div>
        </div>
      </section>

      <!-- Weight -->
      <section class="group" class:active={activePanel === 'weight'}>
        <button class="filter-header" onclick={() => togglePanel('weight')} aria-expanded={activePanel === 'weight'}>
          <span class="label">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="5" r="3"/><path d="M6.5 8a2 2 0 0 0-1.905 1.46L2.1 18.5A2 2 0 0 0 4 21h16a2 2 0 0 0 1.925-2.54L19.4 9.5A2 2 0 0 0 17.48 8Z"/></svg>
            Weight
          </span>
          <span class="chevron" class:open={activePanel === 'weight'}>›</span>
        </button>
        <div class="panel" class:open={activePanel === 'weight'}>
          <div class="panel-inner" inert={activePanel !== 'weight'}>
            <div class="readout"><strong>{$weightValue}</strong> kg</div>
            <input type="range" min={WEIGHT_MIN} max={WEIGHT_MAX} bind:value={$weightValue}
              style="--pct:{pct($weightValue, WEIGHT_MIN, WEIGHT_MAX)}%" aria-label="Average weight in kilograms" />
            <p class="hint">Countries whose average is closest to this value glow brightest.</p>
          </div>
        </div>
      </section>

      <!-- Language -->
      <section class="group" class:active={activePanel === 'language'}>
        <button class="filter-header" onclick={() => togglePanel('language')} aria-expanded={activePanel === 'language'}>
          <span class="label">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m5 8 6 6"/><path d="m4 14 6-6 2-3"/><path d="M2 5h12"/><path d="M7 2h1"/><path d="m22 22-5-10-5 10"/><path d="M14 18h6"/></svg>
            Language
            {#if $selectedLanguages.size}<span class="badge">{$selectedLanguages.size}</span>{/if}
          </span>
          <span class="chevron" class:open={activePanel === 'language'}>›</span>
        </button>
        <div class="panel" class:open={activePanel === 'language'}>
          <div class="panel-inner" inert={activePanel !== 'language'}>
            <ChipPicker
              options={languageOptions}
              selected={$selectedLanguages}
              suggested={POPULAR_LANGUAGES}
              placeholder="Add a language…"
              onadd={(k) => addTo(selectedLanguages, k)}
              onremove={(k) => removeFrom(selectedLanguages, k)}
              onclear={() => clearStore(selectedLanguages)}
            />
            <p class="hint">Shades countries by how widely the language is spoken.</p>
          </div>
        </div>
      </section>

      <!-- Diaspora -->
      <section class="group" class:active={activePanel === 'diaspora'}>
        <button class="filter-header" onclick={() => togglePanel('diaspora')} aria-expanded={activePanel === 'diaspora'}>
          <span class="label">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
            Diaspora
            {#if $selectedDiasporas.size}<span class="badge">{$selectedDiasporas.size}</span>{/if}
          </span>
          <span class="chevron" class:open={activePanel === 'diaspora'}>›</span>
        </button>
        <div class="panel" class:open={activePanel === 'diaspora'}>
          <div class="panel-inner" inert={activePanel !== 'diaspora'}>
            <ChipPicker
              options={originOptions}
              selected={$selectedDiasporas}
              suggested={POPULAR_ORIGINS}
              placeholder="Add an origin country…"
              onadd={(k) => addTo(selectedDiasporas, k)}
              onremove={(k) => removeFrom(selectedDiasporas, k)}
              onclear={() => clearStore(selectedDiasporas)}
            />
            <p class="hint">Shows where people from the chosen countries live abroad.</p>
          </div>
        </div>
      </section>

      <!-- Compare -->
      <section class="group">
        <button class="filter-header" onclick={() => comparisonOpen.set(true)}>
          <span class="label">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
            Compare countries
          </span>
          <span class="chevron">›</span>
        </button>
      </section>
    </div>
  {/if}
</aside>

<style>
  .sidebar {
    --accent: #4f9eff;
    position: fixed;
    top: 20px;
    right: 20px;
    width: 320px;
    max-height: calc(100vh - 40px);
    max-height: calc(100dvh - 40px);
    display: flex;
    flex-direction: column;
    z-index: 10;
    color: #fff;
    font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
    background: linear-gradient(160deg, rgba(30, 32, 44, 0.82), rgba(14, 15, 22, 0.82));
    -webkit-backdrop-filter: blur(16px) saturate(140%);
    backdrop-filter: blur(16px) saturate(140%);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 16px;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
    overflow: hidden;
  }

  .head {
    display: flex; align-items: center; justify-content: space-between;
    width: 100%; padding: 14px 16px; background: none; border: none;
    color: inherit; cursor: pointer; font: inherit;
  }
  .title { display: flex; align-items: center; gap: 10px; font-size: 14px; font-weight: 600; letter-spacing: .01em; }
  .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 10px var(--accent); }
  .chev { opacity: .6; transition: transform .2s ease; }
  .chev.flip { transform: rotate(180deg); }

  .body {
    overflow-y: auto; overscroll-behavior: contain;
    padding: 0 8px 8px; border-top: 1px solid rgba(255, 255, 255, 0.08);
  }

  .group { border-bottom: 1px solid rgba(255, 255, 255, 0.06); }
  .group:last-child { border-bottom: none; }

  .filter-header {
    display: flex; align-items: center; justify-content: space-between;
    width: 100%; box-sizing: border-box; background: none; border: none; color: #fff;
    font-size: 14px; font-weight: 500; padding: 13px 10px; margin-top: 4px;
    cursor: pointer; border-radius: 10px; transition: background .15s ease;
  }
  .filter-header:hover { background: rgba(255, 255, 255, 0.06); }
  .group.active > .filter-header { background: rgba(79, 158, 255, 0.14); }
  .filter-header.static { cursor: default; opacity: .55; }
  .filter-header.static:hover { background: none; }

  .label { display: flex; align-items: center; gap: 10px; }
  .icon { width: 18px; height: 18px; opacity: .8; }
  .group.active .icon { color: var(--accent); opacity: 1; }

  .badge {
    min-width: 18px; padding: 2px 6px; border-radius: 999px; text-align: center;
    background: var(--accent); font-size: 11px; font-weight: 600; line-height: 1.2;
  }
  .soon { font-size: 10px; letter-spacing: .08em; text-transform: uppercase; opacity: .8; }

  .chevron { opacity: .5; font-size: 18px; transition: transform .2s ease; }
  .chevron.open { transform: rotate(90deg); }

  /* Smooth accordion without measuring heights */
  .panel { display: grid; grid-template-rows: 0fr; transition: grid-template-rows .25s ease; }
  .panel.open { grid-template-rows: 1fr; }
  .panel-inner { overflow: hidden; min-height: 0; padding: 0 10px; }
  .panel.open .panel-inner { padding: 6px 10px 16px; }

  .readout { font-size: 13px; opacity: .85; margin-bottom: 10px; }
  .readout strong { font-size: 22px; font-weight: 600; margin-right: 2px; }

  .hint { margin: 12px 0 0; font-size: 12px; line-height: 1.4; color: rgba(255, 255, 255, 0.5); }

  input[type='range'] {
    -webkit-appearance: none; appearance: none; width: 100%; height: 6px; border-radius: 999px; outline: none;
    background: linear-gradient(to right, var(--accent) var(--pct, 50%), rgba(255, 255, 255, 0.16) var(--pct, 50%));
  }
  input[type='range']::-webkit-slider-thumb {
    -webkit-appearance: none; width: 20px; height: 20px; border-radius: 50%;
    background: #fff; border: 4px solid var(--accent); cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,.4);
  }
  input[type='range']::-moz-range-thumb {
    width: 12px; height: 12px; border-radius: 50%;
    background: #fff; border: 4px solid var(--accent); cursor: pointer;
  }

  /* Phones and small tablets: bottom sheet */
  @media (max-width: 640px) {
    .sidebar {
      top: auto; left: 0; right: 0; bottom: 0; width: 100%;
      max-height: 62vh; max-height: 62dvh;
      border-radius: 18px 18px 0 0; border-bottom: none;
      padding-bottom: env(safe-area-inset-bottom);
    }
    .head { padding-top: 18px; position: relative; }
    .head::before {
      content: ''; position: absolute; top: 7px; left: 50%; transform: translateX(-50%);
      width: 36px; height: 4px; border-radius: 999px; background: rgba(255, 255, 255, 0.25);
    }
    .filter-header { padding: 15px 10px; } /* bigger touch targets */
  }

  @media (prefers-reduced-motion: reduce) {
    .panel, .chev, .chevron { transition: none; }
  }
</style>