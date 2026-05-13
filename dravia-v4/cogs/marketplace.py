"""cogs/marketplace.py — Dravia Marketplace 2.0"""

import discord
from discord import app_commands
from discord.ext import commands
import json, time
import database as db
import utils

with open("config.json", encoding="utf-8") as f:
    cfg = json.load(f)

GUILD = discord.Object(id=int(cfg["guild_id"]))
LISTING_FEE = cfg.get("marketplace_listing_fee", 5)
SALES_TAX = cfg.get("sales_tax_percent", 3)

class Marketplace(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    market = app_commands.Group(name="market", description="Dravia Unified Marketplace")

    @market.command(name="sell", description="List an item for sale")
    @app_commands.describe(title="Title", price="Price (or 0 for auction)", description="Description", category="Category")
    async def sell(self, interaction: discord.Interaction, title: str, price: int, description: str, category: str):
        user = db.get_user(interaction.user.id)
        if not user.get("citizen_id"):
            return await interaction.response.send_message("❌ You must `/register` first!", ephemeral=True)
        
        if user["balance"] < LISTING_FEE:
            return await interaction.response.send_message(f"❌ Listing fee is {utils.money(LISTING_FEE)}", ephemeral=True)

        db.update_balance(interaction.user.id, -LISTING_FEE, "Marketplace listing fee", cfg["starting_balance"])
        lid = db.add_market_listing(
            interaction.user.id, interaction.user.display_name,
            title, description, price, category, is_auction=(price == 0)
        )

        e = utils.embed("📦 Listing Created!", color=utils.GREEN)
        e.add_field(name="🆔 Listing ID", value=f"#{lid}", inline=True)
        e.add_field(name="💰 Price", value=utils.money(price) if price > 0 else "Auction", inline=True)
        e.add_field(name="📂 Category", value=category, inline=True)
        await interaction.response.send_message(embed=e)

    @market.command(name="browse", description="Browse marketplace listings")
    @app_commands.describe(category="Filter by category")
    async def browse(self, interaction: discord.Interaction, category: str = None):
        await interaction.response.defer()
        listings = db.get_market_listings(category)
        
        if not listings:
            return await interaction.followup.send("No listings found.")

        lines = [f"**#{l['id']}** | **{l['title']}** — {utils.money(l['price']) if l['price']>0 else 'Auction'} by {l['seller_name']}" 
                for l in listings[:10]]
        
        e = utils.embed("🏪 Dravia Marketplace", "\n".join(lines), color=utils.ORANGE)
        e.set_footer(text="Use /market view [id] for details")
        await interaction.followup.send(embed=e)

    @market.command(name="view", description="View a listing in detail")
    @app_commands.describe(listing_id="Listing ID")
    async def view(self, interaction: discord.Interaction, listing_id: int):
        # Implementation similar to your art view - I'll expand on request
        await interaction.response.send_message(f"Listing #{listing_id} details (full version coming in next message if needed)")

    # Add more commands: /market buy, /auction create, /trade request, etc. as needed

async def setup(bot):
    await bot.add_cog(Marketplace(bot))
