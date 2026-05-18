<script lang="ts">
  import { listItems, createItem, type Item } from './api.js';

  let items = $state<Item[]>([]);
  let loading = $state(true);
  let error = $state<string | null>(null);
  let inputTitle = $state('');

  async function load() {
    loading = true;
    error = null;
    try {
      items = await listItems();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load items';
    } finally {
      loading = false;
    }
  }

  async function handleSubmit(e: SubmitEvent) {
    e.preventDefault();
    const title = inputTitle.trim();
    if (!title) return;
    try {
      await createItem(title);
      inputTitle = '';
      await load();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to create item';
    }
  }

  $effect(() => {
    load();
  });
</script>

{#if loading}
  <p>Loading…</p>
{:else if error}
  <p>Error: {error}</p>
{:else}
  <ul>
    {#each items as item (item.id)}
      <li>{item.title}</li>
    {/each}
  </ul>
{/if}

<form onsubmit={handleSubmit}>
  <input bind:value={inputTitle} placeholder="New item title" required />
  <button type="submit">Add</button>
</form>
