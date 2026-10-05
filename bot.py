import discord
from discord.ext import commands
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

from tickets import OpenView

# ========================= CONFIGURAÇÕES =========================
# Você pode definir essas variáveis de ambiente OU editar direto aqui.
TOKEN = os.getenv("DISCORD_TOKEN", "SEU_TOKEN_AQUI")

# ID do canal onde o comando ,iniciar deve ser usado (onde aparecem os botões)
CANAL_PONTO_ID = int(os.getenv("CANAL_PONTO_ID", "0"))

# ID do canal onde o relatório de horas será enviado/atualizado
CANAL_RELATORIO_ID = int(os.getenv("CANAL_RELATORIO_ID", "0"))

# ID do canal onde o painel fixo de desmute será exibido
CANAL_DESMUTAR_ID = int(os.getenv("CANAL_DESMUTAR_ID", "1553921363440439436"))

# ID do canal onde o comando de declaração será usado
CANAL_DECLARAR_ID = int(os.getenv("CANAL_DECLARAR_ID", "1554252543134142474"))

# Usuários autorizados a declarar filhos e usar comandos restritos
ID_USUARIO_DECLARANTE = int(os.getenv("ID_USUARIO_DECLARANTE", "1187527979388108840"))
ID_USUARIOS_AUTORIZADOS = {ID_USUARIO_DECLARANTE, 420436337011982336}

# Cargo que será concedido automaticamente ao usuário declarado
ID_CARGO_SYSTEM = int(os.getenv("ID_CARGO_SYSTEM", "1554207261755183196"))

# ID do canal onde o embed fixo de avisos será exibido
CANAL_AVISOS_ID = int(os.getenv("CANAL_AVISOS_ID", "1548179013992714270"))

# ID do canal onde o embed fixo de regras será exibido
CANAL_REGRAS_ID = int(os.getenv("CANAL_REGRAS_ID", "1548100800796950678"))

# ID do canal de denúncias
CANAL_DENUNCIAS_ID = int(os.getenv("CANAL_DENUNCIAS_ID", "1548204770152423484"))

# ID do canal de suporte
CANAL_SUPORTE_ID = int(os.getenv("CANAL_SUPORTE_ID", "1548207347753689098"))

# Configuração do sistema de denúncias / tickets
STAFF_ROLE_ID = int(os.getenv("STAFF_ROLE_ID", "0"))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "1552722101641814027")) if os.getenv("LOG_CHANNEL_ID") else 1552722101641814027
CATEGORY_ID = int(os.getenv("TICKET_CATEGORY_ID", "0"))

ARQUIVO_DADOS = "pontos.json"
ARQUIVO_GIF_DESMUTE = os.path.join(os.path.dirname(__file__), "assets", "THE_BOX.gif")
FUSO_BRASILIA = timezone(timedelta(hours=-3), name="BRT")

# ========================= PERSISTÊNCIA =========================
def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
            dados = json.load(f)
    else:
        dados = {"ativos": {}, "registros": [], "casais": []}

    dados.setdefault("ativos", {})
    dados.setdefault("registros", [])
    dados.setdefault("casais", [])
    return dados


def salvar_dados(dados):
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def normalizar_ids(membros):
    return sorted({str(membro_id) for membro_id in membros if membro_id is not None})


def encontrar_casal_por_membro(membro_id):
    membro_id = str(membro_id)
    for casal in dados.get("casais", []):
        if membro_id in normalizar_ids(casal.get("membros", [])):
            return casal
    return None


def casal_ja_registrado(membros):
    ids = set(normalizar_ids(membros))
    if not ids:
        return False

    for casal in dados.get("casais", []):
        membros_existentes = set(normalizar_ids(casal.get("membros", [])))
        if ids & membros_existentes:
            return True
    return False


def registrar_casal(membros, autor_id):
    ids = normalizar_ids(membros)
    if not ids:
        return False, "Nenhum membro foi informado para a declaração."

    if casal_ja_registrado(ids):
        return False, "Um ou mais membros deste casal já foram declarados antes."

    dados.setdefault("casais", []).append(
        {
            "membros": ids,
            "autor_id": str(autor_id),
            "data": datetime.now(timezone.utc).isoformat(),
        }
    )
    salvar_dados(dados)
    return True, None


def remover_casal_por_membros(membros):
    ids = {str(membro_id) for membro_id in membros if membro_id is not None}
    if not ids:
        return 0

    casais_restantes = []
    removidos = 0
    for casal in dados.get("casais", []):
        membros_casal = {str(item) for item in casal.get("membros", [])}
        if ids & membros_casal:
            removidos += 1
        else:
            casais_restantes.append(casal)

    dados["casais"] = casais_restantes
    salvar_dados(dados)
    return removidos


dados = carregar_dados()

# ========================= BOT =========================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Aceita tanto .comando quanto ,comando para manter compatibilidade com a configuração anterior e com o README do projeto.
bot = commands.Bot(command_prefix=[".", ","], intents=intents, help_command=None)


def formatar_duracao(segundos: float) -> str:
    segundos = int(segundos)
    horas = segundos // 3600
    minutos = (segundos % 3600) // 60
    segs = segundos % 60
    return f"{horas}h {minutos}m {segs}s"


def formatar_horario_br(valor: str) -> str:
    horario = datetime.fromisoformat(valor)
    if horario.tzinfo is None:
        horario = horario.replace(tzinfo=timezone.utc)
    return horario.astimezone(FUSO_BRASILIA).strftime("%d/%m/%Y %H:%M:%S")


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
        timestamp=datetime.now(timezone.utc),
    )

    if not resumo:
        embed.description = "Nenhum ponto finalizado ainda."
    else:
        for _, info in sorted(resumo.items(), key=lambda x: -x[1]["total"]):
            ultimo_fmt = formatar_horario_br(info["ultimo"])
            embed.add_field(
                name=info["nome"],
                value=(
                    f"⏱️ Total: **{formatar_duracao(info['total'])}**\n"
                    f"📌 Pontos finalizados: {info['qtd']}\n"
                    f"🕓 Último: {ultimo_fmt} (Brasília)"
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
            "inicio": datetime.now(timezone.utc).isoformat(),
        }
        salvar_dados(dados)

        await interaction.response.send_message(
            f"✅ Ponto batido às **{datetime.now(FUSO_BRASILIA).strftime('%H:%M:%S')}** (Brasília). Bom trabalho!",
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
        if inicio.tzinfo is None:
            inicio = inicio.replace(tzinfo=timezone.utc)
        fim = datetime.now(timezone.utc)
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


class DesmutarView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Desmutar",
        style=discord.ButtonStyle.secondary,
        custom_id="desmutar:confirmar",
    )
    async def confirmar_desmute(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        membro = interaction.user
        if interaction.guild is None or not isinstance(membro, discord.Member):
            await interaction.response.send_message(
                "❌ Este botão só pode ser usado dentro de um servidor.",
                ephemeral=True,
            )
            return

        motivo = f"Desmute realizado por {interaction.user}"
        acoes_concluidas = []
        falhas = []

        try:
            await membro.timeout(
                None, reason=motivo
            )
            acoes_concluidas.append("timeout")
        except discord.Forbidden:
            falhas.append("timeout (o bot precisa de **Moderar Membros**)")
        except discord.HTTPException:
            falhas.append("timeout (erro retornado pelo Discord)")

        if membro.voice is None:
            acoes_concluidas.append("não conectado a um canal de voz")
        else:
            try:
                await membro.edit(mute=False, reason=motivo)
                acoes_concluidas.append("mute de voz removido")
            except discord.Forbidden:
                falhas.append(
                    "mute de voz (o bot precisa de **Silenciar Membros** e de posição superior na hierarquia)"
                )
            except discord.HTTPException:
                falhas.append("mute de voz (erro retornado pelo Discord)")

            try:
                await membro.edit(deafen=False, reason=motivo)
                acoes_concluidas.append("ensurdecimento removido")
            except discord.Forbidden:
                falhas.append(
                    "ensurdecimento (o bot precisa de **Ensurdecer Membros** e de posição superior na hierarquia)"
                )
            except discord.HTTPException:
                falhas.append("ensurdecimento (erro retornado pelo Discord)")

        if falhas:
            resposta = f"⚠️ Auto-desmute parcial de {membro.mention}."
            if acoes_concluidas:
                resposta += f" Concluído: {', '.join(acoes_concluidas)}."
            resposta += f" Não foi possível: {'; '.join(falhas)}."
        else:
            resposta = f"✅ Auto-desmute concluído para {membro.mention}: timeout removido; {', '.join(acoes_concluidas)}."

        await interaction.response.send_message(resposta, ephemeral=True)


class RegrasView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(
                label="Denuncie aqui",
                style=discord.ButtonStyle.link,
                url=f"https://discord.com/channels/{guild_id}/{CANAL_DENUNCIAS_ID}",
            )
        )
        self.add_item(
            discord.ui.Button(
                label="Suporte",
                style=discord.ButtonStyle.link,
                url=f"https://discord.com/channels/{guild_id}/{CANAL_SUPORTE_ID}",
            )
        )


async def garantir_painel_desmutar():
    if not CANAL_DESMUTAR_ID:
        return

    try:
        canal = bot.get_channel(CANAL_DESMUTAR_ID)
        if canal is None:
            canal = await bot.fetch_channel(CANAL_DESMUTAR_ID)
    except discord.HTTPException as erro:
        print(f"❌ Não foi possível acessar o canal de desmute: {erro}")
        return

    if not isinstance(canal, discord.TextChannel):
        print("❌ CANAL_DESMUTAR_ID precisa ser o ID de um canal de texto.")
        return

    embed = discord.Embed(
        title="Liberar comunicação",
        description=(
            "Utilize este canal para realizar a remoção do seu mute, seja ele normal ou ensurdecimento.\n\n"
            "Clique no botão **Desmutar** abaixo para que a remoção seja realizada automaticamente."
        ),
        color=discord.Color.from_rgb(128, 128, 128),
    )
    gif_disponivel = os.path.isfile(ARQUIVO_GIF_DESMUTE)
    if gif_disponivel:
        embed.set_image(url="attachment://THE_BOX.gif")

    try:
        async for mensagem in canal.history(limit=100):
            if (
                mensagem.author == bot.user
                and mensagem.embeds
                and mensagem.embeds[0].title == embed.title
            ):
                if gif_disponivel:
                    await mensagem.edit(
                        embed=embed,
                        view=DesmutarView(),
                        attachments=[discord.File(ARQUIVO_GIF_DESMUTE, filename="THE_BOX.gif")],
                    )
                else:
                    await mensagem.edit(embed=embed, view=DesmutarView())
                return

        if gif_disponivel:
            await canal.send(
                embed=embed,
                view=DesmutarView(),
                file=discord.File(ARQUIVO_GIF_DESMUTE, filename="THE_BOX.gif"),
            )
        else:
            await canal.send(embed=embed, view=DesmutarView())
    except discord.Forbidden:
        print(
            "❌ Sem permissão para ler o histórico ou enviar mensagens no canal de desmute."
        )
    except discord.HTTPException as erro:
        print(f"❌ Não foi possível criar ou atualizar o painel de desmute: {erro}")


async def garantir_embed_avisos():
    if not CANAL_AVISOS_ID:
        return

    try:
        canal = bot.get_channel(CANAL_AVISOS_ID)
        if canal is None:
            canal = await bot.fetch_channel(CANAL_AVISOS_ID)
    except discord.HTTPException as erro:
        print(f"❌ Não foi possível acessar o canal de avisos: {erro}")
        return

    if not isinstance(canal, discord.TextChannel):
        print("❌ CANAL_AVISOS_ID precisa ser o ID de um canal de texto.")
        return

    embed = discord.Embed(
        title="Avisos",
        description=(
            "Mantenha-se por dentro de tudo que acontece no servidor.\n\n"
            "Aqui serão compartilhados avisos importantes, novidades, atualizações, eventos e comunicados da administração. "
            "Acompanhe este canal para não perder nenhuma informação relevante."
        ),
        color=discord.Color.from_rgb(128, 128, 128),
    )
    arquivo_imagem = os.path.join(os.path.dirname(__file__), "assets", "Avisos.png")
    embed.set_image(url="attachment://Avisos.png")
    menções_permitidas = discord.AllowedMentions(
        everyone=True, users=False, roles=False
    )

    try:
        mensagens = [mensagem async for mensagem in canal.history(limit=100)]
        banner = next(
            (
                mensagem
                for mensagem in mensagens
                if mensagem.author == bot.user
                and not mensagem.embeds
                and any(anexo.filename.lower() == "avisos.png" for anexo in mensagem.attachments)
            ),
            None,
        )
        painel = next(
            (
                mensagem
                for mensagem in mensagens
                if mensagem.author == bot.user
                and mensagem.embeds
                and mensagem.embeds[0].title == embed.title
            ),
            None,
        )

        if painel is None:
            await canal.send(
                content="@everyone",
                embed=embed,
                file=discord.File(arquivo_imagem, filename="Avisos.png"),
                allowed_mentions=menções_permitidas,
            )
        else:
            await painel.edit(
                content="@everyone",
                embed=embed,
                attachments=[discord.File(arquivo_imagem, filename="Avisos.png")],
                allowed_mentions=menções_permitidas,
            )

        if banner is not None:
            await banner.delete()
    except discord.Forbidden:
        print("❌ Sem permissão para enviar mensagens no canal de avisos.")
    except discord.HTTPException as erro:
        print(f"❌ Não foi possível criar ou atualizar o embed de avisos: {erro}")


async def garantir_painel_denuncias():
    if not CANAL_DENUNCIAS_ID:
        return

    try:
        canal = bot.get_channel(CANAL_DENUNCIAS_ID)
        if canal is None:
            canal = await bot.fetch_channel(CANAL_DENUNCIAS_ID)
    except discord.HTTPException as erro:
        print(f"❌ Não foi possível acessar o canal de denúncias: {erro}")
        return

    if not isinstance(canal, discord.TextChannel):
        print("❌ CANAL_DENUNCIAS_ID precisa ser o ID de um canal de texto.")
        return

    embed = discord.Embed(
        title="Central de denúncias.",
        description=(
            "Presenciou uma situação que viola as regras do servidor?\n\n"
            "Utilize este canal para realizar uma denúncia à nossa equipe de moderação.\n\n"
            "𝟏. Ao abrir uma denúncia, informe o máximo de detalhes possível e, se tiver, envie provas como prints ou vídeos.\n\n"
            "𝟐. Denúncias falsas ou feitas de má-fé poderão resultar em punição.\n\n"
            "𝟑. Sua denúncia será tratada de forma reservada pela equipe responsável."
        ),
        color=discord.Color.from_rgb(43, 45, 49),
    )

    try:
        async for mensagem in canal.history(limit=100):
            if (
                mensagem.author == bot.user
                and mensagem.embeds
                and mensagem.embeds[0].title == embed.title
            ):
                await mensagem.edit(embed=embed, view=OpenView())
                return

        await canal.send(embed=embed, view=OpenView())
    except discord.Forbidden:
        print("❌ Sem permissão para enviar mensagens no canal de denúncias.")
    except discord.HTTPException as erro:
        print(f"❌ Não foi possível criar ou atualizar o painel de denúncias: {erro}")


async def garantir_embed_regras():
    if not CANAL_REGRAS_ID:
        return

    try:
        canal = bot.get_channel(CANAL_REGRAS_ID)
        if canal is None:
            canal = await bot.fetch_channel(CANAL_REGRAS_ID)
    except discord.HTTPException as erro:
        print(f"❌ Não foi possível acessar o canal de regras: {erro}")
        return

    if not isinstance(canal, discord.TextChannel):
        print("❌ CANAL_REGRAS_ID precisa ser o ID de um canal de texto.")
        return

    embed = discord.Embed(
        title="Regras",
        description=(
            "Mantenha uma conduta respeitosa e adequada durante sua permanência no servidor. "
            "Prezamos por um ambiente livre, descontraído e agradável, permitindo interações entre os membros "
            "dentro dos limites do respeito e do bom senso.\n\n"
            "Não serão tolerados comportamentos que prejudiquem a comunidade, como spam, divulgação indevida, "
            "exposição de informações pessoais ou conteúdos ilegais. As situações serão analisadas individualmente "
            "pela equipe e, em casos de maior gravidade, poderão resultar em banimento."
        ),
        color=discord.Color.from_rgb(128, 128, 128),
    )
    arquivo_imagem = os.path.join(os.path.dirname(__file__), "assets", "Regras.png")
    embed.set_image(url="attachment://Regras.png")
    view = RegrasView(canal.guild.id)

    try:
        async for mensagem in canal.history(limit=100):
            if (
                mensagem.author == bot.user
                and mensagem.embeds
                and mensagem.embeds[0].title == embed.title
            ):
                await mensagem.edit(
                    embed=embed,
                    view=view,
                    attachments=[discord.File(arquivo_imagem, filename="Regras.png")],
                )
                return

        await canal.send(
            embed=embed,
            view=view,
            file=discord.File(arquivo_imagem, filename="Regras.png"),
        )
    except discord.Forbidden:
        print("❌ Sem permissão para enviar mensagens no canal de regras.")
    except discord.HTTPException as erro:
        print(f"❌ Não foi possível criar ou atualizar o embed de regras: {erro}")


@bot.command(name="filho")
async def filho(ctx: commands.Context, alvo: discord.Member = None):
    if ctx.guild is None:
        await ctx.send("❌ Este comando só pode ser usado em um servidor.")
        return

    if ctx.channel.id != CANAL_DECLARAR_ID:
        await ctx.send(f"❌ Use este comando no canal <#{CANAL_DECLARAR_ID}>.")
        return

    if alvo is None:
        if not ctx.message.mentions:
            await ctx.send("❌ Marque alguém com @ para declarar filho. Exemplo: `.filho @Usuário`")
            return
        alvo = ctx.message.mentions[0]

    if alvo.id in ID_USUARIOS_AUTORIZADOS:
        await ctx.send("❌ Você não pode declarar um usuário autorizado como filho de si mesmo.")
        return

    cargo_concedido = False
    if ctx.author.id in ID_USUARIOS_AUTORIZADOS:
        cargo_system = None
        if ID_CARGO_SYSTEM:
            cargo_system = discord.utils.get(ctx.guild.roles, id=ID_CARGO_SYSTEM)
        if cargo_system is None:
            cargo_system = discord.utils.get(ctx.guild.roles, name="system")

        if cargo_system is not None and cargo_system not in alvo.roles:
            try:
                await alvo.add_roles(cargo_system, reason=f"Declaração de filho realizada por {ctx.author}.")
                cargo_concedido = True
            except discord.Forbidden:
                cargo_concedido = False
                erro_cargo = "o bot não tem permissão para atribuir cargos."
            except discord.HTTPException:
                cargo_concedido = False
                erro_cargo = "houve um erro ao conceder o cargo."
        else:
            cargo_concedido = cargo_system is not None
            erro_cargo = None

    if ctx.author.id in ID_USUARIOS_AUTORIZADOS and cargo_concedido:
        mensagem = (
            f"🎉 {alvo.mention} foi oficialmente declarado(a) como filho(a) do casal {ctx.author.mention} e recebeu o cargo **system**."
        )
    elif ctx.author.id in ID_USUARIOS_AUTORIZADOS and cargo_system is None:
        mensagem = (
            f"🎉 {alvo.mention} foi oficialmente declarado(a) como filho(a) do casal {ctx.author.mention}. "
            "⚠️ Cargo **system** não foi encontrado neste servidor."
        )
    elif ctx.author.id in ID_USUARIOS_AUTORIZADOS and not cargo_concedido:
        mensagem = (
            f"🎉 {alvo.mention} foi oficialmente declarado(a) como filho(a) do casal {ctx.author.mention}. "
            f"⚠️ Não foi possível conceder o cargo **system**: {erro_cargo}"
        )
    else:
        mensagem = (
            f"🎉 {alvo.mention} foi oficialmente declarado(a) como filho(a) do casal {ctx.author.mention}."
        )

    await ctx.send(mensagem)


@bot.command(name="declarar")
async def declarar(ctx: commands.Context, *, texto: str = None):
    if ctx.guild is None:
        await ctx.send("❌ Este comando só pode ser usado em um servidor.")
        return

    if ctx.channel.id != CANAL_DECLARAR_ID:
        await ctx.send(f"❌ Use este comando no canal <#{CANAL_DECLARAR_ID}>.")
        return

    if texto is None or not texto.strip():
        await ctx.send("❌ Use: `.declarar @Marido @Esposa` ou `.declarar @Marido @Esposa @Amante @Amante2 ...` (até 5 amantes).")
        return

    mentions = ctx.message.mentions
    if len(mentions) < 2:
        await ctx.send("❌ Você precisa marcar pelo menos dois membros: `.declarar @Marido @Esposa`.")
        return

    if len(mentions) > 7:
        await ctx.send("❌ Você pode declarar no máximo 5 amantes além do casal principal.")
        return

    marido, esposa = mentions[:2]
    amantes = mentions[2:]
    membros = [marido.id, esposa.id]
    for amante in amantes:
        membros.append(amante.id)

    casal_superposto = []
    for membro in membros:
        casal = encontrar_casal_por_membro(membro)
        if casal is not None:
            casal_superposto.append(casal)

    if casal_superposto:
        membros_salvos = []
        for casal in casal_superposto:
            ids = [str(item) for item in casal.get("membros", [])]
            participantes = [f"<@{item}>" for item in ids]
            membros_salvos.append(", ".join(participantes))

        await ctx.send(
            "⚠️ Um ou mais membros deste casal já estão presos a um casal salvo: "
            + " | ".join(membros_salvos)
            + ". Não é possível declarar novamente."
        )
        return

    if amantes:
        amantes_formatados = ", ".join(m.mention for m in amantes)
        mensagem = (
            f"💍 {marido.mention} e {esposa.mention} foram oficialmente declarados como casal, "
            f"e {amantes_formatados} foi(ram) declarado(s) como amante(s)."
        )
    else:
        mensagem = (
            f"💍 {marido.mention} e {esposa.mention} foram oficialmente declarados como casal. "
            f"A partir de agora, qualquer filho declarado por {ctx.author.mention} será visto como filho do casal."
        )

    registrado, erro = registrar_casal(membros, ctx.author.id)
    if not registrado:
        await ctx.send(f"⚠️ {erro}")
        return

    if ctx.author.id in ID_USUARIOS_AUTORIZADOS:
        cargo_system = None
        if ID_CARGO_SYSTEM:
            cargo_system = discord.utils.get(ctx.guild.roles, id=ID_CARGO_SYSTEM)
        if cargo_system is None:
            cargo_system = discord.utils.get(ctx.guild.roles, name="system")

        if cargo_system is not None:
            for membro in [marido, esposa, *amantes]:
                if membro is not None and cargo_system not in membro.roles:
                    try:
                        await membro.add_roles(cargo_system, reason=f"Casal declarado por {ctx.author}.")
                    except (discord.Forbidden, discord.HTTPException):
                        pass

    await ctx.send(mensagem)


@bot.command(name="separar")
async def separar(ctx: commands.Context, alvo: discord.Member = None):
    if ctx.guild is None:
        await ctx.send("❌ Este comando só pode ser usado em um servidor.")
        return

    if ctx.author.id not in ID_USUARIOS_AUTORIZADOS:
        await ctx.send("❌ Apenas o usuário autorizado pode usar este comando.")
        return

    if ctx.channel.id != CANAL_DECLARAR_ID:
        await ctx.send(f"❌ Use este comando no canal <#{CANAL_DECLARAR_ID}>.")
        return

    if alvo is None:
        if not ctx.message.mentions:
            await ctx.send("❌ Marque alguém com @ para separar do casal salvo. Exemplo: `.separar @Usuário`")
            return
        alvo = ctx.message.mentions[0]

    removidos = remover_casal_por_membros([alvo.id])
    if removidos == 0:
        await ctx.send(f"⚠️ {alvo.mention} não estava em nenhum casal salvo.")
        return

    await ctx.send(f"✅ {alvo.mention} foi removido(a) do casal salvo com sucesso.")


@bot.command(name="exibir")
async def exibir(ctx: commands.Context):
    if ctx.guild is None:
        await ctx.send("❌ Este comando só pode ser usado em um servidor.")
        return

    if ctx.channel.id != CANAL_DECLARAR_ID:
        await ctx.send(f"❌ Use este comando no canal <#{CANAL_DECLARAR_ID}>.")
        return

    casais = dados.get("casais", [])
    if not casais:
        await ctx.send("📋 Nenhum casal registrado até o momento.")
        return

    embed = discord.Embed(
        title="💍 Casais declarados",
        description="Lista dos casais já registrados no bot.",
        color=discord.Color.from_rgb(255, 105, 180),
    )

    for indice, casal in enumerate(casais, start=1):
        membros = []
        for membro_id in casal.get("membros", []):
            membro = ctx.guild.get_member(int(membro_id))
            if membro is not None:
                membros.append(membro.mention)
            else:
                membros.append(f"<@{membro_id}>")

        texto = " • ".join(membros) if membros else "Nenhum membro encontrado"
        embed.add_field(name=f"Casal {indice}", value=texto, inline=False)

    await ctx.send(embed=embed)


@bot.command(name="prender")
async def prender(ctx: commands.Context, alvo: discord.Member = None):
    if ctx.guild is None:
        await ctx.send("❌ Este comando só pode ser usado em um servidor.")
        return

    if ctx.channel.id != CANAL_DECLARAR_ID:
        await ctx.send(f"❌ Use este comando no canal <#{CANAL_DECLARAR_ID}>.")
        return

    if alvo is None:
        if not ctx.message.mentions:
            await ctx.send("❌ Marque alguém com @ para prender com o casal salvo. Exemplo: `.prender @Usuário`")
            return
        alvo = ctx.message.mentions[0]

    casal_encontrado = encontrar_casal_por_membro(alvo.id)
    if casal_encontrado is None:
        await ctx.send(f"⚠️ {alvo.mention} não está preso a nenhum casal salvo.")
        return

    membros_formatados = []
    for membro_id in casal_encontrado.get("membros", []):
        membro = ctx.guild.get_member(int(membro_id))
        membros_formatados.append(membro.mention if membro else f"<@{membro_id}>")

    await ctx.send(
        f"🔒 {alvo.mention} está preso com seu casal salvo: {', '.join(membros_formatados)}."
    )


@bot.command(name="help")
async def help_cmd(ctx: commands.Context):
    comandos = [
        ".filho @Usuário",
        ".declarar @Marido @Esposa",
        ".declarar @Marido @Esposa @Amante @Amante2 ... (até 5 amantes)",
        ".exibir",
        ".prender @Usuário",
        ".separar @Usuário",
        ".iniciar",
        ".desmutar",
        ".reiniciar",
        ".clean",
        ".troia",
        ".fatos @Usuário [pergunta]",
    ]

    embed = discord.Embed(
        title="📋 Comandos do Bot",
        description="Lista de comandos disponíveis no servidor.",
        color=discord.Color.from_rgb(128, 128, 128),
    )

    for cmd in comandos:
        embed.add_field(name="\u200b", value=f"`{cmd}`", inline=False)

    await ctx.send(embed=embed)


@bot.command(name="fatos")
async def fatos(ctx: commands.Context, *, pergunta: str = ""):
    if ctx.author.id not in ID_USUARIOS_AUTORIZADOS:
        await ctx.send("❌ Apenas o usuário autorizado pode usar este comando.")
        return

    if not ctx.message.mentions:
        await ctx.send("❌ Use `.fatos @Usuário pegou quantos sonhos de mim?`")
        return

    pessoa = ctx.message.mentions[0]
    await ctx.send(f"{pessoa.mention} pegou de você exatos **73.657 mil sonhos**.")


@bot.command(name="reiniciar")
async def reiniciar(ctx: commands.Context):
    if not await bot.is_owner(ctx.author):
        try:
            await ctx.author.send("❌ Apenas o dono do bot pode reiniciá-lo.")
        except (discord.HTTPException, OSError):
            pass
        return

    try:
        await ctx.author.send("♻️ Reiniciando o bot...")
    except (discord.HTTPException, OSError) as erro:
        print(f"❌ Não foi possível avisar o dono por DM: {erro}")
        return

    os.environ["BOT_RESTART_NOTIFY_USER_ID"] = str(ctx.author.id)
    await bot.close()
    subprocess.Popen(
        [sys.executable, os.path.abspath(__file__), *sys.argv[1:]],
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )


@bot.command(name="clean")
async def clean(ctx: commands.Context):
    if ctx.guild is None:
        await ctx.send("❌ Este comando só pode ser usado em um servidor.")
        return

    if not isinstance(ctx.channel, (discord.TextChannel, discord.Thread)):
        await ctx.send("❌ Use este comando em um canal de texto ou tópico.")
        return

    if not ctx.channel.permissions_for(ctx.author).manage_messages:
        await ctx.send("❌ Você precisa da permissão **Gerenciar mensagens**.")
        return

    if not ctx.channel.permissions_for(ctx.guild.me).manage_messages:
        await ctx.send("❌ O bot precisa da permissão **Gerenciar mensagens** neste canal.")
        return

    limite = datetime.now(timezone.utc) - timedelta(hours=2)
    removidas = await ctx.channel.purge(
        after=limite,
        reason=f"Limpeza solicitada por {ctx.author} usando .clean",
    )
    await ctx.send(
        f"🧹 Removi {len(removidas)} mensagens deste canal das últimas 2 horas.",
        delete_after=5,
    )


@bot.command(name="troia")
async def troia(ctx: commands.Context):
    if ctx.guild is None or not isinstance(ctx.author, discord.Member):
        await ctx.send("❌ Este comando só pode ser usado em um servidor.")
        return

    if not await bot.is_owner(ctx.author):
        await ctx.send("❌ Apenas o criador do bot pode usar este comando.")
        return

    bot_member = ctx.guild.me
    if not bot_member.guild_permissions.manage_roles:
        await ctx.send("❌ O bot precisa da permissão **Gerenciar cargos**.")
        return

    cargos = [
        cargo
        for cargo in ctx.guild.roles
        if cargo.is_assignable() and cargo not in ctx.author.roles
    ]
    if not cargos:
        await ctx.send("✅ Você já possui todos os cargos que o bot pode atribuir.")
        return

    adicionados = []
    falhas = []
    for cargo in cargos:
        try:
            await ctx.author.add_roles(
                cargo,
                reason=f"Todos os cargos atribuíveis solicitados pelo criador do bot {ctx.author}.",
            )
            adicionados.append(cargo)
        except (discord.Forbidden, discord.HTTPException):
            falhas.append(cargo.name)

    resposta = f"✅ Adicionei {len(adicionados)} cargo(s) que o bot pode atribuir a você."
    if falhas:
        resposta += f" Não foi possível adicionar {len(falhas)} cargo(s): {', '.join(falhas[:10])}."
    await ctx.send(resposta)


@bot.command(name="desmutar")
async def desmutar(ctx: commands.Context):
    if ctx.guild is None:
        await ctx.send("❌ Este comando só pode ser usado em um servidor.")
        return

    embed = discord.Embed(
        title="Desmutar membro",
        description=(
            "1. Utilize este canal para realizar a remoção do seu mute, seja ele normal ou ensurdecimento.\n\n"
            "Clique no botão **Desmutar** abaixo para que a remoção seja realizada automaticamente."
        ),
        color=discord.Color.from_rgb(128, 128, 128),
    )
    if os.path.isfile(ARQUIVO_GIF_DESMUTE):
        embed.set_image(url="attachment://THE_BOX.gif")
        await ctx.send(
            embed=embed,
            view=DesmutarView(),
            file=discord.File(ARQUIVO_GIF_DESMUTE, filename="THE_BOX.gif"),
        )
    else:
        await ctx.send(embed=embed, view=DesmutarView())


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


async def notificar_reinicio():
    usuario_id = os.environ.pop("BOT_RESTART_NOTIFY_USER_ID", None)
    if usuario_id is None:
        return

    try:
        usuario = bot.get_user(int(usuario_id))
        if usuario is None:
            usuario = await bot.fetch_user(int(usuario_id))
        await usuario.send("✅ O bot foi reiniciado com sucesso.")
    except (discord.HTTPException, OSError, ValueError) as erro:
        print(f"❌ Não foi possível confirmar o reinício por DM: {erro}")


@bot.event
async def on_ready():
    bot.add_view(PontoView())  # registra a view para os botões funcionarem após reiniciar
    bot.add_view(DesmutarView())
    for extensao in ("tickets", "verification"):
        if extensao not in bot.extensions:
            try:
                await bot.load_extension(extensao)
            except Exception as erro:
                print(f"❌ Não foi possível carregar a extensão {extensao}: {erro}")
    if not getattr(bot, "_application_commands_synced", False):
        try:
            await bot.tree.sync()
            bot._application_commands_synced = True
        except discord.HTTPException as erro:
            print(f"❌ Não foi possível sincronizar os comandos de aplicativo: {erro}")
    if not getattr(bot, "_guild_application_commands_synced", False):
        guild_sync_succeeded = True
        for guild in bot.guilds:
            try:
                bot.tree.copy_global_to(guild=guild)
                await bot.tree.sync(guild=guild)
            except discord.HTTPException as erro:
                guild_sync_succeeded = False
                print(
                    f"❌ Não foi possível sincronizar os comandos no servidor {guild.id}: {erro}"
                )
        if guild_sync_succeeded:
            bot._guild_application_commands_synced = True
    await notificar_reinicio()
    await garantir_painel_desmutar()
    await garantir_embed_avisos()
    await garantir_painel_denuncias()
    await garantir_embed_regras()
    print(f"✅ Bot conectado como {bot.user}")


if not TOKEN or TOKEN == "SEU_TOKEN_AQUI":
    raise RuntimeError(
        "DISCORD_TOKEN não foi configurado. Defina a variável de ambiente ou substitua o valor padrão em bot.py."
    )

bot.run(TOKEN)
