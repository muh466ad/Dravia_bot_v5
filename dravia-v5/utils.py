"""utils.py — Dravia v5 shared helpers"""

import discord, json

with open("config.json", encoding="utf-8") as f:
    cfg = json.load(f)

CURRENCY = cfg["currency"]
SYMBOL   = cfg.get("currency_symbol", "Ð")
RED    = 0xE74C3C; GOLD   = 0xFFB300; GREEN  = 0x2ECC71
BLUE   = 0x3498DB; PURPLE = 0x9B59B6; DARK   = 0x2C3E50
ORANGE = 0xE67E22; TEAL   = 0x1ABC9C; PINK   = 0xE91E8C
FOOTER = "🦢 Dravia — Nation of Law and Unity"

def embed(title, description=None, color=GOLD, footer=True):
    e = discord.Embed(title=title, description=description, color=color)
    e.timestamp = discord.utils.utcnow()
    if footer: e.set_footer(text=FOOTER)
    return e

def money(amount): return f"**{int(amount):,} {CURRENCY}**"

def is_admin(member):
    aid = int(cfg.get("admin_role_id", 0))
    return aid in [r.id for r in member.roles] or member.guild_permissions.administrator

def is_judge(member):
    jid = int(cfg.get("judge_role_id", 0))
    aid = int(cfg.get("admin_role_id", 0))
    ids = [r.id for r in member.roles]
    return jid in ids or aid in ids or member.guild_permissions.administrator

def is_police(member):
    pid = int(cfg.get("police_role_id", 0))
    aid = int(cfg.get("admin_role_id", 0))
    ids = [r.id for r in member.roles]
    return pid in ids or aid in ids or member.guild_permissions.administrator

def xp_to_level(xp):
    level = 0; needed = 100
    while xp >= needed:
        xp -= needed; level += 1; needed = int(needed * 1.4)
    return level

def level_title(level):
    titles = ["Newcomer","Apprentice","Worker","Trader","Merchant",
              "Entrepreneur","Banker","Tycoon","Magnate","Oligarch","Dravia Elite"]
    return titles[min(level, len(titles)-1)]

def xp_bar(xp, level):
    temp = xp; needed = 100
    for _ in range(level):
        temp -= needed; needed = int(needed * 1.4)
    current  = max(0, temp)
    filled   = min(12, int((current / needed) * 12))
    bar      = "█" * filled + "░" * (12 - filled)
    return f"`{bar}` {current}/{needed}"

def require_citizen(func):
    """Decorator to require valid citizen ID"""
    import database as db
    async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
        if not db.is_registered(interaction.user.id):
            e = embed("❌ Registration Required", 
                "You must be a registered citizen to use this command!\nUse `/register` to obtain your Citizen ID.",
                color=RED)
            return await interaction.response.send_message(embed=e, ephemeral=True)
        
        citizen = db.get_citizen(interaction.user.id)
        if citizen["status"] != "active":
            e = embed("❌ Citizenship Suspended",
                f"Your citizenship status: **{citizen['status']}**\nContact government officials for assistance.",
                color=RED)
            return await interaction.response.send_message(embed=e, ephemeral=True)
        
        return await func(self, interaction, *args, **kwargs)
    return wrapper
