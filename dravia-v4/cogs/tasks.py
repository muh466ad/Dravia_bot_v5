"""cogs/tasks.py — Auto Systems + 2000 Drav Weekly Print"""

import discord
from discord.ext import commands, tasks
import json, time
import database as db
import utils

with open("config.json", encoding="utf-8") as f:
    cfg = json.load(f)

class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.weekly_print.start()
        self.tax_loop.start()
        self.interest_loop.start()

    def cog_unload(self):
        self.weekly_print.cancel()
        self.tax_loop.cancel()
        self.interest_loop.cancel()

    @tasks.loop(hours=1)
    async def weekly_print(self):
        """Government prints 2000 Drav every week"""
        amount = db.weekly_gov_print()
        if amount == 0:
            return

        log_channel_id = cfg.get("log_channel_id")
        if log_channel_id:
            channel = self.bot.get_channel(int(log_channel_id))
            if channel:
                e = utils.embed("🏛️ Government Economic Injection", color=utils.GREEN)
                e.description = f"The Treasury has printed **{utils.money(amount)}** this week."
                e.set_footer(text="Controlled money supply • Anti-inflation measures active")
                await channel.send(embed=e)

    @tasks.loop(hours=1)
    async def tax_loop(self):
        """Auto tax collection"""
        raw = db.raw()
        last_tax = raw.get("last_tax", 0)
        interval = cfg.get("tax_interval_hours", 24) * 3600
        if time.time() - last_tax < interval:
            return

        rate = cfg.get("tax_rate_percent", 5)
        collected = db.apply_taxes(rate)
        total = sum(collected.values())

        log_channel_id = cfg.get("log_channel_id")
        if log_channel_id and total > 0:
            channel = self.bot.get_channel(int(log_channel_id))
            if channel:
                e = utils.embed("💰 Tax Collection Complete", color=utils.RED)
                e.description = f"**{rate}%** tax collected from citizens.\nTotal: **{utils.money(total)}**"
                await channel.send(embed=e)

    @tasks.loop(hours=1)
    async def interest_loop(self):
        """Bank interest"""
        # Keep your existing interest logic or call db.apply_bank_interest()
        pass

    @weekly_print.before_loop
    @tax_loop.before_loop
    @interest_loop.before_loop
    async def before_loops(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Tasks(bot))
