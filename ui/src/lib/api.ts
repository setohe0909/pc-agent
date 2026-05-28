export const API_BASE = import.meta.env.VITE_API_BASE || "/api";

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

export async function submitAssistantRequest(payload: unknown, adminToken: string) {
  const response = await fetch(`${API_BASE}/assistant/request`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Admin-Token": adminToken },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

export async function transcribeAssistantAudio(audio: Blob, adminToken: string) {
  const form = new FormData();
  const extension = audio.type.includes("mp4") ? "m4a" : audio.type.includes("ogg") ? "ogg" : "webm";
  form.append("audio", audio, `speech.${extension}`);
  form.append("language", "es");
  const response = await fetch(`${API_BASE}/assistant/transcribe`, {
    method: "POST",
    headers: { "X-Admin-Token": adminToken },
    body: form,
  });
  if (!response.ok) {
    const detail = await response.text().catch(() => "");
    throw new Error(`HTTP ${response.status}${detail ? `: ${detail}` : ""}`);
  }
  return response.json();
}
