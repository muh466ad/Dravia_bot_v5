"""cogs/shop.py — Government shop"""
import discord
from discord import app_commands
from discord.ext import commands
import json
import database as db
import utils

with open("config.json", encoding="utf-8") as f:
    cfg = json.load(f)

GUILD = discord.Object(id=int(cfg["guild_id"]))

class Shop(commands.Cog):
    def __init__(self, bot): self.bot = bot

    shop = app_commands.Group(name="shop", description="Government Shop", guild_ids=[int(cfg["guild_id"])])

    @shop.command(name="browse", description="Browse shop items")
    @utils.require_citizen
    async def browse(self, interaction: discord.Interaction):
        items = db.get_shop()
        e = utils.embed("🏪 Dravia Government Shop", color=utils.GOLD)
        for item in items:
            e.add_field(
                name=f"{item['emoji']} {item['name']} • ID #{item['id']}",
                value=f"{item['description']}\n💰 **{item['price']:,} {cfg['currency']}**",
                inline=False
            )
        e.set_footer(text="Use /shop buy [id]")
        await interaction.response.send_message(embed=e)

    @shop.command(name="buy", description="Buy item")
    @app_commands.describe(item_id="Item ID")
    @utils.require_citizen
    async def buy(self, interaction: discord.Interaction, item_id: int):
        item = db.get_shop_item(item_id)
        if not item:
            return await interaction.response.send_message("❌ Item not found!", ephemeral=True)
        
        data = db.get_user(interaction.user.id, cfg["starting_balance"])
        if data["balance"] < item["price"]:
            return await interaction.response.send_message(f"❌ Need {utils.money(item['price'])}!", ephemeral=True)
        
        db.update_balance(interaction.user.id, -item["price"], f"Bought: {item['name']}", cfg["starting_balance"])
        db.update_treasury(item["price"], f"Shop sale: {item['name']}")
        db.add_to_inventory(interaction.user.id, item)
        
        e = utils.embed(f"✅ Purchased — {item['name']}", color=utils.GREEN)
        e.description = f"{item['emoji']} {item['description']}\n💸 Paid {utils.money(item['price'])}"
        await interaction.response.send_message(embed=e)

async def setup(bot): await bot.add_cog(Shop(bot))
