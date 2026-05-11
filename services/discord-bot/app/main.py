import asyncio
import os
import json
from pathlib import Path
import httpx
from fastapi import FastAPI, Request
import uvicorn


async def _send_assistant_request(payload: dict) -> dict:
    base_url = _get_env("OPEN_CLAW_BASE_URL", "http://assistant-runtime:8100").rstrip("/")
    async with httpx.AsyncClient(timeout=15) as client:
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
        command_list = ("!ask ", "!research ", "!approve_trade ", "!status", "!memory", "!run ", "!claw ", "!help")
        if not content.startswith(command_list):
            return

        # --- COMANDO HELP ---
        if content == "!help":
            embed = discord.Embed(
                title="📖 Guía de Comandos - PC Agent", 
                description="Aquí tienes todo lo que puedo hacer por ti:",
                color=discord.Color.blue()
            )
            embed.add_field(name="🤖 Inteligencia Proactiva", value="`!memory`: Ver qué he aprendido hoy.\n`!run trends`: Forzar búsqueda de tendencias.", inline=False)
            embed.add_field(name="🧠 Asistente Open Claw", value="`!claw <pregunta>`: Abre un hilo de análisis profundo usando mi memoria diaria.", inline=False)
            embed.add_field(name="📊 Trading & Research", value="`!ask <duda>`: Pregunta rápida.\n`!research <tema>`: Investigación profunda.\n`!status`: Estado del sistema.", inline=False)
            embed.add_field(name="⚖️ Decisiones", value="`!approve_trade <id>`: Aprobar una operación sugerida.", inline=False)
            embed.set_footer(text="PC Agent v2.0 - Autonomía y Análisis")
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

        if content == "!memory":
            try:
                base_url = _get_env("CONTROL_API_URL", "http://control-api:8000").rstrip("/")
                async with httpx.AsyncClient(timeout=10) as client_http:
                    resp = await client_http.get(f"{base_url}/intelligence/memory/today")
                
                if resp.status_code == 200:
                    data = resp.json()
                    print(f"[DEBUG MEMORY] Datos recibidos del API: {data}")
                    memory_list = data.get("memory", [])
                    if not memory_list:
                        await message.reply("🧠 **Memoria vacía**: No he recolectado tendencias hoy todavía.")
                        return
                    
                    report = "🧠 **Memoria Reciente del Agente**\n"
                    report += "-----------------------------------\n"
                    for item in memory_list:
                        category = item.get("category", "N/A").upper()
                        date = item.get("date_key", "N/A")
                        body = item.get("summary", "")
                        # Truncamos si es muy largo para el reporte
                        if len(body) > 300: body = body[:300] + "..."
                        report += f"🔹 **{category}** ({date}):\n{body}\n\n"
                    
                    # Usamos nuestra función de mensajes largos por si hay mucha memoria
                    if len(report) > 1900:
                        chunks = [report[i:i+1900] for i in range(0, len(report), 1900)]
                        for chunk in chunks: await message.reply(chunk)
                    else:
                        await message.reply(report)
                else:
                    await message.reply(f"Error al obtener memoria: HTTP {resp.status_code}")
            except Exception as exc:
                await message.reply(f"No pude conectar con el Control API: {exc}")
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
