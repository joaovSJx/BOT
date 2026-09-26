import discord
from discord.ext import commands
import json
import os
from datetime import datetime

# ========================= CONFIGURAÇÕES =========================
# Você pode definir essas variáveis de ambiente OU editar direto aqui.
TOKEN = os.getenv("DISCORD_TOKEN", "SEU_TOKEN_AQUI")

# ID do canal onde o comando ,iniciar deve ser usado (onde aparecem os botões)
CANAL_PONTO_ID = int(os.getenv("CANAL_PONTO_ID", "0"))

# ID do canal onde o relatório de horas será enviado/atualizado
CANAL_RELATORIO_ID = int(os.getenv("CANAL_RELATORIO_ID", "0"))

ARQUIVO_DADOS = "pontos.json"

# ========================= PERSISTÊNCIA =========================
def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"ativos": {}, "registros": []}


def salvar_dados(dados):
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


dados = carregar_dados()

# ========================= BOT =========================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=",", intents=intents)


def formatar_duracao(segundos: float) -> str:
    segundos = int(segundos)
    horas = segundos // 3600
    minutos = (segundos % 3600) // 60
    segs = segundos % 60
    return f"{horas}h {minutos}m {segs}s"


async def atualizar_relatorio(guild: discord.Guild):
    """Envia/atualiza o resumo de horas no canal de relatório."""
    if not CANAL_RELATORIO_ID:
        return
    canal = guild.get_channel(CANAL_RELATORIO_ID)
    if canal is None:
        return

    # Agrupa os registros finalizados por usuário
    resumo = {}
    for reg in dados["registros"]:
        uid = reg["user_id"]
        item = resumo.setdefault(uid, {"nome": reg["nome"], "total": 0, "qtd": 0, "ultimo": reg["fim"]})
        item["total"] += reg["duracao_segundos"]
        item["qtd"] += 1
        if reg["fim"] > item["ultimo"]:
            item["ultimo"] = reg["fim"]

    embed = discord.Embed(
        title="📊 Relatório de Pontos",
        color=discord.Color.blurple(),
        timestamp=datetime.utcnow(),
    )

    if not resumo:
        embed.description = "Nenhum ponto finalizado ainda."
    else:
        for _, info in sorted(resumo.items(), key=lambda x: -x[1]["total"]):
            ultimo_fmt = info["ultimo"][:16].replace("T", " ")
            embed.add_field(
                name=info["nome"],
                value=(
                    f"⏱️ Total: **{formatar_duracao(info['total'])}**\n"
                    f"📌 Pontos finalizados: {info['qtd']}\n"
                    f"🕓 Último: {ultimo_fmt} UTC"
                ),
                inline=False,
            )

    # Apaga o último relatório enviado pelo bot para não acumular mensagens
    async for msg in canal.history(limit=20):
        if msg.author == bot.user and msg.embeds:
            await msg.delete()
            break

    await canal.send(embed=embed)


# ========================= BOTÕES =========================
class PontoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # view persistente (funciona após reiniciar o bot)

    @discord.ui.button(label="Bater Ponto", style=discord.ButtonStyle.success, emoji="🟢", custom_id="bater_ponto")
    async def bater_ponto(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = str(interaction.user.id)

        if uid in dados["ativos"]:
            await interaction.response.send_message(
                "⚠️ Você já bateu o ponto e ainda não finalizou.", ephemeral=True
            )
            return

        dados["ativos"][uid] = {
            "nome": interaction.user.display_name,
            "inicio": datetime.utcnow().isoformat(),
        }
        salvar_dados(dados)

        await interaction.response.send_message(
            f"✅ Ponto batido às **{datetime.utcnow().strftime('%H:%M:%S')} UTC**. Bom trabalho!",
            ephemeral=True,
        )

    @discord.ui.button(label="Finalizar", style=discord.ButtonStyle.danger, emoji="🔴", custom_id="finalizar_ponto")
    async def finalizar_ponto(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = str(interaction.user.id)

        if uid not in dados["ativos"]:
            await interaction.response.send_message(
                "⚠️ Você ainda não bateu o ponto.", ephemeral=True
            )
            return

        ativo = dados["ativos"].pop(uid)
        inicio = datetime.fromisoformat(ativo["inicio"])
        fim = datetime.utcnow()
        duracao = (fim - inicio).total_seconds()

        dados["registros"].append({
            "user_id": uid,
            "nome": ativo["nome"],
            "inicio": ativo["inicio"],
            "fim": fim.isoformat(),
            "duracao_segundos": duracao,
        })
        salvar_dados(dados)

        await interaction.response.send_message(
            f"🔴 Ponto finalizado! Tempo total: **{formatar_duracao(duracao)}**",
            ephemeral=True,
        )

        if interaction.guild:
            await atualizar_relatorio(interaction.guild)


# ========================= COMANDO =========================
@bot.command(name="iniciar")
async def iniciar(ctx: commands.Context):
    if CANAL_PONTO_ID and ctx.channel.id != CANAL_PONTO_ID:
        await ctx.send(f"❌ Use este comando no canal <#{CANAL_PONTO_ID}>.")
        return

    embed = discord.Embed(
        title="🕒 Controle de Ponto",
        description="Clique em **Bater Ponto** para iniciar e em **Finalizar** para encerrar seu ponto.",
        color=discord.Color.green(),
    )
    await ctx.send(embed=embed, view=PontoView())


@bot.event
async def on_ready():
    bot.add_view(PontoView())  # registra a view para os botões funcionarem após reiniciar
    print(f"✅ Bot conectado como {bot.user}")


bot.run(TOKEN)
