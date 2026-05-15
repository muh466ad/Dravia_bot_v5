"""cogs/profile.py — Citizen profiles"""
import discord
from discord import app_commands
from discord.ext import commands
import json
import database as db
import utils

with open("config.json", encoding="utf-8") as f:
    cfg = json.load(f)

GUILD = discord.Object(id=int(cfg["guild_id"]))

class Profile(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="profile", description="View citizen profile")
    @app_commands.guilds(GUILD)
    async def profile(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        data = db.get_user(target.id, cfg["starting_balance"])
        citizen = db.get_citizen(target.id)
        level = utils.xp_to_level(data.get("xp", 0))
        
        e = utils.embed(f"🪪 {target.display_name}", color=utils.PURPLE)
        e.set_thumbnail(url=target.display_avatar.url)
        
        if citizen:
            e.add_field(name="🆔 Citizen ID", value=citizen["citizen_id"], inline=True)
            e.add_field(name="🏠 District", value=citizen["district"], inline=True)
            e.add_field(name="💼 Occupation", value=citizen.get("occupation") or "Unemployed", inline=True)
        
        e.add_field(name="💰 Wallet", value=utils.money(data["balance"]), inline=True)
        e.add_field(name="🏛️ Vault", value=utils.money(data.get("bank", 0)), inline=True)
        e.add_field(name="📊 Level", value=f"{level} — {utils.level_title(level)}", inline=True)
        e.add_field(name="⚡ XP", value=utils.xp_bar(data.get("xp", 0), level), inline=False)
        
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="inventory", description="View items")
    @app_commands.guilds(GUILD)
    async def inventory(self, interaction: discord.Interaction):
        inv = db.get_inventory(interaction.user.id)
        if not inv:
            return await interaction.response.send_message("🎒 Your inventory is empty!", ephemeral=True)
        
        lines = [f"{i['emoji']} **{i['name']}**" for i in inv]
        e = utils.embed("🎒 Your Inventory", "\n".join(lines), color=utils.PURPLE)
        await interaction.response.send_message(embed=e)

async def setup(bot): await bot.add_cog(Profile(bot))
