"""cogs/fun.py — Gambling and fun economy commands"""

import discord
from discord import app_commands
from discord.ext import commands
import json, time, random
import database as db
import utils

with open("config.json", encoding="utf-8") as f:
    cfg = json.load(f)

GUILD    = discord.Object(id=int(cfg["guild_id"]))
STARTING = cfg["starting_balance"]
ROB_CD   = cfg["rob_cooldown_mins"] * 60


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── /coinflip ─────────────────────────────────────────
    @app_commands.command(name="coinflip", description="Bet your Drav on a coin flip!")
    @app_commands.guilds(GUILD)
    @app_commands.describe(amount="How much to bet", side="Heads or tails?")
    @app_commands.choices(side=[
        app_commands.Choice(name="Heads", value="heads"),
        app_commands.Choice(name="Tails", value="tails"),
    ])
    async def coinflip(self, interaction: discord.Interaction, amount: int, side: str):
        uid  = interaction.user.id
        data = db.get_user(uid, STARTING)

        if amount < 1:
            return await interaction.response.send_message("❌ Bet at least 1 Drav.", ephemeral=True)
        if amount > data["balance"]:
            e = utils.embed("❌ Not Enough Drav",
                f"You only have {utils.money(data['balance'])}.", color=utils.RED)
            return await interaction.response.send_message(embed=e, ephemeral=True)

        result = random.choice(["heads", "tails"])
        won    = result == side
        emoji  = "🪙"
        coin   = "HEADS 👑" if result == "heads" else "TAILS 🦢"

        if won:
            new_bal = db.update_balance(uid, amount, f"Coinflip win ({side})", STARTING)
            e = utils.embed(f"{emoji} Coinflip — YOU WIN!", color=utils.GREEN)
            e.description = f"The coin landed on **{coin}**!\nYou bet {side} and **WON** {utils.money(amount)}!"
        else:
            new_bal = db.update_balance(uid, -amount, f"Coinflip loss ({side})", STARTING)
            e = utils.embed(f"{emoji} Coinflip — You lost.", color=utils.RED)
            e.description = f"The coin landed on **{coin}**.\nYou bet {side} and lost {utils.money(amount)}."

        e.add_field(name="💰 New Balance", value=utils.money(new_bal), inline=True)
        await interaction.response.send_message(embed=e)

    # ── /lottery ──────────────────────────────────────────
    @app_commands.command(name="lottery", description="Buy a lottery ticket for a chance at the jackpot!")
    @app_commands.guilds(GUILD)
    async def lottery(self, interaction: discord.Interaction):
        uid       = interaction.user.id
        data      = db.get_user(uid, STARTING)
        ticket_cost = cfg["lottery_ticket_cost"]
        lottery   = db.get_lottery()

        if data["balance"] < ticket_cost:
            return await interaction.response.send_message(
                f"❌ A ticket costs {utils.money(ticket_cost)}. You only have {utils.money(data['balance'])}.",
                ephemeral=True)

        db.update_balance(uid, -ticket_cost, "Lottery ticket", STARTING)
        total_tickets = db.buy_lottery_ticket(uid, ticket_cost)
        lottery       = db.get_lottery()

        e = utils.embed("🎰 Lottery Ticket Purchased!", color=utils.GOLD)
        e.description = f"Good luck, **{interaction.user.display_name}**!"
        e.add_field(name="🎟️ Ticket Cost",    value=utils.money(ticket_cost),        inline=True)
        e.add_field(name="💰 Current Pool",   value=utils.money(lottery["pool"]),    inline=True)
        e.add_field(name="🎟️ Total Tickets",  value=str(total_tickets),              inline=True)
        e.set_footer(text="Use /lottery draw to pick a winner! (Admin only)")
        await interaction.response.send_message(embed=e)

    # ── /lottery draw (admin) ─────────────────────────────
    @app_commands.command(name="lotterydraw", description="Draw the lottery winner [Admin only]")
    @app_commands.guilds(GUILD)
    async def lotterydraw(self, interaction: discord.Interaction):
        if not utils.is_admin(interaction.member):
            return await interaction.response.send_message("❌ Admin only!", ephemeral=True)

        lottery = db.get_lottery()
        tickets = lottery.get("tickets", [])

        if not tickets:
            return await interaction.response.send_message("❌ No tickets sold yet!", ephemeral=True)

        winner_id = random.choice(tickets)
        pool      = lottery["pool"]

        db.update_balance(int(winner_id), pool, "Lottery jackpot win!", STARTING)
        db.reset_lottery(winner_id)

        try:
            winner = await self.bot.fetch_user(int(winner_id))
            winner_text = winner.mention
        except:
            winner_text = f"<@{winner_id}>"

        e = utils.embed("🎰 LOTTERY DRAW!", color=utils.GOLD)
        e.description = (
            f"🥁 *The drum rolls...*\n\n"
            f"🎉 **{winner_text}** wins the jackpot!\n\n"
            f"💰 Prize: {utils.money(pool)}"
        )
        e.add_field(name="🎟️ Total Tickets", value=str(len(tickets)), inline=True)
        e.add_field(name="💰 Prize Pool",    value=utils.money(pool), inline=True)
        await interaction.response.send_message(embed=e)

    # ── /rob ──────────────────────────────────────────────
    @app_commands.command(name="rob", description="Try to rob another citizen... risky!")
    @app_commands.guilds(GUILD)
    @app_commands.describe(citizen="Who to rob (risky — you could get caught!)")
    async def rob(self, interaction: discord.Interaction, citizen: discord.Member):
        robber = interaction.user
        uid    = robber.id

        if citizen.id == uid:
            return await interaction.response.send_message("❌ Can't rob yourself!", ephemeral=True)
        if citizen.bot:
            return await interaction.response.send_message("❌ Can't rob a bot!", ephemeral=True)

        robber_data = db.get_user(uid, STARTING)
        victim_data = db.get_user(citizen.id, STARTING)

        # Cooldown check
        last_rob = robber_data.get("last_rob")
        if last_rob:
            remaining = ROB_CD - (time.time() - last_rob)
            if remaining > 0:
                m = int(remaining // 60)
                return await interaction.response.send_message(
                    f"⏳ You're laying low after your last attempt. Try again in **{m} minutes**.",
                    ephemeral=True)

        if victim_data["balance"] < 10:
            return await interaction.response.send_message(
                f"❌ **{citizen.display_name}** is too broke to rob!", ephemeral=True)

        db.set_last_rob(uid)
        success_chance = cfg.get("rob_success_chance", 40)
        success        = random.randint(1, 100) <= success_chance

        if success:
            pct    = random.randint(cfg.get("rob_min_percent", 10), cfg.get("rob_max_percent", 30))
            stolen = max(1, int(victim_data["balance"] * pct / 100))
            db.update_balance(citizen.id, -stolen, f"Robbed by {robber.name}", STARTING)
            db.update_balance(uid,         stolen, f"Robbed {citizen.name}",   STARTING)
            new_bal = db.get_balance(uid)

            e = utils.embed("🦹 Robbery Successful!", color=utils.GREEN)
            e.description = (
                f"You snuck into **{citizen.display_name}**'s house\n"
                f"and stole {utils.money(stolen)} ({pct}% of their wallet)!"
            )
            e.add_field(name="💰 Stolen",     value=utils.money(stolen),  inline=True)
            e.add_field(name="💳 Your Bal",   value=utils.money(new_bal), inline=True)
            e.set_footer(text="⚠️ Victim can file a /complaint against you!")
        else:
            fine = random.randint(10, 30)
            fine = min(fine, robber_data["balance"])
            db.update_balance(uid, -fine, f"Caught robbing {citizen.name}", STARTING)
            new_bal = db.get_balance(uid)

            e = utils.embed("🚔 Caught Red-Handed!", color=utils.RED)
            e.description = (
                f"You tried to rob **{citizen.display_name}** but got caught!\n"
                f"You were fined {utils.money(fine)} by the police."
            )
            e.add_field(name="💸 Fine Paid",  value=utils.money(fine),    inline=True)
            e.add_field(name="💳 Your Bal",   value=utils.money(new_bal), inline=True)
            e.set_footer(text="Better luck next time, criminal.")

        await interaction.response.send_message(embed=e)


async def setup(bot):
    await bot.add_cog(Fun(bot))
