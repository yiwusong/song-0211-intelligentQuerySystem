/**
 * API 调用封装
 */

const API_BASE = '/api';

export async function queryAPI(question: string): Promise<Response> {
  return fetch(`${API_BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
}

export async function healthCheck(): Promise<{
  status: string;
  service: string;
  version: string;
  model: string;
  database: string;
  schema_index: string;
}> {
  const res = await fetch('/health');
  return res.json();
}

export async function schemaStatus(): Promise<{
  status: string;
  tables_indexed: number;
  message: string;
}> {
  const res = await fetch(`${API_BASE}/schema/status`);
  return res.json();
}

export async function schemaRefresh(): Promise<{
  status: string;
  tables_indexed: number;
  message: string;
}> {
  const res = await fetch(`${API_BASE}/schema/refresh`, { method: 'POST' });
  return res.json();
}
