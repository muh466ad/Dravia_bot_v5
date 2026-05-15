"""cogs/fun.py — Gambling with limits"""
import discord
from discord import app_commands
from discord.ext import commands
import json, random, time
import database as db
import utils

with open("config.json", encoding="utf-8") as f:
    cfg = json.load(f)

GUILD = discord.Object(id=int(cfg["guild_id"]))

class Fun(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="coinflip", description="Bet on coin flip (max 100 Drav)")
    @app_commands.guilds(GUILD)
    @app_commands.describe(amount="Bet amount", side="Heads or tails")
    @app_commands.choices(side=[
        app_commands.Choice(name="Heads", value="heads"),
        app_commands.Choice(name="Tails", value="tails"),
    ])
    @utils.require_citizen
    async def coinflip(self, interaction: discord.Interaction, amount: int, side: str):
        max_bet = cfg["max_bet_coinflip"]
        if amount < 1 or amount > max_bet:
            return await interaction.response.send_message(f"❌ Bet must be 1-{max_bet} Drav!", ephemeral=True)
        
        data = db.get_user(interaction.user.id, cfg["starting_balance"])
        if data["balance"] < amount:
            return await interaction.response.send_message("❌ Not enough Drav!", ephemeral=True)
        
        result = random.choice(["heads", "tails"])
        won = result == side
        coin = "HEADS 👑" if result == "heads" else "TAILS 🦢"
        
        if won:
            db.update_balance(interaction.user.id, amount, "Coinflip win", cfg["starting_balance"])
            e = utils.embed("🪙 You WIN!", f"Coin: **{coin}**\nWon {utils.money(amount)}!", color=utils.GREEN)
        else:
            db.update_balance(interaction.user.id, -amount, "Coinflip loss", cfg["starting_balance"])
            e = utils.embed("🪙 You lost", f"Coin: **{coin}**\nLost {utils.money(amount)}", color=utils.RED)
        
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="rob", description="Try to rob someone (risky!)")
    @app_commands.guilds(GUILD)
    @app_commands.describe(citizen="Target")
    @utils.require_citizen
    async def rob(self, interaction: discord.Interaction, citizen: discord.Member):
        if citizen.id == interaction.user.id or citizen.bot:
            return await interaction.response.send_message("❌ Invalid target!", ephemeral=True)
        
        robber_data = db.get_user(interaction.user.id, cfg["starting_balance"])
        if robber_data.get("last_rob"):
            rem = cfg["rob_cooldown_mins"] * 60 - (time.time() - robber_data["last_rob"])
            if rem > 0:
                return await interaction.response.send_message(f"⏳ Wait {int(rem//60)}m", ephemeral=True)
        
        victim_data = db.get_user(citizen.id, cfg["starting_balance"])
        if victim_data["balance"] < 10:
            return await interaction.response.send_message("❌ Target too broke!", ephemeral=True)
        
        db.set_last_rob(interaction.user.id)
        
        if random.randint(1, 100) <= cfg["rob_success_chance"]:
            stolen = min(cfg["max_rob_amount"], victim_data["balance"] // 3)
            db.update_balance(citizen.id, -stolen, f"Robbed by {interaction.user.name}", cfg["starting_balance"])
            db.update_balance(interaction.user.id, stolen, f"Robbed {citizen.name}", cfg["starting_balance"])
            e = utils.embed("🦹 Success!", f"Stole {utils.money(stolen)}!", color=utils.GREEN)
        else:
            fine = min(50, robber_data["balance"])
            db.update_balance(interaction.user.id, -fine, "Caught robbing", cfg["starting_balance"])
            db.update_treasury(fine, f"Rob fine from {interaction.user.name}")
            e = utils.embed("🚔 Caught!", f"Fined {utils.money(fine)}!", color=utils.RED)
        
        await interaction.response.send_message(embed=e)

async def setup(bot): await bot.add_cog(Fun(bot))
