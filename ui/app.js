const API_BASE = "http://localhost:8000";

function card(title, body, state) {
  const stateClass = state ? `state ${escapeHtml(state)}` : "";
  return `<article class="card"><strong>${escapeHtml(title)}</strong>${state ? `<span class="${stateClass}">${escapeHtml(state)}</span>` : ""}<p>${escapeHtml(body || "")}</p></article>`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function getJson(path) {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) throw new Error(`${path} respondio ${response.status}`);
  return response.json();
}

async function refresh() {
  const [status, config, runtime, sources, supabase, mentis] = await Promise.all([
    getJson("/status"),
    getJson("/config"),
    getJson("/config/runtime"),
    getJson("/knowledge-sources"),
    getJson("/supabase/verify"),
    getJson("/mentis/verify"),
  ]);

  document.querySelector("#services").innerHTML = status.services
    .map((service) => card(service.name, service.detail, service.state))
    .join("");

  document.querySelector("#config").textContent = JSON.stringify(config, null, 2);
  fillConfigForm(config, runtime.runtime);

  const discord = config.discord;
  document.querySelector("#discord").innerHTML = [
    card("Solicitudes", discord.requests_channel_id || "Sin configurar"),
    card("Notificaciones", discord.notifications_channel_id || "Sin configurar"),
    card("Estado", discord.status_channel_id || "Sin configurar"),
    card("Bot", config.discord_control.has_bot_token ? "Token configurado" : "Sin token"),
    card("Aprobadores", config.discord_control.approver_user_ids || "Sin configurar"),
  ].join("");
  fillDiscordForm(config);

  document.querySelector("#sources").innerHTML = sources.sources
    .map((source) => card(source.name, `${source.source_type} · ${source.schedule || "sin cron"} · ${source.url || "sin URL"}`, source.enabled ? "healthy" : "offline"))
    .join("");

  const s = supabase.supabase;
  document.querySelector("#supabase").innerHTML = card(
    "Vector store",
    `${s.detail} · REST: ${s.rest_available} · schema: ${s.knowledge_schema_ready} · service role: ${s.has_service_role_key}`,
    s.knowledge_schema_ready ? "healthy" : s.reachable ? "degraded" : "offline",
  );

  const m = mentis.mentis;
  document.querySelector("#mentis").innerHTML = card(
    "Verificacion",
    `${m.detail} · lectura: ${m.can_read} · escritura: ${m.can_write}`,
    m.reachable ? "healthy" : "offline",
  );
}

document.querySelector("#refresh").addEventListener("click", refresh);
document.querySelector("#source-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const form = new FormData(event.currentTarget);
    const payload = Object.fromEntries(form.entries());
    const adminToken = payload.admin_token;
    delete payload.admin_token;
    payload.enabled = true;
    const response = await fetch(`${API_BASE}/knowledge-sources`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Admin-Token": adminToken },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error(`No se pudo agregar la fuente: HTTP ${response.status}`);
    event.currentTarget.reset();
    await refresh();
  } catch (error) {
    document.querySelector("#sources").innerHTML = card("Fuentes", error.message, "offline");
  }
});

document.querySelector("#config-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const form = new FormData(event.currentTarget);
    const payload = Object.fromEntries(form.entries());
    const adminToken = payload.admin_token;
    delete payload.admin_token;
    for (const [key, value] of Object.entries(payload)) {
      if (value === "") delete payload[key];
    }
    if (payload.embedding_dimensions) payload.embedding_dimensions = Number(payload.embedding_dimensions);
    const response = await fetch(`${API_BASE}/config/runtime`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", "X-Admin-Token": adminToken },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error(`No se pudo guardar configuracion: HTTP ${response.status}`);
    document.querySelector("#config-status").innerHTML = card("Configuracion", "Guardada correctamente", "healthy");
    await refresh();
  } catch (error) {
    document.querySelector("#config-status").innerHTML = card("Configuracion", error.message, "offline");
  }
});

document.querySelector("#discord-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const form = new FormData(event.currentTarget);
    const payload = Object.fromEntries(form.entries());
    const adminToken = payload.admin_token;
    delete payload.admin_token;
    for (const [key, value] of Object.entries(payload)) {
      if (value === "") delete payload[key];
    }
    const response = await fetch(`${API_BASE}/config/runtime`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", "X-Admin-Token": adminToken },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error(`No se pudo guardar Discord: HTTP ${response.status}`);
    document.querySelector("#discord-status").innerHTML = card("Discord", "Configuracion guardada", "healthy");
    event.currentTarget.elements.discord_bot_token.value = "";
    await refresh();
  } catch (error) {
    document.querySelector("#discord-status").innerHTML = card("Discord", error.message, "offline");
  }
});

function fillConfigForm(config, runtime) {
  const form = document.querySelector("#config-form");
  const values = {
    open_claw_base_url: config.integrations.open_claw,
    mentis_base_url: config.integrations.mentis,
    langfuse_host: config.integrations.langfuse,
    ollama_base_url: config.integrations.ollama,
    supabase_url: config.integrations.supabase.url,
    embedding_model: config.integrations.supabase.embedding_model,
    embedding_dimensions: config.integrations.supabase.embedding_dimensions,
    discord_requests_channel_id: config.discord.requests_channel_id || "",
    discord_notifications_channel_id: config.discord.notifications_channel_id || "",
    discord_status_channel_id: config.discord.status_channel_id || "",
  };
  for (const [key, value] of Object.entries(values)) {
    const input = form.elements[key];
    if (input && document.activeElement !== input) input.value = value || "";
  }
  document.querySelector("#config-status").textContent = `Secretos configurados: ${JSON.stringify(runtime.secrets || {})}`;
}

function fillDiscordForm(config) {
  const form = document.querySelector("#discord-form");
  const values = {
    discord_requests_channel_id: config.discord.requests_channel_id || "",
    discord_notifications_channel_id: config.discord.notifications_channel_id || "",
    discord_status_channel_id: config.discord.status_channel_id || "",
    discord_approver_user_ids: config.discord_control.approver_user_ids || "",
  };
  for (const [key, value] of Object.entries(values)) {
    const input = form.elements[key];
    if (input && document.activeElement !== input) input.value = value;
  }
}

refresh().catch((error) => {
  document.querySelector("#services").innerHTML = card("Control API", error.message, "offline");
});
