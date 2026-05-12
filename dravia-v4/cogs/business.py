"""cogs/business.py — Business system"""

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
LIC_COST = cfg.get("business_licence_cost", 200)

CATEGORIES = ["Shop","Restaurant","Bank","Art Gallery","Weapons","Pharmacy","Transport","Entertainment","Other"]


class Business(commands.Cog):
    def __init__(self, bot): self.bot = bot

    biz = app_commands.Group(name="business", description="Business system",
                              guild_ids=[int(cfg["guild_id"])])

    @biz.command(name="open", description=f"Open your own business (costs {cfg.get('business_licence_cost',200)} Drav)")
    @app_commands.describe(name="Business name", description="What does it do?", category="Type of business")
    @app_commands.choices(category=[app_commands.Choice(name=c, value=c) for c in CATEGORIES])
    async def open_biz(self, interaction: discord.Interaction, name: str, description: str, category: str):
        uid  = interaction.user.id
        data = db.get_user(uid, STARTING)

        if db.get_user_business(uid):
            return await interaction.response.send_message("❌ You already own a business!", ephemeral=True)

        inv = db.get_inventory(uid)
        has_licence = any(i["name"] == "Business Licence" for i in inv)
        if not has_licence:
            if data["balance"] < LIC_COST:
                return await interaction.response.send_message(
                    f"❌ You need a Business Licence! Buy one from `/shop browse` for {utils.money(LIC_COST)}.", ephemeral=True)
            db.update_balance(uid, -LIC_COST, "Business licence fee", STARTING)

        bid = db.open_business(uid, name, description, category)
        db.unlock_achievement(uid, "business_owner")

        e = utils.embed(f"🏢 Business Opened — {name}!", color=utils.GOLD)
        e.add_field(name="🆔 Business ID",  value=f"#{bid}",      inline=True)
        e.add_field(name="📂 Category",     value=category,        inline=True)
        e.add_field(name="👤 Owner",        value=interaction.user.mention, inline=True)
        e.add_field(name="📝 Description",  value=description,     inline=False)
        e.set_footer(text="Use /business addproduct to add items to sell!")
        await interaction.response.send_message(embed=e)

    @biz.command(name="addproduct", description="Add a product to your business")
    @app_commands.describe(name="Product name", price="Price in Drav", description="What is it?")
    async def addproduct(self, interaction: discord.Interaction, name: str, price: int, description: str):
        biz = db.get_user_business(interaction.user.id)
        if not biz:
            return await interaction.response.send_message("❌ You don't own a business! Use `/business open` first.", ephemeral=True)
        if price < 1:
            return await interaction.response.send_message("❌ Price must be at least 1 Drav.", ephemeral=True)

        pid = db.add_business_product(biz["id"], name, price, description)
        e   = utils.embed(f"✅ Product Added — {name}", color=utils.GREEN)
        e.add_field(name="🏪 Business",    value=biz["name"],     inline=True)
        e.add_field(name="💰 Price",       value=utils.money(price), inline=True)
        e.add_field(name="🆔 Product ID",  value=f"#{pid}",       inline=True)
        e.add_field(name="📝 Description", value=description,     inline=False)
        e.set_footer(text="Citizens can buy with /business buy [business_id] [product_id]")
        await interaction.response.send_message(embed=e)

    @biz.command(name="view", description="View a business and its products")
    @app_commands.describe(business_id="The business ID (or leave blank for yours)")
    async def view(self, interaction: discord.Interaction, business_id: int = None):
        if business_id:
            biz = db.get_business(business_id)
        else:
            biz = db.get_user_business(interaction.user.id)

        if not biz:
            return await interaction.response.send_message("❌ Business not found!", ephemeral=True)

        e = utils.embed(f"🏢 {biz['name']}", biz["description"], color=utils.ORANGE)
        e.add_field(name="📂 Category", value=biz["category"],          inline=True)
        e.add_field(name="👤 Owner",    value=f"<@{biz['owner_id']}>",  inline=True)
        e.add_field(name="💰 Revenue",  value=utils.money(biz.get("revenue",0)), inline=True)
        e.add_field(name="📊 Status",   value=biz.get("status","open").title(), inline=True)

        products = biz.get("products", [])
        if products:
            prod_lines = [f"**#{p['id']}** {p['name']} — {p['price']:,} {cfg['currency']} *(sold: {p.get('sales',0)})*"
                          for p in products]
            e.add_field(name="🛒 Products", value="\n".join(prod_lines), inline=False)
        else:
            e.add_field(name="🛒 Products", value="*No products yet*", inline=False)

        e.set_footer(text=f"Business #{biz['id']} • /business buy {biz['id']} [product_id]")
        await interaction.response.send_message(embed=e)

    @biz.command(name="buy", description="Buy a product from a business")
    @app_commands.describe(business_id="The business ID", product_id="The product ID")
    async def buy(self, interaction: discord.Interaction, business_id: int, product_id: int):
        product, status = db.buy_business_product(interaction.user.id, business_id, product_id, STARTING)
        if status == "broke":
            return await interaction.response.send_message("❌ Not enough Drav!", ephemeral=True)
        if status == "not_found":
            return await interaction.response.send_message("❌ Product or business not found!", ephemeral=True)

        biz = db.get_business(business_id)
        e   = utils.embed(f"✅ Purchased — {product['name']}!", color=utils.GREEN)
        e.add_field(name="🏪 From",       value=biz["name"],              inline=True)
        e.add_field(name="💰 Paid",       value=utils.money(product["price"]), inline=True)
        e.add_field(name="📝 Item",       value=product["description"],   inline=False)
        await interaction.response.send_message(embed=e)

    @biz.command(name="list", description="See all open businesses in Dravia")
    async def list_biz(self, interaction: discord.Interaction):
        businesses = [b for b in db.get_businesses() if b.get("status") == "open"]
        if not businesses:
            return await interaction.response.send_message("🏢 No businesses open yet! Be the first with `/business open`.")

        lines = [f"**#{b['id']}** {b['name']} [{b['category']}] — <@{b['owner_id']}> — {len(b.get('products',[]))} product(s)"
                 for b in businesses[:10]]
        e = utils.embed("🏢 Dravia Business Directory", "\n".join(lines), color=utils.ORANGE)
        e.set_footer(text="Use /business view [id] for details")
        await interaction.response.send_message(embed=e)

    @biz.command(name="close", description="Close your business permanently")
    async def close(self, interaction: discord.Interaction):
        biz = db.get_user_business(interaction.user.id)
        if not biz:
            return await interaction.response.send_message("❌ You don't own a business!", ephemeral=True)
        db.close_business(biz["id"])
        await interaction.response.send_message(f"✅ **{biz['name']}** has been permanently closed.", ephemeral=True)


async def setup(bot): await bot.add_cog(Business(bot))
