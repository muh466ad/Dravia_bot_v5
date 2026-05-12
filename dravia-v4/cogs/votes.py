"""cogs/votes.py — Democratic voting system"""

import discord
from discord import app_commands
from discord.ext import commands
import json, time
import database as db
import utils

with open("config.json", encoding="utf-8") as f:
    cfg = json.load(f)

GUILD = discord.Object(id=int(cfg["guild_id"]))


class Votes(commands.Cog):
    def __init__(self, bot): self.bot = bot

    vote = app_commands.Group(name="vote", description="Dravia democratic voting",
                               guild_ids=[int(cfg["guild_id"])])

    @vote.command(name="create", description="Create a vote for citizens [Admin only]")
    @app_commands.describe(title="Vote title", description="What are we voting on?",
                           option1="First option", option2="Second option",
                           option3="Third option (optional)", option4="Fourth option (optional)",
                           hours="How long to keep vote open (default 24)")
    async def create(self, interaction: discord.Interaction,
                     title: str, description: str,
                     option1: str, option2: str,
                     option3: str = None, option4: str = None,
                     hours: int = 24):
        if not utils.is_admin(interaction.member):
            return await interaction.response.send_message("❌ Admin only!", ephemeral=True)

        options = [o for o in [option1, option2, option3, option4] if o]
        vid     = db.create_vote(interaction.user.id, title, description, options, hours)

        e = utils.embed(f"🗳️ Vote #{vid} Created!", color=utils.BLUE)
        e.add_field(name="📋 Title",       value=title,       inline=False)
        e.add_field(name="📝 Description", value=description, inline=False)
        for i, opt in enumerate(options):
            e.add_field(name=f"Option {i+1}", value=opt, inline=True)
        e.add_field(name="⏰ Duration", value=f"{hours} hours", inline=True)
        e.set_footer(text=f"Citizens use /vote cast {vid} [option number] to vote!")
        await interaction.response.send_message(embed=e)

    @vote.command(name="cast", description="Cast your vote")
    @app_commands.describe(vote_id="The vote ID", option="Which option number? (1, 2, 3...)")
    async def cast(self, interaction: discord.Interaction, vote_id: int, option: int):
        result = db.cast_vote(vote_id, interaction.user.id, option - 1)
        if result == "already_voted":
            return await interaction.response.send_message("❌ You already voted on this!", ephemeral=True)
        if result == "invalid":
            return await interaction.response.send_message("❌ Invalid option number!", ephemeral=True)
        if result == "not_found":
            return await interaction.response.send_message(f"❌ Vote #{vote_id} not found or closed!", ephemeral=True)

        v   = db.get_vote(vote_id)
        opt = v["options"][option - 1]
        e   = utils.embed(f"✅ Vote Cast!", color=utils.GREEN)
        e.description = f"You voted for **{opt['text']}** in vote #{vote_id}."
        e.set_footer(text="Use /vote results to see current standings")
        await interaction.response.send_message(embed=e, ephemeral=True)

    @vote.command(name="results", description="See the current results of a vote")
    @app_commands.describe(vote_id="The vote ID")
    async def results(self, interaction: discord.Interaction, vote_id: int):
        v = db.get_vote(vote_id)
        if not v:
            return await interaction.response.send_message(f"❌ Vote #{vote_id} not found!", ephemeral=True)

        total = sum(len(o["votes"]) for o in v["options"])
        ends  = v.get("ends_at", 0)
        remaining = ends - time.time()
        time_text = f"Closes in {int(remaining//3600)}h {int((remaining%3600)//60)}m" if remaining > 0 else "Voting closed"

        e = utils.embed(f"🗳️ Vote #{vote_id} — {v['title']}", color=utils.BLUE)
        e.description = v["description"]

        for i, opt in enumerate(v["options"]):
            count = len(opt["votes"])
            pct   = int((count / total) * 100) if total > 0 else 0
            bar   = "█" * (pct // 10) + "░" * (10 - pct // 10)
            e.add_field(
                name=f"Option {i+1}: {opt['text']}",
                value=f"`{bar}` {count} votes ({pct}%)",
                inline=False
            )

        e.add_field(name="👥 Total Votes", value=str(total),   inline=True)
        e.add_field(name="⏰ Status",      value=time_text,     inline=True)
        await interaction.response.send_message(embed=e)

    @vote.command(name="list", description="See all active votes")
    async def list_votes(self, interaction: discord.Interaction):
        votes = db.get_active_votes()
        if not votes:
            return await interaction.response.send_message("🗳️ No active votes right now!", ephemeral=True)

        lines = [f"**Vote #{v['id']}** — {v['title']} *(ends {v['ends_at'].__class__.__name__})*"
                 for v in votes]
        e = utils.embed("🗳️ Active Votes", "\n".join(lines), color=utils.BLUE)
        e.set_footer(text="Use /vote results [id] to see details")
        await interaction.response.send_message(embed=e)


async def setup(bot): await bot.add_cog(Votes(bot))
