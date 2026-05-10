"""
╔═══════════════════════════════════════════════════╗
║         DRAVIA ECONOMY BOT  v3.0                  ║
║         Nation of Law and Unity                   ║
║                                                   ║
║  Cogs:                                            ║
║   • economy  — balance, work, pay, daily          ║
║   • profile  — citizen profile cards              ║
║   • shop     — government shop & items            ║
║   • art      — art marketplace                    ║
║   • court    — complaints, fines, verdicts        ║
║   • gov      — treasury, salary, stats            ║
║   • fun      — coinflip, lottery, rob             ║
╚═══════════════════════════════════════════════════╝
"""

import discord
from discord.ext import commands
import json, os, asyncio

with open("config.json", encoding="utf-8") as f:
    config = json.load(f)

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="d!", intents=intents)
bot.config = config

COGS = [
    "cogs.economy",
    "cogs.profile",
    "cogs.shop",
    "cogs.art",
    "cogs.court",
    "cogs.gov",
    "cogs.fun",
]

@bot.event
async def on_ready():
    print(f"\n{'═'*50}")
    print(f"  🦢  DRAVIA BOT v3.0 — ONLINE")
    print(f"  User : {bot.user}")
    print(f"  Guild: {config['guild_id']}")
    print(f"{'═'*50}\n")

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
    """Give starter balance + welcome message when someone joins."""
    import database as db
    db.get_user(member.id, config["starting_balance"])

    channel_id = config.get("welcome_channel_id")
    if not channel_id:
        return

    channel = bot.get_channel(int(channel_id))
    if not channel:
        return

    embed = discord.Embed(
        title="🦢 Welcome to Dravia!",
        description=(
            f"Welcome, {member.mention}! You are now a citizen of **Dravia**.\n\n"
            f"You have been given **{config['starting_balance']} {config['currency']}** to start your life here.\n\n"
            f"Use `/work` to earn more, `/balance` to check your funds,\n"
            f"and `/shop` to see what you can buy!"
        ),
        color=0xFFB300
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="Dravia — Nation of Law and Unity")
    await channel.send(embed=embed)

bot.run(config["token"])
