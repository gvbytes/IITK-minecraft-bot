import sys
import os
import ssl
import certifi
import asyncio
from typing import Optional
from aiohttp import web

os.environ["SSL_CERT_FILE"] = certifi.where()
ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())

import discord
from discord.ext import commands

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!iitk", intents=intents, help_command=None)

token = os.environ.get("DISCORD_BOT_TOKEN", "").strip() or (sys.argv[1].strip() if len(sys.argv) > 1 else "")
serverIp = os.environ.get("MINECRAFT_SERVER_IP", "").strip() or (sys.argv[2].strip() if len(sys.argv) > 2 else "")
port = int(os.environ.get("PORT", 10000))
ROLES_SPEC = [
    {"name": "👑 Server Admin / OP", "color": discord.Color.from_rgb(231, 76, 60), "hoist": True, "mentionable": True},
    {"name": "⚙️ SysAdmin / Host", "color": discord.Color.from_rgb(155, 89, 182), "hoist": True, "mentionable": True},
    {"name": "🛡️ Moderator", "color": discord.Color.from_rgb(46, 204, 113), "hoist": True, "mentionable": True},
    {"name": "🎓 Verified IITKian", "color": discord.Color.from_rgb(33, 150, 243), "hoist": True, "mentionable": False},
    {"name": "⛏️ SMP Whitelisted", "color": discord.Color.from_rgb(26, 188, 156), "hoist": True, "mentionable": True},
    {"name": "⚡ Redstone Engineer", "color": discord.Color.from_rgb(230, 126, 34), "hoist": False, "mentionable": False},
    {"name": "🎨 Master Builder", "color": discord.Color.from_rgb(241, 196, 15), "hoist": False, "mentionable": False},
    {"name": "⚔️ PvP / Tourneys", "color": discord.Color.from_rgb(233, 30, 99), "hoist": False, "mentionable": False},
    {"name": "📢 Event Pings", "color": discord.Color.from_rgb(255, 171, 0), "hoist": False, "mentionable": True},
    {"name": "⚠️ Server Restarts", "color": discord.Color.from_rgb(255, 87, 34), "hoist": False, "mentionable": True},
    {"name": "💻 Java Edition", "color": discord.Color.from_rgb(52, 152, 219), "hoist": False, "mentionable": False},
    {"name": "📱 Bedrock / PE", "color": discord.Color.from_rgb(0, 184, 217), "hoist": False, "mentionable": False},
    {"name": "🌐 Guest / Visitor", "color": discord.Color.from_rgb(149, 165, 166), "hoist": False, "mentionable": False}
]

HALL_ROLES = [
    "🏰 Hall 1", "🏰 Hall 2", "🏰 Hall 3", "🏰 Hall 4", "🏰 Hall 5",
    "🏰 Hall 6", "🏰 Hall 7", "🏰 Hall 8", "🏰 Hall 9", "🏰 Hall 10",
    "🏰 Hall 11", "🏰 Hall 12", "🏰 Hall 13", "🏰 Hall 14", "🏰 GH / Towers"
]

STRUCTURE = {
    "📌 ── WELCOME & INFO ──": {
        "text": [
            ("📜・rules-and-conduct", "Server rules and code of conduct.", True, 0),
            ("🌐・server-ip-and-guide", "Connection address, ports, and info.", True, 0),
            ("🎭・pick-your-roles", "Self-assign roles and notification pings.", True, 0),
            ("📢・announcements", "Server news, updates, and maintenance.", True, 0),
            ("📋・whitelist-requests", "Apply for server whitelist.", False, 10),
            ("👋・welcome-lobby", "Welcome lobby for new players.", False, 3)
        ],
        "voice": []
    },
    "⛏️ ── IITK MINECRAFT SMP ──": {
        "text": [
            ("💬・in-game-chat", "Synced with in-game chat.", False, 0),
            ("🗺️・dynmap-and-coords", "Key coordinates and map links.", False, 0),
            ("🏰・hall-factions", "Hostel bases and settlements.", False, 0),
            ("💰・campus-marketplace", "Trade items and materials.", False, 5),
            ("📸・build-showcase", "Screenshots and builds.", False, 5),
            ("⚡・redstone-and-farms", "Farms and redstone tech.", False, 0),
            ("🏆・events-and-tourneys", "Tournaments and events.", False, 0)
        ],
        "voice": []
    },
    "💬 ── CAMPUS HANGOUT ──": {
        "text": [
            ("💬・general-chat", "General discussions.", False, 3),
            ("🎮・other-games", "Other games and coop.", False, 0),
            ("🤖・bot-commands", "Bot commands channel.", False, 5),
            ("💡・suggestions-and-polls", "Suggestions and voting.", False, 0)
        ],
        "voice": []
    },
    "🆘 ── SUPPORT & TICKETS ──": {
        "text": [
            ("🎫・create-a-ticket", "Support tickets and inquiries.", True, 0)
        ],
        "voice": []
    },
    "🔊 ── VOICE CHANNELS ──": {
        "text": [],
        "voice": [
            ("🔊・Lobby VC", 0),
            ("⛏️・Mining & Grinding", 2),
            ("🏰・Hall Squad", 4),
            ("⚡・Redstone Lab (Stream)", 6),
            ("🎵・Music & Chill", 0),
            ("➕・Create Temp VC", 0)
        ]
    },
    "🛡️ ── STAFF COMMAND ──": {
        "staff_only": True,
        "text": [
            ("🛡️・staff-chat", "Staff discussion.", False, 0),
            ("📋・whitelist-review", "Whitelist review queue.", False, 0),
            ("📋・console-and-logs", "Console and server logs.", True, 0)
        ],
        "voice": [("🔊・Staff Meeting Room", 0)]
    }
}

class HallSelect(discord.ui.Select):
    def __init__(self):
        opts = [discord.SelectOption(label=h, description=f"join {h}", emoji="🏰") for h in HALL_ROLES]
        super().__init__(placeholder="select your hostel / hall...", min_values=0, max_values=1, options=opts, custom_id="iitk_mc_hall_select")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user
        for h in HALL_ROLES:
            r = discord.utils.get(guild.roles, name=h)
            if r and r in member.roles:
                await member.remove_roles(r)
        if len(self.values) == 0:
            await interaction.response.send_message("cleared hostel role.", ephemeral=True)
            return
        chosen = self.values[0]
        role = discord.utils.get(guild.roles, name=chosen)
        if role:
            await member.add_roles(role)
            await interaction.response.send_message(f"assigned {chosen}.", ephemeral=True)
        else:
            await interaction.response.send_message("role not found.", ephemeral=True)

class RolesView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(HallSelect())

    async def toggle(self, interaction: discord.Interaction, role_name: str):
        guild = interaction.guild
        member = interaction.user
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            await interaction.response.send_message(f"role {role_name} not found.", ephemeral=True)
            return
        if role in member.roles:
            await member.remove_roles(role)
            await interaction.response.send_message(f"removed {role_name}.", ephemeral=True)
        else:
            await member.add_roles(role)
            await interaction.response.send_message(f"added {role_name}.", ephemeral=True)

    @discord.ui.button(label="Java Edition", style=discord.ButtonStyle.primary, emoji="💻", custom_id="role_btn_java")
    async def btn_java(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle(interaction, "💻 Java Edition")

    @discord.ui.button(label="Bedrock / PE", style=discord.ButtonStyle.primary, emoji="📱", custom_id="role_btn_bedrock")
    async def btn_bedrock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle(interaction, "📱 Bedrock / PE")

    @discord.ui.button(label="Redstone Tech", style=discord.ButtonStyle.secondary, emoji="⚡", custom_id="role_btn_redstone")
    async def btn_redstone(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle(interaction, "⚡ Redstone Engineer")

    @discord.ui.button(label="Master Builder", style=discord.ButtonStyle.secondary, emoji="🎨", custom_id="role_btn_builder")
    async def btn_builder(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle(interaction, "🎨 Master Builder")

    @discord.ui.button(label="Event Pings", style=discord.ButtonStyle.success, emoji="📢", custom_id="role_btn_events")
    async def btn_events(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle(interaction, "📢 Event Pings")

    @discord.ui.button(label="Server Restarts", style=discord.ButtonStyle.danger, emoji="⚠️", custom_id="role_btn_restarts")
    async def btn_restarts(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle(interaction, "⚠️ Server Restarts")

class WhitelistModal(discord.ui.Modal, title="whitelist application"):
    ign = discord.ui.TextInput(label="Minecraft IGN", placeholder="Steve_IITK", required=True, min_length=3, max_length=24)
    edition = discord.ui.TextInput(label="Edition", placeholder="Java or Bedrock", required=True, max_length=10)
    roll_no = discord.ui.TextInput(label="IITK Roll Number", placeholder="210456", required=True, min_length=5, max_length=12)
    hostel = discord.ui.TextInput(label="Hostel / Hall", placeholder="Hall 3", required=False, max_length=20)

    # submit whitelist application form
    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        revCh = discord.utils.get(guild.text_channels, name="📋・whitelist-review")
        if not revCh:
            revCh = discord.utils.get(guild.text_channels, name="📋・whitelist-requests")
        emb = discord.Embed(title="new whitelist application", color=discord.Color.from_rgb(26, 188, 156), timestamp=discord.utils.utcnow())
        emb.set_thumbnail(url=interaction.user.display_avatar.url)
        emb.add_field(name="Discord User", value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=False)
        emb.add_field(name="Minecraft IGN", value=f"`{self.ign.value.strip()}`", inline=True)
        emb.add_field(name="Edition", value=f"`{self.edition.value.strip().capitalize()}`", inline=True)
        emb.add_field(name="Roll Number", value=f"`{self.roll_no.value.strip()}`", inline=True)
        emb.add_field(name="Hostel", value=f"`{self.hostel.value.strip() or 'N/A'}`", inline=True)
        view = WhitelistApprovalView(applicant_id=interaction.user.id, ign=self.ign.value.strip())
        if revCh:
            await revCh.send(embed=emb, view=view)
        await interaction.response.send_message(f"application submitted for `{self.ign.value.strip()}`.", ephemeral=True)

class WhitelistApprovalView(discord.ui.View):
    def __init__(self, applicant_id: Optional[int] = None, ign: Optional[str] = None):
        super().__init__(timeout=None)
        self.applicant_id = applicant_id
        self.ign = ign

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success, emoji="✅", custom_id="wl_approve")
    async def on_approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        staff = any(r.name in ["👑 Server Admin / OP", "🛡️ Moderator", "⚙️ SysAdmin / Host"] for r in interaction.user.roles)
        if not (staff or interaction.user.guild_permissions.administrator):
            await interaction.response.send_message("staff only.", ephemeral=True)
            return
        member = guild.get_member(self.applicant_id) if self.applicant_id else None
        if member:
            wlRole = discord.utils.get(guild.roles, name="⛏️ SMP Whitelisted")
            vRole = discord.utils.get(guild.roles, name="🎓 Verified IITKian")
            if wlRole:
                await member.add_roles(wlRole)
            if vRole:
                await member.add_roles(vRole)
            try:
                await member.send(f"whitelisted as `{self.ign}`.")
            except Exception:
                pass
        for item in self.children:
            item.disabled = True
        emb = interaction.message.embeds[0]
        emb.color = discord.Color.green()
        emb.title = f"approved by {interaction.user.display_name}"
        await interaction.message.edit(embed=emb, view=self)
        await interaction.response.send_message(f"approved `{self.ign}`.", ephemeral=True)

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger, emoji="❌", custom_id="wl_reject")
    async def on_reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff = any(r.name in ["👑 Server Admin / OP", "🛡️ Moderator", "⚙️ SysAdmin / Host"] for r in interaction.user.roles)
        if not (staff or interaction.user.guild_permissions.administrator):
            await interaction.response.send_message("staff only.", ephemeral=True)
            return
        for item in self.children:
            item.disabled = True
        emb = interaction.message.embeds[0]
        emb.color = discord.Color.red()
        emb.title = f"rejected by {interaction.user.display_name}"
        await interaction.message.edit(embed=emb, view=self)
        await interaction.response.send_message(f"rejected `{self.ign}`.", ephemeral=True)

class WhitelistLandingView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Apply for Whitelist", style=discord.ButtonStyle.success, emoji="📝", custom_id="open_wl_modal")
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(WhitelistModal())

class TicketLauncher(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Report Grief", style=discord.ButtonStyle.danger, emoji="🚨", custom_id="ticket_grief")
    async def btn_grief(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.mk_ticket(interaction, "grief-report")

    @discord.ui.button(label="Bug or Lag", style=discord.ButtonStyle.secondary, emoji="🐛", custom_id="ticket_bug")
    async def btn_bug(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.mk_ticket(interaction, "bug-report")

    @discord.ui.button(label="General Help", style=discord.ButtonStyle.primary, emoji="❓", custom_id="ticket_general")
    async def btn_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.mk_ticket(interaction, "general-help")

    # create a private thread for support ticket
    async def mk_ticket(self, interaction: discord.Interaction, cat: str):
        channel = interaction.channel
        user = interaction.user
        t_name = f"ticket-{user.name[:10]}-{cat}"
        try:
            is_priv = discord.ChannelType.private_thread if interaction.guild.features and "PRIVATE_THREADS" in interaction.guild.features else discord.ChannelType.public_thread
            thread = await channel.create_thread(name=t_name, type=is_priv, auto_archive_duration=1440, reason=f"ticket by {user}")
            await thread.add_user(user)
            modRole = discord.utils.get(interaction.guild.roles, name="🛡️ Moderator")
            modMention = modRole.mention if modRole else "staff"
            desc = f"hi {user.mention}, explain your issue below.\ninclude ign, coords, or screenshots if relevant.\n{modMention} will help shortly."
            emb = discord.Embed(title=f"support: {cat}", description=desc, color=discord.Color.from_rgb(231, 76, 60))
            await thread.send(embed=emb)
            await interaction.response.send_message(f"ticket created in {thread.mention}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"failed to create ticket: {e}", ephemeral=True)

@bot.tree.command(name="help", description="Show server guide and commands")
async def cmd_slash_help(interaction: discord.Interaction):
    emb = discord.Embed(title="server guide & commands", color=discord.Color.from_rgb(33, 150, 243))
    emb.add_field(name="getting started", value="• roles: <#pick-your-roles>\n• whitelist: <#whitelist-requests>\n• support: <#create-a-ticket>", inline=False)
    emb.add_field(name="commands", value="• `/ip` or `!iitk ip` - server address\n• `/coords` or `!iitk coords` - key coordinates\n• `/rules` or `!iitk rules` - rules summary\n• `/ping` or `!iitk ping` - bot latency\n• `/whitelist_list` - whitelisted players\n• `/help` - this guide", inline=False)
    emb.add_field(name="staff", value="• `/whitelist_add <user> <ign>` - add player\n• `/whitelist_export` - export commands and json", inline=False)
    await interaction.response.send_message(embed=emb)

@bot.command(name="help")
async def cmd_text_help(ctx):
    emb = discord.Embed(title="server guide & commands", color=discord.Color.from_rgb(33, 150, 243))
    emb.add_field(name="getting started", value="• roles: #pick-your-roles\n• whitelist: #whitelist-requests\n• support: #create-a-ticket", inline=False)
    emb.add_field(name="commands", value="• `!iitk ip` - server address\n• `!iitk coords` - key coordinates\n• `!iitk rules` - rules summary\n• `!iitk ping` - bot latency\n• `!iitk help` - this guide", inline=False)
    await ctx.send(embed=emb)

@bot.tree.command(name="ip", description="Get server connection details")
async def cmd_slash_ip(interaction: discord.Interaction):
    ip_str = serverIp if serverIp else "Campus LAN IP (172.x.x.x) or Playit tunnel"
    emb = discord.Embed(title="server connection info", color=discord.Color.from_rgb(46, 204, 113))
    emb.add_field(name="Java Edition", value=f"Address: `{ip_str}`\nPort: `25565`\nVersion: `1.20.x / 1.21.x`", inline=False)
    emb.add_field(name="Bedrock / PE", value=f"Address: `{ip_str}`\nPort: `19132`", inline=False)
    emb.add_field(name="Campus Network", value="Direct connection on hostel wifi/lan. Check <#announcements> for tunnel links.", inline=False)
    await interaction.response.send_message(embed=emb)

@bot.command(name="ip")
async def cmd_text_ip(ctx):
    ip_str = serverIp if serverIp else "Campus LAN IP (172.x.x.x) or Playit tunnel"
    emb = discord.Embed(title="server connection info", color=discord.Color.from_rgb(46, 204, 113))
    emb.add_field(name="Java Edition", value=f"Address: `{ip_str}`\nPort: `25565`\nVersion: `1.20.x / 1.21.x`", inline=False)
    emb.add_field(name="Bedrock / PE", value=f"Address: `{ip_str}`\nPort: `19132`", inline=False)
    await ctx.send(embed=emb)

@bot.tree.command(name="coords", description="View landmark coordinates")
async def cmd_slash_coords(interaction: discord.Interaction):
    emb = discord.Embed(title="coordinates", color=discord.Color.from_rgb(241, 196, 15))
    emb.add_field(name="Spawn", value="`X: 0, Y: 70, Z: 0`", inline=True)
    emb.add_field(name="Nether Hub", value="`X: 0, Y: 120, Z: 0`", inline=True)
    emb.add_field(name="Marketplace", value="check <#campus-marketplace>", inline=True)
    emb.add_field(name="End Portal", value="check <#dynmap-and-coords>", inline=True)
    emb.add_field(name="Halls", value="check <#hall-factions>", inline=True)
    await interaction.response.send_message(embed=emb)

@bot.command(name="coords")
async def cmd_text_coords(ctx):
    emb = discord.Embed(title="coordinates", color=discord.Color.from_rgb(241, 196, 15))
    emb.add_field(name="Spawn", value="`X: 0, Y: 70, Z: 0`", inline=True)
    emb.add_field(name="Nether Hub", value="`X: 0, Y: 120, Z: 0`", inline=True)
    emb.add_field(name="Marketplace", value="check #campus-marketplace", inline=True)
    await ctx.send(embed=emb)

@bot.tree.command(name="rules", description="Quick overview of server rules")
async def cmd_slash_rules(interaction: discord.Interaction):
    emb = discord.Embed(title="server rules", description="1. No griefing or stealing (CoreProtect logged).\n2. No hacked clients or x-ray.\n3. Fair combat and no combat logging.\n4. Campus honor code.\n5. Farms need an accessible off-switch.\n\nFull details in <#rules-and-conduct>.", color=discord.Color.from_rgb(33, 150, 243))
    await interaction.response.send_message(embed=emb)

@bot.command(name="rules")
async def cmd_text_rules(ctx):
    await ctx.send("rules summary in `#rules-and-conduct`.")

@bot.tree.command(name="ping", description="Check bot latency")
async def cmd_slash_ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"pong: `{latency}ms`")

@bot.command(name="ping")
async def cmd_text_ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"pong: `{latency}ms`")

@bot.tree.command(name="whitelist_add", description="Staff: Manually whitelist a player")
async def cmd_slash_whitelist_add(interaction: discord.Interaction, member: discord.Member, ign: str):
    staff = any(r.name in ["👑 Server Admin / OP", "🛡️ Moderator", "⚙️ SysAdmin / Host"] for r in interaction.user.roles)
    if not (staff or interaction.user.guild_permissions.administrator):
        await interaction.response.send_message("staff only.", ephemeral=True)
        return
    wlRole = discord.utils.get(interaction.guild.roles, name="⛏️ SMP Whitelisted")
    vRole = discord.utils.get(interaction.guild.roles, name="🎓 Verified IITKian")
    if wlRole:
        await member.add_roles(wlRole)
    if vRole:
        await member.add_roles(vRole)
    try:
        await member.send(f"whitelisted on IITK Minecraft as `{ign}`. check #server-ip-and-guide for connection details.")
    except Exception:
        pass
    saveWl(ign=ign, uid=member.id)
    await interaction.response.send_message(f"whitelisted {member.mention} as `{ign}`.")


@bot.event
async def on_ready():
    print(f"bot connected as {bot.user} (id: {bot.user.id})", flush=True)
    bot.add_view(RolesView())
    bot.add_view(WhitelistLandingView())
    bot.add_view(WhitelistApprovalView())
    bot.add_view(TicketLauncher())
    try:
        synced = await bot.tree.sync()
        print(f"synced {len(synced)} commands", flush=True)
    except Exception as e:
        print(f"sync error: {e}", flush=True)
    for guild in bot.guilds:
        await initSrv(guild)
    print("server setup done", flush=True)

# create default roles, categories, and channels
async def initSrv(guild: discord.Guild):
    everyone = guild.default_role
    for role_info in reversed(ROLES_SPEC):
        existing = discord.utils.get(guild.roles, name=role_info["name"])
        if not existing:
            try:
                await guild.create_role(name=role_info["name"], color=role_info["color"], hoist=role_info["hoist"], mentionable=role_info["mentionable"])
            except Exception:
                pass
    for hall in HALL_ROLES:
        existing = discord.utils.get(guild.roles, name=hall)
        if not existing:
            try:
                await guild.create_role(name=hall, color=discord.Color.from_rgb(120, 144, 156), hoist=False)
            except Exception:
                pass
    admin_role = discord.utils.get(guild.roles, name="👑 Server Admin / OP")
    mod_role = discord.utils.get(guild.roles, name="🛡️ Moderator")
    for cat_name, cat_data in STRUCTURE.items():
        is_staff_only = cat_data.get("staff_only", False)
        cat_overwrites = {everyone: discord.PermissionOverwrite(read_messages=True, connect=True)}
        if is_staff_only:
            cat_overwrites[everyone] = discord.PermissionOverwrite(read_messages=False, connect=False)
            if admin_role:
                cat_overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, connect=True)
            if mod_role:
                cat_overwrites[mod_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, connect=True)
        existing_cat = discord.utils.get(guild.categories, name=cat_name)
        if not existing_cat:
            category = await guild.create_category(cat_name, overwrites=cat_overwrites)
        else:
            category = existing_cat
            await category.edit(overwrites=cat_overwrites)
        for ch_tuple in cat_data.get("text", []):
            ch_name, ch_topic, is_readonly, slowmode = ch_tuple
            existing_ch = discord.utils.get(guild.text_channels, name=ch_name)
            ch_overwrites = {everyone: discord.PermissionOverwrite(read_messages=True, send_messages=False if is_readonly else True, create_public_threads=False if is_readonly else True, add_reactions=True)}
            if is_readonly:
                if admin_role:
                    ch_overwrites[admin_role] = discord.PermissionOverwrite(send_messages=True)
                if mod_role:
                    ch_overwrites[mod_role] = discord.PermissionOverwrite(send_messages=True)
            if not existing_ch:
                await category.create_text_channel(name=ch_name, topic=ch_topic, overwrites=ch_overwrites, slowmode_delay=slowmode)
            else:
                await existing_ch.edit(category=category, topic=ch_topic, slowmode_delay=slowmode)
                if is_readonly:
                    await existing_ch.set_permissions(everyone, send_messages=False)
        for vc_name, limit in cat_data.get("voice", []):
            existing_vc = discord.utils.get(guild.voice_channels, name=vc_name)
            if not existing_vc:
                await category.create_voice_channel(name=vc_name, user_limit=limit or 0)
            else:
                await existing_vc.edit(category=category, user_limit=limit or 0)
    for old_name in ["🏰・Hall Squad 1", "🏰・Hall Squad 2"]:
        old_vc = discord.utils.get(guild.voice_channels, name=old_name)
        if old_vc:
            try:
                await old_vc.delete()
            except Exception:
                pass
    stats_cat = discord.utils.get(guild.categories, name="📊 ── SERVER STATS ──")
    if stats_cat:
        try:
            for ch in stats_cat.channels:
                await ch.delete()
            await stats_cat.delete()
        except Exception:
            pass
    await initPanels(guild)

# post panel embed if bot has not already sent one
async def postP(ch: Optional[discord.TextChannel], emb: discord.Embed, view: Optional[discord.ui.View] = None):
    if not ch:
        return
    try:
        async for m in ch.history(limit=5):
            if m.author == bot.user:
                return
        await ch.send(embed=emb, view=view)
    except discord.Forbidden:
        pass

# setup info, rules, roles, and ticket panels
async def initPanels(guild: discord.Guild):
    # rules panel
    r_emb = discord.Embed(title="server rules & guidelines", description="rules and fair play guidelines for the campus server.", color=discord.Color.from_rgb(33, 150, 243))
    r_emb.add_field(name="1. Griefing & Theft", value="Stealing or breaking others builds is not allowed. CoreProtect logs all actions.", inline=False)
    r_emb.add_field(name="2. Fair Play", value="No hacked clients, baritone, or x-ray packs.", inline=False)
    r_emb.add_field(name="3. Campus Code", value="Keep discussions civil. No harassment or toxic behavior.", inline=False)
    r_emb.add_field(name="4. Farms & Tech", value="Large farms must have an accessible off-switch.", inline=False)
    await postP(discord.utils.get(guild.text_channels, name="📜・rules-and-conduct"), r_emb)
    # guide panel
    ip_str = serverIp if serverIp else "Campus LAN IP (172.x.x.x) or Playit tunnel"
    g_emb = discord.Embed(title="connection guide", description="how to connect to the server from campus hostels or remote.", color=discord.Color.from_rgb(46, 204, 113))
    g_emb.add_field(name="Java Edition", value=f"Address: `{ip_str}`\nPort: `25565`", inline=False)
    g_emb.add_field(name="Bedrock / Mobile", value=f"Address: `{ip_str}`\nPort: `19132`", inline=False)
    g_emb.add_field(name="Network", value="Works directly on hostel LAN. Check #announcements for tunnel info.", inline=False)
    await postP(discord.utils.get(guild.text_channels, name="🌐・server-ip-and-guide"), g_emb)

    # roles panel
    role_emb = discord.Embed(title="pick your roles", description="select your hall, platform, and notification pings below.", color=discord.Color.from_rgb(155, 89, 182))
    await postP(discord.utils.get(guild.text_channels, name="🎭・pick-your-roles"), role_emb, RolesView())

    # whitelist application panel
    wl_emb = discord.Embed(title="whitelist applications", description="apply for whitelist access using the button below.\nrequires your minecraft ign and roll number.", color=discord.Color.from_rgb(26, 188, 156))
    await postP(discord.utils.get(guild.text_channels, name="📋・whitelist-requests"), wl_emb, WhitelistLandingView())

    # tickets panel
    t_emb = discord.Embed(title="support tickets", description="open a ticket thread for grief reports, lag issues, or general help.", color=discord.Color.from_rgb(231, 76, 60))
    await postP(discord.utils.get(guild.text_channels, name="🎫・create-a-ticket"), t_emb, TicketLauncher())

async def health(req):
    return web.Response(text="ok", content_type="text/plain")

async def runWeb():
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"health check listening on port {port}", flush=True)

async def main():
    if not token:
        print("error: DISCORD_BOT_TOKEN missing or arg not provided")
        sys.exit(1)
    await runWeb()
    await bot.start(token)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("bot stopped")
