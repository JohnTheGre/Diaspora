<script>
  import { onMount } from 'svelte';
  import { get } from 'svelte/store';
  import { API_BASE } from './config.js';
  import { activeFilterType, heightValue, weightValue, selectedLanguages, selectedDiasporas } from './stores.js';


  console.log('[0 globe] script loaded');
  let container;
  let globe;
  let geoData = [];
  let heightData = {};  // { iso: value }
  let weightData = {};
  let languageData = {};  // { iso: percentage }
  let diasporaData = {};  // { iso: population }

  const DEFAULT_COLOR = 'rgba(255,255,255,0.06)';

  async function loadGeoData() {
    const res = await fetch('https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json');
    const json = await res.json();
    geoData = json.features; // each feature.id is an ISO alpha-3 code
  }

  async function loadHeightData() {
    const res = await fetch(`${API_BASE}/api/height`);
    const rows = await res.json();
    heightData = Object.fromEntries(rows.map(r => [r.iso_code, r.value]));
  }

  async function loadWeightData() {
    const res = await fetch(`${API_BASE}/api/weight`);
    const rows = await res.json();
    weightData = Object.fromEntries(rows.map(r => [r.iso_code, r.value]));
  }

  async function loadLanguageData(languages) {
    if (languages.size === 0) { languageData = {}; return; }
    try {
      const results = await Promise.all(
        [...languages].map(async lang => {
          const res = await fetch(`${API_BASE}/api/language/${encodeURIComponent(lang)}?min_percent=0`);
          if (!res.ok) throw new Error(`Language fetch failed: ${res.status}`);
          return res.json();
        })
      );
      const next = {};
      for (const r of results.flat()) {
        next[r.iso_code] = Math.max(next[r.iso_code] ?? 0, r.value ?? 0);  // strongest language wins
      }
      languageData = next;
      console.log('[4 data] languageData', languageData);
    } catch (err) {
      console.error(err);
      languageData = {};
    }
  }

  async function loadDiasporaData(groups) {
    if (groups.size === 0) { diasporaData = {}; return; }
    try {
      const results = await Promise.all(
        [...groups].map(async g => {
          const res = await fetch(`${API_BASE}/api/diaspora/${encodeURIComponent(g)}?include_candidates=true`);
          if (!res.ok) throw new Error(`Diaspora fetch failed: ${res.status}`);
          return res.json();
        })
      );
      const next = {};
      for (const r of results.flat()) {
        next[r.iso_code] = (next[r.iso_code] ?? 0) + (r.value ?? 1);  // sum across selected groups
      }
      diasporaData = next;
      console.log('[4 data] diasporaData', diasporaData);
    } catch (err) {
      console.error(err);
      diasporaData = {};
    }
  }

  // Color a country based on how close its value is to the slider target
  function continuousColor(value, target, spread = 15) {
    if (value == null) return DEFAULT_COLOR;
    const diff = Math.abs(value - target);
    const intensity = Math.max(0, 1 - diff / spread); // 1 = exact match, 0 = far off
    if (intensity <= 0.02) return DEFAULT_COLOR;
    return `rgba(79, 158, 255, ${0.15 + intensity * 0.65})`;
  }

  function heatColor(t) {
    const clamped = Math.min(1, Math.max(0, t));
    const hue = 220 - 220 * clamped;
    return `hsla(${hue}, 90%, 55%, ${0.35 + 0.55 * clamped})`;
  }

  function applyColors() {
    console.log('[5 apply] called, globe =', !!globe);
    if (!globe) return;
    const filter = get(activeFilterType);
    console.log('[5 apply] filter =', filter, 'geoData =', geoData.length,
      'lang =', Object.keys(languageData).length, 'dia =', Object.keys(diasporaData).length);
    const h = get(heightValue);
    const w = get(weightValue);

    const maxDiaspora = Math.max(1, ...Object.values(diasporaData));

    globe.polygonCapColor(feature => {
      const iso = feature.id;
      switch (filter) {
        case 'height':
          return continuousColor(heightData[iso], h, 15);
        case 'weight':
          return continuousColor(weightData[iso], w, 15);
        case 'language': {
          const pct = languageData[iso];
          return pct == null ? DEFAULT_COLOR : heatColor(pct / 100);
        }
        case 'diaspora': {
          const pop = diasporaData[iso];
          if (pop == null) return DEFAULT_COLOR;
          // log scale so a 30M population doesn't wash out the 200k ones
          return heatColor(Math.log10(pop + 1) / Math.log10(maxDiaspora + 1));
        }
        default:
          return DEFAULT_COLOR;
      }
    });

    if (geoData.length) globe.polygonsData([...geoData]);
  }

  async function safe(label, fn) {
    try {
      await fn();
      console.log(`[globe] ${label} loaded`);
    } catch (err) {
      console.error(`[globe] ${label} FAILED`, err);
    }
  }

  onMount(() => {
    console.log('[2 globe] onMount fired, container =', container);
    let unsubs = [];
    let handleResize;

    (async () => {
      const GlobeModule = await import('globe.gl');
      console.log('[2 globe] globe.gl imported', typeof GlobeModule.default);
      const Globe = GlobeModule.default;
      if (!container) return;

      globe = Globe()(container)
        .globeImageUrl('//unpkg.com/three-globe/example/img/earth-blue-marble.jpg')
        .bumpImageUrl('//unpkg.com/three-globe/example/img/earth-topology.png')
        .backgroundImageUrl('//unpkg.com/three-globe/example/img/night-sky.png')
        .width(container.clientWidth)
        .height(container.clientHeight)
        .polygonSideColor(() => 'rgba(0,0,0,0)')
        .polygonStrokeColor(() => 'rgba(255,255,255,0.2)')
        .polygonAltitude(0.005)
        .polygonsTransitionDuration(0);

      console.log('[2 globe] globe created', globe)
      window.__globe = globe
      globe.controls().autoRotate = false;

      handleResize = () => {
        if (!container || !globe) return;
        globe.width(container.clientWidth).height(container.clientHeight);
      };
      window.addEventListener('resize', handleResize);

      // 1. Subscribe first, so filters work even if a data load fails
      unsubs = [
        activeFilterType.subscribe(v => { console.log('[3 store] activeFilterType', v); applyColors(); }),
        heightValue.subscribe(() => applyColors()),
        weightValue.subscribe(() => applyColors()),
        selectedLanguages.subscribe(async (langs) => {
          console.log('[3 store] selectedLanguages', [...langs]);
          await loadLanguageData(langs);
          applyColors();
        }),
        selectedDiasporas.subscribe(async (groups) => {
          console.log('[3 store] selectedDiasporas', [...groups]);
          await loadDiasporaData(groups);
          applyColors();
        }),
      ];

      // 2. Load each dataset independently
      await Promise.all([
        safe('geo', loadGeoData),
        safe('height', loadHeightData),
        safe('weight', loadWeightData),
      ]);

      console.log('[globe] features:', geoData.length, 'sample id:', geoData[0]?.id);
      globe.polygonsData(geoData);
      applyColors();
    })();

    return () => {
      if (handleResize) window.removeEventListener('resize', handleResize);
      unsubs.forEach(u => u());
    };
  });
</script>

<div bind:this={container} class="globe-container"></div>

<style>
  .globe-container {
    width: 100vw;
    height: 100vh;
    overflow: hidden;
    background: #000;
  }
</style>