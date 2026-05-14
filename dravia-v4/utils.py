"""
utils.py — Shared helpers for Dravia Bot v4
"""
import discord
from discord import Embed
import json

with open("config.json", encoding="utf-8") as f:
    cfg = json.load(f)

CURRENCY = cfg["currency"]
SYMBOL   = cfg.get("currency_symbol", "✨")

# ── Brand Colours ───────────────────────────────────────
RED    = 0xE74C3C
GOLD   = 0xFFB300
GREEN  = 0x2ECC71
BLUE   = 0x3498DB
PURPLE = 0x9B59B6
DARK   = 0x2C3E50
ORANGE = 0xE67E22
FOOTER = "🦢 Dravia — Nation of Law and Unity"

def embed(title, description=None, color=GOLD, footer=True) -> Embed:
    """Create a standardized embed"""
    e = Embed(title=title, description=description, color=color)
    e.timestamp = discord.utils.utcnow()
    if footer:
        e.set_footer(text=FOOTER)
    return e

def money(amount: int) -> str:
    """Format currency with commas"""
    return f"{amount:,} {CURRENCY}"

def is_admin(member: discord.Member) -> bool:
    """Check if member has admin role"""
    admin_id = int(cfg.get("admin_role_id", 0))
    return admin_id in [r.id for r in member.roles] or member.guild_permissions.administrator

def is_judge(member: discord.Member) -> bool:
    """Check if member has judge role"""
    judge_id = int(cfg.get("judge_role_id", 0))
    admin_id = int(cfg.get("admin_role_id", 0))
    ids = [r.id for r in member.roles]
    return judge_id in ids or admin_id in ids or member.guild_permissions.administrator

def xp_to_level(xp: int) -> int:
    """Calculate level from XP"""
    level = 0
    needed = 100
    while xp >= needed:
        xp -= needed
        level += 1
        needed = int(needed * 1.4)
    return level

def level_title(level: int) -> str:
    """Get title for a level"""
    titles = [
        "Newcomer", "Apprentice", "Worker", "Trader",
        "Merchant", "Entrepreneur", "Banker", "Tycoon",
        "Magnate", "Oligarch", "Dravia Elite"
    ]
    return titles[min(level, len(titles) - 1)]

def xp_bar(xp: int, level: int) -> str:
    """Create XP progress bar"""
    needed = int(100 * (1.4 ** level))
    progress = min(int((xp / needed) * 10), 10)
    return f"{'█' * progress}{'░' * (10 - progress)} ({xp}/{needed} XP)"
