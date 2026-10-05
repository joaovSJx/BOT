import asyncio
import json
import os

import discord
from discord import app_commands
from discord.ext import commands


VERIFY_CHANNEL_ID = int(os.getenv("VERIFY_CHANNEL_ID", "1556670356595409018"))
GUIDE_CHANNEL_ID = int(os.getenv("GUIDE_CHANNEL_ID", "1556014650389438604"))
VERIFIED_ROLE_ID = int(os.getenv("VERIFIED_ROLE_ID", "1551012475707850792"))
VERIFY_LOG_CHANNEL_ID = int(os.getenv("VERIFY_LOG_CHANNEL_ID", "0"))
BANNER_URL = os.getenv("VERIFY_BANNER_URL", "")
ACCENT_COLOR = discord.Color.from_rgb(128, 128, 128)
MIN_AGE, MAX_AGE = 14, 49
GUIDE_CHANNELS = {
    "Avisos": 1548179013992714270,
    "Regras": 1548100800796950678,
    "Eventos": 1555742453791854722,
    "Suporte": 1548207347753689098,
    "Denúncias": 1548204770152423484,
    "Desmutar": 1553921363440439436,
    "SMS": 1553906082471223297,
    "Verificar": 1549904027167236266,
}


class VerifyModal(discord.ui.Modal, title="Verificação • Turquia"):
    def __init__(self, track_assignment):
        super().__init__()
        self.track_assignment = track_assignment
        self.age = discord.ui.Label(
            text="Idade",
            description=f"apenas número · entre {MIN_AGE} e {MAX_AGE} anos",
            component=discord.ui.TextInput(
                placeholder="18", min_length=2, max_length=2, required=True
            ),
        )
        self.calls = discord.ui.Label(
            text="Pretende participar de calls?",
            description="sim ou não",
            component=discord.ui.Select(
                placeholder="Sim ou Não",
                required=True,
                options=[
                    discord.SelectOption(label="Sim", value="sim"),
                    discord.SelectOption(label="Não", value="nao"),
                ],
            ),
        )
        self.old_family = discord.ui.Label(
            text="Já fez parte de família?",
            description="opcional · nome da família anterior (se sim)",
            component=discord.ui.TextInput(
                placeholder="nome da família anterior", max_length=50, required=False
            ),
        )
        self.referrer = discord.ui.Label(
            text="Veio por alguém?",
            description="opcional · quem te indicou",
            component=discord.ui.UserSelect(
                placeholder="Selecione quem indicou você",
                min_values=0,
                max_values=1,
                required=False,
            ),
        )
        for item in (self.age, self.calls, self.old_family, self.referrer):
            self.add_item(item)

    async def on_submit(self, interaction: discord.Interaction):
        age_raw = self.age.component.value.strip()
        if not age_raw.isdigit() or not MIN_AGE <= int(age_raw) <= MAX_AGE:
            return await interaction.response.send_message(
                f"❌ Idade inválida. Informe apenas números, entre {MIN_AGE} e {MAX_AGE} anos.",
                ephemeral=True,
            )

        guild = interaction.guild
        if guild is None or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message(
                "❌ Esta verificação só pode ser concluída dentro do servidor.",
                ephemeral=True,
            )

        age = int(age_raw)
        calls = self.calls.component.values[0] == "sim"
        old_family = self.old_family.component.value.strip() or None
        referrers = self.referrer.component.values
        referrer = referrers[0] if referrers else None

        if referrer and referrer.id == interaction.user.id:
            return await interaction.response.send_message(
                "❌ Você não pode indicar a si mesmo.", ephemeral=True
            )

        role = guild.get_role(VERIFIED_ROLE_ID)
        if role is None:
            return await interaction.response.send_message(
                "⚠️ Cargo de verificado não configurado. Avise a staff.", ephemeral=True
            )

        try:
            await interaction.user.add_roles(role, reason="Verificação concluída")
        except discord.HTTPException:
            return await interaction.response.send_message(
                "⚠️ Não consegui te dar o cargo. Avise a staff.", ephemeral=True
            )
        await self.track_assignment(guild.id, interaction.user.id)

        await interaction.response.send_message(
            f"✅ Verificação concluída! Seja bem-vindo(a), confira o <#{GUIDE_CHANNEL_ID}>.",
            ephemeral=True,
        )

        if VERIFY_LOG_CHANNEL_ID:
            log_channel = guild.get_channel(VERIFY_LOG_CHANNEL_ID)
            if log_channel:
                embed = discord.Embed(
                    title="Nova verificação",
                    colour=ACCENT_COLOR,
                    timestamp=discord.utils.utcnow(),
                )
                embed.set_thumbnail(url=interaction.user.display_avatar.url)
                embed.add_field(
                    name="Membro",
                    value=f"{interaction.user.mention} (`{interaction.user.id}`)",
                    inline=False,
                )
                embed.add_field(name="Idade", value=str(age))
                embed.add_field(name="Calls", value="Sim" if calls else "Não")
                embed.add_field(name="Família anterior", value=old_family or "—")
                embed.add_field(
                    name="Indicado por", value=referrer.mention if referrer else "—"
                )
                await log_channel.send(embed=embed)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        print(f"[verificação] Erro no modal: {error!r}")
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "⚠️ Ocorreu um erro. Tente novamente.", ephemeral=True
            )


class VerifyButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Verificar-se",
            style=discord.ButtonStyle.secondary,
            custom_id="verify_open",
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message(
                "❌ Este botão só pode ser usado dentro do servidor.", ephemeral=True
            )
        role = interaction.guild.get_role(VERIFIED_ROLE_ID)
        if role and role in interaction.user.roles:
            return await interaction.response.send_message(
                "✅ Você já está verificado!", ephemeral=True
            )
        verification = interaction.client.get_cog("Verification")
        await interaction.response.send_modal(
            VerifyModal(verification.track_assignment)
        )


class PanelView(discord.ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)
        container = discord.ui.Container(accent_colour=ACCENT_COLOR)

        if BANNER_URL:
            container.add_item(
                discord.ui.MediaGallery(discord.MediaGalleryItem(BANNER_URL))
            )

        container.add_item(
            discord.ui.Section(
                "Junte-se a The Box!",
                accessory=VerifyButton(),
            )
        )
        container.add_item(
            discord.ui.TextDisplay(
                "*Por medidas de segurança e organização, para acessar o nosso "
                "servidor é necessário passar pela verificação.*\n"
                "-# ↳ Sem a verificação, não será possível participar das conversas, "
                "eventos e sorteios da nossa família."
            )
        )
        self.add_item(container)


def guide_embed() -> discord.Embed:
    return discord.Embed(
        title="Guia do servidor",
        description=(
            "Utilize este guia para acessar rapidamente os canais e áreas disponíveis no servidor.\n\n"
            "Selecione abaixo o canal que deseja acessar e o bot direcionará você automaticamente "
            "para o local escolhido.\n\n"
            "Navegue de forma rápida, organizada e prática."
        ),
        colour=ACCENT_COLOR,
    )


class GuideSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="Selecione um canal para acessar",
            min_values=1,
            max_values=1,
            custom_id="guide_channel_select",
            options=[
                discord.SelectOption(label=name, value=str(channel_id))
                for name, channel_id in GUIDE_CHANNELS.items()
            ],
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.guild is None:
            return await interaction.response.send_message(
                "Este menu só pode ser usado dentro do servidor.", ephemeral=True
            )

        channel_id = int(self.values[0])
        channel = interaction.guild.get_channel(channel_id)
        if channel is None:
            return await interaction.response.send_message(
                "Não encontrei esse canal. Avise a equipe do servidor.", ephemeral=True
            )

        await interaction.response.send_message(
            f"Canal selecionado: {channel.mention}\n"
            f"[Abrir canal](https://discord.com/channels/{interaction.guild.id}/{channel_id})",
            ephemeral=True,
        )


class GuideView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(GuideSelect())


def possui_botao_verificacao(component):
    if getattr(component, "custom_id", None) == "verify_open":
        return True
    accessory = getattr(component, "accessory", None)
    if accessory is not None and possui_botao_verificacao(accessory):
        return True
    return any(
        possui_botao_verificacao(child)
        for child in getattr(component, "children", ())
    )


def possui_menu_guia(component):
    if getattr(component, "custom_id", None) == "guide_channel_select":
        return True
    return any(
        possui_menu_guia(child)
        for child in getattr(component, "children", ())
    )


class Verification(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.panel_task = None
        self.guide_task = None
        self.assignment_path = os.path.join(
            os.path.dirname(__file__), "verified-role-assignments.json"
        )
        self.assignment_lock = asyncio.Lock()
        self.assignments = self.load_assignments()

    def load_assignments(self):
        try:
            with open(self.assignment_path, encoding="utf-8") as assignments_file:
                data = json.load(assignments_file)
            return {
                int(guild_id): {int(member_id) for member_id in member_ids}
                for guild_id, member_ids in data.items()
            }
        except FileNotFoundError:
            return {}
        except (OSError, ValueError, TypeError, AttributeError) as error:
            print(f"[verificação] Não consegui carregar registros de cargos: {error}")
            return {}

    def save_assignments(self):
        temporary_path = f"{self.assignment_path}.tmp"
        with open(temporary_path, "w", encoding="utf-8") as assignments_file:
            json.dump(
                {
                    str(guild_id): sorted(member_ids)
                    for guild_id, member_ids in self.assignments.items()
                },
                assignments_file,
            )
        os.replace(temporary_path, self.assignment_path)

    async def track_assignment(self, guild_id: int, member_id: int):
        async with self.assignment_lock:
            members = self.assignments.setdefault(guild_id, set())
            already_tracked = member_id in members
            members.add(member_id)
            try:
                self.save_assignments()
            except OSError as error:
                if not already_tracked:
                    members.discard(member_id)
                print(f"[verificação] Não consegui salvar registro de cargo: {error}")

    async def cog_load(self):
        self.bot.add_view(PanelView())
        self.bot.add_view(GuideView())
        self.panel_task = asyncio.create_task(self.ensure_panel())
        self.guide_task = asyncio.create_task(self.ensure_guide_panel())

    async def cog_unload(self):
        if self.panel_task:
            self.panel_task.cancel()
        if self.guide_task:
            self.guide_task.cancel()

    async def ensure_panel(self):
        await self.bot.wait_until_ready()
        try:
            channel = self.bot.get_channel(VERIFY_CHANNEL_ID)
            if channel is None:
                channel = await self.bot.fetch_channel(VERIFY_CHANNEL_ID)
            if not isinstance(channel, discord.TextChannel):
                print("[verificação] VERIFY_CHANNEL_ID precisa ser um canal de texto.")
                return

            async for message in channel.history(limit=50):
                if message.author == self.bot.user and any(
                    possui_botao_verificacao(component)
                    for component in message.components
                ):
                    await message.edit(view=PanelView())
                    return
            await channel.send(view=PanelView())
        except discord.Forbidden:
            print("[verificação] Sem permissão para ler o histórico ou enviar o painel.")
        except discord.HTTPException as error:
            print(f"[verificação] Não consegui criar/atualizar o painel: {error}")

    async def ensure_guide_panel(self):
        await self.bot.wait_until_ready()
        try:
            channel = self.bot.get_channel(GUIDE_CHANNEL_ID)
            if channel is None:
                channel = await self.bot.fetch_channel(GUIDE_CHANNEL_ID)
            if not isinstance(channel, discord.TextChannel):
                print("[guia] GUIDE_CHANNEL_ID precisa ser um canal de texto.")
                return

            async for message in channel.history(limit=50):
                if message.author == self.bot.user and any(
                    possui_menu_guia(component)
                    for component in message.components
                ):
                    await message.edit(embed=guide_embed(), view=GuideView())
                    return
            await channel.send(embed=guide_embed(), view=GuideView())
        except discord.Forbidden:
            print("[guia] Sem permissão para ler o histórico ou enviar o painel.")
        except discord.HTTPException as error:
            print(f"[guia] Não consegui criar/atualizar o painel: {error}")

    @app_commands.command(
        name="setup_verificacao",
        description="Configura as permissões: novatos só veem verificação e guia.",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def setup_verificacao(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        if guild is None:
            return await interaction.followup.send(
                "❌ Este comando só pode ser usado em um servidor.", ephemeral=True
            )

        verified = guild.get_role(VERIFIED_ROLE_ID)
        if verified is None:
            return await interaction.followup.send(
                "❌ Configure VERIFIED_ROLE_ID primeiro.", ephemeral=True
            )

        everyone_permissions = guild.default_role.permissions
        everyone_permissions.update(view_channel=False)
        await guild.default_role.edit(permissions=everyone_permissions)

        verified_permissions = verified.permissions
        verified_permissions.update(view_channel=True)
        await verified.edit(permissions=verified_permissions)

        for channel_id in (VERIFY_CHANNEL_ID, GUIDE_CHANNEL_ID):
            channel = guild.get_channel(channel_id)
            if channel:
                await channel.set_permissions(
                    guild.default_role,
                    view_channel=True,
                    read_message_history=True,
                    send_messages=False,
                    add_reactions=False,
                )

        await interaction.followup.send(
            "✅ Permissões configuradas.", ephemeral=True
        )

    @app_commands.command(
        name="setar",
        description="Atribui o cargo de verificado aos membros que têm outro cargo.",
    )
    @app_commands.describe(cargo="Cargo que os membros precisam ter para serem verificados.")
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def setar(self, interaction: discord.Interaction, cargo: discord.Role):
        await interaction.response.defer(ephemeral=True, thinking=True)
        guild = interaction.guild
        if guild is None:
            return await interaction.followup.send(
                "❌ Este comando só pode ser usado em um servidor.", ephemeral=True
            )

        role = guild.get_role(VERIFIED_ROLE_ID)
        if role is None:
            return await interaction.followup.send(
                f"❌ Não encontrei o cargo configurado ({VERIFIED_ROLE_ID}).",
                ephemeral=True,
            )
        if not role.is_assignable():
            return await interaction.followup.send(
                "❌ Não consigo atribuir esse cargo. Confira se meu cargo está acima dele na hierarquia.",
                ephemeral=True,
            )

        added = 0
        already_had = 0
        failed = 0
        matched = 0
        try:
            async for member in guild.fetch_members(limit=None):
                if cargo not in member.roles:
                    continue
                matched += 1
                if role in member.roles:
                    already_had += 1
                    continue
                try:
                    await member.add_roles(
                        role, reason=f"Cargo de verificado atribuído por {interaction.user} via /setar"
                    )
                    added += 1
                    await self.track_assignment(guild.id, member.id)
                except discord.HTTPException:
                    failed += 1
        except discord.Forbidden:
            return await interaction.followup.send(
                "❌ Não consegui listar os membros. Ative o Server Members Intent no Developer Portal e confira as permissões do bot.",
                ephemeral=True,
            )
        except discord.HTTPException as error:
            print(f"[verificação] Erro ao listar membros para /setar: {error}")
            return await interaction.followup.send(
                "⚠️ O Discord não permitiu listar todos os membros. Tente novamente mais tarde.",
                ephemeral=True,
            )

        await interaction.followup.send(
            f"✅ `/setar` concluído para **{matched}** membros com o cargo {cargo.mention}. "
            f"Cargo de verificado atribuído a **{added}** membros; "
            f"**{already_had}** já tinham o cargo; **{failed}** falharam.",
            ephemeral=True,
        )

    @app_commands.command(
        name="reset",
        description="Remove o cargo de verificado atribuído pelo bot.",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def reset(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        guild = interaction.guild
        if guild is None:
            return await interaction.followup.send(
                "❌ Este comando só pode ser usado em um servidor.", ephemeral=True
            )

        role = guild.get_role(VERIFIED_ROLE_ID)
        if role is None:
            return await interaction.followup.send(
                "❌ Não encontrei o cargo de verificado configurado.", ephemeral=True
            )
        if not role.is_assignable():
            return await interaction.followup.send(
                "❌ Não consigo remover esse cargo. Confira a hierarquia do bot.",
                ephemeral=True,
            )

        removed = 0
        unchanged = 0
        failed = 0
        completed = set()
        async with self.assignment_lock:
            member_ids = self.assignments.get(guild.id, set()).copy()
            for member_id in member_ids:
                try:
                    member = await guild.fetch_member(member_id)
                except discord.NotFound:
                    completed.add(member_id)
                    continue
                except discord.HTTPException:
                    failed += 1
                    continue

                if role not in member.roles:
                    unchanged += 1
                    completed.add(member_id)
                    continue
                try:
                    await member.remove_roles(
                        role, reason=f"Reset de verificações por {interaction.user}"
                    )
                    removed += 1
                    completed.add(member_id)
                except discord.HTTPException:
                    failed += 1

            remaining = self.assignments.get(guild.id, set()) - completed
            if remaining:
                self.assignments[guild.id] = remaining
            else:
                self.assignments.pop(guild.id, None)
            try:
                self.save_assignments()
            except OSError as error:
                print(f"[verificação] Não consegui atualizar registros de cargos: {error}")
                self.assignments[guild.id] = member_ids
                failed += len(completed)

        await interaction.followup.send(
            f"✅ `/reset` concluído: **{removed}** cargos removidos, "
            f"**{unchanged}** membros já não tinham o cargo e **{failed}** falharam. "
            "Só foram considerados membros registrados pelo bot; concessões anteriores "
            "à ativação do registro não podem ser identificadas.",
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Verification(bot))