import { describe, it, expect, vi, beforeEach } from 'vitest';
import { listItems, createItem } from '../../src/lib/api.js';

function mockFetch(body: unknown, status = 200) {
  return vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? 'OK' : 'Error',
    json: () => Promise.resolve(body),
  });
}

beforeEach(() => {
  vi.restoreAllMocks();
});

describe('listItems', () => {
  it('calls GET /api/items/ and returns the parsed array', async () => {
    const fixture = [{ id: 1, title: 'hello', created_at: '2026-01-01T00:00:00Z' }];
    vi.stubGlobal('fetch', mockFetch(fixture));

    const result = await listItems();

    expect(fetch).toHaveBeenCalledWith('/api/items/', undefined);
    expect(result).toEqual(fixture);
  });
});

describe('createItem', () => {
  it('calls POST /api/items/ with the right body and returns the parsed item', async () => {
    const fixture = { id: 2, title: 'world', created_at: '2026-01-02T00:00:00Z' };
    vi.stubGlobal('fetch', mockFetch(fixture, 201));

    const result = await createItem('world');

    expect(fetch).toHaveBeenCalledWith('/api/items/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: 'world' }),
    });
    expect(result).toEqual(fixture);
  });
});
