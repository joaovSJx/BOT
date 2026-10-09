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
EVENT_SIGNUP_CHANNEL_ID = 1557918667759685783
SUPPORT_IMAGE_PATH = Path(__file__).parent / "assets" / "SUPORTE.png"
DENUNCIE_IMAGE_PATH = Path(__file__).parent / "assets" / "DENUNCIE.png"
COUNTER_FILE = Path(__file__).parent / "ticket-counter.json"
# ===================================================

ID_OPEN = "ticket_open_denuncia"
ID_OPEN_INSTAGRAM = "ticket_open_instagram"
ID_OPEN_SUPPORT = "ticket_open_support"
ID_OPEN_CAMPEONATO = "ticket_open_campeonato"
ID_DELETE_CAMPEONATO_APPLICATION = "ticket_delete_campeonato_application"
ID_APPLY_STAFF = "ticket_apply_staff"
ID_CLOSE = "ticket_close"
COR = discord.Color.from_rgb(43, 45, 49)


def campeonato_panel_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🏆 CAMPEONATO THE BOX",
        description="Leia os requisitos e o regulamento antes de se inscrever.",
        color=COR,
    )
    embed.add_field(
        name="📋 REQUISITOS OBRIGATÓRIOS",
        value=(
            "• Preencher completamente o formulário oficial.\n"
            "• Seguir os canais informados do evento.\n"
            "• Manter o link do servidor e a etiqueta na bio.\n"
            "• Formar a equipe previamente e confirmar a disponibilidade de todos.\n"
            "• Ter disponibilidade para participar ativamente de chamadas de voz.\n"
            "• Manter participação ativa no servidor."
        ),
        inline=False,
    )
    embed.add_field(
        name="📜 REGULAMENTO E PROIBIÇÕES",
        value=(
            "• É proibido usar qualquer tipo de trapaça.\n"
            "• Não remova o link do servidor nem a etiqueta da bio até o encerramento do evento.\n"
            "• Esteja no canal de voz no horário estabelecido e mantenha a disciplina no uso do microfone.\n"
            "• Participe da votação para a seleção dos jogos.\n"
            "• Não serão permitidas substituições de membros, independentemente da justificativa."
        ),
        inline=False,
    )
    embed.add_field(
        name="⚠️ AVISO",
        value=(
            "O cumprimento de todos os requisitos e regras é indispensável. "
            "Cada participante será verificado antes do início do evento."
        ),
        inline=False,
    )
    embed.add_field(
        name="🎮 COMO VAI FUNCIONAR",
        value=(
            "• O evento terá vários minijogos, em formatos individuais e por equipe.\n"
            "• A fase inicial terá tabela de pontuação, seguida por eliminatórias em grupos.\n"
            "• Os minijogos serão escolhidos por votação no canal reservado aos participantes.\n"
            "• O evento contará com transmissão ao vivo e narração oficial."
        ),
        inline=False,
    )
    embed.add_field(
        name="🏅 PREMIAÇÃO",
        value="**R$ 100,00 + 1 mês de Discord Nitro** para o participante eleito MVP.",
        inline=False,
    )
    embed.set_footer(
        text=f"Para se inscrever, abra um ticket no canal <#{EVENT_SIGNUP_CHANNEL_ID}>."
    )
    return embed


def campeonato_signup_embed() -> discord.Embed:
    return discord.Embed(
        title="Inscrições para o Campeonato The Box",
        description=(
            "Quer participar do campeonato? Clique no botão abaixo para abrir seu ticket "
            "de inscrição. A equipe vai orientar você por lá."
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


def campo_embed(embed: discord.Embed, name: str) -> str:
    return next((field.value for field in embed.fields if field.name == name), "")


def participante_id_da_inscricao(embed: discord.Embed) -> int | None:
    participant = campo_embed(embed, "Participante")
    if "(" not in participant:
        return None
    value = participant.rsplit("(", 1)[1].strip("`)")
    return int(value) if value.isdecimal() else None


def embed_mensagem_participante(message: discord.Message) -> discord.Embed:
    embed = discord.Embed(
        title="Mensagem do participante",
        description=message.content or "Mensagem sem texto.",
        color=COR,
        timestamp=message.created_at,
    )
    embed.set_author(
        name=f"{message.author.display_name} ({message.author.id})",
        icon_url=message.author.display_avatar.url,
    )
    for index, attachment in enumerate(message.attachments, start=1):
        embed.add_field(
            name=f"Anexo {index}",
            value=attachment.url,
            inline=False,
        )
    return embed


async def copiar_mensagem_participante(
    message: discord.Message, thread: discord.Thread
):
    await thread.send(
        embed=embed_mensagem_participante(message),
        allowed_mentions=discord.AllowedMentions.none(),
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
    existing = next(
        (
            channel
            for channel in guild.text_channels
            if channel.topic == topic
            or (
                ticket_type == "campeonato"
                and channel.topic
                and channel.topic.startswith(f"{topic}:log:")
            )
        ),
        None,
    )
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
        application_thread = await notify_event_application(guild, user, channel)
        notification_sent = application_thread is not None
        if application_thread is not None:
            await channel.edit(topic=f"{topic}:log:{application_thread.id}")

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
) -> discord.Thread | None:
    try:
        target = guild.get_channel(EVENT_APPLICATION_CHANNEL_ID)
        if target is None:
            target = await guild.fetch_channel(EVENT_APPLICATION_CHANNEL_ID)
        if not isinstance(target, discord.TextChannel):
            print("[tickets] EVENT_APPLICATION_CHANNEL_ID precisa ser um canal de texto.")
            return None

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
        log_message = await target.send(
            embed=embed,
            view=DeleteCampeonatoApplicationView(),
            allowed_mentions=discord.AllowedMentions.none(),
        )
        thread = await log_message.create_thread(
            name=f"Inscrição - {user.display_name}"[:100],
            auto_archive_duration=10080,
        )
        embed.add_field(name="Acompanhamento", value=thread.mention, inline=False)
        await log_message.edit(embed=embed)
        await thread.send(
            "As mensagens e anexos enviados pelo participante no ticket serão registrados aqui.",
            allowed_mentions=discord.AllowedMentions.none(),
        )
        return thread
    except discord.Forbidden:
        print("[tickets] Sem permissão para criar a inscrição ou seu tópico de acompanhamento.")
    except discord.HTTPException as error:
        print(f"[tickets] Não consegui criar a inscrição ou seu tópico de acompanhamento: {error}")
    return None


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
        } or (
            channel.topic
            and channel.topic.startswith(f"ticket:{member.id}:campeonato:log:")
        )
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
        emoji=discord.PartialEmoji(name="pureza_i", id=1169319223001092158),
        style=discord.ButtonStyle.secondary,
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


class DeleteCampeonatoApplicationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Remover participante",
        emoji="🗑️",
        style=discord.ButtonStyle.danger,
        custom_id=ID_DELETE_CAMPEONATO_APPLICATION,
    )
    async def delete_application(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        guild = interaction.guild
        member = interaction.user
        if guild is None or not isinstance(member, discord.Member):
            return await interaction.response.send_message(
                "Esta ação só pode ser usada dentro do servidor.", ephemeral=True
            )

        is_staff = member.guild_permissions.manage_channels or any(
            role.id == STAFF_ROLE_ID for role in member.roles
        )
        if not is_staff:
            return await interaction.response.send_message(
                "Você não tem permissão para remover participantes.", ephemeral=True
            )

        log_message = interaction.message
        if (
            interaction.client.user is None
            or log_message.author.id != interaction.client.user.id
        ):
            return await interaction.response.send_message(
                "Esta mensagem de inscrição não é válida.", ephemeral=True
            )
        ticket_field = next(
            (
                field.value
                for field in (log_message.embeds[0].fields if log_message.embeds else ())
                if field.name == "Ticket"
            ),
            "",
        )
        ticket_id_value = ticket_field[2:-1] if (
            ticket_field.startswith("<#") and ticket_field.endswith(">")
        ) else ""
        if not ticket_id_value.isdecimal():
            return await interaction.response.send_message(
                "Não encontrei o ticket relacionado a esta inscrição.", ephemeral=True
            )

        if (
            not log_message.embeds
            or log_message.embeds[0].title != "Nova inscrição — Campeonato The Box"
        ):
            return await interaction.response.send_message(
                "Esta mensagem não é um registro de inscrição válido.", ephemeral=True
            )

        ticket_id = int(ticket_id_value)
        ticket_channel = guild.get_channel(ticket_id)
        if ticket_channel is None:
            try:
                fetched_channel = await guild.fetch_channel(ticket_id)
            except discord.NotFound:
                fetched_channel = None
            except discord.HTTPException as error:
                print(f"[tickets] Não consegui localizar o ticket da inscrição: {error}")
                return await interaction.response.send_message(
                    "Não consegui acessar o ticket. A inscrição não foi removida.",
                    ephemeral=True,
                )
            ticket_channel = fetched_channel

        thread_field = next(
            (
                field.value
                for field in log_message.embeds[0].fields
                if field.name == "Acompanhamento"
            ),
            "",
        )
        thread_id_value = thread_field[2:-1] if (
            thread_field.startswith("<#") and thread_field.endswith(">")
        ) else ""
        thread_id = int(thread_id_value) if thread_id_value.isdecimal() else None
        if ticket_channel is not None and (
            not isinstance(ticket_channel, discord.TextChannel)
            or not ticket_channel.topic
            or ":campeonato:log:" not in ticket_channel.topic
        ):
            return await interaction.response.send_message(
                "O canal associado não é um ticket de inscrição válido.",
                ephemeral=True,
            )

        await interaction.response.defer(ephemeral=True)
        try:
            if isinstance(ticket_channel, discord.TextChannel):
                await ticket_channel.delete(
                    reason=f"Inscrição removida por {member} ({member.id})"
                )
            thread = guild.get_thread(thread_id) if thread_id is not None else None
            if thread is None and thread_id is not None:
                try:
                    fetched_thread = await guild.fetch_channel(thread_id)
                except discord.NotFound:
                    fetched_thread = None
                if isinstance(fetched_thread, discord.Thread):
                    thread = fetched_thread
            if thread is not None:
                await thread.delete(reason=f"Inscrição removida por {member} ({member.id})")
            await log_message.delete()
        except discord.HTTPException as error:
            print(f"[tickets] Não consegui remover a inscrição do campeonato: {error}")
            return await interaction.followup.send(
                "Ocorreu um erro ao remover a inscrição. Verifique as permissões do bot.",
                ephemeral=True,
            )

        await interaction.followup.send(
            "Inscrição removida e ticket apagado.", ephemeral=True
        )


class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.panel_task = None
        self.support_panel_task = None
        self.campeonato_panel_task = None
        self.campeonato_signup_panel_task = None
        self.campeonato_logs_task = None

    async def cog_load(self):
        self.bot.add_view(OpenView())
        self.bot.add_view(InstagramOpenView())
        self.bot.add_view(SupportView())
        self.bot.add_view(CampeonatoOpenView())
        self.bot.add_view(DeleteCampeonatoApplicationView())
        self.bot.add_view(CloseView())
        self.panel_task = asyncio.create_task(self.ensure_instagram_panel())
        self.support_panel_task = asyncio.create_task(self.ensure_support_panel())
        self.campeonato_panel_task = asyncio.create_task(self.ensure_campeonato_panel())
        self.campeonato_signup_panel_task = asyncio.create_task(
            self.ensure_campeonato_signup_panel()
        )
        self.campeonato_logs_task = asyncio.create_task(
            self.ensure_campeonato_application_logs()
        )

    async def cog_unload(self):
        if self.panel_task:
            self.panel_task.cancel()
        if self.support_panel_task:
            self.support_panel_task.cancel()
        if self.campeonato_panel_task:
            self.campeonato_panel_task.cancel()
        if self.campeonato_signup_panel_task:
            self.campeonato_signup_panel_task.cancel()
        if self.campeonato_logs_task:
            self.campeonato_logs_task.cancel()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return
        if not isinstance(message.channel, discord.TextChannel):
            return

        topic = message.channel.topic or ""
        parts = topic.split(":")
        if (
            len(parts) != 5
            or parts[:3] != ["ticket", str(message.author.id), "campeonato"]
            or parts[3] != "log"
        ):
            return

        thread = self.bot.get_channel(int(parts[4]))
        if thread is None:
            try:
                thread = await self.bot.fetch_channel(int(parts[4]))
            except discord.HTTPException as error:
                print(f"[tickets] Não consegui localizar o tópico da inscrição: {error}")
                return
        if not isinstance(thread, discord.Thread):
            print("[tickets] O tópico de acompanhamento da inscrição não é um thread válido.")
            return

        await copiar_mensagem_participante(message, thread)

    async def ensure_campeonato_application_logs(self):
        await self.bot.wait_until_ready()
        try:
            channel = self.bot.get_channel(EVENT_APPLICATION_CHANNEL_ID)
            if channel is None:
                channel = await self.bot.fetch_channel(EVENT_APPLICATION_CHANNEL_ID)
            if not isinstance(channel, discord.TextChannel):
                print("[tickets] EVENT_APPLICATION_CHANNEL_ID precisa ser um canal de texto.")
                return

            async for log_message in channel.history(limit=100):
                if (
                    log_message.author != self.bot.user
                    or not log_message.embeds
                    or log_message.embeds[0].title
                    != "Nova inscrição — Campeonato The Box"
                ):
                    continue

                embed = log_message.embeds[0].copy()
                participant_id = participante_id_da_inscricao(embed)
                ticket_value = campo_embed(embed, "Ticket")
                ticket_value = (
                    ticket_value[2:-1]
                    if ticket_value.startswith("<#") and ticket_value.endswith(">")
                    else ""
                )
                ticket_channel = None
                if ticket_value.isdecimal():
                    ticket_channel = self.bot.get_channel(int(ticket_value))
                    if ticket_channel is None:
                        try:
                            ticket_channel = await self.bot.fetch_channel(int(ticket_value))
                        except discord.NotFound:
                            ticket_channel = None

                if not isinstance(ticket_channel, discord.TextChannel):
                    await log_message.edit(view=DeleteCampeonatoApplicationView())
                    continue
                if participant_id is None:
                    topic_parts = (ticket_channel.topic or "").split(":")
                    if len(topic_parts) >= 3 and topic_parts[0] == "ticket":
                        participant_id = int(topic_parts[1]) if topic_parts[1].isdecimal() else None
                if participant_id is None:
                    print(f"[tickets] Não consegui identificar o participante em {log_message.id}.")
                    continue

                ticket_prefix = f"ticket:{participant_id}:campeonato"
                ticket_topic = ticket_channel.topic or ""
                if ticket_topic != ticket_prefix and not ticket_topic.startswith(
                    f"{ticket_prefix}:log:"
                ):
                    await log_message.edit(view=DeleteCampeonatoApplicationView())
                    continue

                thread_field = campo_embed(embed, "Acompanhamento")
                thread_value = (
                    thread_field[2:-1]
                    if thread_field.startswith("<#") and thread_field.endswith(">")
                    else ""
                )
                thread = None
                if thread_value.isdecimal():
                    candidate = self.bot.get_channel(int(thread_value))
                    if isinstance(candidate, discord.Thread):
                        thread = candidate
                if thread is None and ticket_channel.topic and ":log:" in ticket_channel.topic:
                    thread_id_value = ticket_channel.topic.rsplit(":log:", 1)[1]
                    if thread_id_value.isdecimal():
                        candidate = self.bot.get_channel(int(thread_id_value))
                        if candidate is None:
                            try:
                                candidate = await self.bot.fetch_channel(int(thread_id_value))
                            except discord.NotFound:
                                candidate = None
                        if isinstance(candidate, discord.Thread):
                            thread = candidate
                if thread is None:
                    thread = log_message.thread
                if thread is None:
                    thread = await log_message.create_thread(
                        name=f"Inscrição - {ticket_channel.name}"[:100],
                        auto_archive_duration=10080,
                    )

                has_thread_field = any(
                    field.name == "Acompanhamento" for field in embed.fields
                )
                if not has_thread_field:
                    async for ticket_message in ticket_channel.history(oldest_first=True):
                        if ticket_message.author.id == participant_id:
                            await copiar_mensagem_participante(ticket_message, thread)
                    embed.add_field(
                        name="Acompanhamento", value=thread.mention, inline=False
                    )

                await log_message.edit(
                    embed=embed,
                    view=DeleteCampeonatoApplicationView(),
                )
                if ticket_channel.topic != f"{ticket_prefix}:log:{thread.id}":
                    await ticket_channel.edit(topic=f"{ticket_prefix}:log:{thread.id}")
        except discord.Forbidden:
            print("[tickets] Sem permissão para atualizar os registros de inscrição do campeonato.")
        except discord.HTTPException as error:
            print(f"[tickets] Não consegui atualizar os registros de inscrição: {error}")

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
                if (
                    message.author == self.bot.user
                    and any(
                        embed.title == "🏆 CAMPEONATO THE BOX"
                        for embed in message.embeds
                    )
                ):
                    await message.edit(
                        embed=campeonato_panel_embed(),
                        view=None,
                    )
                    return
            await channel.send(
                embed=campeonato_panel_embed(),
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except discord.Forbidden:
            print("[tickets] Sem permissão para ler o histórico ou enviar o painel do campeonato.")
        except discord.HTTPException as error:
            print(f"[tickets] Não consegui criar/atualizar o painel do campeonato: {error}")

    async def ensure_campeonato_signup_panel(self):
        await self.bot.wait_until_ready()
        try:
            channel = self.bot.get_channel(EVENT_SIGNUP_CHANNEL_ID)
            if channel is None:
                channel = await self.bot.fetch_channel(EVENT_SIGNUP_CHANNEL_ID)
            if not isinstance(channel, discord.TextChannel):
                print("[tickets] EVENT_SIGNUP_CHANNEL_ID precisa ser um canal de texto.")
                return

            async for message in channel.history(limit=50):
                if message.author == self.bot.user and any(
                    possui_botao_campeonato(component)
                    for component in message.components
                ):
                    await message.edit(
                        content=None,
                        embed=campeonato_signup_embed(),
                        view=CampeonatoOpenView(),
                    )
                    return
            await channel.send(
                embed=campeonato_signup_embed(),
                view=CampeonatoOpenView(),
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except discord.Forbidden:
            print("[tickets] Sem permissão para ler o histórico ou enviar o painel de inscrição do campeonato.")
        except discord.HTTPException as error:
            print(f"[tickets] Não consegui criar/atualizar o painel de inscrição do campeonato: {error}")

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
