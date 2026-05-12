"""cogs/tasks.py — Automatic tax collection and bank interest"""

import discord
from discord.ext import commands, tasks
import json, time
import database as db
import utils

with open("config.json", encoding="utf-8") as f:
    cfg = json.load(f)


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot        = bot
        self.tax_loop.start()
        self.interest_loop.start()

    def cog_unload(self):
        self.tax_loop.cancel()
        self.interest_loop.cancel()

    @tasks.loop(hours=1)
    async def tax_loop(self):
        """Check if 24 hours have passed and collect taxes."""
        raw       = db.raw()
        last_tax  = raw.get("last_tax", 0)
        interval  = cfg.get("tax_interval_hours", 24) * 3600
        if time.time() - last_tax < interval:
            return

        rate      = cfg.get("tax_rate_percent", 5)
        collected = db.apply_taxes(rate)
        total     = sum(collected.values())

        log_channel_id = cfg.get("log_channel_id")
        if not log_channel_id: return

        channel = self.bot.get_channel(int(log_channel_id))
        if not channel: return

        e = utils.embed("🏛️ Tax Collection Complete", color=utils.RED)
        e.description = (
            f"The government has collected **{rate}%** tax from all citizens.\n\n"
            f"👥 Citizens taxed: **{len(collected)}**\n"
            f"💰 Total collected: **{total:,} {cfg['currency']}**"
        )
        e.set_footer(text="Dravia Treasury Department")
        await channel.send(embed=e)

    @tasks.loop(hours=1)
    async def interest_loop(self):
        """Pay bank interest every 24 hours."""
        raw           = db.raw()
        last_interest = raw.get("last_interest", 0)
        interval      = 24 * 3600
        if time.time() - last_interest < interval:
            return

        rate = cfg.get("bank_interest_rate", 2)
        paid = db.apply_bank_interest(rate)
        total = sum(paid.values())

        log_channel_id = cfg.get("log_channel_id")
        if not log_channel_id: return

        channel = self.bot.get_channel(int(log_channel_id))
        if not channel: return

        e = utils.embed("🏦 Bank Interest Paid", color=utils.GREEN)
        e.description = (
            f"**{rate}%** interest has been paid to all vault holders!\n\n"
            f"👥 Citizens paid: **{len(paid)}**\n"
            f"💰 Total paid out: **{total:,} {cfg['currency']}**"
        )
        e.set_footer(text="Dravia National Bank")
        await channel.send(embed=e)

    @tax_loop.before_loop
    @interest_loop.before_loop
    async def before_loops(self):
        await self.bot.wait_until_ready()


async def setup(bot): await bot.add_cog(Tasks(bot))
