"""cogs/shop.py — Government shop"""

import discord
from discord import app_commands
from discord.ext import commands
import json
import database as db
import utils

with open("config.json", encoding="utf-8") as f:
    cfg = json.load(f)

GUILD    = discord.Object(id=int(cfg["guild_id"]))
STARTING = cfg["starting_balance"]


class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    shop_group = app_commands.Group(
        name="shop", description="Dravia Government Shop",
        guild_ids=[int(cfg["guild_id"])]
    )

    # ── /shop browse ─────────────────────────────────────
    @shop_group.command(name="browse", description="Browse items for sale in the government shop")
    async def browse(self, interaction: discord.Interaction):
        items = db.get_shop()
        if not items:
            return await interaction.response.send_message("🏪 The shop is empty right now!", ephemeral=True)

        e = utils.embed("🏪 Dravia Government Shop", color=utils.GOLD)
        e.description = "Use `/shop buy [ID]` to purchase an item."
        for item in items:
            e.add_field(
                name=f"{item['emoji']} {item['name']}  •  ID #{item['id']}",
                value=f"{item['description']}\n💰 **{item['price']:,} {cfg['currency']}**",
                inline=False
            )
        await interaction.response.send_message(embed=e)

    # ── /shop buy ─────────────────────────────────────────
    @shop_group.command(name="buy", description="Buy an item from the shop")
    @app_commands.describe(item_id="The item ID number from /shop browse")
    async def buy(self, interaction: discord.Interaction, item_id: int):
        item = db.get_shop_item(item_id)
        if not item:
            return await interaction.response.send_message(f"❌ Item #{item_id} not found!", ephemeral=True)

        uid  = interaction.user.id
        data = db.get_user(uid, STARTING)

        if data["balance"] < item["price"]:
            e = utils.embed("❌ Not Enough Drav",
                f"You need {utils.money(item['price'])} but only have {utils.money(data['balance'])}.",
                color=utils.RED)
            return await interaction.response.send_message(embed=e, ephemeral=True)

        # Check if already owned (for unique items)
        inv = db.get_inventory(uid)
        if any(i["item_id"] == item_id for i in inv):
            return await interaction.response.send_message(
                f"❌ You already own **{item['name']}**!", ephemeral=True)

        new_bal = db.update_balance(uid, -item["price"], f"Bought: {item['name']}", STARTING)
        db.add_to_inventory(uid, item)

        e = utils.embed(f"✅ Purchase Successful!", color=utils.GREEN)
        e.description = f"You bought **{item['emoji']} {item['name']}**!"
        e.add_field(name="💸 Price Paid",   value=utils.money(item["price"]), inline=True)
        e.add_field(name="💰 New Balance",  value=utils.money(new_bal),       inline=True)
        e.add_field(name="📝 Description",  value=item["description"],        inline=False)
        e.set_footer(text="Item added to your inventory! Use /inventory to view it.")
        await interaction.response.send_message(embed=e)

    # ── /shop add (admin) ─────────────────────────────────
    @shop_group.command(name="add", description="Add an item to the shop [Admin only]")
    @app_commands.describe(name="Item name", emoji="Item emoji", price="Price in Drav", description="Description")
    async def add(self, interaction: discord.Interaction,
                  name: str, emoji: str, price: int, description: str):
        if not utils.is_admin(interaction.member):
            return await interaction.response.send_message("❌ Admin only!", ephemeral=True)

        new_id = db.add_shop_item(name, emoji, price, description)
        e = utils.embed("✅ Shop Item Added", color=utils.GREEN)
        e.add_field(name="🆔 ID",          value=f"#{new_id}",            inline=True)
        e.add_field(name="📦 Item",        value=f"{emoji} {name}",       inline=True)
        e.add_field(name="💰 Price",       value=utils.money(price),      inline=True)
        e.add_field(name="📝 Description", value=description,             inline=False)
        await interaction.response.send_message(embed=e)

    # ── /shop remove (admin) ──────────────────────────────
    @shop_group.command(name="remove", description="Remove an item from the shop [Admin only]")
    @app_commands.describe(item_id="The item ID to remove")
    async def remove(self, interaction: discord.Interaction, item_id: int):
        if not utils.is_admin(interaction.member):
            return await interaction.response.send_message("❌ Admin only!", ephemeral=True)

        item = db.get_shop_item(item_id)
        if not item:
            return await interaction.response.send_message(f"❌ Item #{item_id} not found!", ephemeral=True)

        db.remove_shop_item(item_id)
        await interaction.response.send_message(
            f"✅ Removed **{item['emoji']} {item['name']}** from the shop.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Shop(bot))
