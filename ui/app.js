const API_BASE = "http://localhost:8000";

const state = {
  config: null,
  runtime: null,
  status: null,
  sources: null,
  supabase: null,
  mentis: null,
  ingestion: null,
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function badge(value) {
  return `<span class="state ${escapeHtml(value)}">${escapeHtml(value)}</span>`;
}

function card(title, body, status) {
  return `
    <article class="card">
      <div class="card-title">
        <strong>${escapeHtml(title)}</strong>
        ${status ? badge(status) : ""}
      </div>
      <p>${escapeHtml(body || "")}</p>
    </article>
  `;
}

function summaryCard(label, value) {
  return `<article class="summary-card"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></article>`;
}

async function getJson(path) {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) throw new Error(`${path} respondio ${response.status}`);
  return response.json();
}

async function refresh() {
  const [status, config, runtime, sources, supabase, mentis, ingestion] = await Promise.all([
    getJson("/status"),
    getJson("/config"),
    getJson("/config/runtime"),
    getJson("/knowledge-sources"),
    getJson("/supabase/verify"),
    getJson("/mentis/verify"),
    getJson("/ingestion"),
  ]);

  Object.assign(state, { status, config, runtime, sources, supabase, mentis, ingestion });
  render();
  document.querySelector("#last-refresh").textContent = new Date().toLocaleTimeString();
}

function render() {
  renderSummary();
  renderServices();
  renderDiscord();
  renderKnowledge();
  renderIngestion();
  renderIntegrations();
  renderConfig();
}

function renderSummary() {
  const services = state.status.services || [];
  const healthy = services.filter((service) => service.state === "healthy").length;
  const sources = state.sources.sources || [];
  const discordConfigured = [
    state.config.discord.requests_channel_id,
    state.config.discord.notifications_channel_id,
    state.config.discord.status_channel_id,
  ].filter(Boolean).length;

  document.querySelector("#summary").innerHTML = [
    summaryCard("Servicios healthy", `${healthy}/${services.length}`),
    summaryCard("Fuentes activas", sources.filter((source) => source.enabled).length),
    summaryCard("Discord", `${discordConfigured}/3 canales`),
    summaryCard("Embedding", state.config.integrations.supabase.embedding_model || "Sin configurar"),
  ].join("");
}

function renderServices() {
  document.querySelector("#services").innerHTML = state.status.services
    .map((service) => card(service.name, service.detail, service.state))
    .join("");
}

function renderDiscord() {
  const discord = state.config.discord;
  const control = state.config.discord_control;
  document.querySelector("#discord").innerHTML = [
    card("Solicitudes", discord.requests_channel_id || "Sin configurar", discord.requests_channel_id ? "healthy" : "offline"),
    card("Notificaciones", discord.notifications_channel_id || "Sin configurar", discord.notifications_channel_id ? "healthy" : "offline"),
    card("Estado", discord.status_channel_id || "Sin configurar", discord.status_channel_id ? "healthy" : "offline"),
    card("Bot", control.has_bot_token ? "Token configurado" : "Sin token", control.has_bot_token ? "healthy" : "offline"),
    card("Aprobadores", control.approver_user_ids || "Sin configurar", control.approver_user_ids ? "healthy" : "offline"),
  ].join("");
  fillDiscordForm();
}

function renderKnowledge() {
  const sources = state.sources.sources || [];
  document.querySelector("#sources").innerHTML = sources.length
    ? sources
        .map((source) =>
          card(
            source.name,
            `${source.source_type} · ${source.schedule || "sin cron"} · ${source.url || "sin URL"}`,
            source.enabled ? "healthy" : "offline",
          ),
        )
        .join("")
    : card("Fuentes", "No hay fuentes configuradas todavia.", "unknown");
}

function renderIngestion() {
  const schedule = state.ingestion.schedule;
  fillForm(document.querySelector("#ingestion-schedule-form"), schedule);
  const runs = state.ingestion.runs || [];
  document.querySelector("#ingestion-runs").innerHTML = runs.length
    ? runs
        .map((run) => card(run.target, `${run.detail} · ${run.started_at}`, run.status === "queued" ? "unknown" : run.status))
        .join("")
    : card("Runs", "Todavia no hay ejecuciones registradas.", "unknown");
}

function renderIntegrations() {
  const supabase = state.supabase.supabase;
  document.querySelector("#supabase").innerHTML = card(
    "Vector store",
    `${supabase.detail} · REST: ${supabase.rest_available} · schema: ${supabase.knowledge_schema_ready} · service role: ${supabase.has_service_role_key}`,
    supabase.knowledge_schema_ready ? "healthy" : supabase.reachable ? "degraded" : "offline",
  );

  const mentis = state.mentis.mentis;
  const mentisEnabled = state.config.integrations.mentis_enabled;
  document.querySelector("#mentis").innerHTML = card(
    mentisEnabled ? "Verificacion" : "Opcional",
    `${mentis.detail} · lectura: ${mentis.can_read} · escritura: ${mentis.can_write}`,
    mentisEnabled ? (mentis.reachable ? "healthy" : "offline") : "unknown",
  );
}

function renderConfig() {
  document.querySelector("#config").textContent = JSON.stringify(state.config, null, 2);
  fillConfigForm();
  const secrets = state.runtime.runtime?.secrets || {};
  document.querySelector("#config-status").textContent = `Secretos configurados: ${JSON.stringify(secrets)}`;
}

function adminToken() {
  return document.querySelector("#global-admin-token").value;
}

function formPayload(form) {
  const payload = Object.fromEntries(new FormData(form).entries());
  for (const [key, value] of Object.entries(payload)) {
    if (value === "") delete payload[key];
  }
  if (payload.embedding_dimensions) payload.embedding_dimensions = Number(payload.embedding_dimensions);
  for (const key of ["mentis_enabled", "langfuse_enabled"]) {
    if (payload[key] === "true") payload[key] = true;
    if (payload[key] === "false") payload[key] = false;
  }
  return payload;
}

async function saveRuntimeConfig(payload) {
  const response = await fetch(`${API_BASE}/config/runtime`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", "X-Admin-Token": adminToken() },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

document.querySelector("#refresh").addEventListener("click", refresh);

document.querySelectorAll(".tab").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((tab) => tab.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.remove("active"));
    button.classList.add("active");
    document.querySelector(`#tab-${button.dataset.tab}`).classList.add("active");
  });
});

document.querySelector("#source-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const payload = formPayload(event.currentTarget);
    payload.enabled = true;
    const response = await fetch(`${API_BASE}/knowledge-sources`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Admin-Token": adminToken() },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    event.currentTarget.reset();
    await refresh();
  } catch (error) {
    document.querySelector("#sources").innerHTML = card("Fuentes", `No se pudo agregar: ${error.message}`, "offline");
  }
});

document.querySelector("#ingestion-schedule-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const response = await fetch(`${API_BASE}/ingestion/schedule`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", "X-Admin-Token": adminToken() },
      body: JSON.stringify(formPayload(event.currentTarget)),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    document.querySelector("#ingestion-status").textContent = "Crons guardados correctamente.";
    await refresh();
  } catch (error) {
    document.querySelector("#ingestion-status").innerHTML = card("Crons", `No se pudo guardar: ${error.message}`, "offline");
  }
});

document.querySelectorAll("[data-run-target]").forEach((button) => {
  button.addEventListener("click", async () => {
    try {
      const response = await fetch(`${API_BASE}/ingestion/runs`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Admin-Token": adminToken() },
        body: JSON.stringify({ target: button.dataset.runTarget }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      document.querySelector("#ingestion-status").textContent = `Run ${button.dataset.runTarget} registrado.`;
      await refresh();
    } catch (error) {
      document.querySelector("#ingestion-status").innerHTML = card("Run manual", `No se pudo registrar: ${error.message}`, "offline");
    }
  });
});

document.querySelector("#config-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await saveRuntimeConfig(formPayload(event.currentTarget));
    document.querySelector("#config-status").textContent = "Configuracion guardada correctamente.";
    await refresh();
  } catch (error) {
    document.querySelector("#config-status").innerHTML = card("Configuracion", `No se pudo guardar: ${error.message}`, "offline");
  }
});

document.querySelector("#discord-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await saveRuntimeConfig(formPayload(event.currentTarget));
    document.querySelector("#discord-status").textContent = "Configuracion de Discord guardada.";
    event.currentTarget.elements.discord_bot_token.value = "";
    await refresh();
  } catch (error) {
    document.querySelector("#discord-status").innerHTML = card("Discord", `No se pudo guardar: ${error.message}`, "offline");
  }
});

function fillConfigForm() {
  const form = document.querySelector("#config-form");
  const config = state.config;
  const values = {
    open_claw_base_url: config.integrations.open_claw,
    mentis_base_url: config.integrations.mentis,
    mentis_enabled: String(config.integrations.mentis_enabled),
    langfuse_host: config.integrations.langfuse,
    langfuse_enabled: String(config.integrations.langfuse_enabled),
    ollama_base_url: config.integrations.ollama,
    supabase_url: config.integrations.supabase.url,
    embedding_model: config.integrations.supabase.embedding_model,
    embedding_dimensions: config.integrations.supabase.embedding_dimensions,
  };
  fillForm(form, values);
}

function fillDiscordForm() {
  const form = document.querySelector("#discord-form");
  const config = state.config;
  fillForm(form, {
    discord_requests_channel_id: config.discord.requests_channel_id || "",
    discord_notifications_channel_id: config.discord.notifications_channel_id || "",
    discord_status_channel_id: config.discord.status_channel_id || "",
    discord_approver_user_ids: config.discord_control.approver_user_ids || "",
  });
}

function fillForm(form, values) {
  for (const [key, value] of Object.entries(values)) {
    const input = form.elements[key];
    if (input && document.activeElement !== input) input.value = value || "";
  }
}

refresh().catch((error) => {
  document.querySelector("#summary").innerHTML = summaryCard("Control API", "Offline");
  document.querySelector("#services").innerHTML = card("Control API", error.message, "offline");
});
