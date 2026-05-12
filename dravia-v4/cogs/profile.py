"""cogs/profile.py — Citizen profiles and achievements"""

import discord
from discord import app_commands
from discord.ext import commands
import json
import database as db
import utils

with open("config.json", encoding="utf-8") as f:
    cfg = json.load(f)

GUILD    = discord.Object(id=int(cfg["guild_id"]))
STARTING = cfg["starting_balance"]


class Profile(commands.Cog):
    def __init__(self, bot): self.bot = bot

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
        biz    = db.get_user_business(target.id)
        achieved = data.get("achievements", [])
        cases  = [c for c in db.raw().get("cases",[]) if c["plaintiff"] == str(target.id)]

        ach_text = " ".join(db.ACHIEVEMENTS[a]["emoji"] for a in achieved) if achieved else "*None yet*"
        inv_text = ", ".join(f"{i['emoji']} {i['name']}" for i in inv) if inv else "*Nothing yet*"
        biz_text = f"🏢 {biz['name']}" if biz else "*No business*"

        e = utils.embed(f"🪪 Citizen #{data.get('citizen_id','?')} — {target.display_name}", color=utils.PURPLE)
        e.set_thumbnail(url=target.display_avatar.url)
        e.add_field(name="🏅 Title",         value=f"Level {level} — *{title}*",                    inline=True)
        e.add_field(name="💰 Wallet",         value=utils.money(data["balance"]),                    inline=True)
        e.add_field(name="🏛️ Vault",          value=utils.money(data.get("bank",0)),                 inline=True)
        e.add_field(name="⚡ XP",             value=utils.xp_bar(data.get("xp",0), level),           inline=False)
        e.add_field(name="💼 Jobs Worked",    value=f"{data.get('work_count',0):,}",                 inline=True)
        e.add_field(name="💸 Total Earned",   value=utils.money(data.get("total_earned",0)),          inline=True)
        e.add_field(name="🏢 Business",       value=biz_text,                                        inline=True)
        e.add_field(name="🎨 Art Owned",      value=f"{len(art)} piece(s)",                          inline=True)
        e.add_field(name="📜 Cases Filed",    value=str(len(cases)),                                 inline=True)
        e.add_field(name="🏆 Achievements",   value=ach_text,                                        inline=False)
        e.add_field(name="🎒 Inventory",      value=inv_text,                                        inline=False)
        e.add_field(name="📅 Citizen Since",  value=data.get("joined","?")[:10],                     inline=True)
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="achievements", description="View all available achievements")
    @app_commands.guilds(GUILD)
    @app_commands.describe(user="Whose achievements to view")
    async def achievements(self, interaction: discord.Interaction, user: discord.Member = None):
        target   = user or interaction.user
        data     = db.get_user(target.id, STARTING)
        achieved = data.get("achievements", [])
        lines    = []
        for aid, ach in db.ACHIEVEMENTS.items():
            status = "✅" if aid in achieved else "🔒"
            lines.append(f"{status} {ach['emoji']} **{ach['name']}** — {ach['desc']}")

        e = utils.embed(f"🏆 {target.display_name}'s Achievements",
                        "\n".join(lines), color=utils.GOLD)
        e.set_thumbnail(url=target.display_avatar.url)
        e.add_field(name="Unlocked", value=f"{len(achieved)}/{len(db.ACHIEVEMENTS)}", inline=True)
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="inventory", description="View your items")
    @app_commands.guilds(GUILD)
    @app_commands.describe(user="Whose inventory to view")
    async def inventory(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        inv    = db.get_inventory(target.id)
        if not inv:
            return await interaction.response.send_message(
                f"🎒 {'You have' if not user else target.display_name + ' has'} no items! Use `/shop browse`.", ephemeral=True)
        lines = [f"{i['emoji']} **{i['name']}** — bought {i['bought_at'][:10]}" for i in inv]
        e = utils.embed(f"🎒 {target.display_name}'s Inventory", "\n".join(lines), color=utils.PURPLE)
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="citizenid", description="View your official Dravia citizen ID card")
    @app_commands.guilds(GUILD)
    async def citizenid(self, interaction: discord.Interaction):
        data  = db.get_user(interaction.user.id, STARTING)
        level = utils.xp_to_level(data.get("xp", 0))
        e     = utils.embed("🪪 Official Dravia Citizen ID", color=utils.DARK)
        e.set_thumbnail(url=interaction.user.display_avatar.url)
        e.add_field(name="👤 Full Name",    value=interaction.user.display_name,       inline=True)
        e.add_field(name="🆔 Citizen #",   value=str(data.get("citizen_id","?")),      inline=True)
        e.add_field(name="🏅 Rank",         value=utils.level_title(level),            inline=True)
        e.add_field(name="📅 Issued",       value=data.get("joined","?")[:10],         inline=True)
        e.add_field(name="🏛️ Nation",       value="Dravia",                            inline=True)
        e.add_field(name="✅ Status",       value="Active Citizen",                    inline=True)
        e.set_footer(text="🦢 Dravia — Nation of Law and Unity • Est. 19__")
        await interaction.response.send_message(embed=e)


async def setup(bot): await bot.add_cog(Profile(bot))
