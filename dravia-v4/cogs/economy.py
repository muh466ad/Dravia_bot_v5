"""cogs/economy.py — Real economy system (no infinite money!)"""

import discord
from discord import app_commands
from discord.ext import commands
import json, time
import database as db
import utils

with open("config.json", encoding="utf-8") as f:
    cfg = json.load(f)

GUILD = discord.Object(id=int(cfg["guild_id"]))
STARTING = cfg["starting_balance"]

class Economy(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="balance", description="Check your balance")
    @app_commands.guilds(GUILD)
    async def balance(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        data = db.get_user(target.id, STARTING)
        citizen = db.get_citizen(target.id)
        level = utils.xp_to_level(data.get("xp", 0))
        
        e = utils.embed("🏦 Dravia National Bank", color=utils.GOLD)
        e.set_thumbnail(url=target.display_avatar.url)
        
        if citizen:
            e.add_field(name="🆔 Citizen ID", value=citizen["citizen_id"], inline=True)
        
        e.add_field(name="💰 Wallet", value=utils.money(data["balance"]), inline=True)
        e.add_field(name="🏛️ Vault", value=utils.money(data.get("bank", 0)), inline=True)
        e.add_field(name="📊 Level", value=f"**{level}** — *{utils.level_title(level)}*", inline=True)
        e.add_field(name="⚡ XP", value=utils.xp_bar(data.get("xp",0), level), inline=False)
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="pay", description="Send Drav to another citizen")
    @app_commands.guilds(GUILD)
    @app_commands.describe(citizen="Who to pay", amount="Amount", reason="What for")
    @utils.require_citizen
    async def pay(self, interaction: discord.Interaction, citizen: discord.Member, amount: int, reason: str = "Payment"):
        if citizen.id == interaction.user.id or citizen.bot:
            return await interaction.response.send_message("❌ Invalid target!", ephemeral=True)
        if amount < 1:
            return await interaction.response.send_message("❌ Amount must be at least 1.", ephemeral=True)
        
        data = db.get_user(interaction.user.id, STARTING)
        if data["balance"] < amount:
            return await interaction.response.send_message(
                f"❌ You need {utils.money(amount)} but only have {utils.money(data['balance'])}.", ephemeral=True)
        
        new_s = db.update_balance(interaction.user.id, -amount, f"Paid {citizen.name}: {reason}", STARTING)
        new_r = db.update_balance(citizen.id, amount, f"From {interaction.user.name}: {reason}", STARTING)
        
        e = utils.embed("💸 Drav Transfer", color=utils.GOLD)
        e.add_field(name="📤 From", value=interaction.user.mention, inline=True)
        e.add_field(name="📥 To", value=citizen.mention, inline=True)
        e.add_field(name="💰 Amount", value=utils.money(amount), inline=True)
        e.add_field(name="📝 Reason", value=reason, inline=False)
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="welfare", description="Claim unemployment welfare (50 Drav/week)")
    @app_commands.guilds(GUILD)
    @utils.require_citizen
    async def welfare(self, interaction: discord.Interaction):
        uid = interaction.user.id
        data = db.get_user(uid, STARTING)
        
        # Check if on government payroll
        salaries = db.get_all_salaries()
        if str(uid) in salaries:
            return await interaction.response.send_message(
                "❌ You are employed by the government! You cannot claim welfare.", ephemeral=True)
        
        # Check cooldown (7 days)
        last_claim = data.get("last_welfare")
        if last_claim:
            days_since = (time.time() - last_claim) / 86400
            if days_since < 7:
                days_left = 7 - days_since
                return await interaction.response.send_message(
                    f"❌ You can claim welfare again in {days_left:.1f} days.", ephemeral=True)
        
        amount = cfg["welfare_amount"]
        treasury = db.get_treasury_balance()
        
        if treasury < amount:
            return await interaction.response.send_message(
                "❌ Treasury is empty! Government cannot afford welfare payments.", ephemeral=True)
        
        db.update_balance(uid, amount, "Unemployment welfare", STARTING)
        db.update_treasury(-amount, f"Welfare payment to {interaction.user.name}")
        
        # Update last claim
        raw = db.raw()
        raw["users"][str(uid)]["last_welfare"] = time.time()
        db._save(raw)
        
        e = utils.embed("💵 Welfare Payment Received", color=utils.GREEN)
        e.description = f"You received {utils.money(amount)} in unemployment benefits."
        e.set_footer(text="🏛️ Department of Social Services • Come back in 7 days")
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="deposit", description="Move Drav to vault (safe + earns interest)")
    @app_commands.guilds(GUILD)
    @app_commands.describe(amount="Amount to deposit")
    async def deposit(self, interaction: discord.Interaction, amount: int):
        uid = interaction.user.id
        data = db.get_user(uid, STARTING)
        if amount < 1 or amount > data["balance"]:
            return await interaction.response.send_message(
                f"❌ You only have {utils.money(data['balance'])} in your wallet.", ephemeral=True)
        
        raw = db.raw()
        raw["users"][str(uid)]["balance"] -= amount
        raw["users"][str(uid)]["bank"] = raw["users"][str(uid)].get("bank", 0) + amount
        db._save(raw)
        
        e = utils.embed("🏦 Deposit Successful", color=utils.GREEN)
        e.add_field(name="📥 Deposited", value=utils.money(amount), inline=True)
        e.add_field(name="🏛️ Vault Total", value=utils.money(raw["users"][str(uid)]["bank"]), inline=True)
        e.set_footer(text=f"Earns {cfg['bank_interest_rate']}% interest • Safe from robbery")
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="withdraw", description="Take Drav from vault")
    @app_commands.guilds(GUILD)
    @app_commands.describe(amount="Amount to withdraw")
    async def withdraw(self, interaction: discord.Interaction, amount: int):
        uid = interaction.user.id
        data = db.get_user(uid, STARTING)
        bank = data.get("bank", 0)
        if amount < 1 or amount > bank:
            return await interaction.response.send_message(
                f"❌ You only have {utils.money(bank)} in your vault.", ephemeral=True)
        
        raw = db.raw()
        raw["users"][str(uid)]["balance"] += amount
        raw["users"][str(uid)]["bank"] -= amount
        db._save(raw)
        
        e = utils.embed("🏦 Withdrawal Successful", color=utils.GREEN)
        e.add_field(name="📤 Withdrawn", value=utils.money(amount), inline=True)
        e.add_field(name="💰 Wallet Total", value=utils.money(raw["users"][str(uid)]["balance"]), inline=True)
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="leaderboard", description="Wealthiest citizens")
    @app_commands.guilds(GUILD)
    async def leaderboard(self, interaction: discord.Interaction):
        await interaction.response.defer()
        top = db.get_leaderboard(10)
        medals = ["🥇","🥈","🥉"]
        lines = []
        for i, entry in enumerate(top):
            try: u = await self.bot.fetch_user(int(entry["id"])); name = u.display_name
            except: name = "Unknown"
            badge = medals[i] if i < 3 else f"`#{i+1}`"
            lines.append(f"{badge} **{name}** — {entry['balance']:,} {cfg['currency']}")
        
        e = utils.embed("🏆 Dravia Wealth Leaderboard", "\n".join(lines) or "No citizens yet!", color=utils.GOLD)
        await interaction.followup.send(embed=e)

    @app_commands.command(name="history", description="Your transaction history")
    @app_commands.guilds(GUILD)
    async def history(self, interaction: discord.Interaction):
        txs = db.get_transactions(interaction.user.id)
        if not txs: return await interaction.response.send_message("📭 No transactions yet!", ephemeral=True)
        
        lines = []
        for t in reversed(txs[-10:]):
            sign = "+" if t["amount"] > 0 else ""
            emoji = "🟢" if t["amount"] > 0 else "🔴"
            lines.append(f"{emoji} `{sign}{t['amount']:,}` — {t['reason']}")
        
        e = utils.embed("📋 Transaction History", "\n".join(lines), color=utils.BLUE)
        e.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=e, ephemeral=True)


async def setup(bot): await bot.add_cog(Economy(bot))
