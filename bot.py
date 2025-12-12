import discord
import re
import asyncio
import json
from datetime import datetime
import os

TOKEN = os.getenv("TOKEN")

CANAIS = {
    "skkypper": 1444038643239878786,
    "Cain": 1444054228501921915,
    "Ryujin": 1444054190258131096
}

CANAL_RANKING = 1449048189486235728
CANAL_MENSAL = 1444038643239878781

ARQUIVO_MENSAGEM = "mensagem_ranking.txt"
ARQUIVO_XP = "xp.json"

XP_POR_CAPITULO = 10

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


def carregar_xp():
    try:
        with open(ARQUIVO_XP, "r") as f:
            return json.load(f)
    except:
        return {u: {"xp": 0, "nivel": 0, "medalha": "Nenhuma"} for u in CANAIS.keys()}


def salvar_xp(dados):
    with open(ARQUIVO_XP, "w") as f:
        json.dump(dados, f, indent=4)


def medalha_por_nivel(nivel):
    if nivel >= 10:
        return "🥇 Ouro"
    elif nivel >= 5:
        return "🥈 Prata"
    elif nivel >= 1:
        return "🥉 Bronze"
    return "Nenhuma"


async def contar_capitulos_mes():
    resultados = {}
    agora = datetime.now()

    for usuario, canal_id in CANAIS.items():
        canal = client.get_channel(canal_id)
        total = 0

        if canal is None:
            resultados[usuario] = 0
            continue

        async for msg in canal.history(limit=None):
            data = msg.created_at
            if data.year == agora.year and data.month == agora.month:
                texto = msg.content.lower()
                blocos = re.findall(r'\bcap\s*([\d,\s]+)', texto)
                for bloco in blocos:
                    numeros = bloco.split(',')
                    for n in numeros:
                        if n.strip().isdigit():
                            total += 1

        resultados[usuario] = total

    return resultados


async def atualizar_ranking():
    resultados = await contar_capitulos_mes()
    xp_data = carregar_xp()

    for usuario, caps in resultados.items():
        ganho = caps * XP_POR_CAPITULO
        xp_data[usuario]["xp"] = ganho
        xp_data[usuario]["nivel"] = xp_data[usuario]["xp"] // 100
        xp_data[usuario]["medalha"] = medalha_por_nivel(xp_data[usuario]["nivel"])

    salvar_xp(xp_data)

    ranking = sorted(resultados.items(), key=lambda x: x[1], reverse=True)
    total_geral = sum(resultados.values())
    podio = ["🥇", "🥈", "🥉"]

    texto = "**🏆 Ranking Geral do Mês (Atualizado automaticamente) 🏆**\n\n"
    for i, (usuario, total) in enumerate(ranking):
        emoji = podio[i] if i < 3 else "🔹"
        xp = xp_data[usuario]["xp"]
        nivel = xp_data[usuario]["nivel"]
        medalha = xp_data[usuario]["medalha"]
        texto += (
            f"{emoji} **{usuario}** — {total} capítulos\n"
            f"   ➤ XP: {xp} | Nível: {nivel} | Medalha: {medalha}\n\n"
        )

    texto += f"\n📘 **Total do mês: {total_geral} capítulos!**\n"

    try:
        with open(ARQUIVO_MENSAGEM, "r") as f:
            mensagem_id = int(f.read().strip())
    except:
        mensagem_id = None

    canal = client.get_channel(CANAL_RANKING)
    if mensagem_id is None:
        msg = await canal.send(texto)
        with open(ARQUIVO_MENSAGEM, "w") as f:
            f.write(str(msg.id))
    else:
        try:
            msg = await canal.fetch_message(mensagem_id)
            await msg.edit(content=texto)
        except:
            msg = await canal.send(texto)
            with open(ARQUIVO_MENSAGEM, "w") as f:
                f.write(str(msg.id))


async def enviar_ranking_mensal():
    resultados = await contar_capitulos_mes()
    xp_data = carregar_xp()

    ranking = sorted(resultados.items(), key=lambda x: x[1], reverse=True)
    total_mes = sum(resultados.values())
    podio = ["🥇", "🥈", "🥉"]

    texto = "@everyone\n**📅 Ranking do Mês que se Passou! 📅**\n\n"
    for i, (usuario, total) in enumerate(ranking):
        emoji = podio[i] if i < 3 else "🔹"
        nivel = xp_data[usuario]["nivel"]
        medalha = xp_data[usuario]["medalha"]
        texto += (
            f"{emoji} **{usuario}** — {total} capítulos\n"
            f"   ➤ Nível: {nivel} | Medalha: {medalha}\n\n"
        )

    texto += f"\n📘 **Total do mês: {total_mes} capítulos!**\n"
    campeao, pontos = ranking[0]
    texto += f"\n🎉 **Parabéns {campeao}!** Você foi o maior uploader do mês! 🎉\n"
    texto += "🏅 Receba sua gratificação simbólica pelo excelente trabalho!\n"

    canal = client.get_channel(CANAL_MENSAL)
    await canal.send(texto)


async def tarefa_diaria():
    await client.wait_until_ready()
    while not client.is_closed():
        agora = datetime.now()
        if agora.day == 1 and agora.hour == 0 and agora.minute == 0:
            await enviar_ranking_mensal()
        await asyncio.sleep(60)


@client.event
async def on_ready():
    print(f"Bot logado como {client.user}")
    client.loop.create_task(tarefa_diaria())
    await atualizar_ranking()


@client.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.id in CANAIS.values():
        await atualizar_ranking()


@client.event
async def on_message_delete(message):
    if message.channel.id in CANAIS.values():
        await atualizar_ranking()


@client.event
async def on_message_edit(before, after):
    if after.channel.id in CANAIS.values():
        await atualizar_ranking()


client.run(TOKEN)
