import sys
import os
import ssl
import certifi
import asyncio
import json
import io
import re
import uuid
from typing import Optional
from aiohttp import web
from dotenv import load_dotenv

load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()
ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())

import discord
from discord.ext import commands

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!iitk", intents=intents, help_command=None)

token = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
server_ip = os.environ.get("MINECRAFT_SERVER_IP", "").strip()
port = int(os.environ.get("PORT", 10000))

db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "whitelist_registry.json")

def get_db():
    if os.path.exists(db_file):
        try:
            with open(db_file, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_wl(ign: str, uid: int, roll: str = "", hostel: str = "", edition: str = ""):
    db = get_db()
    db[ign.strip()] = {
        "ign": ign.strip(),
        "discord_id": uid,
        "roll_no": roll,
        "hostel": hostel,
        "edition": edition,
        "whitelisted_at": discord.utils.utcnow().isoformat()
    }
    try:
        with open(db_file, "w") as f:
            json.dump(db, f, indent=2)
    except Exception as e:
        print(f"error saving whitelist db: {e}")

async def sync_wl(guild: discord.Guild):
    db = get_db()
    rev_ch = discord.utils.get(guild.text_channels, name="📋・whitelist-review")
    if rev_ch:
        try:
            async for msg in rev_ch.history(limit=200):
                if msg.embeds:
                    emb = msg.embeds[0]
                    if "approved" in (emb.title or "").lower():
                        ign, uid, roll, edition, hostel = "", 0, "", "", ""
                        for f in emb.fields:
                            if "IGN" in f.name:
                                ign = f.value.replace("`", "").strip()
                            elif "Discord" in f.name:
                                m = re.search(r"`(\d+)`", f.value)
                                if m:
                                    uid = int(m.group(1))
                            elif "Roll" in f.name:
                                roll = f.value.replace("`", "").strip()
                            elif "Edition" in f.name:
                                edition = f.value.replace("`", "").strip()
                            elif "Hostel" in f.name:
                                hostel = f.value.replace("`", "").strip()
                        if ign and ign not in db:
                            db[ign] = {
                                "ign": ign,
                                "discord_id": uid,
                                "roll_no": roll,
                                "edition": edition,
                                "hostel": hostel,
                                "whitelisted_at": msg.created_at.isoformat()
                            }
            with open(db_file, "w") as f:
                json.dump(db, f, indent=2)
        except Exception as e:
            print(f"error syncing history: {e}")
    return db

ROLES_SPEC = [
    {"name": "👑 Server Admin / OP", "color": discord.Color.red(), "hoist": True, "mentionable": True},
    {"name": "⚙️ SysAdmin / Host", "color": discord.Color.purple(), "hoist": True, "mentionable": True},
    {"name": "🛡️ Moderator", "color": discord.Color.green(), "hoist": True, "mentionable": True},
    {"name": "🎓 Verified IITKian", "color": discord.Color.blue(), "hoist": True, "mentionable": False},
    {"name": "⛏️ SMP Whitelisted", "color": discord.Color.teal(), "hoist": True, "mentionable": True},
    {"name": "⚡ Redstone Engineer", "color": discord.Color.orange(), "hoist": False, "mentionable": False},
    {"name": "🎨 Master Builder", "color": discord.Color.gold(), "hoist": False, "mentionable": False},
    {"name": "⚔️ PvP / Tourneys", "color": discord.Color.magenta(), "hoist": False, "mentionable": False},
    {"name": "📢 Event Pings", "color": discord.Color.dark_gold(), "hoist": False, "mentionable": True},
    {"name": "⚠️ Server Restarts", "color": discord.Color.dark_orange(), "hoist": False, "mentionable": True},
    {"name": "💻 Java Edition", "color": discord.Color.blurple(), "hoist": False, "mentionable": False},
    {"name": "📱 Bedrock / PE", "color": discord.Color.dark_teal(), "hoist": False, "mentionable": False},
    {"name": "🌐 Guest / Visitor", "color": discord.Color.light_grey(), "hoist": False, "mentionable": False}
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

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        rev_ch = discord.utils.get(guild.text_channels, name="📋・whitelist-review")
        if not rev_ch:
            rev_ch = discord.utils.get(guild.text_channels, name="📋・whitelist-requests")
        ign = self.ign.value.strip()
        roll = self.roll_no.value.strip()
        db = get_db()
        for ex_ign, data in db.items():
            if ex_ign.lower() == ign.lower():
                await interaction.response.send_message(f"ign {ign} is already registered.", ephemeral=True)
                return
            if roll and data.get("roll_no") == roll and (data.get("discord_id") != interaction.user.id):
                await interaction.response.send_message(f"roll number {roll} is already registered.", ephemeral=True)
                return
        if rev_ch:
            try:
                async for msg in rev_ch.history(limit=50):
                    if msg.embeds:
                        emb = msg.embeds[0]
                        if "application" in (emb.title or "").lower():
                            for f in emb.fields:
                                if "Discord" in f.name and str(interaction.user.id) in f.value:
                                    await interaction.response.send_message("you already have a pending application.", ephemeral=True)
                                    return
                                elif "IGN" in f.name and f.value.replace("`", "").strip().lower() == ign.lower():
                                    await interaction.response.send_message(f"application for {ign} is already pending.", ephemeral=True)
                                    return
            except Exception:
                pass
        emb = discord.Embed(title="new whitelist application", color=discord.Color.teal(), timestamp=discord.utils.utcnow())
        emb.set_thumbnail(url=interaction.user.display_avatar.url)
        emb.add_field(name="Discord User", value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=False)
        emb.add_field(name="Minecraft IGN", value=f"`{ign}`", inline=True)
        emb.add_field(name="Edition", value=f"`{self.edition.value.strip().capitalize()}`", inline=True)
        emb.add_field(name="Roll Number", value=f"`{roll}`", inline=True)
        emb.add_field(name="Hostel", value=f"`{self.hostel.value.strip() or 'N/A'}`", inline=True)
        view = WhitelistApprovalView(uid=interaction.user.id, ign=ign)
        if rev_ch:
            await rev_ch.send(embed=emb, view=view)
        await interaction.response.send_message(f"application for {ign} submitted.", ephemeral=True)

class WhitelistApprovalView(discord.ui.View):
    def __init__(self, uid: Optional[int] = None, ign: Optional[str] = None):
        super().__init__(timeout=None)
        self.uid = uid
        self.ign = ign

    def _get_info(self, msg):
        uid = self.uid
        ign = self.ign
        if msg and msg.embeds:
            emb = msg.embeds[0]
            for f in emb.fields:
                if "Discord" in f.name and not uid:
                    m = re.search(r"`(\d+)`", f.value)
                    if m:
                        uid = int(m.group(1))
                elif "IGN" in f.name and not ign:
                    ign = f.value.replace("`", "").strip()
        return (uid, ign or "player")

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success, emoji="✅", custom_id="wl_approve")
    async def on_approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        staff = any(r.name in ["👑 Server Admin / OP", "🛡️ Moderator", "⚙️ SysAdmin / Host"] for r in interaction.user.roles)
        if not (staff or interaction.user.guild_permissions.administrator):
            await interaction.response.send_message("staff only.", ephemeral=True)
            return
        uid, ign = self._get_info(interaction.message)
        member = None
        if uid:
            member = guild.get_member(uid)
            if not member:
                try:
                    member = await guild.fetch_member(uid)
                except Exception:
                    member = None
        if member:
            wl_role = discord.utils.get(guild.roles, name="⛏️ SMP Whitelisted")
            v_role = discord.utils.get(guild.roles, name="🎓 Verified IITKian")
            if wl_role:
                await member.add_roles(wl_role)
            if v_role:
                await member.add_roles(v_role)
            try:
                await member.send(f"you have been whitelisted as `{ign}`. check #server-ip-and-guide for connection details.")
            except Exception:
                pass
        roll, edition, hostel = "", "", ""
        if interaction.message and interaction.message.embeds:
            for f in interaction.message.embeds[0].fields:
                if "Roll" in f.name:
                    roll = f.value.replace("`", "").strip()
                elif "Edition" in f.name:
                    edition = f.value.replace("`", "").strip()
                elif "Hostel" in f.name:
                    hostel = f.value.replace("`", "").strip()
        save_wl(ign=ign, uid=uid or 0, roll=roll, hostel=hostel, edition=edition)
        for item in self.children:
            item.disabled = True
        emb = interaction.message.embeds[0]
        emb.color = discord.Color.green()
        emb.title = f"approved by {interaction.user.display_name}"
        await interaction.message.edit(embed=emb, view=self)
        await interaction.response.send_message(f"approved {ign}.", ephemeral=True)

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger, emoji="❌", custom_id="wl_reject")
    async def on_reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff = any(r.name in ["👑 Server Admin / OP", "🛡️ Moderator", "⚙️ SysAdmin / Host"] for r in interaction.user.roles)
        if not (staff or interaction.user.guild_permissions.administrator):
            await interaction.response.send_message("staff only.", ephemeral=True)
            return
        uid, ign = self._get_info(interaction.message)
        for item in self.children:
            item.disabled = True
        emb = interaction.message.embeds[0]
        emb.color = discord.Color.red()
        emb.title = f"rejected by {interaction.user.display_name}"
        await interaction.message.edit(embed=emb, view=self)
        await interaction.response.send_message(f"rejected {ign}.", ephemeral=True)

class WhitelistLandingView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Apply for Whitelist", style=discord.ButtonStyle.success, emoji="📝", custom_id="open_wl_modal")
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user
        wl_role = discord.utils.get(guild.roles, name="⛏️ SMP Whitelisted")
        if wl_role and wl_role in member.roles:
            await interaction.response.send_message("you are already whitelisted.", ephemeral=True)
            return
        db = get_db()
        for ign, data in db.items():
            if data.get("discord_id") == member.id:
                await interaction.response.send_message(f"already whitelisted as `{ign}`.", ephemeral=True)
                return
        rev_ch = discord.utils.get(guild.text_channels, name="📋・whitelist-review")
        if rev_ch:
            try:
                async for msg in rev_ch.history(limit=50):
                    if msg.embeds:
                        emb = msg.embeds[0]
                        if "application" in (emb.title or "").lower():
                            for f in emb.fields:
                                if "Discord" in f.name and str(member.id) in f.value:
                                    await interaction.response.send_message("you already have a pending application.", ephemeral=True)
                                    return
            except Exception:
                pass
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

    async def mk_ticket(self, interaction: discord.Interaction, cat: str):
        channel = interaction.channel
        user = interaction.user
        t_name = f"ticket-{user.name[:10]}-{cat}"
        try:
            is_priv = discord.ChannelType.private_thread if interaction.guild.features and "PRIVATE_THREADS" in interaction.guild.features else discord.ChannelType.public_thread
            thread = await channel.create_thread(name=t_name, type=is_priv, auto_archive_duration=1440, reason=f"ticket by {user}")
            await thread.add_user(user)
            mod_role = discord.utils.get(interaction.guild.roles, name="🛡️ Moderator")
            mod_mention = mod_role.mention if mod_role else "staff"
            desc = f"hi {user.mention}, explain your issue below.\ninclude ign, coords, or screenshots if relevant.\n{mod_mention} will help shortly."
            emb = discord.Embed(title=f"support: {cat}", description=desc, color=discord.Color.red())
            await thread.send(embed=emb)
            await interaction.response.send_message(f"ticket created in {thread.mention}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"failed to create ticket: {e}", ephemeral=True)

@bot.tree.command(name="help", description="Show server guide and commands")
async def cmd_slash_help(interaction: discord.Interaction):
    emb = discord.Embed(title="server guide & commands", color=discord.Color.blue())
    emb.add_field(name="getting started", value="• roles: <#pick-your-roles>\n• whitelist: <#whitelist-requests>\n• support: <#create-a-ticket>", inline=False)
    emb.add_field(name="commands", value="• `/ip` or `!iitk ip` - server address\n• `/coords` or `!iitk coords` - key coordinates\n• `/rules` or `!iitk rules` - rules summary\n• `/ping` or `!iitk ping` - bot latency\n• `/whitelist_list` - whitelisted players\n• `/help` - this guide", inline=False)
    emb.add_field(name="staff", value="• `/whitelist_add <user> <ign>` - add player\n• `/whitelist_export` - export commands and json", inline=False)
    await interaction.response.send_message(embed=emb)

@bot.command(name="help")
async def cmd_text_help(ctx):
    emb = discord.Embed(title="server guide & commands", color=discord.Color.blue())
    emb.add_field(name="getting started", value="• roles: #pick-your-roles\n• whitelist: #whitelist-requests\n• support: #create-a-ticket", inline=False)
    emb.add_field(name="commands", value="• `!iitk ip` - server address\n• `!iitk coords` - key coordinates\n• `!iitk rules` - rules summary\n• `!iitk ping` - bot latency\n• `!iitk help` - this guide", inline=False)
    await ctx.send(embed=emb)

@bot.tree.command(name="ip", description="Get server connection details")
async def cmd_slash_ip(interaction: discord.Interaction):
    ip_str = server_ip if server_ip else "Campus LAN IP (172.x.x.x) or Playit tunnel"
    emb = discord.Embed(title="server connection info", color=discord.Color.green())
    emb.add_field(name="Java Edition", value=f"Address: `{ip_str}`\nPort: `25565`\nVersion: `1.20.x / 1.21.x`", inline=False)
    emb.add_field(name="Bedrock / PE", value=f"Address: `{ip_str}`\nPort: `19132`", inline=False)
    emb.add_field(name="Campus Network", value="Direct connection on hostel wifi/lan. Check <#announcements> for tunnel links.", inline=False)
    await interaction.response.send_message(embed=emb)

@bot.command(name="ip")
async def cmd_text_ip(ctx):
    ip_str = server_ip if server_ip else "Campus LAN IP (172.x.x.x) or Playit tunnel"
    emb = discord.Embed(title="server connection info", color=discord.Color.green())
    emb.add_field(name="Java Edition", value=f"Address: `{ip_str}`\nPort: `25565`\nVersion: `1.20.x / 1.21.x`", inline=False)
    emb.add_field(name="Bedrock / PE", value=f"Address: `{ip_str}`\nPort: `19132`", inline=False)
    await ctx.send(embed=emb)

@bot.tree.command(name="coords", description="View landmark coordinates")
async def cmd_slash_coords(interaction: discord.Interaction):
    emb = discord.Embed(title="coordinates", color=discord.Color.gold())
    emb.add_field(name="Spawn", value="`X: 0, Y: 70, Z: 0`", inline=True)
    emb.add_field(name="Nether Hub", value="`X: 0, Y: 120, Z: 0`", inline=True)
    emb.add_field(name="Marketplace", value="check <#campus-marketplace>", inline=True)
    emb.add_field(name="End Portal", value="check <#dynmap-and-coords>", inline=True)
    emb.add_field(name="Halls", value="check <#hall-factions>", inline=True)
    await interaction.response.send_message(embed=emb)

@bot.command(name="coords")
async def cmd_text_coords(ctx):
    emb = discord.Embed(title="coordinates", color=discord.Color.gold())
    emb.add_field(name="Spawn", value="`X: 0, Y: 70, Z: 0`", inline=True)
    emb.add_field(name="Nether Hub", value="`X: 0, Y: 120, Z: 0`", inline=True)
    emb.add_field(name="Marketplace", value="check #campus-marketplace", inline=True)
    await ctx.send(embed=emb)

@bot.tree.command(name="rules", description="Quick overview of server rules")
async def cmd_slash_rules(interaction: discord.Interaction):
    emb = discord.Embed(title="server rules", description="1. No griefing or stealing (CoreProtect logged).\n2. No hacked clients or x-ray.\n3. Fair combat and no combat logging.\n4. Campus honor code.\n5. Farms need an accessible off-switch.\n\nFull details in <#rules-and-conduct>.", color=discord.Color.blue())
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
    wl_role = discord.utils.get(interaction.guild.roles, name="⛏️ SMP Whitelisted")
    v_role = discord.utils.get(interaction.guild.roles, name="🎓 Verified IITKian")
    if wl_role:
        await member.add_roles(wl_role)
    if v_role:
        await member.add_roles(v_role)
    try:
        await member.send(f"whitelisted on IITK Minecraft as `{ign}`. check #server-ip-and-guide for connection details.")
    except Exception:
        pass
    save_wl(ign=ign, uid=member.id)
    await interaction.response.send_message(f"whitelisted {member.mention} as `{ign}`.")

@bot.tree.command(name="whitelist_export", description="Staff: Export all whitelisted players")
async def cmd_slash_whitelist_export(interaction: discord.Interaction):
    staff = any(r.name in ["👑 Server Admin / OP", "🛡️ Moderator", "⚙️ SysAdmin / Host"] for r in interaction.user.roles)
    if not (staff or interaction.user.guild_permissions.administrator):
        await interaction.response.send_message("staff only.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    db = await sync_wl(interaction.guild)
    if not db:
        await interaction.followup.send("no whitelisted players found.", ephemeral=True)
        return
    cmds = [f"/whitelist add {ign}" for ign in db.keys()]
    c_file = discord.File(io.BytesIO("\n".join(cmds).encode("utf-8")), filename="whitelist_commands.txt")
    mc_data = [{"uuid": str(uuid.uuid3(uuid.NAMESPACE_DNS, f"OfflinePlayer:{ign}")), "name": ign} for ign in db.keys()]
    j_file = discord.File(io.BytesIO(json.dumps(mc_data, indent=2).encode("utf-8")), filename="whitelist.json")
    preview = "\n".join(cmds[:15])
    if len(cmds) > 15:
        preview += f"\n... and {len(cmds) - 15} more"
    emb = discord.Embed(title=f"whitelist export ({len(db)} players)", description=f"```text\n{preview}\n```", color=discord.Color.green())
    await interaction.followup.send(embed=emb, files=[c_file, j_file], ephemeral=True)

@bot.command(name="whitelist_export", aliases=["export_whitelist"])
async def cmd_text_whitelist_export(ctx):
    staff = any(r.name in ["👑 Server Admin / OP", "🛡️ Moderator", "⚙️ SysAdmin / Host"] for r in ctx.author.roles)
    if not (staff or ctx.author.guild_permissions.administrator):
        await ctx.send("staff only.")
        return
    db = await sync_wl(ctx.guild)
    if not db:
        await ctx.send("no whitelisted players found.")
        return
    cmds = [f"/whitelist add {ign}" for ign in db.keys()]
    c_file = discord.File(io.BytesIO("\n".join(cmds).encode("utf-8")), filename="whitelist_commands.txt")
    preview = "\n".join(cmds[:15])
    if len(cmds) > 15:
        preview += f"\n... and {len(cmds) - 15} more"
    emb = discord.Embed(title=f"whitelist export ({len(db)} players)", description=f"```text\n{preview}\n```", color=discord.Color.green())
    await ctx.send(embed=emb, file=c_file)

@bot.tree.command(name="whitelist_list", description="List whitelisted players")
async def cmd_slash_whitelist_list(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)
    db = await sync_wl(interaction.guild)
    if not db:
        await interaction.followup.send("no whitelisted players found.")
        return
    items = []
    for ign, data in db.items():
        roll = f" ({data.get('roll_no')})" if data.get("roll_no") else ""
        items.append(f"• `{ign}`{roll}")
    preview = "\n".join(items[:30])
    if len(items) > 30:
        preview += f"\n*...and {len(items) - 30} more*"
    emb = discord.Embed(title=f"whitelisted players ({len(db)})", description=preview, color=discord.Color.teal())
    await interaction.followup.send(embed=emb)

@bot.command(name="whitelist_list")
async def cmd_text_whitelist_list(ctx):
    db = await sync_wl(ctx.guild)
    if not db:
        await ctx.send("no whitelisted players found.")
        return
    items = [f"• `{ign}`" for ign in db.keys()]
    preview = "\n".join(items[:30])
    if len(items) > 30:
        preview += f"\n*...and {len(items) - 30} more*"
    emb = discord.Embed(title=f"whitelisted players ({len(db)})", description=preview, color=discord.Color.teal())
    await ctx.send(embed=emb)

@bot.event
async def on_ready():
    print(f"bot connected as {bot.user} (id: {bot.user.id})", flush=True)
    bot.add_view(RolesView())
    bot.add_view(WhitelistLandingView())
    bot.add_view(WhitelistApprovalView())
    bot.add_view(TicketLauncher())
    for guild in bot.guilds:
        try:
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            print(f"synced {len(synced)} commands to {guild.name}", flush=True)
        except Exception as e:
            print(f"sync error on {guild.name}: {e}", flush=True)
    for guild in bot.guilds:
        await init_srv(guild)
    print("server setup done", flush=True)

async def init_srv(guild: discord.Guild):
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
                await guild.create_role(name=hall, color=discord.Color.light_grey(), hoist=False)
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
    await init_panels(guild)

async def post_panel(ch: Optional[discord.TextChannel], emb: discord.Embed, view: Optional[discord.ui.View] = None):
    if not ch:
        return
    try:
        async for m in ch.history(limit=5):
            if m.author == bot.user:
                return
        await ch.send(embed=emb, view=view)
    except discord.Forbidden:
        pass

async def init_panels(guild: discord.Guild):
    r_emb = discord.Embed(title="server rules & guidelines", description="rules and fair play guidelines for the campus server.", color=discord.Color.blue())
    r_emb.add_field(name="1. Griefing & Theft", value="Stealing or breaking others builds is not allowed. CoreProtect logs all actions.", inline=False)
    r_emb.add_field(name="2. Fair Play", value="No hacked clients, baritone, or x-ray packs.", inline=False)
    r_emb.add_field(name="3. Campus Code", value="Keep discussions civil. No harassment or toxic behavior.", inline=False)
    r_emb.add_field(name="4. Farms & Tech", value="Large farms must have an accessible off-switch.", inline=False)
    r_emb.add_field(name="5. PvP Rules", value="No combat logging during fights. No spawn camping or portal trapping.", inline=False)
    await post_panel(discord.utils.get(guild.text_channels, name="📜・rules-and-conduct"), r_emb)

    ip_str = server_ip if server_ip else "Campus LAN IP (172.x.x.x) or Playit tunnel"
    g_emb = discord.Embed(title="connection guide", description="how to connect to the server from campus hostels or remote.", color=discord.Color.green())
    g_emb.add_field(name="Java Edition", value=f"Address: `{ip_str}`\nPort: `25565`", inline=False)
    g_emb.add_field(name="Bedrock / Mobile", value=f"Address: `{ip_str}`\nPort: `19132`", inline=False)
    g_emb.add_field(name="Network", value="Works directly on hostel LAN. Check #announcements for tunnel info.", inline=False)
    await post_panel(discord.utils.get(guild.text_channels, name="🌐・server-ip-and-guide"), g_emb)

    role_emb = discord.Embed(title="pick your roles", description="select your hall, platform, and notification pings below.", color=discord.Color.purple())
    await post_panel(discord.utils.get(guild.text_channels, name="🎭・pick-your-roles"), role_emb, RolesView())

    wl_emb = discord.Embed(title="whitelist applications", description="apply for whitelist access using the button below.\nrequires your minecraft ign and roll number.", color=discord.Color.teal())
    await post_panel(discord.utils.get(guild.text_channels, name="📋・whitelist-requests"), wl_emb, WhitelistLandingView())

    t_emb = discord.Embed(title="support tickets", description="open a ticket thread for grief reports, lag issues, or general help.", color=discord.Color.red())
    await post_panel(discord.utils.get(guild.text_channels, name="🎫・create-a-ticket"), t_emb, TicketLauncher())

async def health(req):
    return web.Response(text="ok", content_type="text/plain")

async def run_web():
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
        print("error: DISCORD_BOT_TOKEN missing")
        sys.exit(1)
    await run_web()
    await bot.start(token)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("bot stopped")
