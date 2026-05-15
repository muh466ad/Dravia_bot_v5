"""cogs/marketplace.py — Unified Marketplace"""
import discord
from discord import app_commands
from discord.ext import commands
import json
import database as db
import utils

with open("config.json", encoding="utf-8") as f:
    cfg = json.load(f)

GUILD = discord.Object(id=int(cfg["guild_id"]))

class Marketplace(commands.Cog):
    def __init__(self, bot): self.bot = bot

    market = app_commands.Group(name="market", description="Dravia Marketplace", guild_ids=[int(cfg["guild_id"])])

    @market.command(name="browse", description="Browse marketplace listings")
    @app_commands.describe(category="Filter by category")
    @utils.require_citizen
    async def browse(self, interaction: discord.Interaction, category: str = None):
        listings = db.get_marketplace_listings(category=category)
        if not listings:
            return await interaction.response.send_message("🏪 No listings found!", ephemeral=True)
        
        e = utils.embed("🏪 Dravia Marketplace", color=utils.ORANGE)
        for listing in listings[:10]:
            e.add_field(
                name=f"#{listing['id']} — {listing['title']}",
                value=f"💰 {listing['price']:,} {cfg['currency']} | Seller: <@{listing['seller_id']}>",
                inline=False
            )
        e.set_footer(text="Use /market buy [id] to purchase")
        await interaction.response.send_message(embed=e)

    @market.command(name="sell", description="List an item for sale")
    @app_commands.describe(title="Item title", price="Price in Drav", description="Description")
    @utils.require_citizen
    async def sell(self, interaction: discord.Interaction, title: str, price: int, description: str):
        if price < 1:
            return await interaction.response.send_message("❌ Price must be at least 1 Drav!", ephemeral=True)
        
        fee = cfg["marketplace_listing_fee"]
        data = db.get_user(interaction.user.id, cfg["starting_balance"])
        
        if data["balance"] < fee:
            return await interaction.response.send_message(f"❌ Listing fee is {utils.money(fee)}.", ephemeral=True)
        
        db.update_balance(interaction.user.id, -fee, "Marketplace listing fee", cfg["starting_balance"])
        db.update_treasury(fee, f"Marketplace fee from {interaction.user.name}")
        
        listing_id = db.create_marketplace_listing(
            interaction.user.id, "📦 Physical Goods", title, description, price
        )
        
        e = utils.embed(f"✅ Listed — {title}", color=utils.GREEN)
        e.add_field(name="🆔 Listing ID", value=f"#{listing_id}", inline=True)
        e.add_field(name="💰 Price", value=utils.money(price), inline=True)
        e.add_field(name="💸 Listing Fee", value=utils.money(fee), inline=True)
        await interaction.response.send_message(embed=e)

    @market.command(name="buy", description="Purchase a listing")
    @app_commands.describe(listing_id="The listing ID")
    @utils.require_citizen
    async def buy(self, interaction: discord.Interaction, listing_id: int):
        listing, status = db.buy_marketplace_listing(
            interaction.user.id, listing_id, 1, cfg["starting_balance"]
        )
        
        if status == "not_found":
            return await interaction.response.send_message("❌ Listing not found!", ephemeral=True)
        if status == "own_listing":
            return await interaction.response.send_message("❌ Can't buy your own listing!", ephemeral=True)
        if status == "insufficient_funds":
            return await interaction.response.send_message("❌ Not enough Drav!", ephemeral=True)
        
        e = utils.embed(f"✅ Purchase Complete — {listing['title']}", color=utils.GREEN)
        e.add_field(name="💰 Paid", value=utils.money(listing['price']), inline=True)
        e.add_field(name="🏪 Seller", value=f"<@{listing['seller_id']}>", inline=True)
        await interaction.response.send_message(embed=e)

async def setup(bot): await bot.add_cog(Marketplace(bot))
