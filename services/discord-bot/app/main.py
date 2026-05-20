import asyncio
import os
import json
from pathlib import Path
import re
import tempfile
import httpx
from fastapi import FastAPI, Request
import uvicorn


async def _send_assistant_request(payload: dict) -> dict:
    base_url = _get_env("OPEN_CLAW_BASE_URL", "http://assistant-runtime:8100").rstrip("/")
    async with httpx.AsyncClient(timeout=300) as client:
        response = await client.post(f"{base_url}/assistant/request", json=payload)
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = response.text[:1200] if response.text else str(exc)
        raise RuntimeError(f"Assistant Runtime HTTP {response.status_code}: {detail}") from exc
    return response.json()


def _get_env(key: str, default: str | None = None) -> str | None:
    # 1. Check environment
    val = os.getenv(key)
    if val:
        return val
    # 2. Check shared runtime config
    config_path = os.getenv("RUNTIME_CONFIG_PATH", "/config/runtime-config.json")
    try:
        if Path(config_path).exists():
            config = json.loads(Path(config_path).read_text(encoding="utf-8"))
            return config.get(key.lower()) or default
    except Exception:
        pass
    return default


def _is_requests_channel(channel_id: int) -> bool:
    expected = _get_env("DISCORD_REQUESTS_CHANNEL_ID")
    return bool(expected) and str(channel_id) == expected


def _approvers() -> set[str]:
    return {value.strip() for value in _get_env("DISCORD_APPROVER_USER_IDS", "").split(",") if value.strip()}


def _extract_post_suggestion(message: str) -> dict | None:
    if "Sugerencia de publicación" not in message or "Hashtags:" not in message:
        return None

    normalized = message.replace("\r\n", "\n")
    body = re.split(r"Sugerencia de publicación para [^:\n]+:\s*", normalized, maxsplit=1)
    if len(body) != 2:
        return None

    description, hashtags_text = body[1].split("Hashtags:", 1)
    description = re.sub(r"^[\s*📝]+", "", description).strip()
    description = re.sub(r"\*+\s*$", "", description).strip()
    hashtags = re.findall(r"#\w+", hashtags_text)
    if not description:
        return None

    caption = f"{description}\n\n{' '.join(hashtags)}".strip()
    return {
        "enhanced_description": description,
        "hashtags": hashtags,
        "caption": caption,
    }


def _extract_free_model_flag(raw_query: str) -> tuple[str, bool]:
    has_flag = bool(re.search(r"(^|\s)--free-model(?=\s|$)", raw_query))
    cleaned = re.sub(r"(^|\s)--free-model(?=\s|$)", " ", raw_query).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned, has_flag


def _extract_source_flag(raw_query: str) -> tuple[str, str | None]:
    match = re.search(r"(^|\s)--source\s+([a-zA-Z0-9_-]+)(?=\s|$)", raw_query)
    source = match.group(2).strip().lower() if match else None
    cleaned = re.sub(r"(^|\s)--source\s+[a-zA-Z0-9_-]+(?=\s|$)", " ", raw_query).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned, source


def _extract_account_flag(raw_query: str) -> tuple[str, str | None]:
    match = re.search(r"(^|\s)--account\s+([a-zA-Z0-9_-]+)(?=\s|$)", raw_query)
    account_id = match.group(2).strip() if match else None
    cleaned = re.sub(r"(^|\s)--account\s+[a-zA-Z0-9_-]+(?=\s|$)", " ", raw_query).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned, account_id


async def _decide_whatsapp_campaign(campaign_id: str, approved: bool, decided_by: str) -> dict:
    base_url = _get_env("CONTROL_API_URL", "http://control-api:8000").rstrip("/")
    token = _get_env("ADMIN_API_TOKEN", "")
    async with httpx.AsyncClient(timeout=15) as client_http:
        response = await client_http.post(
            f"{base_url}/marketing/whatsapp/campaigns/{campaign_id}/decision",
            headers={"x-admin-token": token},
            json={"approved": approved, "decided_by": decided_by},
        )
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = response.text[:800] if response.text else str(exc)
        raise RuntimeError(f"Control API HTTP {response.status_code}: {detail}") from exc
    return response.json()


async def main() -> None:
    token = None
    while not token:
        token = _get_env("DISCORD_BOT_TOKEN") or _get_env("DISCORD_TOKEN")
        if not token:
            print("Discord bot en espera: falta DISCORD_BOT_TOKEN o DISCORD_TOKEN en env o runtime config")
            await asyncio.sleep(10)

    import discord
    from discord.ui import Button, View

    class TradeView(View):
        def __init__(self, payload, message_author):
            super().__init__(timeout=120)
            self.payload = payload
            self.message_author = message_author

        @discord.ui.button(label="✅ Confirmar Orden", style=discord.ButtonStyle.green)
        async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
            if str(interaction.user.id) != str(self.message_author.id):
                await interaction.response.send_message("No eres el autor de esta solicitud.", ephemeral=True)
                return
            
            await interaction.response.edit_message(content="⏳ Procesando ejecución con análisis dual...", view=None)
            try:
                result = await _send_assistant_request(self.payload)
                
                if result.get("status") == "executed":
                    embed = discord.Embed(
                        title="🚀 TRADE EJECUTADO",
                        description=result.get("message"),
                        color=discord.Color.green()
                    )
                    order = result.get("order", {})
                    embed.add_field(name="Ticker", value=order.get("ticker", "N/A"), inline=True)
                    embed.add_field(name="ID Orden", value=order.get("order_id", "N/A"), inline=True)
                    embed.add_field(name="🛡️ Nota Crítica", value=result.get("critic_note", "N/A"), inline=False)
                    embed.set_footer(text="Confirmado vía botón - PC Agent Pro")
                    await interaction.message.edit(content=None, embed=embed)
                else:
                    embed = discord.Embed(
                        title="⚠️ Operación Detenida",
                        description=result.get("message"),
                        color=discord.Color.orange()
                    )
                    await interaction.message.edit(content=None, embed=embed)
            except Exception as e:
                await interaction.message.edit(content=f"❌ Error técnico: {e}", embed=None)

        @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.red)
        async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.edit_message(content="🚫 Orden cancelada y descartada.", embed=None, view=None)

    class MarketingView(View):
        def __init__(self, message_author):
            super().__init__(timeout=60)
            self.message_author = message_author

        @discord.ui.button(label="🎯 Qualify Leads", style=discord.ButtonStyle.primary)
        async def qualify(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self._run_marketing(interaction, "qualify", "cualifica leads")

        @discord.ui.button(label="📣 Campaign", style=discord.ButtonStyle.primary)
        async def campaign(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self._run_marketing(interaction, "campaign", "campaña de crecimiento")

        @discord.ui.button(label="🗂️ Posts", style=discord.ButtonStyle.secondary)
        async def posts(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self._run_marketing(interaction, "posts", "posts para campaña de crecimiento")

        @discord.ui.button(label="🚀 Trends", style=discord.ButtonStyle.success)
        async def trends(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self._run_marketing(interaction, "trends", "busca tendencias")

        @discord.ui.button(label="📊 Sentiment", style=discord.ButtonStyle.secondary)
        async def sentiment(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self._run_marketing(interaction, "sentiment", "analiza sentimiento")

        async def _run_marketing(self, interaction, sub_cmd, prompt):
            if str(interaction.user.id) != str(self.message_author.id):
                await interaction.response.send_message("No autorizado.", ephemeral=True)
                return
            
            await interaction.response.edit_message(content=f"⏳ Procesando `{sub_cmd}` vía LangGraph...", view=None)
            payload = {
                "action_type": "marketing",
                "prompt": prompt,
                "source": {"platform": "discord", "channel_id": str(interaction.channel_id), "user_id": str(interaction.user.id)},
                "payload": {"sub_command": sub_cmd, "autonomy_level": "assisted"}
            }
            try:
                result = await _send_assistant_request(payload)
                msg = result.get("message", "No hubo respuesta.")
                await interaction.message.edit(content=msg)
            except Exception as e:
                await interaction.message.edit(content=f"❌ Error: {e}")

    class ConfirmationView(View):
        def __init__(self, context: str, message_author):
            super().__init__(timeout=60)
            self.context = context
            self.message_author = message_author

        @discord.ui.button(label="✅ Sí, Borrar Memoria", style=discord.ButtonStyle.danger)
        async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
            if str(interaction.user.id) != str(self.message_author.id):
                await interaction.response.send_message("No estás autorizado.", ephemeral=True)
                return
            
            await interaction.response.edit_message(content=f"⏳ Borrando memoria ({self.context})...", view=None)
            try:
                base_url = _get_env("CONTROL_API_URL", "http://control-api:8000").rstrip("/")
                async with httpx.AsyncClient(timeout=10) as client_http:
                    resp = await client_http.delete(f"{base_url}/intelligence/memory/today?context={self.context}")
                
                if resp.status_code == 200:
                    await interaction.message.edit(content=f"✅ **Memoria ({self.context}) borrada con éxito.**")
                else:
                    await interaction.message.edit(content=f"❌ Error al borrar: HTTP {resp.status_code}")
            except Exception as e:
                await interaction.message.edit(content=f"❌ Error técnico: {e}")

        @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary)
        async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.message.edit(content="🚫 Acción cancelada. La memoria sigue intacta.", view=None)

    class WhatsAppCampaignApprovalView(View):
        def __init__(self, campaign_id: str, message_author):
            super().__init__(timeout=180)
            self.campaign_id = campaign_id
            self.message_author = message_author

        def _can_approve(self, user_id: int) -> bool:
            approvers = _approvers()
            if approvers:
                return str(user_id) in approvers
            return str(user_id) == str(self.message_author.id)

        @discord.ui.button(label="✅ Aprobar WhatsApp", style=discord.ButtonStyle.green)
        async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
            if not self._can_approve(interaction.user.id):
                await interaction.response.send_message("No estás autorizado como aprobador.", ephemeral=True)
                return
            await interaction.response.edit_message(content="⏳ Aprobando campaña WhatsApp...", embed=None, view=None)
            try:
                result = await _decide_whatsapp_campaign(self.campaign_id, True, str(interaction.user.id))
                campaign = result.get("campaign", {})
                await interaction.message.edit(
                    content=(
                        f"✅ Campaña WhatsApp `{campaign.get('name', self.campaign_id)}` aprobada "
                        f"y marcada como `{campaign.get('status', 'queued')}`."
                    ),
                    embed=None,
                    view=None,
                )
            except Exception as exc:
                await interaction.message.edit(content=f"❌ No pude aprobar la campaña: {exc}", embed=None, view=None)

        @discord.ui.button(label="❌ Denegar", style=discord.ButtonStyle.red)
        async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
            if not self._can_approve(interaction.user.id):
                await interaction.response.send_message("No estás autorizado como aprobador.", ephemeral=True)
                return
            await interaction.response.edit_message(content="⏳ Denegando campaña WhatsApp...", embed=None, view=None)
            try:
                result = await _decide_whatsapp_campaign(self.campaign_id, False, str(interaction.user.id))
                campaign = result.get("campaign", {})
                await interaction.message.edit(
                    content=f"🚫 Campaña WhatsApp `{campaign.get('name', self.campaign_id)}` denegada.",
                    embed=None,
                    view=None,
                )
            except Exception as exc:
                await interaction.message.edit(content=f"❌ No pude denegar la campaña: {exc}", embed=None, view=None)

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready() -> None:
        print(f"Discord conectado como {client.user}")

    def _is_thread_channel(channel) -> bool:
        return isinstance(channel, discord.Thread)

    async def _get_or_create_agent_thread(message, agent_name: str, title: str):
        if _is_thread_channel(message.channel):
            return message.channel

        clean_title = " ".join(title.split()).strip() or "conversación"
        if len(clean_title) > 48:
            clean_title = clean_title[:48].rstrip() + "..."
        return await message.create_thread(name=f"{agent_name}: {clean_title}")

    async def _send_long(destination, text: str, prefix: str | None = None):
        text = text or "No hubo respuesta."
        if prefix:
            text = f"{prefix}\n\n{text}"

        if len(text) <= 1900:
            await destination.send(text)
            return

        chunks = [text[i:i+1900] for i in range(0, len(text), 1900)]
        for index, chunk in enumerate(chunks, start=1):
            header = f"**Parte {index}/{len(chunks)}**\n" if len(chunks) > 1 else ""
            await destination.send(f"{header}{chunk}")

    async def _send_model_status(message, agent: str):
        payload = {
            "action_type": "model_status",
            "prompt": agent,
            "source": {"platform": "discord", "channel_id": str(message.channel.id), "user_id": str(message.author.id)},
            "payload": {"agent": agent},
        }
        try:
            result = await _send_assistant_request(payload)
            text = result.get("message", "No pude obtener el estado de modelos.")
            if len(text) <= 1900:
                await message.reply(text)
            else:
                await _send_long(message.channel, text)
        except Exception as exc:
            hint = ""
            if "422" in str(exc) and "model_status" in str(exc):
                hint = "\n\nPista: `assistant-runtime` parece estar corriendo una versión anterior. Reinicia `assistant-runtime` y luego `discord-bot`."
            await message.reply(f"❌ Error consultando modelos de `{agent}`: {exc}{hint}")

    def _metric_number(value) -> float:
        if value is None:
            return 0.0
        text = str(value).strip().upper().replace(",", "")
        match = re.search(r"-?\d+(?:\.\d+)?", text)
        if not match:
            return 0.0
        number = float(match.group(0))
        if "K" in text:
            return number * 1000
        if "M" in text:
            return number * 1000000
        return number

    def _render_dashboard_chart(dashboard: dict) -> str | None:
        try:
            os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from matplotlib.patches import FancyBboxPatch
        except Exception as exc:
            print(f"[DASHBOARD CHART] matplotlib no disponible: {exc}")
            return None

        accounts = dashboard.get("accounts", {})
        platforms = dashboard.get("platforms", {})
        instagram = platforms.get("instagram", {})
        tiktok = platforms.get("tiktok", {})
        metrics = dashboard.get("metrics", {})
        audience = dashboard.get("audience", {})
        best_windows = dashboard.get("best_posting_windows", {})
        recommendations = dashboard.get("recommendations", [])

        ig_top = instagram.get("top_content") or {}
        tt_top = tiktok.get("top_content") or {}

        ig_user = str(accounts.get("instagram", "—")).replace("@", "")
        tt_user = str(accounts.get("tiktok", "—")).replace("@", "")

        fig = plt.figure(figsize=(14, 8), facecolor="#f1f5f9")
        grid = fig.add_gridspec(3, 6, height_ratios=[0.15, 1, 1.2], hspace=0.4, wspace=0.35)

        fig.suptitle("📊 Dashboard Zernio", fontsize=22, fontweight="bold", color="#0f172a", y=0.975)
        fig.text(0.5, 0.942, dashboard.get("period", "Últimos 30 días"), ha="center", fontsize=10, color="#64748b")

        # ── KPI cards row ──
        ig_followers = instagram.get("followers", 0)
        tt_followers = tiktok.get("followers", 0)
        total_reach = metrics.get("total_reach", "N/D")
        total_engagement = metrics.get("total_engagement_rate", "N/D")
        total_posts = metrics.get("posts_last_30d", "N/D")

        kpi_data = [
            ("Alcance", str(total_reach)),
            ("Engagement", str(total_engagement)),
            ("Posts (30d)", str(total_posts)),
            ("IG Seguidores", str(ig_followers)),
            ("TT Seguidores", str(tt_followers)),
        ]

        for idx, (label, value) in enumerate(kpi_data):
            ax = fig.add_subplot(grid[0, idx])
            ax.set_facecolor("#ffffff")
            for s in ax.spines.values():
                s.set_edgecolor("#e2e8f0")
            ax.set_xticks([])
            ax.set_yticks([])
            ax.text(0.08, 0.55, value, fontsize=14, fontweight="bold", color="#0f172a", transform=ax.transAxes)
            ax.text(0.08, 0.18, label, fontsize=8, color="#64748b", transform=ax.transAxes)

        # ── IG Metrics Panel ──
        ax_ig = fig.add_subplot(grid[1, :3])
        ax_ig.set_facecolor("#ffffff")
        for s in ax_ig.spines.values():
            s.set_edgecolor("#e2e8f0")
        ax_ig.set_xticks([])
        ax_ig.set_yticks([])
        ax_ig.set_title(f"Instagram @{ig_user}", fontsize=13, fontweight="bold", color="#0f172a", loc="left", pad=8)

        ig_metrics_lines = [
            f"👥 Seguidores: {instagram.get('followers', 'N/D')}",
            f"📸 Posts: {instagram.get('external_posts', 'N/D')}",
            f"👁 Alcance (30d): {instagram.get('reach', 'N/D')}",
            f"▶️ Views (30d): {instagram.get('views', 'N/D')}",
            f"❤️ Interacciones: {instagram.get('total_interactions', 'N/D')}",
            f"🔄 Cuentas alcanzadas: {instagram.get('accounts_engaged', 'N/D')}",
        ]
        if ig_top.get("title"):
            ig_metrics_lines.append(f"🏆 Top: {ig_top['title'][:35]}...")
            ig_metrics_lines.append(f"   ER: {ig_top.get('engagement_rate', 'N/A')} · 👍 {ig_top.get('likes', '?')}")
        ig_text = "\n".join(ig_metrics_lines)
        ax_ig.text(0.06, 0.92, ig_text, va="top", fontsize=9, color="#334155",
                   linespacing=1.6, transform=ax_ig.transAxes,
                   bbox=dict(facecolor="#fafafa", edgecolor="none", pad=8, boxstyle="round,pad=0.5"))

        # ── TT Metrics Panel ──
        ax_tt = fig.add_subplot(grid[1, 3:])
        ax_tt.set_facecolor("#ffffff")
        for s in ax_tt.spines.values():
            s.set_edgecolor("#e2e8f0")
        ax_tt.set_xticks([])
        ax_tt.set_yticks([])
        ax_tt.set_title(f"TikTok @{tt_user}", fontsize=13, fontweight="bold", color="#0f172a", loc="left", pad=8)

        tt_metrics_lines = [
            f"👥 Seguidores: {tiktok.get('followers', 'N/D')}",
            f"🎬 Videos: {tiktok.get('video_count', tiktok.get('external_posts', 'N/D'))}",
            f"❤️ Likes totales: {tiktok.get('likes_count', 'N/D')}",
        ]
        if tt_top.get("title"):
            tt_metrics_lines.append(f"🏆 Top: {tt_top['title'][:35]}...")
            tt_metrics_lines.append(f"   ER: {tt_top.get('engagement_rate', 'N/A')} · 👍 {tt_top.get('likes', '?')}")
        else:
            tt_metrics_lines.append("📭 Sin datos de contenido todavía")
        tt_text = "\n".join(tt_metrics_lines)
        ax_tt.text(0.06, 0.92, tt_text, va="top", fontsize=9, color="#334155",
                   linespacing=1.6, transform=ax_tt.transAxes,
                   bbox=dict(facecolor="#fafafa", edgecolor="none", pad=8, boxstyle="round,pad=0.5"))

        # ── Audience + Horarios Panel ──
        ax_info = fig.add_subplot(grid[2, :3])
        ax_info.set_facecolor("#ffffff")
        for s in ax_info.spines.values():
            s.set_edgecolor("#e2e8f0")
        ax_info.set_xticks([])
        ax_info.set_yticks([])
        ax_info.set_title("Audiencia y Horarios", fontsize=13, fontweight="bold", color="#0f172a", loc="left", pad=8)

        age_range = audience.get("top_age_range", "N/D")
        top_locs = audience.get("top_locations", [])
        loc_text = ", ".join(top_locs[:3]) if top_locs else "N/D"
        windows_rec = best_windows.get("recommendation", "Acumula datos para obtener recomendaciones.")

        info_lines = [
            f"📅 Edad principal: {age_range}",
            f"📍 Ubicaciones: {loc_text}",
            f"⏰ {windows_rec[:80]}",
        ]
        ax_info.text(0.06, 0.92, "\n".join(info_lines), va="top", fontsize=9, color="#334155",
                     linespacing=1.8, transform=ax_info.transAxes,
                     bbox=dict(facecolor="#fafafa", edgecolor="none", pad=8, boxstyle="round,pad=0.5"))

        # ── Recommendations Panel ──
        ax_recs = fig.add_subplot(grid[2, 3:])
        ax_recs.set_facecolor("#ffffff")
        for s in ax_recs.spines.values():
            s.set_edgecolor("#e2e8f0")
        ax_recs.set_xticks([])
        ax_recs.set_yticks([])
        ax_recs.set_title("Acciones Sugeridas", fontsize=13, fontweight="bold", color="#0f172a", loc="left", pad=8)

        if recommendations:
            rec_text = "\n".join(f"• {r[:90]}" for r in recommendations[:4])
        else:
            rec_text = "Sigue publicando para obtener recomendaciones personalizadas."
        ax_recs.text(0.06, 0.92, rec_text, va="top", fontsize=9, color="#334155",
                     linespacing=1.6, transform=ax_recs.transAxes,
                     bbox=dict(facecolor="#f0f9ff", edgecolor="#bae6fd", pad=8, boxstyle="round,pad=0.5"))

        # ── Platfom badges at bottom ──
        fig.text(0.5, 0.008, f"IG: @{ig_user}  ·  TT: @{tt_user}  ·  Datos vía Zernio API",
                 ha="center", fontsize=8, color="#94a3b8", style="italic")

        output = tempfile.NamedTemporaryFile(prefix="zernio-dashboard-", suffix=".png", delete=False)
        output.close()
        fig.savefig(output.name, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)
        return output.name

    async def _send_dashboard_chart(destination, dashboard: dict | None):
        if not dashboard:
            return
        chart_path = _render_dashboard_chart(dashboard)
        if not chart_path:
            return
        try:
            await destination.send(file=discord.File(chart_path, filename="zernio-dashboard.png"))
        finally:
            try:
                os.unlink(chart_path)
            except OSError:
                pass

    @client.event
    async def on_message(message) -> None:
        if message.author == client.user:
            return
            
        is_thread = isinstance(message.channel, discord.Thread)
        # Solo procesamos si es el canal correcto o si es un hilo de este bot
        if not is_thread and not _is_requests_channel(message.channel.id):
            return
        
        # Si es un hilo, verificamos que sea nuestro o que nos mencionen
        if is_thread and message.channel.owner_id != client.user.id:
            return

        content = message.content.strip()
        command_list = ("!ask ", "!research ", "!approve_trade ", "!status", "!memory", "!run ", "!claw ", "!marketer ", "!marketer-status", "!writer ", "!picture ", "!coder-web ", "!help")
        
        # Si NO es un comando Y NO estamos en un hilo nuestro, ignorar
        if not content.startswith(command_list) and not content in ("!picture", "!coder-web") and not is_thread:
            return

        # Si estamos en un hilo pero no hay comando, inyectar el comando basado en el nombre del hilo
        if is_thread and not content.startswith(command_list):
            thread_name = message.channel.name.lower()
            if "marketer" in thread_name:
                content = f"!marketer {content}"
            elif "writer" in thread_name:
                content = f"!writer {content}"
            elif "picture" in thread_name or "imagen" in thread_name:
                content = f"!picture {content}"
            elif "pilot" in thread_name or "coder" in thread_name:
                content = f"!coder-web {content}"
            elif "claw" in thread_name:
                content = f"!claw {content}"
            else:
                content = f"!ask {content}"

        # --- COMANDO HELP ---
        if content in ("!help marketer", "!help marketing", "!help !marketer"):
            embed = discord.Embed(
                title="📣 Ayuda de Marketer Agent",
                description="Comandos de marketing, fuentes de datos y modelos conectados.",
                color=discord.Color.purple()
            )
            embed.add_field(
                name="Datos",
                value="`!marketer-status`: Estado del agente.\n`!marketer dashboard`: Dashboard visual Zernio.\n`!marketer comments`: Comentarios desde memoria operativa.\n`!marketer leads`: Leads guardados.\n`!marketer top-content`: Mejores contenidos.\n`!marketer audience`: Audiencia y segmentos.\n`!marketer alerts`: Alertas.\n`!marketer best-hours`: Horarios recomendados.",
                inline=False
            )
            embed.add_field(
                name="Acciones",
                value="`!marketer campaign <objetivo>`: Plan de campaña.\n`!marketer posts <tema>`: Cola de posts.\n`!marketer respond`: Borradores de respuesta.\n`!marketer qualify`: Cualificar leads.\n`!marketer magnet`: Lead magnets por DM.\n`!marketer sentiment`: Sentimiento y crisis.\n`!marketer funnel <tema>`: Embudo.\n`!marketer --free-model <descripción>`: Visual con proveedor gratuito.",
                inline=False
            )
            embed.add_field(
                name="Usar Zernio con --source",
                value="`--source zernio` fuerza lectura de comentarios reales desde Zernio.\n`--account <id>` selecciona la cuenta cuando hay varias marcas.\n`!marketer --source zernio comments --account <id>`\n`!marketer --source zernio qualify --account <id>`\n`!marketer --source zernio magnet --account <id>`\n`!marketer --source zernio sentiment --account <id>`",
                inline=False
            )
            embed.add_field(
                name="Modelos",
                value="`!marketer --model-status`: Ver proveedores/modelos que usa este sub-agent.",
                inline=False
            )
            await message.reply(embed=embed)
            return

        if content == "!help":
            embed = discord.Embed(
                title="🤖 PC Agent v0.6.1 - Guía de Operaciones", 
                description="Guía actualizada con Picture, Zernio, `--source`, `--free-model` y estado de modelos:",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="🎨 Imagenes y Free Model",
                value="`!marketer --free-model poster cuadrado para Instagram de café artesanal, texto \"Sabor de Origen\"`: Crear pieza visual de marketing con Together.\n`!picture --free-model portada editorial futurista para una marca de skincare`: Crear imagen de prueba con Together.\n`!picture <descripción>`: Crear una imagen con memoria visual.\nAdjunta una imagen + `!picture cambia el texto \"A\" por \"B\"`: Editar texto conservando estilo.",
                inline=False
            )
            embed.add_field(
                name="🔌 Model Status",
                value="`!marketer --model-status`: Modelos de marketing y visuales.\n`!picture --model-status`: Modelos de generación/edición.\n`!claw --model-status`: Modelo de chat/research.\n`!writer --model-status`: Modelo de redacción.\n`!coder-web --model-status`: Modelos de análisis y adapter Pilot.",
                inline=False
            )
            embed.add_field(
                name="🤖 Inteligencia Proactiva", 
                value="`!memory`: Ver qué he aprendido hoy.\n`!run trends`: Forzar búsqueda de tendencias.", 
                inline=False
            )
            embed.add_field(
                name="📣 Marketing Datos",
                value="`!marketer-status`: Estado del marketer.\n`!marketer dashboard`: Dashboard visual Zernio.\n`!marketer top-content`: Mejores contenidos.\n`!marketer audience`: Audiencia y segmentos.\n`!marketer alerts`: Alertas de crecimiento.\n`!marketer comments`: Comentarios recientes desde memoria operativa.\n`!marketer leads`: Leads detectados.\n`!marketer whatsapp`: CRM/campañas WhatsApp.\n`!marketer best-hours`: Mejores horarios.",
                inline=False
            )
            embed.add_field(
                name="📣 Marketing Acciones",
                value="`!marketer campaign <objetivo>`: Campaña asistida.\n`!marketer posts <tema>`: Borradores de posts.\n`!marketer whatsapp send <campaign_id>`: Pedir aprobación por botones para una campaña WhatsApp.\n`!marketer reply-drafts`: Borradores para aprobación.\n`!marketer content-plan`: Calendario con métricas.\n`!marketer repurpose`: Reutilizar contenido ganador.\n`!marketer respond`: Borradores de respuesta.\n`!marketer qualify`: Detectar leads calientes.\n`!marketer magnet`: Lead Magnets (DM).\n`!marketer trends`: Buscar tendencias virales.\n`!marketer sentiment`: Análisis de sentimiento/crisis.\n`!marketer funnel <tema>`: Diseñar embudo.",
                inline=False
            )
            embed.add_field(
                name="📣 Marketing Fuente Zernio",
                value="Usa `--source zernio` para leer comentarios reales desde Zernio en vez de memoria local.\n`!marketer --source zernio comments --account <id>`: Ver comentarios reales.\n`!marketer --source zernio negative-comments --account <id>`: Revisar comentarios de riesgo.\n`!marketer --source zernio qualify --account <id>`: Cualificar leads con trazabilidad.\n`!marketer --source zernio magnet --account <id>`: Preparar DMs por triggers.\n`!marketer --source zernio sentiment --account <id>`: Analizar sentimiento.",
                inline=False
            )
            embed.add_field(
                name="✍️ Writer Sub-Agent", 
                value="`!writer blog <es/en> <tema>`: Crear blog y guardar en Obsidian.\n`!writer story <es/en> <tema>`: Crear storytelling y guardar en Obsidian.\n`!writer <mensaje>`: Chat con el redactor.", 
                inline=False
            )
            embed.add_field(
                name="🧠 Asistente Open Claw", 
                value="`!claw <pregunta>`: Abre un hilo de análisis profundo usando mi memoria diaria.", 
                inline=False
            )
            embed.add_field(
                name="📊 Trading & Research", 
                value="`!ask <duda>`: Pregunta rápida.\n`!research <tema>`: Investigación profunda.\n`!status`: Estado del sistema.", 
                inline=False
            )
            embed.add_field(
                name="⚖️ Decisiones", 
                value="`!approve_trade <id>`: Aprobar una operación sugerida.", 
                inline=False
            )
            embed.add_field(
                name="🎨 Picture Sub-Agent", 
                value="`!picture memory`: Ver estilo y aprendizajes visuales.\n`!picture memory --clean`: Limpiar memoria de imágenes.\nEl bloque de arriba contiene los comandos creativos principales.", 
                inline=False
            )
            embed.add_field(
                name="💻 Coder Web Sub-Agent", 
                value="`!coder-web <descripción>`: Crear/ajustar e-commerce (Repositorio).\n`!coder-web memory`: Ver aprendizajes del desarrollador web.\n`!coder-web memory --clean`: Borrar memoria del día.", 
                inline=False
            )
            embed.set_footer(text="PC Agent v0.6.1 - Help actualizado")
            await message.reply(embed=embed)
            return

        if content.startswith("!claw"):
            query = content.removeprefix("!claw").strip()
            if query == "--model-status":
                await _send_model_status(message, "claw")
                return
            if not query:
                await message.reply("⚠️ Por favor, añade una pregunta después de `!claw`.")
                return
            
            try:
                thread = await _get_or_create_agent_thread(message, "Claw", query)
                await thread.send("🔍 Consultando a Open Claw (Analizando memoria de Mentis)...")
                
                # 2. Llamamos al assistant-runtime
                payload = {
                    "action_type": "chat",
                    "prompt": query,
                    "source": {
                        "platform": "discord",
                        "channel_id": str(message.channel.id),
                        "user_id": str(message.author.id)
                    }
                }
                answer_data = await _send_assistant_request(payload)
                answer = answer_data.get("message", "No hubo respuesta.")
                
                await _send_long(thread, answer, prefix="🤖 **Respuesta de Open Claw:**")
            except discord.Forbidden:
                await message.reply("❌ No tengo permiso para crear hilos en este canal. Por favor, dales permiso a 'Crear hilos públicos'.")
            except Exception as e:
                await message.reply(f"❌ Error al contactar a Open Claw: {e}")
            return

        if content.startswith("!run "):
            target = content.removeprefix("!run ").strip()
            await message.reply(f"🚀 Ejecución iniciada: El trabajo **{target}** está corriendo en segundo plano.")
            try:
                # Llamada al control-api usando el nombre estatico definido en docker-compose
                control_api_url = "http://control-api:8000"
                print(f"[DEBUG] Bot llamando a Control API en: {control_api_url}/ingestion/runs")
                
                async with httpx.AsyncClient(timeout=15) as client_http:
                    resp = await client_http.post(
                        f"{control_api_url}/ingestion/runs",
                        json={"target": target},
                        headers={"x-admin-token": os.getenv("ADMIN_API_TOKEN")}
                    )
                    print(f"[DEBUG] Respuesta Control API: {resp.status_code} - {resp.text}")
                    if resp.status_code != 200:
                        await message.reply(f"⚠️ Error del Servidor ({resp.status_code}): {resp.text}")
            except Exception as e:
                print(f"[CONNECTION ERROR] Fallo al contactar a {control_api_url}: {e}")
                await message.reply(f"⚠️ Error de Conexión: No pude contactar al cerebro del sistema ({e})")
            return

        if content.startswith("!memory"):
            if "--clean" in content:
                embed = discord.Embed(
                    title="⚠️ Confirmación de Borrado",
                    description="¿Estás seguro de que deseas borrar la **memoria general** de hoy? Esta acción no se puede deshacer.",
                    color=discord.Color.red()
                )
                await message.reply(embed=embed, view=ConfirmationView("general", message.author))
                return

            try:
                from datetime import datetime
                today_str = datetime.now().strftime("%Y-%m-%d")
                
                # 1. Crear el hilo para la memoria
                thread = await message.create_thread(
                    name=f"🧠 Memoria de Inteligencia - {today_str}",
                    auto_archive_duration=60
                )
                await thread.send("🔍 Extrayendo inteligencia recolectada hoy...")

                base_url = _get_env("CONTROL_API_URL", "http://control-api:8000").rstrip("/")
                async with httpx.AsyncClient(timeout=10) as client_http:
                    resp = await client_http.get(f"{base_url}/intelligence/memory/today?context=general")
                
                if resp.status_code == 200:
                    data = resp.json()
                    memory_list = data.get("memory", [])
                    if not memory_list:
                        await thread.send("📭 No he recolectado tendencias hoy todavía.")
                        return
                    
                    full_report = f"## 🧠 Reporte de Inteligencia Diaria ({today_str})\n\n"
                    for item in memory_list:
                        category = item.get("category", "N/A").upper()
                        body = item.get("summary", "Sin contenido.")
                        full_report += f"### 🔹 {category}\n{body}\n\n---\n\n"
                    
                    # 3. Enviar al hilo (con soporte para mensajes muy largos)
                    if len(full_report) > 1900:
                        chunks = [full_report[i:i+1900] for i in range(0, len(full_report), 1900)]
                        for i, chunk in enumerate(chunks):
                            await thread.send(chunk)
                    else:
                        await thread.send(full_report)
                    
                    await thread.send("✅ Reporte finalizado.")
                else:
                    await thread.send(f"❌ Error al obtener memoria: HTTP {resp.status_code}")
            except discord.Forbidden:
                await message.reply("❌ Necesito permiso para 'Crear hilos públicos' para mostrarte la memoria.")
            except Exception as exc:
                await message.reply(f"❌ Error crítico en memoria: {exc}")
            return

        if content == "!status":
            try:
                base_url = _get_env("CONTROL_API_URL", "http://control-api:8000").rstrip("/")
                async with httpx.AsyncClient(timeout=5) as client_http:
                    resp = await client_http.get(f"{base_url}/status")
                
                if resp.status_code == 200:
                    status_data = resp.json()
                    services = status_data.get("services", [])
                    report = "**PC Agent - System Status**\n"
                    for s in services:
                        emoji = "✅" if s["state"] == "healthy" else "❌" if s["state"] == "offline" else "⚠️"
                        report += f"{emoji} **{s['name']}**: {s['state']} ({s['detail']})\n"
                    await message.reply(report)
                else:
                    await message.reply(f"Error al obtener status: HTTP {resp.status_code}")
            except Exception as exc:
                await message.reply(f"No pude conectar con el Control API: {exc}")
            return

        if content.startswith("!marketer-status"):
            print(f"[DEBUG] Comando !marketer-status detectado")
            try:
                thread = await _get_or_create_agent_thread(message, "Marketer", "estado")
            except discord.Forbidden:
                await message.reply("❌ Necesito permiso para 'Crear hilos públicos' para conversar con el Marketer Agent.")
                return

            payload = {
                "action_type": "marketing",
                "prompt": "dame tu estado",
                "source": {"platform": "discord", "channel_id": str(thread.id), "user_id": str(message.author.id)},
                "payload": {"sub_command": "status"}
            }
            print(f"[DEBUG] Enviando solicitud !marketer-status al assistant-runtime")
            try:
                await thread.send("📣 **Marketer Agent consultando estado...**")
                result = await _send_assistant_request(payload)
                await _send_long(thread, result.get("message", "No pude obtener el estado del marketer."))
            except Exception as e:
                await thread.send(f"❌ Error al contactar al marketer: {e}")
            return

        if content.startswith("!marketer "):
            raw_query = content.removeprefix("!marketer ").strip()
            raw_query, use_free_model = _extract_free_model_flag(raw_query)
            raw_query, data_source = _extract_source_flag(raw_query)
            raw_query, account_id = _extract_account_flag(raw_query)

            if raw_query == "--model-status":
                await _send_model_status(message, "marketer")
                return
            
            if "memory --clean" in raw_query:
                embed = discord.Embed(
                    title="⚠️ Confirmación de Borrado (Marketer)",
                    description="¿Estás seguro de que deseas borrar la **memoria de marketing** de hoy? Esta acción no se puede deshacer.",
                    color=discord.Color.red()
                )
                await message.reply(embed=embed, view=ConfirmationView("marketer", message.author))
                return

            sub_command = "chat"
            prompt = raw_query
            is_approved_marketing = False
            
            if not raw_query or raw_query.strip() == "":
                embed = discord.Embed(
                    title="📣 Centro de Control de Marketing",
                    description="Selecciona una acción rápida o escribe un comando después de `!marketer`.",
                    color=discord.Color.purple()
                )
                await message.reply(embed=embed, view=MarketingView(message.author))
                return

            # Capturar imágenes/video adjuntos
            images_b64 = []
            media_urls = []
            if message.attachments:
                import base64
                for att in message.attachments:
                    if any(att.filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"]):
                        img_data = await att.read()
                        images_b64.append(base64.b64encode(img_data).decode("utf-8"))
                        media_urls.append(att.url)
                    elif any(att.filename.lower().endswith(ext) for ext in [".mp4", ".mov", ".webm"]):
                        media_urls.append(att.url)

            extra = {}
            if data_source:
                extra["data_source"] = data_source
            if account_id:
                extra["account_id"] = account_id
            if use_free_model:
                extra.update({
                    "prefer_free_model": True,
                    "image_generation_provider": "together",
                    "image_edit_provider": "local",
                })
            if raw_query.startswith("post "):
                sub_command = "publish"
                rest = raw_query.removeprefix("post ").strip()
                import re as _re
                plat_match = _re.search(r'--platform\s+(\S+)', rest)
                if plat_match:
                    extra["platform"] = plat_match.group(1).lower()
                    rest = rest.replace(plat_match.group(0), "")
                account_match = _re.search(r'--account\s+(\S+)', rest)
                if account_match:
                    extra["account_id"] = account_match.group(1)
                    rest = rest.replace(account_match.group(0), "")
                sched_match = _re.search(r'--schedule\s+"([^"]+)"', rest)
                if sched_match:
                    extra["scheduled_for"] = sched_match.group(1)
                    rest = rest.replace(sched_match.group(0), "")
                prompt = rest.strip()
            elif raw_query.startswith("respond"):
                sub_command = "respond"
                prompt = "responde comentarios"
            elif raw_query.startswith("campaign "):
                sub_command = "campaign"
                prompt = raw_query.removeprefix("campaign ").strip()
            elif raw_query.startswith("posts "):
                sub_command = "posts"
                prompt = raw_query.removeprefix("posts ").strip()
            elif raw_query.startswith("approve-campaign"):
                sub_command = "campaign"
                prompt = raw_query.removeprefix("approve-campaign").strip() or "campaña aprobada"
                is_approved_marketing = True
            elif raw_query.startswith("approve-posts"):
                sub_command = "posts"
                prompt = raw_query.removeprefix("approve-posts").strip() or "posts aprobados"
                is_approved_marketing = True
            elif raw_query.startswith("plan "):
                sub_command = "plan"
                prompt = raw_query.removeprefix("plan ").strip()
            elif raw_query.startswith("research "):
                sub_command = "research"
                prompt = raw_query.removeprefix("research ").strip()
            elif raw_query.startswith("competitors"):
                sub_command = "competitors"
                prompt = raw_query.removeprefix("competitors").strip() or "competidor_generico"
            elif raw_query.startswith("qualify"):
                sub_command = "qualify"
                prompt = "cualifica leads"
            elif raw_query.startswith("magnet"):
                sub_command = "magnet"
                prompt = "procesa lead magnets"
            elif raw_query.startswith("funnel "):
                sub_command = "funnel"
                prompt = raw_query.removeprefix("funnel ").strip()
            elif raw_query.startswith("trends"):
                sub_command = "trends"
                prompt = "busca tendencias"
            elif raw_query.startswith("sentiment"):
                sub_command = "sentiment"
                prompt = "analiza sentimiento"
            elif raw_query.startswith("collab "):
                sub_command = "collab"
                prompt = raw_query.removeprefix("collab ").strip()
            elif raw_query.startswith("memory"):
                sub_command = "memory"
                prompt = "ver memoria"
            elif raw_query.startswith("dashboard"):
                sub_command = "dashboard"
                prompt = "genera dashboard"
            elif raw_query.startswith("report"):
                sub_command = "report"
                prompt = raw_query.removeprefix("report").strip() or "general"
            elif raw_query.startswith("top-content"):
                sub_command = "top-content"
                prompt = "ver top content"
            elif raw_query.startswith("audience"):
                sub_command = "audience"
                prompt = "ver audiencia"
            elif raw_query.startswith("alerts"):
                sub_command = "alerts"
                prompt = "ver alertas"
            elif raw_query.startswith("negative-comments"):
                sub_command = "negative-comments"
                prompt = "ver comentarios negativos"
            elif raw_query.startswith("comments"):
                sub_command = "comments"
                prompt = "ver comentarios recientes"
            elif raw_query.startswith("reply-drafts"):
                sub_command = "reply-drafts"
                prompt = "prepara borradores de respuesta"
            elif raw_query.startswith("leads"):
                sub_command = "leads"
                prompt = "ver leads"
            elif raw_query.startswith("whatsapp send "):
                campaign_id = raw_query.removeprefix("whatsapp send ").strip()
                if not campaign_id:
                    await message.reply("⚠️ Usa `!marketer whatsapp send <campaign_id>`.")
                    return
                embed = discord.Embed(
                    title="⚖️ Aprobación WhatsApp requerida",
                    description=(
                        f"¿Aprobar la campaña WhatsApp `{campaign_id}`?\n\n"
                        "Si apruebas, quedará marcada como `queued`. El envío real debe ejecutarse "
                        "por el worker OpenWA con rate limits, opt-out y auditoría."
                    ),
                    color=discord.Color.orange(),
                )
                try:
                    await message.reply(embed=embed, view=WhatsAppCampaignApprovalView(campaign_id, message.author))
                except discord.Forbidden:
                    await message.reply(
                        "❌ No tengo permisos para enviar botones en este canal. "
                        "Revisa permisos de `Send Messages`, `Use Application Commands`, `Embed Links` y `Create Public Threads`."
                    )
                return
            elif raw_query.startswith("whatsapp"):
                sub_command = "whatsapp"
                prompt = "ver whatsapp outreach"
            elif raw_query.startswith("content-plan"):
                sub_command = "content-plan"
                prompt = raw_query.removeprefix("content-plan").strip() or "7 días"
            elif raw_query.startswith("repurpose"):
                sub_command = "repurpose"
                prompt = "reutiliza contenido ganador"
            elif raw_query.startswith("best-hours"):
                sub_command = "best-hours"
                prompt = "ver mejores horarios"

            try:
                thread = await _get_or_create_agent_thread(message, "Marketer", raw_query)
            except discord.Forbidden:
                await message.reply("❌ Necesito permiso para 'Crear hilos públicos' para conversar con el Marketer Agent.")
                return

            if use_free_model and sub_command == "chat":
                picture_payload = {
                    "action_type": "picture",
                    "prompt": prompt,
                    "source": {"platform": "discord", "channel_id": str(thread.id), "user_id": str(message.author.id)},
                    "images": images_b64,
                    "payload": {
                        "prefer_free_model": True,
                        "image_generation_provider": "together",
                        "image_edit_provider": "local",
                        "requested_by": "marketer",
                    }
                }

                await thread.send("📣 **Marketer usando modelo gratuito/local para crear visual...**")
                try:
                    result = await _send_assistant_request(picture_payload)
                    msg = result.get("message", "No hubo respuesta.")
                    if result.get("image_b64"):
                        import io
                        import base64

                        await thread.send(msg)
                        image_bytes = base64.b64decode(result["image_b64"])
                        await thread.send(file=discord.File(io.BytesIO(image_bytes), filename="marketer-free-model.png"))
                    elif result.get("image_url"):
                        image_url = result["image_url"]
                        text_msg = msg.removesuffix(f"\n\n{image_url}")
                        await thread.send(text_msg)
                        embed = discord.Embed(title="Resultado Free Model", color=discord.Color.purple())
                        embed.set_image(url=image_url)
                        await thread.send(embed=embed)
                    else:
                        await _send_long(thread, msg)
                except Exception as e:
                    await thread.send(f"❌ Error usando modelo gratuito/local: {e}")
                return

            payload = {
                "action_type": "marketing",
                "prompt": prompt,
                "source": {"platform": "discord", "channel_id": str(thread.id), "user_id": str(message.author.id)},
                "images": images_b64,
                "payload": {"sub_command": sub_command, "autonomy_level": "assisted", "is_approved": is_approved_marketing, "media_urls": media_urls, **extra}
            }
            
            await thread.send(f"📣 **Marketer Agent procesando `{sub_command}`...**")
            try:
                result = await _send_assistant_request(payload)
                msg = result.get("message", "No hubo respuesta.")
                
                if result.get("status") == "requires_approval":
                    suggestion = result.get("suggestion") or _extract_post_suggestion(msg)
                    if suggestion:
                        embed = discord.Embed(
                            title="📝 Vista Previa del Post",
                            description=(
                                f"{suggestion['enhanced_description']}\n\n"
                                f"**Hashtags:** {' '.join(suggestion['hashtags'])}"
                            ),
                            color=discord.Color.purple()
                        )
                        embed.set_footer(text="Publica ahora, guarda como draft, o escribe tu propio texto.")

                        approval_payload = {
                            **payload,
                            "payload": {**payload["payload"], "is_approved": True, "suggestion": suggestion},
                        }
                        draft_payload = {
                            **payload,
                            "payload": {**payload["payload"], "is_approved": True, "suggestion": suggestion, "draft": True},
                        }

                        class PostRejectModal(discord.ui.Modal, title="Tu descripción personalizada"):
                            custom_text = discord.ui.TextInput(
                                label="Descripción del post",
                                style=discord.TextStyle.paragraph,
                                placeholder="Escribe tu propia descripción para el post...",
                                required=True,
                                max_length=2000,
                            )

                            def __init__(self, pld, thread, author):
                                super().__init__()
                                self.pld = pld
                                self.thread = thread
                                self.author = author

                            async def on_submit(self, interaction: discord.Interaction):
                                publish_pld = {
                                    **self.pld,
                                    "prompt": self.custom_text.value,
                                    "payload": {**self.pld["payload"], "is_approved": True},
                                }
                                publish_pld["payload"].pop("suggestion", None)
                                await interaction.response.edit_message(
                                    content="⏳ Publicando con tu texto personalizado...", view=None, embed=None
                                )
                                res = await _send_assistant_request(publish_pld)
                                await self.thread.send(res.get("message", "Post publicado."))

                        class PostApprovalView(View):
                            def __init__(self, pld, draft_pld, author, thread):
                                super().__init__(timeout=120)
                                self.pld = pld
                                self.draft_pld = draft_pld
                                self.author = author
                                self.thread = thread

                            @discord.ui.button(label="✅ Aceptar", style=discord.ButtonStyle.green)
                            async def accept(self, itn, btn):
                                approvers = _approvers()
                                if approvers and str(itn.user.id) not in approvers:
                                    if str(itn.user.id) != str(self.author.id):
                                        await itn.response.send_message("No estás autorizado como aprobador.", ephemeral=True)
                                        return
                                await itn.response.edit_message(content="⏳ Publicando con la sugerencia...", view=None)
                                res = await _send_assistant_request(self.pld)
                                await itn.message.edit(content="✅ Publicado exitosamente.")
                                await _send_long(self.thread, res.get("message", "Post publicado."))

                            @discord.ui.button(label="📋 Subir como Draft", style=discord.ButtonStyle.blurple)
                            async def draft(self, itn, btn):
                                approvers = _approvers()
                                if approvers and str(itn.user.id) not in approvers:
                                    if str(itn.user.id) != str(self.author.id):
                                        await itn.response.send_message("No estás autorizado como aprobador.", ephemeral=True)
                                        return
                                await itn.response.edit_message(content="⏳ Guardando como draft...", view=None)
                                res = await _send_assistant_request(self.draft_pld)
                                await itn.message.edit(content="✅ Draft guardado.")
                                await _send_long(self.thread, res.get("message", "Post guardado como draft."))

                            @discord.ui.button(label="❌ Rechazar", style=discord.ButtonStyle.red)
                            async def reject(self, itn, btn):
                                await itn.response.send_modal(PostRejectModal(self.pld, self.thread, self.author))

                        await thread.send(embed=embed, view=PostApprovalView(approval_payload, draft_payload, message.author, thread))
                    else:
                        embed = discord.Embed(
                            title="⚖️ Aprobación de Marketing Requerida",
                            description=msg,
                            color=discord.Color.orange()
                        )
                        approval_payload = {
                            **payload,
                            "payload": {**payload["payload"], "is_approved": True},
                        }

                        class MarketingApprovalView(View):
                            def __init__(self, pld, author):
                                super().__init__(timeout=120)
                                self.pld = pld
                                self.author = author
                            @discord.ui.button(label="✅ Aprobar Ejecución", style=discord.ButtonStyle.green)
                            async def approve(self, itn, btn):
                                approvers = _approvers()
                                if approvers and str(itn.user.id) not in approvers:
                                    if str(itn.user.id) != str(self.author.id):
                                        await itn.response.send_message("No estás autorizado como aprobador.", ephemeral=True)
                                        return
                                await itn.response.edit_message(content="⏳ Ejecutando acción aprobada...", view=None)
                                res = await _send_assistant_request(self.pld)
                                await itn.message.edit(content="✅ Acción aprobada. Resultado enviado debajo.")
                                await _send_long(thread, res.get("message", "Acción completada."))
                            @discord.ui.button(label="❌ Denegar", style=discord.ButtonStyle.red)
                            async def deny(self, itn, btn):
                                await itn.response.edit_message(content="🚫 Acción denegada.", embed=None, view=None)

                        await thread.send(embed=embed, view=MarketingApprovalView(approval_payload, message.author))
                    return

                await _send_long(thread, msg)
                await _send_dashboard_chart(thread, result.get("dashboard"))

            except Exception as e:
                await thread.send(f"❌ Error en Marketer Agent: {e}")
            return

        if content.startswith("!writer "):
            raw_query = content.removeprefix("!writer ").strip()
            if raw_query == "--model-status":
                await _send_model_status(message, "writer")
                return

            sub_command = "chat"
            language = "es"
            prompt = raw_query
            
            parts = raw_query.split(" ", 2)
            if len(parts) >= 1:
                cmd = parts[0].lower()
                if cmd in ["blog", "story", "storytelling"]:
                    sub_command = "blog" if cmd == "blog" else "storytelling"
                    if len(parts) >= 2:
                        lang_part = parts[1].lower()
                        if lang_part in ["es", "en", "español", "ingles", "english"]:
                            language = "es" if lang_part in ["es", "español"] else "en"
                            prompt = parts[2] if len(parts) > 2 else f"crea un {sub_command}"
                        else:
                            prompt = " ".join(parts[1:])
                    else:
                        prompt = f"crea un {sub_command}"

            payload = {
                "action_type": "writer",
                "prompt": prompt,
                "source": {"platform": "discord", "channel_id": str(message.channel.id), "user_id": str(message.author.id)},
                "payload": {"sub_command": sub_command, "language": language}
            }
            
            try:
                thread = await _get_or_create_agent_thread(message, "Writer", raw_query)
                payload["source"]["channel_id"] = str(thread.id)
                await thread.send(f"✍️ **Writer Sub-Agent procesando `{sub_command}` en `{language}`...**")
                result = await _send_assistant_request(payload)
                msg = result.get("message", "No hubo respuesta.")
                await _send_long(thread, msg)
            except discord.Forbidden:
                await message.reply("❌ Necesito permiso para 'Crear hilos públicos' para conversar con el Writer Agent.")
            except Exception as e:
                destination = message.channel if _is_thread_channel(message.channel) else message
                if hasattr(destination, "send"):
                    await destination.send(f"❌ Error en Writer Agent: {e}")
                else:
                    await message.reply(f"❌ Error en Writer Agent: {e}")
            return

        if content.startswith("!picture"):
            raw_query = content.removeprefix("!picture").strip()
            raw_query, use_free_model = _extract_free_model_flag(raw_query)

            if raw_query == "--model-status":
                await _send_model_status(message, "picture")
                return
            
            # Gestión de Memoria
            if "memory --clean" in raw_query:
                embed = discord.Embed(
                    title="⚠️ Confirmación de Borrado (Picture)",
                    description="¿Estás seguro de que deseas borrar la **memoria de imágenes**? Esta acción no se puede deshacer.",
                    color=discord.Color.red()
                )
                await message.reply(embed=embed, view=ConfirmationView("picture", message.author))
                return

            if raw_query == "memory":
                try:
                    base_url = _get_env("CONTROL_API_URL", "http://control-api:8000").rstrip("/")
                    async with httpx.AsyncClient(timeout=10) as client_http:
                        resp = await client_http.get(f"{base_url}/intelligence/memory/today?context=picture")
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        memory_list = data.get("memory", [])
                        if not memory_list:
                            await message.reply("📭 No hay memoria de imágenes guardada hoy.")
                        else:
                            report = "### 🎨 Memoria de Picture Agent\n"
                            for item in memory_list:
                                report += f"- {item['summary']}\n"
                            await message.reply(report)
                    else:
                        await message.reply(f"❌ Error al obtener memoria: HTTP {resp.status_code}")
                except Exception as e:
                    await message.reply(f"❌ Error: {e}")
                return

            if not raw_query:
                await message.reply("🎨 Por favor, añade una descripción para generar la imagen. Ejemplo: `!picture un gato astronauta`.")
                return

            try:
                thread = await _get_or_create_agent_thread(message, "Picture", raw_query)
                await thread.send("⏳ **Picture Agent** está procesando tu solicitud con memoria proactiva...")

                # Capturar imágenes adjuntas
                images_b64 = []
                image_metadata = []
                if message.attachments:
                    import base64
                    for att in message.attachments:
                        if any(att.filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"]):
                            img_data = await att.read()
                            images_b64.append(base64.b64encode(img_data).decode("utf-8"))
                            image_metadata.append({
                                "filename": att.filename,
                                "content_type": att.content_type,
                                "size": att.size,
                            })

                payload = {
                    "action_type": "picture",
                    "prompt": raw_query,
                    "source": {"platform": "discord", "channel_id": str(thread.id), "user_id": str(message.author.id)},
                    "images": images_b64,
                    "image_metadata": image_metadata,
                    "payload": {
                        **({
                            "prefer_free_model": True,
                            "image_generation_provider": "together",
                            "image_edit_provider": "local",
                        } if use_free_model else {})
                    }
                }

                result = await _send_assistant_request(payload)
                msg = result.get("message", "No hubo respuesta.")

                if result.get("image_b64"):
                    import io
                    import base64

                    await thread.send(msg)
                    image_bytes = base64.b64decode(result["image_b64"])
                    await thread.send(file=discord.File(io.BytesIO(image_bytes), filename="picture-result.png"))
                    return

                if result.get("image_url"):
                    image_url = result["image_url"]
                    text_msg = msg.removesuffix(f"\n\n{image_url}")
                    await thread.send(text_msg)
                    embed = discord.Embed(title="Resultado Final", color=discord.Color.brand_green())
                    embed.set_image(url=image_url)
                    await thread.send(embed=embed)
                    return
                
                # Extraer URL de la imagen si está presente en el mensaje
                # El formato del mensaje es: Prompt... \n\n URL
                parts = msg.split("\n\n")
                if len(parts) > 1:
                    image_url = parts[-1].strip()
                    text_msg = "\n\n".join(parts[:-1])
                    
                    await thread.send(text_msg)
                    # Enviar la imagen como un embed para que se vea mejor
                    embed = discord.Embed(title="Resultado Final", color=discord.Color.brand_green())
                    embed.set_image(url=image_url)
                    await thread.send(embed=embed)
                else:
                    await thread.send(msg)

            except discord.Forbidden:
                await message.reply("❌ Necesito permiso para 'Crear hilos públicos'.")
            except Exception as e:
                await message.reply(f"❌ Error en Picture Agent: {e}")
            return
        
        if content.startswith("!coder-web"):
            raw_query = content.removeprefix("!coder-web").strip()

            if raw_query == "--model-status":
                await _send_model_status(message, "coder-web")
                return
            
            # Gestión de Memoria
            if "memory --clean" in raw_query:
                embed = discord.Embed(
                    title="⚠️ Confirmación de Borrado (Coder-Web)",
                    description="¿Estás seguro de que deseas borrar la **memoria de desarrollo web**? Esta acción no se puede deshacer.",
                    color=discord.Color.red()
                )
                await message.reply(embed=embed, view=ConfirmationView("coder-web", message.author))
                return

            if raw_query == "memory":
                try:
                    base_url = _get_env("CONTROL_API_URL", "http://control-api:8000").rstrip("/")
                    async with httpx.AsyncClient(timeout=10) as client_http:
                        resp = await client_http.get(f"{base_url}/intelligence/memory/today?context=coder-web")
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        memory_list = data.get("memory", [])
                        if not memory_list:
                            await message.reply("📭 No hay memoria de desarrollo web guardada hoy.")
                        else:
                            report = "### 💻 Memoria de Coder Web Agent\n"
                            for item in memory_list:
                                report += f"- {item['summary']}\n"
                            await message.reply(report)
                    else:
                        await message.reply(f"❌ Error al obtener memoria: HTTP {resp.status_code}")
                except Exception as e:
                    await message.reply(f"❌ Error: {e}")
                return

            if not raw_query:
                await message.reply("💻 Por favor, añade una descripción para el proyecto web. Ejemplo: `!coder-web crea un ecommerce de zapatos con React`.")
                return

            try:
                thread = await _get_or_create_agent_thread(message, "Coder", raw_query)
                await thread.send("⏳ **Coder Web Agent** (Pilot) está analizando la arquitectura y preparando el stack...")

                # Capturar imágenes adjuntas (Mockups/Referencias)
                images_b64 = []
                if message.attachments:
                    import base64
                    for att in message.attachments:
                        if any(att.filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"]):
                            img_data = await att.read()
                            images_b64.append(base64.b64encode(img_data).decode("utf-8"))

                payload = {
                    "action_type": "coder-web",
                    "prompt": raw_query,
                    "source": {"platform": "discord", "channel_id": str(thread.id), "user_id": str(message.author.id)},
                    "images": images_b64,
                    "payload": {}
                }

                result = await _send_assistant_request(payload)
                msg = result.get("message", "No hubo respuesta.")
                
                await _send_long(thread, msg)

            except discord.Forbidden:
                await message.reply("❌ Necesito permiso para 'Crear hilos públicos'.")
            except Exception as e:
                await message.reply(f"❌ Error en Coder Web Agent: {e}")
            return

        action_type = "chat"
        prompt = content
        approval = None
        
        if content.startswith("!research "):
            action_type = "research"
            prompt = content.removeprefix("!research ").strip()
        elif content.startswith("!ask "):
            prompt = content.removeprefix("!ask ").strip()
        elif content.startswith("!approve_trade "):
            approvers = _approvers()
            if approvers and str(message.author.id) not in approvers:
                await message.reply("No estas autorizado para aprobar decisiones de trading.")
                return
            
            action_type = "trade_decision"
            prompt = content.removeprefix("!approve_trade ").strip()
            
            payload = {
                "action_type": action_type,
                "prompt": prompt,
                "source": {"platform": "discord", "channel_id": str(message.channel.id), "user_id": str(message.author.id)},
                "approval": {"status": "approved"}
            }

            embed = discord.Embed(
                title="⚖️ Confirmación de Operación",
                description=f"Instrucción: **{prompt}**\n\n¿Deseas que el Analista y el Crítico procesen esta orden?",
                color=discord.Color.blue()
            )
            embed.set_footer(text="Haz clic en un botón para proceder.")
            
            await message.reply(embed=embed, view=TradeView(payload, message.author))
            return

        payload = {
            "action_type": action_type,
            "prompt": prompt,
            "source": {
                "platform": "discord",
                "channel_id": str(message.channel.id),
                "user_id": str(message.author.id),
            },
            "approval": approval,
        }
        try:
            result = await _send_assistant_request(payload)
            response_text = result.get('message') or "El asistente no devolvio una respuesta."
            
            # Si el mensaje es muy largo, lo dividimos en partes de 1900 caracteres
            if len(response_text) > 1900:
                chunks = [response_text[i:i+1900] for i in range(0, len(response_text), 1900)]
                for i, chunk in enumerate(chunks):
                    prefix = f"**Parte {i+1}/{len(chunks)}**:\n" if len(chunks) > 1 else ""
                    await message.reply(f"{prefix}{chunk}")
            else:
                await message.reply(f"Respuesta: {response_text}")
        except Exception as exc:
            await message.reply(f"No pude contactar al runtime: {exc}")

    # --- Servidor API interno para notificaciones ---
    app_api = FastAPI()

    @app_api.post("/notify/trade")
    async def notify_trade(request: Request):
        data = await request.json()
        channel_id = _get_env("DISCORD_NOTIFICATIONS_CHANNEL_ID")
        print(f"[NOTIFY] Intentando enviar alerta al canal: {channel_id}")
        if not channel_id:
            return {"status": "error", "message": "No hay canal de notificaciones configurado"}
        
        title = data.get("title", "🚀 OPORTUNIDAD DETECTADA")
        message_text = data.get("message", "")
        trade_payload = data.get("payload", {})
        
        channel = client.get_channel(int(channel_id))
        if channel:
            embed = discord.Embed(title=title, description=message_text, color=discord.Color.gold())
            embed.set_footer(text="Inteligencia Social de PC Agent")
            
            # Buscamos un autor valido (el primer aprobador) para que el boton funcione
            approvers = list(_approvers())
            class DummyAuthor:
                def __init__(self, id): self.id = id
            
            author = DummyAuthor(approvers[0]) if approvers else client.user
            
            await channel.send(embed=embed, view=TradeView(trade_payload, author))
            return {"status": "sent"}
        return {"status": "error", "message": "Canal no encontrado"}

    # Ejecutamos el servidor API en segundo plano
    config = uvicorn.Config(app_api, host="0.0.0.0", port=8001, log_level="info")
    server = uvicorn.Server(config)
    asyncio.create_task(server.serve())

    while True:
        try:
            await client.start(token)
        except discord.errors.HTTPException as e:
            if e.status == 429:
                wait_time = 60
                print(f"RATE LIMIT: Discord nos ha bloqueado temporalmente (429). Durmiendo {wait_time}s antes de reintentar...")
                await asyncio.sleep(wait_time)
            else:
                print(f"Error de conexion con Discord: {e}")
                await asyncio.sleep(10)
        except Exception as e:
            print(f"Error inesperado en el bot: {e}")
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
