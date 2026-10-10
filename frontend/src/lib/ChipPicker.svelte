<script>
  let {
    options = [],          // [{ key, label, hint? }]
    selected = new Set(),  // Set of keys
    suggested = [],        // keys shown as quick-add chips
    placeholder = 'Search…',
    onadd,
    onremove,
    onclear
  } = $props();

  let query = $state('');

  const byKey = $derived(new Map(options.map((o) => [o.key, o])));
  const labelFor = (key) => byKey.get(key)?.label ?? key;

  const matches = $derived.by(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    return options
      .filter((o) => !selected.has(o.key) && o.label.toLowerCase().includes(q))
      .slice(0, 6);
  });

  const quick = $derived(
    suggested.map((k) => byKey.get(k)).filter((o) => o && !selected.has(o.key))
  );

  function add(key) {
    onadd?.(key);
    query = '';
  }

  function onKeydown(e) {
    if (e.key === 'Enter' && matches.length) add(matches[0].key);
    else if (e.key === 'Escape') query = '';
  }
</script>

<div class="picker">
  {#if selected.size}
    <div class="row">
      <div class="chips">
        {#each [...selected] as key (key)}
          <span class="chip active">
            {labelFor(key)}
            <button class="x" aria-label="Remove {labelFor(key)}" onclick={() => onremove?.(key)}>×</button>
          </span>
        {/each}
      </div>
      <button class="link" onclick={() => onclear?.()}>Clear all</button>
    </div>
  {/if}

  <input
    type="text"
    bind:value={query}
    {placeholder}
    aria-label={placeholder}
    onkeydown={onKeydown}
    autocomplete="off"
  />

  {#if matches.length}
    <ul class="results">
      {#each matches as m (m.key)}
        <li>
          <button onclick={() => add(m.key)}>
            <span>{m.label}</span>
            {#if m.hint}<small>{m.hint}</small>{/if}
          </button>
        </li>
      {/each}
    </ul>
  {:else if query.trim()}
    <p class="empty">No matches</p>
  {/if}

  {#if quick.length}
    <p class="label">Suggestions</p>
    <div class="chips">
      {#each quick as q (q.key)}
        <button class="chip ghost" onclick={() => onadd?.(q.key)}>+ {q.label}</button>
      {/each}
    </div>
  {/if}
</div>

<style>
  .picker { display: flex; flex-direction: column; gap: 10px; }
  .row { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; }
  .chips { display: flex; flex-wrap: wrap; gap: 6px; }

  .chip {
    display: inline-flex; align-items: center; gap: 4px;
    font-size: 12px; line-height: 1; padding: 7px 10px;
    border-radius: 999px; border: 1px solid rgba(255,255,255,0.14);
    color: #fff; background: rgba(255,255,255,0.06);
  }
  .chip.active { background: var(--accent, #4f9eff); border-color: var(--accent, #4f9eff); padding-right: 4px; }
  .chip.ghost { cursor: pointer; color: rgba(255,255,255,0.75); border-style: dashed; transition: all .15s ease; }
  .chip.ghost:hover { background: rgba(255,255,255,0.12); color: #fff; }

  .x {
    width: 18px; height: 18px; border-radius: 50%; border: none; cursor: pointer;
    background: rgba(0,0,0,0.25); color: #fff; font-size: 14px; line-height: 1;
    display: grid; place-items: center; padding: 0;
  }
  .x:hover { background: rgba(0,0,0,0.45); }

  .link {
    background: none; border: none; color: rgba(255,255,255,0.6);
    font-size: 11px; cursor: pointer; white-space: nowrap; padding: 4px 0;
  }
  .link:hover { color: #fff; text-decoration: underline; }

  input {
    width: 100%; box-sizing: border-box; padding: 9px 12px; font-size: 13px;
    color: #fff; background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12); border-radius: 10px; outline: none;
    transition: border-color .15s ease, background .15s ease;
  }
  input::placeholder { color: rgba(255,255,255,0.4); }
  input:focus { border-color: var(--accent, #4f9eff); background: rgba(255,255,255,0.09); }

  .results { list-style: none; margin: 0; padding: 4px; border-radius: 10px;
    background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); }
  .results button {
    width: 100%; display: flex; justify-content: space-between; align-items: center; gap: 8px;
    background: none; border: none; color: #fff; font-size: 13px; text-align: left;
    padding: 8px 10px; border-radius: 8px; cursor: pointer;
  }
  .results button:hover { background: rgba(255,255,255,0.1); }
  .results small { color: rgba(255,255,255,0.45); font-size: 11px; }

  .empty { margin: 0; font-size: 12px; color: rgba(255,255,255,0.45); }
  .label { margin: 2px 0 -4px; font-size: 11px; letter-spacing: .06em; text-transform: uppercase; color: rgba(255,255,255,0.4); }
</style>