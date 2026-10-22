import time

import discord
from google.genai import types

from config import COOLDOWN_SEGUNDOS, GEMINI_MODEL, LIMITE_DISCORD, MAX_TURNOS
from llm import responder

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

conversas: dict[int, dict] = {}  
ultimo_uso: dict[int, float] = {} 


@bot.event
async def on_ready():
    print(f"Online como {bot.user} | modelo: {GEMINI_MODEL}")


@bot.event
async def on_message(msg: discord.Message):
    if msg.author.bot or bot.user not in msg.mentions:
        return

    agora = time.monotonic()
    if agora - ultimo_uso.get(msg.author.id, 0) < COOLDOWN_SEGUNDOS:
        await msg.reply("Calma! Espere alguns segundos antes de perguntar de novo.")
        return
    ultimo_uso[msg.author.id] = agora

    pergunta = (
        msg.content.replace(f"<@{bot.user.id}>", "")
        .replace(f"<@!{bot.user.id}>", "")
        .strip()
    )
    if not pergunta:
        await msg.reply("Oi! Me pergunte algo, tipo: que horas são em Tóquio?")
        return

    conversa = conversas.get(msg.channel.id)
    if conversa is None or conversa["turnos"] >= MAX_TURNOS:
        conversa = {"historico": [], "turnos": 0}
        conversas[msg.channel.id] = conversa
    conversa["turnos"] += 1
    conversa["historico"].append(types.Content(role="user", parts=[types.Part(text=pergunta)]))

    try:
        async with msg.channel.typing():
            texto, usadas = await responder(conversa["historico"])
    except Exception as erro:
        print(f"Erro no Gemini: {erro!r}")
        conversas.pop(msg.channel.id, None)  # histórico pode ter ficado pela metade
        await msg.reply("Deu erro ao falar com a IA. Tente de novo em 1 minuto.")
        return

    rodape = "\n-# 🔧 " + ", ".join(dict.fromkeys(usadas)) if usadas else ""

    await msg.reply(texto[: LIMITE_DISCORD - len(rodape)] + rodape)
