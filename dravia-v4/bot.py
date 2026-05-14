"""
╔═══════════════════════════════════════════════════════╗
║           DRAVIA ECONOMY BOT  v4.0                    ║
║           Nation of Law and Unity                     ║
║                                                       ║
║  Cogs:                                                ║
║   economy   — balance, work, pay, daily, bank         ║
║   profile   — profile cards, inventory, achievements  ║
║   shop      — government shop                         ║
║   art        — art marketplace                        ║
║   court     — complaints, evidence, appeals           ║
║   gov        — treasury, salary, taxes, stats         ║
║   business  — open shops, sell products               ║
║   fun        — blackjack, dice, slots, rob, lottery   ║
║   votes     — democratic voting system                ║
║   tasks      — auto tax & interest scheduler          ║
╚═══════════════════════════════════════════════════════╝
"""

import discord, json, os
from discord.ext import commands

with open("config.json", encoding="utf-8") as f:
    config = json.load(f)

config["token"] = os.environ.get("token", config["token"])

intents         = discord.Intents.default()
intents.members = True

bot        = commands.Bot(command_prefix="d!", intents=intents)
bot.config = config

COGS = [
 "cogs.economy", "cogs.profile", "cogs.shop",
 "cogs.art", "cogs.court", "cogs.gov",
 "cogs.business", "cogs.fun", "cogs.votes",
 "cogs.tasks", "cogs.citizen_id"  # ← ADD THIS LINE
]

@bot.event
async def on_ready():
    print(f"\n{'═'*55}")
    print(f"  🦢  DRAVIA BOT v4.0 — ONLINE")
    print(f"  User : {bot.user}")
    print(f"{'═'*55}\n")
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"  ✅  {cog}")
        except Exception as e:
            print(f"  ❌  {cog}: {e}")
    try:
        guild  = discord.Object(id=int(config["guild_id"]))
        synced = await bot.tree.sync(guild=guild)
        print(f"\n  ✅  {len(synced)} slash commands synced\n")
    except Exception as e:
        print(f"  ❌  Sync failed: {e}\n")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="over the Dravia economy 🦢"
        )
    )

@bot.event
async def on_member_join(member):
    import database as db
    db.get_user(member.id, config["starting_balance"])
    channel_id = config.get("welcome_channel_id")
    if not channel_id: return
    channel = bot.get_channel(int(channel_id))
    if not channel: return
    e = discord.Embed(
        title="🦢 Welcome to Dravia!",
        description=(
            f"Welcome, {member.mention}! You are now **Citizen #{db.get_user(member.id)['citizen_id']}** of Dravia.\n\n"
            f"You have been given **{config['starting_balance']} {config['currency']}** to start your life here.\n\n"
            f"➡️ `/work` to earn Drav\n"
            f"➡️ `/daily` for your daily reward\n"
            f"➡️ `/profile` to see your citizen card\n"
            f"➡️ `/shop browse` to spend your Drav"
        ),
        color=0xFFB300
    )
    e.set_thumbnail(url=member.display_avatar.url)
    e.set_footer(text="Dravia — Nation of Law and Unity")
    await channel.send(embed=e)

bot.run(config["token"])
