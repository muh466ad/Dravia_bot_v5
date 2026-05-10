"""cogs/profile.py — Citizen profile cards"""

import discord
from discord import app_commands
from discord.ext import commands
import json
import database as db
import utils

with open("config.json", encoding="utf-8") as f:
    cfg = json.load(f)

GUILD    = discord.Object(id=int(cfg["guild_id"]))
CURRENCY = cfg["currency"]
STARTING = cfg["starting_balance"]


class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="profile", description="View a citizen's full profile card")
    @app_commands.guilds(GUILD)
    @app_commands.describe(user="Whose profile to view")
    async def profile(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        data   = db.get_user(target.id, STARTING)

        level  = utils.xp_to_level(data.get("xp", 0))
        title  = utils.level_title(level)
        inv    = db.get_inventory(target.id)
        art    = db.get_collection(target.id)
        cases  = [c for c in db.raw().get("cases", []) if c["plaintiff"] == str(target.id)]

        # XP bar
        xp       = data.get("xp", 0)
        xp_temp  = xp
        needed   = 100
        for _ in range(level):
            xp_temp -= needed
            needed   = int(needed * 1.4)
        xp_current = max(0, xp_temp)
        bar_filled = min(10, int((xp_current / needed) * 10))
        xp_bar     = "█" * bar_filled + "░" * (10 - bar_filled)

        inv_text = ", ".join(f"{i['emoji']} {i['name']}" for i in inv) if inv else "*Nothing yet*"
        art_text = f"{len(art)} artwork(s)" if art else "*No collection yet*"

        e = utils.embed(f"🪪 Citizen Profile", color=utils.PURPLE)
        e.set_author(name=f"{target.display_name}", icon_url=target.display_avatar.url)
        e.set_thumbnail(url=target.display_avatar.url)
        e.add_field(name="🏅 Title",          value=f"Level {level} — *{title}*",                        inline=True)
        e.add_field(name="💰 Wallet",          value=utils.money(data["balance"]),                        inline=True)
        e.add_field(name="🏛️ Bank Vault",      value=utils.money(data.get("bank", 0)),                   inline=True)
        e.add_field(name="⚡ XP Progress",     value=f"`{xp_bar}` {xp_current}/{needed}",                inline=False)
        e.add_field(name="💼 Jobs Worked",     value=f"{data.get('work_count', 0):,}",                   inline=True)
        e.add_field(name="💸 Total Earned",    value=utils.money(data.get("total_earned", 0)),            inline=True)
        e.add_field(name="🛒 Total Spent",     value=utils.money(data.get("total_spent", 0)),             inline=True)
        e.add_field(name="🎨 Art Collection",  value=art_text,                                            inline=True)
        e.add_field(name="📜 Cases Filed",     value=str(len(cases)),                                     inline=True)
        e.add_field(name="🎒 Inventory",       value=inv_text,                                            inline=False)
        e.add_field(name="📅 Citizen Since",   value=data.get("joined", "Unknown")[:10],                 inline=True)
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="inventory", description="View your items")
    @app_commands.guilds(GUILD)
    @app_commands.describe(user="Whose inventory to view")
    async def inventory(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        inv    = db.get_inventory(target.id)

        if not inv:
            e = utils.embed("🎒 Empty Inventory",
                f"{'You have' if not user else target.display_name + ' has'} no items yet!\nBuy some from `/shop`.",
                color=utils.ORANGE)
            return await interaction.response.send_message(embed=e, ephemeral=True)

        lines = [f"{i['emoji']} **{i['name']}** — bought {i['bought_at'][:10]}" for i in inv]
        e = utils.embed(f"🎒 {target.display_name}'s Inventory", "\n".join(lines), color=utils.PURPLE)
        e.set_thumbnail(url=target.display_avatar.url)
        await interaction.response.send_message(embed=e)


async def setup(bot):
    await bot.add_cog(Profile(bot))
