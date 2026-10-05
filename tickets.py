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
COUNTER_FILE = Path(__file__).parent / "ticket-counter.json"
# ===================================================

ID_OPEN = "ticket_open_denuncia"
ID_OPEN_INSTAGRAM = "ticket_open_instagram"
ID_OPEN_SUPPORT = "ticket_open_support"
ID_APPLY_STAFF = "ticket_apply_staff"
ID_CLOSE = "ticket_close"
COR = discord.Color.from_rgb(43, 45, 49)


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
    return discord.Embed(
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
    await interaction.followup.send(
        f"Sua solicitação foi criada: {channel.mention}", ephemeral=True
    )
    await send_log(
        guild,
        f"📩 Ticket de {ticket_type} **{channel.name}** aberto por {user.mention} ({user.id})",
    )


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


class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.panel_task = None
        self.support_panel_task = None

    async def cog_load(self):
        self.bot.add_view(OpenView())
        self.bot.add_view(InstagramOpenView())
        self.bot.add_view(SupportView())
        self.bot.add_view(CloseView())
        self.panel_task = asyncio.create_task(self.ensure_instagram_panel())
        self.support_panel_task = asyncio.create_task(self.ensure_support_panel())

    async def cog_unload(self):
        if self.panel_task:
            self.panel_task.cancel()
        if self.support_panel_task:
            self.support_panel_task.cancel()

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
                    await message.edit(embed=support_panel_embed(), view=SupportView())
                    return
            await channel.send(embed=support_panel_embed(), view=SupportView())
        except discord.Forbidden:
            print("[tickets] Sem permissão para ler o histórico ou enviar o painel de suporte.")
        except discord.HTTPException as error:
            print(f"[tickets] Não consegui criar/atualizar o painel de suporte: {error}")

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
        await interaction.channel.send(embed=embed, view=OpenView())
        await interaction.response.send_message("Painel enviado!", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))
