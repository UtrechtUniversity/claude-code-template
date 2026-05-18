import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import Items from '../../src/lib/Items.svelte';

describe('Items', () => {
  it('renders an item title returned by the API', async () => {
    const fixture = [{ id: 1, title: 'Test item', created_at: '2026-01-01T00:00:00Z' }];
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      statusText: 'OK',
      json: () => Promise.resolve(fixture),
    }));

    render(Items);

    expect(await screen.findByText('Test item')).toBeTruthy();
  });
});
