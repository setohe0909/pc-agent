import asyncio
import os
import json
from pathlib import Path
import httpx
from fastapi import FastAPI, Request
import uvicorn


async def _send_assistant_request(payload: dict) -> dict:
    base_url = _get_env("OPEN_CLAW_BASE_URL", "http://assistant-runtime:8100").rstrip("/")
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(f"{base_url}/assistant/request", json=payload)
    response.raise_for_status()
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
                "payload": {"sub_command": sub_cmd}
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

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready() -> None:
        print(f"Discord conectado como {client.user}")

    @client.event
    async def on_message(message) -> None:
        if message.author == client.user or not _is_requests_channel(message.channel.id):
            return

        content = message.content.strip()
        command_list = ("!ask ", "!research ", "!approve_trade ", "!status", "!memory", "!run ", "!claw ", "!marketer ", "!marketer-status", "!writer ", "!help")
        if not content.startswith(command_list):
            return

        # --- COMANDO HELP ---
        if content == "!help":
            embed = discord.Embed(
                title="🤖 PC Agent v0.3.0 - Guía de Operaciones", 
                description="Sistema de agentes autónomos con flujos de estados (LangGraph) y memoria proactiva.",
                color=discord.Color.blue()
            )
            embed.add_field(name="🧠 Inteligencia & Memoria", value="`!memory`: Ver tendencias del día.\n`!memory --clean`: Borrar memoria general.\n`!run consolidation`: Forzar consolidación de memoria diaria.", inline=False)
            embed.add_field(name="📣 Marketing (LangGraph)", value="`!marketer`: Centro de Control interactivo (Botones).\n`!marketer <petición>`: El agente decidirá qué herramienta usar (Native Tool Calling).\n`!marketer memory`: Ver aprendizajes consolidados.", inline=False)
            embed.add_field(name="✍️ Redactor (Writer)", value="`!writer blog <tema>`: Crear blog y guardar en Obsidian.\n`!writer <mensaje>`: Chat con el redactor creativo.", inline=False)
            embed.add_field(name="📊 Research & Trading", value="`!research <tema>`: Investigación profunda.\n`!status`: Estado de salud de los microservicios.\n`!approve_trade <id>`: Evaluar propuesta de inversión.", inline=False)
            embed.set_footer(text="Usa los botones en los mensajes para una experiencia mejorada.")
            await message.reply(embed=embed)
            return

        if content.startswith("!claw"):
            query = content.removeprefix("!claw").strip()
            if not query:
                await message.reply("⚠️ Por favor, añade una pregunta después de `!claw`.")
                return
            
            # 1. Creamos un hilo para la consulta
            try:
                thread = await message.create_thread(name=f"Claw: {query[:30]}...")
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
                
                # 3. Respondemos en el hilo (con soporte para mensajes largos)
                if len(answer) > 1900:
                    chunks = [answer[i:i+1900] for i in range(0, len(answer), 1900)]
                    await thread.send("🤖 **Respuesta de Open Claw (Parte 1):**")
                    for i, chunk in enumerate(chunks):
                        await thread.send(f"{chunk}")
                else:
                    await thread.send(f"🤖 **Respuesta de Open Claw:**\n\n{answer}")
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
            payload = {
                "action_type": "marketing",
                "prompt": "dame tu estado",
                "source": {"platform": "discord", "channel_id": str(message.channel.id), "user_id": str(message.author.id)},
                "payload": {"sub_command": "status"}
            }
            print(f"[DEBUG] Enviando solicitud !marketer-status al assistant-runtime")
            try:
                result = await _send_assistant_request(payload)
                await message.reply(result.get("message", "No pude obtener el estado del marketer."))
            except Exception as e:
                await message.reply(f"❌ Error al contactar al marketer: {e}")
            return

        if content.startswith("!marketer "):
            raw_query = content.removeprefix("!marketer ").strip()
            
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
            
            if not raw_query or raw_query.strip() == "":
                embed = discord.Embed(
                    title="📣 Centro de Control de Marketing",
                    description="Selecciona una acción rápida o escribe un comando después de `!marketer`.",
                    color=discord.Color.purple()
                )
                await message.reply(embed=embed, view=MarketingView(message.author))
                return

            if raw_query.startswith("respond"):
                sub_command = "respond"
                prompt = "responde comentarios"
            elif raw_query.startswith("plan "):
                sub_command = "plan"
                prompt = raw_query.removeprefix("plan ").strip()
            elif raw_query.startswith("research "):
                sub_command = "research"
                prompt = raw_query.removeprefix("research ").strip()
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

            payload = {
                "action_type": "marketing",
                "prompt": prompt,
                "source": {"platform": "discord", "channel_id": str(message.channel.id), "user_id": str(message.author.id)},
                "payload": {"sub_command": sub_command}
            }
            
            await message.reply(f"📣 **Marketer Agent procesando `{sub_command}`...**")
            try:
                result = await _send_assistant_request(payload)
                msg = result.get("message", "No hubo respuesta.")
                
                if result.get("status") == "requires_approval":
                    embed = discord.Embed(
                        title="⚖️ Aprobación de Marketing Requerida",
                        description=msg,
                        color=discord.Color.orange()
                    )
                    approval_payload = payload.copy()
                    approval_payload["payload"]["is_approved"] = True
                    
                    class MarketingApprovalView(View):
                        def __init__(self, pld, author):
                            super().__init__(timeout=120)
                            self.pld = pld
                            self.author = author
                        @discord.ui.button(label="✅ Aprobar Ejecución", style=discord.ButtonStyle.green)
                        async def approve(self, itn, btn):
                            if str(itn.user.id) != str(self.author.id): return
                            await itn.response.edit_message(content="⏳ Ejecutando acción aprobada...", view=None)
                            res = await _send_assistant_request(self.pld)
                            await itn.message.edit(content=res.get("message", "Acción completada."))
                        @discord.ui.button(label="❌ Denegar", style=discord.ButtonStyle.red)
                        async def deny(self, itn, btn):
                            await itn.response.edit_message(content="🚫 Acción denegada.", embed=None, view=None)

                    await message.reply(embed=embed, view=MarketingApprovalView(approval_payload, message.author))
                    return

                if len(msg) > 1900:
                    chunks = [msg[i:i+1900] for i in range(0, len(msg), 1900)]
                    for chunk in chunks:
                        await message.reply(chunk)
                else:
                    await message.reply(msg)

            except Exception as e:
                await message.reply(f"❌ Error en Marketer Agent: {e}")
            return

        if content.startswith("!writer "):
            raw_query = content.removeprefix("!writer ").strip()
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
            
            await message.reply(f"✍️ **Writer Sub-Agent procesando `{sub_command}` en `{language}`...**")
            try:
                result = await _send_assistant_request(payload)
                msg = result.get("message", "No hubo respuesta.")
                if len(msg) > 1900:
                    chunks = [msg[i:i+1900] for i in range(0, len(msg), 1900)]
                    for chunk in chunks:
                        await message.reply(chunk)
                else:
                    await message.reply(msg)
            except Exception as e:
                await message.reply(f"❌ Error en Writer Agent: {e}")
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
