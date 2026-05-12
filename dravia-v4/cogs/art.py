"""cogs/art.py — Art marketplace v4"""

import discord
from discord import app_commands
from discord.ext import commands
import json, re
import database as db
import utils

with open("config.json", encoding="utf-8") as f:
    cfg = json.load(f)

GUILD    = discord.Object(id=int(cfg["guild_id"]))
STARTING = cfg["starting_balance"]
TAX_PCT  = cfg.get("art_tax_percent", 5)
IMG_RE   = re.compile(r"^https?://.+\.(png|jpg|jpeg|gif|webp)(\?.*)?$", re.I)


class Art(commands.Cog):
    def __init__(self, bot): self.bot = bot

    art = app_commands.Group(name="art", description="Dravia Art Marketplace",
                              guild_ids=[int(cfg["guild_id"])])

    @art.command(name="sell", description="List your artwork for sale")
    @app_commands.describe(title="Title", price="Price", image_url="Image link", description="Describe it")
    async def sell(self, interaction: discord.Interaction, title: str, price: int, image_url: str, description: str = "No description."):
        if price < 1 or not IMG_RE.match(image_url):
            return await interaction.response.send_message("❌ Invalid price or image URL!", ephemeral=True)
        lid = db.add_art(interaction.user.id, interaction.user.display_name, title, price, image_url, description)
        e = utils.embed(f"🎨 Art Listed — \"{title}\"", color=utils.ORANGE)
        e.set_image(url=image_url)
        e.add_field(name="💰 Price",   value=utils.money(price),     inline=True)
        e.add_field(name="🆔 ID",      value=f"#{lid}",              inline=True)
        e.add_field(name="🏛️ Tax",     value=f"{TAX_PCT}% on sale",  inline=True)
        e.set_footer(text=f"Use /art buy {lid} to purchase")
        await interaction.response.send_message(embed=e)

    @art.command(name="browse", description="Browse all art for sale")
    async def browse(self, interaction: discord.Interaction):
        await interaction.response.defer()
        listings = db.get_art_listings()
        if not listings:
            return await interaction.followup.send("🖼️ No art listed yet!")
        lines = [f"**#{l['id']}** — *\"{l['title']}\"* by **{l['seller_name']}** — {l['price']:,} {cfg['currency']}"
                 for l in listings[:10]]
        featured = listings[-1]
        e = utils.embed("🏛️ Dravia Art Marketplace", "\n".join(lines), color=utils.ORANGE)
        e.set_image(url=featured["image"])
        e.set_footer(text=f"{len(listings)} listing(s) • /art buy [ID]")
        await interaction.followup.send(embed=e)

    @art.command(name="view", description="View one listing in detail")
    @app_commands.describe(id="Listing ID")
    async def view(self, interaction: discord.Interaction, id: int):
        l = db.get_art(id)
        if not l: return await interaction.response.send_message(f"❌ Listing #{id} not found!", ephemeral=True)
        e = utils.embed(f"🖼️ \"{l['title']}\"", l["description"], color=utils.ORANGE)
        e.set_image(url=l["image"])
        e.add_field(name="🖌️ Artist", value=f"<@{l['seller_id']}>", inline=True)
        e.add_field(name="💰 Price",  value=utils.money(l["price"]), inline=True)
        e.set_footer(text=f"Use /art buy {id}")
        await interaction.response.send_message(embed=e)

    @art.command(name="buy", description="Purchase an artwork")
    @app_commands.describe(id="Listing ID")
    async def buy(self, interaction: discord.Interaction, id: int):
        l = db.get_art(id)
        if not l: return await interaction.response.send_message(f"❌ Listing #{id} not found!", ephemeral=True)
        if l["seller_id"] == str(interaction.user.id):
            return await interaction.response.send_message("❌ Can't buy your own art!", ephemeral=True)
        data = db.get_user(interaction.user.id, STARTING)
        if data["balance"] < l["price"]:
            return await interaction.response.send_message(f"❌ Need {utils.money(l['price'])}.", ephemeral=True)
        tax = max(1, int(l["price"] * TAX_PCT / 100))
        seller_gets = l["price"] - tax
        db.update_balance(interaction.user.id, -l["price"],  f"Bought art: \"{l['title']}\"", STARTING)
        db.update_balance(l["seller_id"],      seller_gets, f"Sold art: \"{l['title']}\"",   STARTING)
        db.add_to_collection(interaction.user.id, l)
        db.remove_art(id)
        db.unlock_achievement(l["seller_id"], "art_sold")
        db.unlock_achievement(interaction.user.id, "art_bought")
        e = utils.embed(f"✅ Art Purchased — \"{l['title']}\"", color=utils.GREEN)
        e.set_image(url=l["image"])
        e.add_field(name="💸 Paid",         value=utils.money(l["price"]), inline=True)
        e.add_field(name="🏛️ Tax",          value=utils.money(tax),        inline=True)
        e.add_field(name="🎨 Artist Earns", value=utils.money(seller_gets),inline=True)
        await interaction.response.send_message(embed=e)

    @art.command(name="collection", description="View art collection")
    @app_commands.describe(user="View someone else's collection")
    async def collection(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        col = db.get_collection(target.id)
        if not col:
            return await interaction.response.send_message(f"🖼️ No art yet!", ephemeral=True)
        lines = [f"**{i+1}.** *\"{a['title']}\"* by {a['seller_name']}" for i, a in enumerate(col)]
        e = utils.embed(f"🖼️ {target.display_name}'s Collection", "\n".join(lines), color=utils.PURPLE)
        e.set_image(url=col[-1]["image"])
        await interaction.response.send_message(embed=e)

    @art.command(name="remove", description="Remove your listing")
    @app_commands.describe(id="Listing ID")
    async def remove(self, interaction: discord.Interaction, id: int):
        l = db.get_art(id)
        if not l: return await interaction.response.send_message(f"❌ Listing #{id} not found!", ephemeral=True)
        if l["seller_id"] != str(interaction.user.id) and not utils.is_admin(interaction.member):
            return await interaction.response.send_message("❌ You can only remove your own listings!", ephemeral=True)
        db.remove_art(id)
        await interaction.response.send_message(f"✅ Listing **#{id}** removed.", ephemeral=True)


async def setup(bot): await bot.add_cog(Art(bot))
