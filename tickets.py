import asyncio
import json
import os
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

# ================== CONFIGURAÇÃO ==================
STAFF_ROLE_ID = int(os.getenv("STAFF_ROLE_ID", "0"))
STAFF_APPLICATION_ROLE_IDS = (1551012886384742440, 1551011646661595226)
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "1552722101641814027")) or None
CATEGORY_ID = int(os.getenv("TICKET_CATEGORY_ID", "0")) or None
INSTAGRAM_VERIFY_CHANNEL_ID = int(
    os.getenv("INSTAGRAM_VERIFY_CHANNEL_ID", "1549904027167236266")
)
SUPPORT_CHANNEL_ID = int(os.getenv("CANAL_SUPORTE_ID", "1548207347753689098"))
EVENT_CHANNEL_ID = 1555742453791854722
EVENT_APPLICATION_CHANNEL_ID = 1557914825059860651
SUPPORT_IMAGE_PATH = Path(__file__).parent / "assets" / "SUPORTE.png"
DENUNCIE_IMAGE_PATH = Path(__file__).parent / "assets" / "DENUNCIE.png"
COUNTER_FILE = Path(__file__).parent / "ticket-counter.json"
# ===================================================

ID_OPEN = "ticket_open_denuncia"
ID_OPEN_INSTAGRAM = "ticket_open_instagram"
ID_OPEN_SUPPORT = "ticket_open_support"
ID_OPEN_CAMPEONATO = "ticket_open_campeonato"
ID_APPLY_STAFF = "ticket_apply_staff"
ID_CLOSE = "ticket_close"
COR = discord.Color.from_rgb(43, 45, 49)


def campeonato_panel_embed() -> discord.Embed:
    return discord.Embed(
        title="<:tr_11:1549374249247182971> CAMPEONATO THE BOX",
        description=(
            "<:emoji_18:1547470852042530856> <:emoji_14:1547470846237478973> "
            "<:b_2:1547470823034724444> <:emoji_12:1547470842747818004> "
            "<:emoji_14:1547470846237478973> <:emoji_25:1548493251449716876>\n"
            "---\n\n"
            "### <a:pureza_i:1327091619505246218> "
            "<:pureza_i:1333172482366242896> REQUISITOS OBRIGATÓRIOS\n"
            "<:d_seta01:1547470839258157066> Preenchimento completo do formulário oficial.\n"
            "<:d_seta01:1547470839258157066> Seguir os canais informados do evento.\n"
            "<:d_seta01:1547470839258157066> Inclusão obrigatória do link do servidor e da etiqueta na bio.\n"
            "<:d_seta01:1547470839258157066> Constituição prévia de equipes com disponibilidade confirmada.\n"
            "<:d_seta01:1547470839258157066> Disponibilidade para participação ativa em chamada de voz.\n"
            "<:d_seta01:1547470839258157066> Manter participação ativa no servidor.\n\n"
            "---\n\n"
            "### <a:pureza_i:1327091636085461134> "
            "<:pureza_i:1333172482366242896> REGULAMENTO E PROIBIÇÕES\n"
            "<:d_seta01:1547470839258157066> Estritamente proibido o uso de qualquer tipo de trapaça.\n"
            "<:d_seta01:1547470839258157066> É proibido remover o link do servidor e a etiqueta da bio até ao encerramento do evento.\n"
            "<:d_seta01:1547470839258157066> É obrigatória a presença no canal de voz no horário estabelecido, mantendo a disciplina de uso do microfone.\n"
            "<:d_seta01:1547470839258157066> É obrigatória a participação no processo de votação para a seleção dos jogos.\n"
            "<:d_seta01:1547470839258157066> Não serão permitidas substituições de membros, independentemente da justificativa apresentada.\n\n"
            "> **AVISO:** O cumprimento de todos os requisitos e regras é indispensável. "
            "Será realizada uma verificação individual de cada participante previamente ao início do evento.\n\n"
            "---\n\n"
            "### <a:pureza_i:1327091661289029685> "
            "<:pureza_i:1333172482366242896> DINÂMICA DE FUNCIONAMENTO\n"
            "<:d_seta01:1547470839258157066> O evento será composto por múltiplos minijogos, disputados em formatos individual e em equipe.\n"
            "<:d_seta01:1547470839258157066> Fase inicial com tabela de pontuação, seguida de uma fase eliminatória por grupos.\n"
            "<:d_seta01:1547470839258157066> A escolha dos minijogos será definida via votação direta no canal reservado aos participantes.\n"
            "<:d_seta01:1547470839258157066> O evento contará com transmissão ao vivo e narração oficial.\n\n"
            "---\n\n"
            "### <a:pureza_i:1241818474918056102> PREMIAÇÃO FINAL\n"
            "**R$ 100,00** + **1 Mês de Discord Nitro** para o participante que ganhar MVP.\n\n"
            "Clique no botão abaixo para abrir seu ticket de inscrição. "
            "A equipe receberá o link do ticket no canal reservado."
        ),
        color=COR,
    )


def possui_botao_campeonato(component) -> bool:
    if getattr(component, "custom_id", None) == ID_OPEN_CAMPEONATO:
        return True
    return any(
        possui_botao_campeonato(child)
        for child in getattr(component, "children", ())
    )


def instagram_panel_embed() -> discord.Embed:
    return discord.Embed(
        title="Verificação Instagram",
        description=(
            "Solicite sua verificação através deste ticket.\n\n"
            "Após a abertura, um membro da Staff irá atender sua solicitação e, em seguida, "
            "chamará você para uma Call de verificação com vídeo.\n\n"
            "Durante a Call, será realizada a confirmação do perfil. Após a verificação, "
            "seu Instagram será validado pela Staff"
        ),
        color=COR,
    )


def possui_botao_instagram(component) -> bool:
    if getattr(component, "custom_id", None) == ID_OPEN_INSTAGRAM:
        return True
    return any(
        possui_botao_instagram(child)
        for child in getattr(component, "children", ())
    )


def support_panel_embed() -> discord.Embed:
    embed = discord.Embed(
        title="Central de suporte",
        description=(
            "Precisa de ajuda ou deseja fazer parte da nossa equipe?\n\n"
            "**1. Abrir Ticket**\n"
            "Utilize para solicitar ajuda, tirar dúvidas ou resolver qualquer situação relacionada "
            "ao servidor.\n\n"
            "**2. Seja Staff**\n"
            "Utilize para se candidatar a uma vaga na equipe e enviar sua candidatura para Staff."
        ),
        color=COR,
    )
    if SUPPORT_IMAGE_PATH.is_file():
        embed.set_image(url="attachment://SUPORTE.png")
    return embed


async def create_support_ticket(
    interaction: discord.Interaction,
    ticket_type: str,
    title: str,
    description: str,
):
    guild = interaction.guild
    user = interaction.user
    if guild is None or not isinstance(user, discord.Member):
        return await interaction.response.send_message(
            "Este botão só pode ser usado dentro do servidor.", ephemeral=True
        )

    topic = f"ticket:{user.id}:{ticket_type}"
    existing = discord.utils.get(guild.text_channels, topic=topic)
    if existing:
        return await interaction.response.send_message(
            f"Você já tem uma solicitação aberta: {existing.mention}", ephemeral=True
        )

    await interaction.response.defer(ephemeral=True)
    number = next_ticket_number()
    if ticket_type == "staff":
        staff_roles = [
            role
            for role_id in STAFF_APPLICATION_ROLE_IDS
            if (role := guild.get_role(role_id)) is not None
        ]
    else:
        staff_role = guild.get_role(STAFF_ROLE_ID)
        staff_roles = [staff_role] if staff_role else []

    member_permissions = discord.PermissionOverwrite(
        view_channel=True, send_messages=True, read_message_history=True, attach_files=True
    )
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        user: member_permissions,
        guild.me: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, manage_channels=True
        ),
    }
    for staff_role in staff_roles:
        overwrites[staff_role] = member_permissions

    category = guild.get_channel(CATEGORY_ID) if CATEGORY_ID else interaction.channel.category
    channel = await guild.create_text_channel(
        name=f"ticket-{number}",
        category=category,
        topic=topic,
        overwrites=overwrites,
    )
    embed = discord.Embed(title=title, description=description, color=COR)
    mention_staff = " ".join(role.mention for role in staff_roles)
    await channel.send(
        content=f"Olá {user.mention}, sua solicitação foi aberta. {mention_staff}",
        embed=embed,
        view=CloseView(),
        allowed_mentions=discord.AllowedMentions(users=True, roles=True),
    )
    notification_sent = True
    if ticket_type == "campeonato":
        notification_sent = await notify_event_application(guild, user, channel)

    confirmation = f"Sua solicitação foi criada: {channel.mention}"
    if not notification_sent:
        confirmation += (
            "\n⚠️ O ticket foi criado, mas não consegui avisar o canal da equipe. "
            "Avise a Staff para que sua inscrição seja vista."
        )
    await interaction.followup.send(
        confirmation, ephemeral=True
    )
    await send_log(
        guild,
        f"📩 Ticket de {ticket_type} **{channel.name}** aberto por {user.mention} ({user.id})",
    )


async def notify_event_application(
    guild: discord.Guild, user: discord.Member, ticket_channel: discord.TextChannel
) -> bool:
    try:
        target = guild.get_channel(EVENT_APPLICATION_CHANNEL_ID)
        if target is None:
            target = await guild.fetch_channel(EVENT_APPLICATION_CHANNEL_ID)
        if not isinstance(target, discord.TextChannel):
            print("[tickets] EVENT_APPLICATION_CHANNEL_ID precisa ser um canal de texto.")
            return False

        embed = discord.Embed(
            title="Nova inscrição — Campeonato The Box",
            color=COR,
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(
            name="Participante",
            value=f"{user.display_name} (`{user.id}`)",
            inline=False,
        )
        embed.add_field(name="Ticket", value=ticket_channel.mention, inline=False)
        await target.send(
            embed=embed,
            allowed_mentions=discord.AllowedMentions.none(),
        )
        return True
    except discord.Forbidden:
        print("[tickets] Sem permissão para acessar ou avisar o canal de inscrições do campeonato.")
    except discord.HTTPException as error:
        print(f"[tickets] Não consegui avisar o canal de inscrições do campeonato: {error}")
    return False


def next_ticket_number() -> str:
    try:
        data = json.loads(COUNTER_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"last": 0}

    data["last"] += 1
    COUNTER_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(data["last"]).zfill(4)


async def send_log(guild: discord.Guild, text: str):
    if not LOG_CHANNEL_ID:
        return
    ch = guild.get_channel(LOG_CHANNEL_ID)
    if ch:
        try:
            await ch.send(text)
        except discord.HTTPException:
            pass


class CloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fechar", emoji="🔒", style=discord.ButtonStyle.danger, custom_id=ID_CLOSE)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel
        member = interaction.user

        is_owner = channel.topic in {
            f"ticket:{member.id}",
            f"ticket:{member.id}:instagram",
            f"ticket:{member.id}:support",
            f"ticket:{member.id}:staff",
            f"ticket:{member.id}:campeonato",
        }
        authorized_role_ids = (
            STAFF_APPLICATION_ROLE_IDS
            if channel.topic and channel.topic.endswith(":staff")
            else (STAFF_ROLE_ID,)
        )
        is_staff = any(
            role.id in authorized_role_ids for role in member.roles
        ) or member.guild_permissions.manage_channels

        if not (is_owner or is_staff):
            return await interaction.response.send_message("Você não pode fechar este ticket.", ephemeral=True)

        await interaction.response.send_message("🔒 Ticket será fechado em 5 segundos...")
        await send_log(interaction.guild, f"🔒 Ticket **{channel.name}** fechado por {member.mention}")
        await asyncio.sleep(5)
        try:
            await channel.delete()
        except discord.HTTPException:
            pass


class OpenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Denuncie aqui",
        style=discord.ButtonStyle.secondary,
        custom_id=ID_OPEN,
    )
    async def open(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user

        existing = discord.utils.get(guild.text_channels, topic=f"ticket:{user.id}")
        if existing:
            return await interaction.response.send_message(
                f"Você já tem uma denúncia aberta: {existing.mention}", ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        number = next_ticket_number()
        staff_role = guild.get_role(STAFF_ROLE_ID)

        pode = discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True, attach_files=True
        )
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: pode,
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
        }
        if staff_role:
            overwrites[staff_role] = pode

        category = guild.get_channel(CATEGORY_ID) if CATEGORY_ID else interaction.channel.category

        channel = await guild.create_text_channel(
            name=f"ticket-{number}",
            category=category,
            topic=f"ticket:{user.id}",
            overwrites=overwrites,
        )

        embed = discord.Embed(
            title="Ticket Criado",
            description=(
                "Obrigado por criar um ticket!\n"
                "Por favor, descreva seu problema em detalhes e nossa equipe de suporte estará com você em breve."
            ),
            color=COR,
            timestamp=discord.utils.utcnow(),
        )

        mention_staff = staff_role.mention if staff_role else ""
        await channel.send(
            content=f"Olá {user.mention}, bem-vindo à sua denúncia! {mention_staff}",
            embed=embed,
            view=CloseView(),
            allowed_mentions=discord.AllowedMentions(users=True, roles=True),
        )

        await interaction.followup.send(f"Seu ticket foi criado: {channel.mention}", ephemeral=True)
        await send_log(guild, f"📩 Ticket **{channel.name}** aberto por {user.mention} ({user.id})")


class InstagramOpenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Verificar",
        emoji=discord.PartialEmoji(name="emoji_108", id=1554631035093000275),
        style=discord.ButtonStyle.secondary,
        custom_id=ID_OPEN_INSTAGRAM,
    )
    async def open(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user
        if guild is None or not isinstance(user, discord.Member):
            return await interaction.response.send_message(
                "Este botão só pode ser usado dentro do servidor.", ephemeral=True
            )

        topic = f"ticket:{user.id}:instagram"
        existing = discord.utils.get(guild.text_channels, topic=topic)
        if existing:
            return await interaction.response.send_message(
                f"Você já tem uma verificação aberta: {existing.mention}", ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)
        number = next_ticket_number()
        staff_role = guild.get_role(STAFF_ROLE_ID)
        member_permissions = discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True, attach_files=True
        )
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: member_permissions,
            guild.me: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, manage_channels=True
            ),
        }
        if staff_role:
            overwrites[staff_role] = member_permissions

        category = guild.get_channel(CATEGORY_ID) if CATEGORY_ID else interaction.channel.category
        channel = await guild.create_text_channel(
            name=f"ticket-{number}",
            category=category,
            topic=topic,
            overwrites=overwrites,
        )

        embed = discord.Embed(
            title="Ticket Criado",
            description=(
                "Obrigado por solicitar sua verificação!\n"
                "A equipe de Staff atenderá você em breve."
            ),
            color=COR,
            timestamp=discord.utils.utcnow(),
        )
        mention_staff = staff_role.mention if staff_role else ""
        await channel.send(
            content=f"Olá {user.mention}, seu ticket de verificação foi aberto. {mention_staff}",
            embed=embed,
            view=CloseView(),
            allowed_mentions=discord.AllowedMentions(users=True, roles=True),
        )
        await interaction.followup.send(
            f"Seu ticket de verificação foi criado: {channel.mention}", ephemeral=True
        )
        await send_log(guild, f"📷 Verificação Instagram **{channel.name}** aberta por {user.mention} ({user.id})")


class SupportView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Abrir Ticket",
        emoji="🎟️",
        style=discord.ButtonStyle.secondary,
        custom_id=ID_OPEN_SUPPORT,
    )
    async def open_support(self, interaction: discord.Interaction, button: discord.ui.Button):
        await create_support_ticket(
            interaction,
            "support",
            "Ticket de Suporte",
            "Descreva sua dúvida ou situação relacionada ao servidor. A equipe de suporte "
            "atenderá você assim que possível.",
        )

    @discord.ui.button(
        label="Seja Staff",
        emoji="🛡️",
        style=discord.ButtonStyle.secondary,
        custom_id=ID_APPLY_STAFF,
    )
    async def apply_staff(self, interaction: discord.Interaction, button: discord.ui.Button):
        await create_support_ticket(
            interaction,
            "staff",
            "Candidatura à Staff",
            "Envie sua candidatura para a equipe e conte por que deseja fazer parte da Staff.",
        )


class CampeonatoOpenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Inscrever-se",
        emoji="🎟️",
        style=discord.ButtonStyle.primary,
        custom_id=ID_OPEN_CAMPEONATO,
    )
    async def open_campeonato(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await create_support_ticket(
            interaction,
            "campeonato",
            "Inscrição — Campeonato The Box",
            "Envie neste ticket a confirmação de que preencheu o formulário oficial e as "
            "informações necessárias sobre sua equipe e disponibilidade. A equipe fará a "
            "verificação dos requisitos antes do início do evento.",
        )


class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.panel_task = None
        self.support_panel_task = None
        self.campeonato_panel_task = None

    async def cog_load(self):
        self.bot.add_view(OpenView())
        self.bot.add_view(InstagramOpenView())
        self.bot.add_view(SupportView())
        self.bot.add_view(CampeonatoOpenView())
        self.bot.add_view(CloseView())
        self.panel_task = asyncio.create_task(self.ensure_instagram_panel())
        self.support_panel_task = asyncio.create_task(self.ensure_support_panel())
        self.campeonato_panel_task = asyncio.create_task(self.ensure_campeonato_panel())

    async def cog_unload(self):
        if self.panel_task:
            self.panel_task.cancel()
        if self.support_panel_task:
            self.support_panel_task.cancel()
        if self.campeonato_panel_task:
            self.campeonato_panel_task.cancel()

    async def ensure_instagram_panel(self):
        await self.bot.wait_until_ready()
        try:
            channel = self.bot.get_channel(INSTAGRAM_VERIFY_CHANNEL_ID)
            if channel is None:
                channel = await self.bot.fetch_channel(INSTAGRAM_VERIFY_CHANNEL_ID)
            if not isinstance(channel, discord.TextChannel):
                print("[tickets] INSTAGRAM_VERIFY_CHANNEL_ID precisa ser um canal de texto.")
                return

            async for message in channel.history(limit=50):
                if message.author == self.bot.user and any(
                    possui_botao_instagram(component)
                    for component in message.components
                ):
                    await message.edit(view=InstagramOpenView())
                    return
            await channel.send(embed=instagram_panel_embed(), view=InstagramOpenView())
        except discord.Forbidden:
            print("[tickets] Sem permissão para ler o histórico ou enviar o painel Instagram.")
        except discord.HTTPException as error:
            print(f"[tickets] Não consegui criar/atualizar o painel Instagram: {error}")

    async def ensure_support_panel(self):
        await self.bot.wait_until_ready()
        try:
            channel = self.bot.get_channel(SUPPORT_CHANNEL_ID)
            if channel is None:
                channel = await self.bot.fetch_channel(SUPPORT_CHANNEL_ID)
            if not isinstance(channel, discord.TextChannel):
                print("[tickets] CANAL_SUPORTE_ID precisa ser um canal de texto.")
                return

            async for message in channel.history(limit=50):
                if message.author == self.bot.user and any(
                    any(
                        getattr(component, "custom_id", None) in {
                            ID_OPEN_SUPPORT,
                            ID_APPLY_STAFF,
                        }
                        for component in getattr(row, "children", (row,))
                    )
                    for row in message.components
                ):
                    if SUPPORT_IMAGE_PATH.is_file():
                        await message.edit(
                            embed=support_panel_embed(),
                            view=SupportView(),
                            attachments=[
                                discord.File(SUPPORT_IMAGE_PATH, filename="SUPORTE.png")
                            ],
                        )
                    else:
                        await message.edit(
                            embed=support_panel_embed(), view=SupportView(), attachments=[]
                        )
                    return
            if SUPPORT_IMAGE_PATH.is_file():
                await channel.send(
                    embed=support_panel_embed(),
                    view=SupportView(),
                    file=discord.File(SUPPORT_IMAGE_PATH, filename="SUPORTE.png"),
                )
            else:
                await channel.send(embed=support_panel_embed(), view=SupportView())
        except discord.Forbidden:
            print("[tickets] Sem permissão para ler o histórico ou enviar o painel de suporte.")
        except discord.HTTPException as error:
            print(f"[tickets] Não consegui criar/atualizar o painel de suporte: {error}")

    async def ensure_campeonato_panel(self):
        await self.bot.wait_until_ready()
        try:
            channel = self.bot.get_channel(EVENT_CHANNEL_ID)
            if channel is None:
                channel = await self.bot.fetch_channel(EVENT_CHANNEL_ID)
            if not isinstance(channel, discord.TextChannel):
                print("[tickets] EVENT_CHANNEL_ID precisa ser um canal de texto.")
                return

            async for message in channel.history(limit=50):
                if message.author == self.bot.user and any(
                    possui_botao_campeonato(component)
                    for component in message.components
                ):
                    await message.edit(
                        embed=campeonato_panel_embed(),
                        view=CampeonatoOpenView(),
                    )
                    return
            await channel.send(
                embed=campeonato_panel_embed(),
                view=CampeonatoOpenView(),
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except discord.Forbidden:
            print("[tickets] Sem permissão para ler o histórico ou enviar o painel do campeonato.")
        except discord.HTTPException as error:
            print(f"[tickets] Não consegui criar/atualizar o painel do campeonato: {error}")

    @app_commands.command(
        name="painel_verificacao_instagram",
        description="Envia o painel para solicitar verificação do Instagram neste canal",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def painel_verificacao_instagram(self, interaction: discord.Interaction):
        await interaction.channel.send(embed=instagram_panel_embed(), view=InstagramOpenView())
        await interaction.response.send_message("Painel enviado!", ephemeral=True)

    @app_commands.command(name="painel_denuncias", description="Envia o painel de denúncias neste canal")
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def painel_denuncias(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Central de denúncias.",
            description=(
                "Presenciou uma situação que viola as regras do servidor?\n\n"
                "Utilize este canal para realizar uma denúncia à nossa equipe de moderação.\n\n"
                "**1.** Ao abrir uma denúncia, informe o máximo de detalhes possível e, se tiver, "
                "envie provas como prints ou vídeos.\n\n"
                "**2.** Denúncias falsas ou feitas de má-fé poderão resultar em punição.\n\n"
                "**3.** Sua denúncia será tratada de forma reservada pela equipe responsável."
            ),
            color=COR,
        )
        if DENUNCIE_IMAGE_PATH.is_file():
            embed.set_image(url="attachment://DENUNCIE.png")
            await interaction.channel.send(
                embed=embed,
                view=OpenView(),
                file=discord.File(DENUNCIE_IMAGE_PATH, filename="DENUNCIE.png"),
            )
        else:
            await interaction.channel.send(embed=embed, view=OpenView())
        await interaction.response.send_message("Painel enviado!", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))
