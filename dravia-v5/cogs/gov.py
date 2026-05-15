"""cogs/gov.py — Government commands with salary system"""
import discord
from discord import app_commands
from discord.ext import commands
import json
import database as db
import utils

with open("config.json", encoding="utf-8") as f:
    cfg = json.load(f)

GUILD = discord.Object(id=int(cfg["guild_id"]))

class Gov(commands.Cog):
    def __init__(self, bot): self.bot = bot

    gov = app_commands.Group(name="gov", description="Government [Admin]", guild_ids=[int(cfg["guild_id"])])

    @gov.command(name="give", description="Give Drav to citizen")
    @app_commands.describe(citizen="Who", amount="Amount", reason="Why")
    async def give(self, interaction: discord.Interaction, citizen: discord.Member, amount: int, reason: str = "Government payment"):
        if not utils.is_admin(interaction.member):
            return await interaction.response.send_message("❌ Admin only!", ephemeral=True)
        
        treasury = db.get_treasury_balance()
        if treasury < amount:
            return await interaction.response.send_message(f"❌ Treasury only has {utils.money(treasury)}!", ephemeral=True)
        
        db.update_balance(citizen.id, amount, reason, cfg["starting_balance"])
        db.update_treasury(-amount, f"Payment to {citizen.name}: {reason}")
        
        e = utils.embed("🏛️ Treasury Payment", color=utils.GREEN)
        e.add_field(name="📥 To", value=citizen.mention, inline=True)
        e.add_field(name="💰 Amount", value=utils.money(amount), inline=True)
        e.add_field(name="📝 Reason", value=reason, inline=False)
        e.add_field(name="🏦 Treasury Balance", value=utils.money(db.get_treasury_balance()), inline=True)
        await interaction.response.send_message(embed=e)

    @gov.command(name="salary", description="Pay government salaries (weekly)")
    async def salary(self, interaction: discord.Interaction):
        if not utils.is_admin(interaction.member):
            return await interaction.response.send_message("❌ Admin only!", ephemeral=True)
        
        await interaction.response.defer()
        
        tax_rate = cfg["income_tax_percent"]
        results = db.pay_salaries(tax_rate)
        
        total_gross = sum(r["gross"] for r in results)
        total_tax = sum(r["tax"] for r in results)
        total_net = sum(r["net"] for r in results)
        
        e = utils.embed("💼 Salary Disbursement Complete", color=utils.GREEN)
        e.add_field(name="👥 Employees Paid", value=str(len(results)), inline=True)
        e.add_field(name="💰 Total Gross", value=utils.money(total_gross), inline=True)
        e.add_field(name="💸 Total Net", value=utils.money(total_net), inline=True)
        e.add_field(name="🏛️ Tax Collected", value=utils.money(total_tax), inline=True)
        e.set_footer(text=f"Income tax rate: {tax_rate}%")
        await interaction.followup.send(embed=e)

    @gov.command(name="hire", description="Add someone to government payroll")
    @app_commands.describe(citizen="Who to hire", role_name="Job title", weekly_salary="Weekly pay")
    async def hire(self, interaction: discord.Interaction, citizen: discord.Member, role_name: str, weekly_salary: int):
        if not utils.is_admin(interaction.member):
            return await interaction.response.send_message("❌ Admin only!", ephemeral=True)
        
        db.set_salary(citizen.id, role_name, weekly_salary)
        db.update_citizen_field(citizen.id, "occupation", role_name)
        db.update_citizen_field(citizen.id, "employer", "Government")
        
        e = utils.embed("✅ Government Employee Hired", color=utils.GREEN)
        e.add_field(name="👤 Employee", value=citizen.mention, inline=True)
        e.add_field(name="💼 Position", value=role_name, inline=True)
        e.add_field(name="💰 Salary", value=f"{utils.money(weekly_salary)}/week", inline=True)
        e.set_footer(text="Paid weekly via /gov salary")
        await interaction.response.send_message(embed=e)

    @gov.command(name="fire", description="Remove from payroll")
    @app_commands.describe(citizen="Who to fire")
    async def fire(self, interaction: discord.Interaction, citizen: discord.Member):
        if not utils.is_admin(interaction.member):
            return await interaction.response.send_message("❌ Admin only!", ephemeral=True)
        
        if db.remove_salary(citizen.id):
            db.update_citizen_field(citizen.id, "occupation", None)
            db.update_citizen_field(citizen.id, "employer", None)
            await interaction.response.send_message(f"✅ {citizen.mention} removed from payroll.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Not on payroll!", ephemeral=True)

    @gov.command(name="treasury", description="View treasury balance")
    async def treasury(self, interaction: discord.Interaction):
        if not utils.is_admin(interaction.member):
            return await interaction.response.send_message("❌ Admin only!", ephemeral=True)
        
        balance = db.get_treasury_balance()
        txs = db.get_treasury_transactions()
        
        e = utils.embed("🏛️ National Treasury", color=utils.GOLD)
        e.add_field(name="💰 Current Balance", value=utils.money(balance), inline=True)
        
        if txs:
            recent = "\n".join([f"{'🟢' if t['amount'] > 0 else '🔴'} {t['amount']:+,} — {t['reason'][:30]}" 
                               for t in reversed(txs[-5:])])
            e.add_field(name="📋 Recent Transactions", value=recent, inline=False)
        
        await interaction.response.send_message(embed=e, ephemeral=True)

async def setup(bot): await bot.add_cog(Gov(bot))
