export const API_BASE = "http://localhost:8000";

export async function getJson(path: string) {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) throw new Error(`${path} respondio ${response.status}`);
  return response.json();
}

export async function saveRuntimeConfig(payload: any, adminToken: string) {
  const response = await fetch(`${API_BASE}/config/runtime`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", "X-Admin-Token": adminToken },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

export async function addKnowledgeSource(payload: any, adminToken: string) {
  const response = await fetch(`${API_BASE}/knowledge-sources`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Admin-Token": adminToken },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

export async function saveIngestionSchedule(payload: any, adminToken: string) {
  const response = await fetch(`${API_BASE}/ingestion/schedule`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", "X-Admin-Token": adminToken },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

export async function triggerIngestionRun(target: string, adminToken: string) {
  const response = await fetch(`${API_BASE}/ingestion/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Admin-Token": adminToken },
    body: JSON.stringify({ target }),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

export async function getLeads() {
  return getJson("/marketing/leads");
}
