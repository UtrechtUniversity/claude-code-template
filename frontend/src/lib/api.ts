export type Item = {
  id: number;
  title: string;
  created_at: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init);
  if (!res.ok) {
    throw new Error(`${init?.method ?? 'GET'} ${path} failed: ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export function listItems(): Promise<Item[]> {
  return request<Item[]>('/api/items/');
}

export function createItem(title: string): Promise<Item> {
  return request<Item>('/api/items/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });
}
