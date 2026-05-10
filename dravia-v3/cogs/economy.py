"""cogs/economy.py — Core economy commands"""

import discord
from discord import app_commands
from discord.ext import commands
import json, time, random
import database as db
import utils

with open("config.json", encoding="utf-8") as f:
    cfg = json.load(f)

GUILD    = discord.Object(id=int(cfg["guild_id"]))
CURRENCY = cfg["currency"]
STARTING = cfg["starting_balance"]
COOLDOWN = cfg["work_cooldown_mins"] * 60

JOBS = [
    ("⛏️  Miner",        "mined iron ore deep in the Dravia mountains"),
    ("🌾  Farmer",        "harvested golden wheat on the state farmlands"),
    ("🏗️  Builder",       "constructed a government wall section"),
    ("🛡️  Guard",         "patrolled the Dravia border all night"),
    ("🐟  Fisherman",     "caught fish from the great Dravia river"),
    ("📦  Courier",       "delivered urgent government parcels"),
    ("🧑‍🍳  Chef",          "cooked a lavish banquet for the state"),
    ("🪵  Lumberjack",    "chopped timber in the northern forests"),
    ("📜  Scribe",        "wrote official government documents"),
    ("🔧  Mechanic",      "repaired the governor's fleet of vehicles"),
    ("🎨  Street Artist", "painted murals across the capital"),
    ("🧱  Stonemason",    "laid cobblestones in the city square"),
    ("⚗️  Alchemist",     "brewed rare potions for the treasury"),
    ("🌊  Sailor",        "navigated the Dravia seas on a trade voyage"),
]


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── /balance ──────────────────────────────────────────
    @app_commands.command(name="balance", description="Check your Drav balance")
    @app_commands.guilds(GUILD)
    @app_commands.describe(user="Check someone else's balance")
    async def balance(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        data   = db.get_user(target.id, STARTING)
        level  = utils.xp_to_level(data.get("xp", 0))
        title  = utils.level_title(level)

        e = utils.embed(f"🏦 Dravia National Bank", color=utils.GOLD)
        e.set_thumbnail(url=target.display_avatar.url)
        e.add_field(name="👤 Citizen",       value=target.mention,                      inline=True)
        e.add_field(name="💰 Wallet",        value=utils.money(data["balance"]),         inline=True)
        e.add_field(name="🏛️ Bank Vault",    value=utils.money(data.get("bank", 0)),     inline=True)
        e.add_field(name="📊 Citizen Level", value=f"Level {level} — *{title}*",         inline=True)
        e.add_field(name="⚡ XP",            value=f"{data.get('xp', 0):,}",             inline=True)
        e.add_field(name="💼 Jobs Done",     value=f"{data.get('work_count', 0):,}",     inline=True)
        await interaction.response.send_message(embed=e)

    # ── /work ─────────────────────────────────────────────
    @app_commands.command(name="work", description="Work to earn Drav (1 hour cooldown)")
    @app_commands.guilds(GUILD)
    async def work(self, interaction: discord.Interaction):
        uid       = interaction.user.id
        data      = db.get_user(uid, STARTING)
        last_work = data.get("last_work")

        if last_work:
            remaining = COOLDOWN - (time.time() - last_work)
            if remaining > 0:
                m, s = int(remaining // 60), int(remaining % 60)
                e = utils.embed("⏳ Too Tired!", f"Rest for **{m}m {s}s** before working again.", color=utils.ORANGE)
                return await interaction.response.send_message(embed=e, ephemeral=True)

        job_name, job_action = random.choice(JOBS)
        pay     = random.randint(cfg["work_min_pay"], cfg["work_max_pay"])
        new_bal = db.update_balance(uid, pay, f"Work: {job_name}", STARTING)
        db.set_last_work(uid)

        level   = utils.xp_to_level(db.get_user(uid)["xp"])

        e = utils.embed("💼 Work Report", color=utils.GREEN)
        e.description = f"**{interaction.user.display_name}** {job_action}\nand earned {utils.money(pay)}!"
        e.add_field(name="💰 New Balance",  value=utils.money(new_bal),              inline=True)
        e.add_field(name="📊 Level",        value=f"Level {level}",                  inline=True)
        e.add_field(name="⏰ Next work",    value=f"In {cfg['work_cooldown_mins']}m", inline=True)
        e.set_footer(text="Dravia Department of Labour • 🦢")
        await interaction.response.send_message(embed=e)

    # ── /daily ────────────────────────────────────────────
    @app_commands.command(name="daily", description="Claim your daily Drav reward (once per day)")
    @app_commands.guilds(GUILD)
    async def daily(self, interaction: discord.Interaction):
        from datetime import date
        uid  = interaction.user.id
        data = db.get_user(uid, STARTING)

        if data.get("last_daily") == str(date.today()):
            e = utils.embed("📅 Already Claimed!", "You already claimed your daily reward today!\nCome back tomorrow.", color=utils.ORANGE)
            return await interaction.response.send_message(embed=e, ephemeral=True)

        reward  = random.randint(cfg["daily_min"], cfg["daily_max"])
        new_bal = db.update_balance(uid, reward, "Daily reward", STARTING)
        db.set_last_daily(uid)

        e = utils.embed("🎁 Daily Reward Claimed!", color=utils.GOLD)
        e.description = f"You collected your daily reward of {utils.money(reward)}!"
        e.add_field(name="💰 New Balance", value=utils.money(new_bal), inline=True)
        e.add_field(name="📅 Next reward", value="Tomorrow!",          inline=True)
        await interaction.response.send_message(embed=e)

    # ── /pay ──────────────────────────────────────────────
    @app_commands.command(name="pay", description="Send Drav to another citizen")
    @app_commands.guilds(GUILD)
    @app_commands.describe(citizen="Who to pay", amount="How many Drav", reason="What for")
    async def pay(self, interaction: discord.Interaction,
                  citizen: discord.Member, amount: int, reason: str = "No reason given"):

        sender = interaction.user
        if citizen.id == sender.id:
            return await interaction.response.send_message("❌ You can't pay yourself!", ephemeral=True)
        if citizen.bot:
            return await interaction.response.send_message("❌ You can't pay a bot!", ephemeral=True)
        if amount < 1:
            return await interaction.response.send_message("❌ Amount must be at least 1.", ephemeral=True)

        data = db.get_user(sender.id, STARTING)
        if data["balance"] < amount:
            e = utils.embed("❌ Insufficient Funds",
                f"You need {utils.money(amount)} but only have {utils.money(data['balance'])}.", color=utils.RED)
            return await interaction.response.send_message(embed=e, ephemeral=True)

        new_s = db.update_balance(sender.id,  -amount, f"Paid {citizen.name}: {reason}", STARTING)
        new_r = db.update_balance(citizen.id,  amount, f"Received from {sender.name}: {reason}", STARTING)

        e = utils.embed("💸 Drav Transfer", color=utils.GOLD)
        e.add_field(name="📤 From",        value=sender.mention,    inline=True)
        e.add_field(name="📥 To",          value=citizen.mention,   inline=True)
        e.add_field(name="💰 Amount",      value=utils.money(amount), inline=True)
        e.add_field(name="📝 Reason",      value=reason,            inline=False)
        e.add_field(name="Sender Balance", value=utils.money(new_s), inline=True)
        e.add_field(name="Receiver Bal",   value=utils.money(new_r), inline=True)
        await interaction.response.send_message(embed=e)

    # ── /leaderboard ──────────────────────────────────────
    @app_commands.command(name="leaderboard", description="Wealthiest citizens of Dravia")
    @app_commands.guilds(GUILD)
    async def leaderboard(self, interaction: discord.Interaction):
        await interaction.response.defer()
        top    = db.get_leaderboard(10)
        medals = ["🥇", "🥈", "🥉"]
        lines  = []
        for i, entry in enumerate(top):
            try:
                u = await self.bot.fetch_user(int(entry["id"]))
                name = u.display_name
            except:
                name = "Unknown"
            badge = medals[i] if i < 3 else f"`#{i+1}`"
            lines.append(f"{badge} **{name}** — {entry['balance']:,} {CURRENCY}")

        e = utils.embed("🏆 Dravia Wealth Leaderboard", "\n".join(lines) or "No citizens yet!", color=utils.GOLD)
        await interaction.followup.send(embed=e)

    # ── /history ──────────────────────────────────────────
    @app_commands.command(name="history", description="Your recent transaction history")
    @app_commands.guilds(GUILD)
    async def history(self, interaction: discord.Interaction):
        txs = db.get_transactions(interaction.user.id)
        if not txs:
            return await interaction.response.send_message("📭 No transactions yet!", ephemeral=True)

        lines = []
        for t in reversed(txs[-10:]):
            sign  = "+" if t["amount"] > 0 else ""
            emoji = "🟢" if t["amount"] > 0 else "🔴"
            lines.append(f"{emoji} `{sign}{t['amount']:,} {CURRENCY}` — {t['reason']} _{t['date'][:10]}_")

        e = utils.embed(f"📋 Transaction History", "\n".join(lines), color=utils.BLUE)
        e.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=e, ephemeral=True)

    # ── /deposit & /withdraw ──────────────────────────────
    @app_commands.command(name="deposit", description="Deposit Drav into your secure bank vault")
    @app_commands.guilds(GUILD)
    @app_commands.describe(amount="Amount to deposit (or 'all')")
    async def deposit(self, interaction: discord.Interaction, amount: int):
        uid  = interaction.user.id
        data = db.get_user(uid, STARTING)
        if amount < 1 or amount > data["balance"]:
            return await interaction.response.send_message(
                f"❌ Invalid amount. You have {utils.money(data['balance'])} in your wallet.", ephemeral=True)

        raw = db.raw()
        raw["users"][str(uid)]["balance"] -= amount
        raw["users"][str(uid)]["bank"]     = raw["users"][str(uid)].get("bank", 0) + amount
        raw["users"][str(uid)].setdefault("transactions", []).append(
            {"amount": -amount, "reason": f"Deposited to bank", "date": db._now()})
        db._save(raw)

        e = utils.embed("🏦 Deposit Successful", color=utils.GREEN)
        e.add_field(name="📥 Deposited",    value=utils.money(amount),                             inline=True)
        e.add_field(name="💳 Wallet",       value=utils.money(data["balance"] - amount),           inline=True)
        e.add_field(name="🏛️ Bank Vault",   value=utils.money(raw["users"][str(uid)]["bank"]),     inline=True)
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="withdraw", description="Withdraw Drav from your bank vault")
    @app_commands.guilds(GUILD)
    @app_commands.describe(amount="Amount to withdraw")
    async def withdraw(self, interaction: discord.Interaction, amount: int):
        uid  = interaction.user.id
        data = db.get_user(uid, STARTING)
        bank = data.get("bank", 0)
        if amount < 1 or amount > bank:
            return await interaction.response.send_message(
                f"❌ You only have {utils.money(bank)} in your vault.", ephemeral=True)

        raw = db.raw()
        raw["users"][str(uid)]["balance"] += amount
        raw["users"][str(uid)]["bank"]    -= amount
        raw["users"][str(uid)].setdefault("transactions", []).append(
            {"amount": amount, "reason": "Withdrew from bank", "date": db._now()})
        db._save(raw)

        e = utils.embed("🏦 Withdrawal Successful", color=utils.GREEN)
        e.add_field(name="📤 Withdrawn",  value=utils.money(amount),         inline=True)
        e.add_field(name="💳 Wallet",     value=utils.money(data["balance"] + amount), inline=True)
        e.add_field(name="🏛️ Vault",      value=utils.money(bank - amount),  inline=True)
        await interaction.response.send_message(embed=e)


async def setup(bot):
    await bot.add_cog(Economy(bot))
