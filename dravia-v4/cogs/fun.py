"""cogs/fun.py — Blackjack, Dice, Slots, Rob, Lottery"""

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

# ── Blackjack helpers ─────────────────────────────────────
SUITS  = ["♠️","♥️","♦️","♣️"]
VALUES = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"]

def new_deck():
    deck = [f"{v}{s}" for s in SUITS for v in VALUES]
    random.shuffle(deck)
    return deck

def card_value(card):
    v = card[:-2] if len(card) > 2 else card[0]
    if v in ("J","Q","K"): return 10
    if v == "A":           return 11
    return int(v)

def hand_value(hand):
    total = sum(card_value(c) for c in hand)
    aces  = sum(1 for c in hand if c.startswith("A"))
    while total > 21 and aces:
        total -= 10; aces -= 1
    return total

def hand_str(hand): return " ".join(hand)


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bj_games = {}  # user_id → game state

    # ── /coinflip ─────────────────────────────────────────
    @app_commands.command(name="coinflip", description="Bet Drav on a coin flip!")
    @app_commands.guilds(GUILD)
    @app_commands.describe(amount="How much to bet", side="Heads or tails?")
    @app_commands.choices(side=[
        app_commands.Choice(name="Heads", value="heads"),
        app_commands.Choice(name="Tails", value="tails"),
    ])
    async def coinflip(self, interaction: discord.Interaction, amount: int, side: str):
        uid  = interaction.user.id
        data = db.get_user(uid, STARTING)
        if amount < 1 or amount > data["balance"]:
            return await interaction.response.send_message(f"❌ Invalid bet. You have {utils.money(data['balance'])}.", ephemeral=True)
        result = random.choice(["heads","tails"])
        won    = result == side
        coin   = "HEADS 👑" if result == "heads" else "TAILS 🦢"
        if won:
            new_bal = db.update_balance(uid, amount,  f"Coinflip win",  STARTING)
            e = utils.embed("🪙 You WIN!", f"Coin landed **{coin}**!\nYou bet {side} and won {utils.money(amount)}!", color=utils.GREEN)
        else:
            new_bal = db.update_balance(uid, -amount, f"Coinflip loss", STARTING)
            e = utils.embed("🪙 You lost.", f"Coin landed **{coin}**.\nYou bet {side} and lost {utils.money(amount)}.", color=utils.RED)
        e.add_field(name="💰 Balance", value=utils.money(new_bal), inline=True)
        await interaction.response.send_message(embed=e)

    # ── /dice ─────────────────────────────────────────────
    @app_commands.command(name="dice", description="Roll dice and bet on the outcome!")
    @app_commands.guilds(GUILD)
    @app_commands.describe(amount="Bet amount", guess="Guess the total (2–12)")
    async def dice(self, interaction: discord.Interaction, amount: int, guess: int):
        uid  = interaction.user.id
        data = db.get_user(uid, STARTING)
        if amount < 1 or amount > data["balance"]:
            return await interaction.response.send_message(f"❌ Invalid bet.", ephemeral=True)
        if guess < 2 or guess > 12:
            return await interaction.response.send_message("❌ Guess must be between 2 and 12!", ephemeral=True)
        d1   = random.randint(1,6); d2 = random.randint(1,6)
        roll = d1 + d2
        won  = roll == guess
        mult = 6 if guess in (2,12) else 4 if guess in (3,11) else 3 if guess in (4,10) else 2
        if won:
            winnings = amount * mult
            new_bal  = db.update_balance(uid, winnings, f"Dice win (rolled {roll})", STARTING)
            e = utils.embed(f"🎲 You WIN! ({mult}x)", f"Dice: **{d1}** + **{d2}** = **{roll}**\nYou guessed {guess} and won {utils.money(winnings)}!", color=utils.GREEN)
        else:
            new_bal = db.update_balance(uid, -amount, f"Dice loss (rolled {roll})", STARTING)
            e = utils.embed("🎲 Wrong guess!", f"Dice: **{d1}** + **{d2}** = **{roll}**\nYou guessed {guess} and lost {utils.money(amount)}.", color=utils.RED)
        e.add_field(name="💰 Balance", value=utils.money(new_bal), inline=True)
        await interaction.response.send_message(embed=e)

    # ── /slots ────────────────────────────────────────────
    @app_commands.command(name="slots", description="Spin the slot machine!")
    @app_commands.guilds(GUILD)
    @app_commands.describe(amount="How much to bet")
    async def slots(self, interaction: discord.Interaction, amount: int):
        uid  = interaction.user.id
        data = db.get_user(uid, STARTING)
        if amount < 1 or amount > data["balance"]:
            return await interaction.response.send_message(f"❌ Invalid bet. You have {utils.money(data['balance'])}.", ephemeral=True)

        SYMBOLS = ["🍒","🍋","🍊","🍇","⭐","💎","🦢"]
        WEIGHTS = [30,  25,  20,  15,  6,   3,   1]
        reels   = random.choices(SYMBOLS, weights=WEIGHTS, k=3)

        if reels[0] == reels[1] == reels[2]:
            sym = reels[0]
            mult = {"🦢":50,"💎":20,"⭐":10,"🍇":5,"🍊":4,"🍋":3,"🍒":2}.get(sym, 2)
            win  = amount * mult
            new_bal = db.update_balance(uid, win, f"Slots jackpot ({sym}x{mult})", STARTING)
            e = utils.embed(f"🎰 JACKPOT! {mult}x!", f"**{' | '.join(reels)}**\n\nThree {sym}! You won {utils.money(win)}!", color=utils.GOLD)
        elif reels[0] == reels[1] or reels[1] == reels[2]:
            win = amount
            new_bal = db.update_balance(uid, win, "Slots pair win", STARTING)
            e = utils.embed("🎰 Pair! 1x", f"**{' | '.join(reels)}**\n\nA pair! You got your bet back plus {utils.money(win)}!", color=utils.GREEN)
        else:
            new_bal = db.update_balance(uid, -amount, "Slots loss", STARTING)
            e = utils.embed("🎰 No luck!", f"**{' | '.join(reels)}**\n\nNo match. You lost {utils.money(amount)}.", color=utils.RED)

        e.add_field(name="💰 Balance", value=utils.money(new_bal), inline=True)
        await interaction.response.send_message(embed=e)

    # ── /blackjack ────────────────────────────────────────
    @app_commands.command(name="blackjack", description="Play blackjack against the dealer!")
    @app_commands.guilds(GUILD)
    @app_commands.describe(amount="How much to bet")
    async def blackjack(self, interaction: discord.Interaction, amount: int):
        uid  = interaction.user.id
        data = db.get_user(uid, STARTING)
        if amount < 1 or amount > data["balance"]:
            return await interaction.response.send_message(f"❌ Invalid bet.", ephemeral=True)
        if uid in self.bj_games:
            return await interaction.response.send_message("❌ You already have an active blackjack game! Use `/hit` or `/stand`.", ephemeral=True)

        deck          = new_deck()
        player_hand   = [deck.pop(), deck.pop()]
        dealer_hand   = [deck.pop(), deck.pop()]
        self.bj_games[uid] = {"bet": amount, "deck": deck, "player": player_hand, "dealer": dealer_hand}
        db.update_balance(uid, -amount, "Blackjack bet", STARTING)

        pval = hand_value(player_hand)
        e    = utils.embed("🃏 Blackjack!", color=utils.BLUE)
        e.add_field(name="Your hand", value=f"{hand_str(player_hand)} = **{pval}**", inline=False)
        e.add_field(name="Dealer shows", value=f"{dealer_hand[0]} + 🂠", inline=False)
        e.add_field(name="Bet", value=utils.money(amount), inline=True)

        if pval == 21:
            win = int(amount * 2.5)
            db.update_balance(uid, win, "Blackjack natural!", STARTING)
            del self.bj_games[uid]
            e.color = utils.GOLD
            e.title = "🃏 BLACKJACK! Natural 21!"
            e.add_field(name="💰 Won", value=utils.money(win), inline=True)
        else:
            e.set_footer(text="Use /hit to draw a card or /stand to hold")
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="hit", description="Draw another card in blackjack")
    @app_commands.guilds(GUILD)
    async def hit(self, interaction: discord.Interaction):
        uid  = interaction.user.id
        if uid not in self.bj_games:
            return await interaction.response.send_message("❌ No active game! Start with `/blackjack`.", ephemeral=True)
        game = self.bj_games[uid]
        game["player"].append(game["deck"].pop())
        pval = hand_value(game["player"])
        e    = utils.embed("🃏 Hit!", color=utils.BLUE)
        e.add_field(name="Your hand",    value=f"{hand_str(game['player'])} = **{pval}**", inline=False)
        e.add_field(name="Dealer shows", value=f"{game['dealer'][0]} + 🂠",                inline=False)
        if pval > 21:
            del self.bj_games[uid]
            e.color = utils.RED
            e.title = "🃏 BUST! You lose."
            e.add_field(name="💸 Lost", value=utils.money(game["bet"]), inline=True)
        elif pval == 21:
            await self._resolve_stand(interaction, uid, game, e)
            return
        else:
            e.set_footer(text="Use /hit to draw again or /stand to hold")
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="stand", description="Hold your hand in blackjack")
    @app_commands.guilds(GUILD)
    async def stand(self, interaction: discord.Interaction):
        uid  = interaction.user.id
        if uid not in self.bj_games:
            return await interaction.response.send_message("❌ No active game!", ephemeral=True)
        game = self.bj_games[uid]
        e    = utils.embed("🃏 Stand", color=utils.BLUE)
        await self._resolve_stand(interaction, uid, game, e)

    async def _resolve_stand(self, interaction, uid, game, e):
        while hand_value(game["dealer"]) < 17:
            game["dealer"].append(game["deck"].pop())
        pval = hand_value(game["player"])
        dval = hand_value(game["dealer"])
        e.add_field(name="Your hand",    value=f"{hand_str(game['player'])} = **{pval}**", inline=False)
        e.add_field(name="Dealer hand",  value=f"{hand_str(game['dealer'])} = **{dval}**", inline=False)
        if dval > 21 or pval > dval:
            win = game["bet"] * 2
            db.update_balance(uid, win, "Blackjack win", STARTING)
            e.color = utils.GREEN; e.title = "🃏 You WIN!"
            e.add_field(name="💰 Won", value=utils.money(win), inline=True)
        elif pval == dval:
            db.update_balance(uid, game["bet"], "Blackjack push", STARTING)
            e.color = utils.ORANGE; e.title = "🃏 Push! Tie game."
            e.add_field(name="↩️ Refunded", value=utils.money(game["bet"]), inline=True)
        else:
            e.color = utils.RED; e.title = "🃏 Dealer wins."
            e.add_field(name="💸 Lost", value=utils.money(game["bet"]), inline=True)
        del self.bj_games[uid]
        await interaction.response.send_message(embed=e)

    # ── /lottery ──────────────────────────────────────────
    @app_commands.command(name="lottery", description="Buy a lottery ticket!")
    @app_commands.guilds(GUILD)
    async def lottery(self, interaction: discord.Interaction):
        uid     = interaction.user.id
        cost    = cfg["lottery_ticket_cost"]
        data    = db.get_user(uid, STARTING)
        lottery = db.get_lottery()
        if data["balance"] < cost:
            return await interaction.response.send_message(f"❌ A ticket costs {utils.money(cost)}.", ephemeral=True)
        db.update_balance(uid, -cost, "Lottery ticket", STARTING)
        total = db.buy_lottery_ticket(uid, cost)
        lottery = db.get_lottery()
        e = utils.embed("🎰 Ticket Purchased!", color=utils.GOLD)
        e.add_field(name="🎟️ Cost",           value=utils.money(cost),          inline=True)
        e.add_field(name="💰 Current Pool",   value=utils.money(lottery["pool"]),inline=True)
        e.add_field(name="🎟️ Total Tickets",  value=str(total),                 inline=True)
        e.set_footer(text="Admin uses /lotterydraw to pick the winner!")
        await interaction.response.send_message(embed=e)

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
        db.update_balance(int(winner_id), pool, "Lottery jackpot!", STARTING)
        db.unlock_achievement(winner_id, "lottery_win")
        db.reset_lottery(winner_id)
        try:    winner = await self.bot.fetch_user(int(winner_id)); wtext = winner.mention
        except: wtext  = f"<@{winner_id}>"
        e = utils.embed("🎰 LOTTERY DRAW!", color=utils.GOLD)
        e.description = f"🥁 *The drum rolls...*\n\n🎉 **{wtext}** wins the jackpot!\n💰 Prize: {utils.money(pool)}"
        e.add_field(name="🎟️ Tickets Sold", value=str(len(tickets)), inline=True)
        await interaction.response.send_message(embed=e)

    # ── /rob ──────────────────────────────────────────────
    @app_commands.command(name="rob", description="Try to rob someone... risky!")
    @app_commands.guilds(GUILD)
    @app_commands.describe(citizen="Who to rob")
    async def rob(self, interaction: discord.Interaction, citizen: discord.Member):
        robber = interaction.user; uid = robber.id
        if citizen.id == uid or citizen.bot:
            return await interaction.response.send_message("❌ Invalid target!", ephemeral=True)
        robber_data = db.get_user(uid, STARTING)
        victim_data = db.get_user(citizen.id, STARTING)
        if robber_data.get("last_rob"):
            rem = ROB_CD - (time.time() - robber_data["last_rob"])
            if rem > 0:
                return await interaction.response.send_message(
                    f"⏳ Lay low for **{int(rem//60)} more minutes**.", ephemeral=True)
        if victim_data["balance"] < 10:
            return await interaction.response.send_message(f"❌ {citizen.display_name} is too broke!", ephemeral=True)
        db.set_last_rob(uid)
        if random.randint(1,100) <= cfg.get("rob_success_chance", 40):
            pct    = random.randint(cfg.get("rob_min_percent",10), cfg.get("rob_max_percent",30))
            stolen = max(1, int(victim_data["balance"] * pct / 100))
            db.update_balance(citizen.id, -stolen, f"Robbed by {robber.name}", STARTING)
            db.update_balance(uid,         stolen, f"Robbed {citizen.name}",   STARTING)
            db.unlock_achievement(uid, "rob_success")
            e = utils.embed("🦹 Robbery Successful!", color=utils.GREEN)
            e.description = f"You snuck into **{citizen.display_name}**'s house and stole {utils.money(stolen)}!"
            e.add_field(name="💰 Your Balance", value=utils.money(db.get_balance(uid)), inline=True)
            e.set_footer(text="⚠️ Victim can /complaint against you!")
        else:
            fine = min(random.randint(10,40), robber_data["balance"])
            db.update_balance(uid, -fine, f"Caught robbing {citizen.name}", STARTING)
            e = utils.embed("🚔 Caught Red-Handed!", color=utils.RED)
            e.description = f"You tried to rob **{citizen.display_name}** but got caught!\nFined {utils.money(fine)} by the police."
            e.add_field(name="💰 Your Balance", value=utils.money(db.get_balance(uid)), inline=True)
        await interaction.response.send_message(embed=e)


async def setup(bot): await bot.add_cog(Fun(bot))
