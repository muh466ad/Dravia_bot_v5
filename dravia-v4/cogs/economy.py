"""cogs/economy.py — Updated with Weekly Government Print"""

# ... keep most of your existing code ...

    @app_commands.command(name="work", description="Work to earn Drav")
    async def work(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user.get("citizen_id"):
            return await interaction.response.send_message("❌ Register with `/register` first!", ephemeral=True)
        # ... rest of your work command ...

# Add this new command
    @app_commands.command(name="treasury", description="View government treasury [Admin]")
    async def treasury(self, interaction: discord.Interaction):
        if not utils.is_admin(interaction.member):
            return await interaction.response.send_message("❌ Admin only!", ephemeral=True)
        bal = db.get_treasury()
        await interaction.response.send_message(f"🏛️ **Dravia Treasury**: {utils.money(bal)}")

# Government weekly print will be handled in tasks.py (next)
