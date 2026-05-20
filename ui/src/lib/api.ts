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

export async function getWhatsAppOutreach() {
  return getJson("/marketing/whatsapp");
}

export async function addWhatsAppContact(payload: any, adminToken: string) {
  const response = await fetch(`${API_BASE}/marketing/whatsapp/contacts`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Admin-Token": adminToken },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

export async function createWhatsAppCampaign(payload: any, adminToken: string) {
  const response = await fetch(`${API_BASE}/marketing/whatsapp/campaigns`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Admin-Token": adminToken },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

export async function decideWhatsAppCampaign(campaignId: string, payload: any, adminToken: string) {
  const response = await fetch(`${API_BASE}/marketing/whatsapp/campaigns/${campaignId}/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Admin-Token": adminToken },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}
