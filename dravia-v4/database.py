"""
database.py — Dravia v5 — Citizen ID + Marketplace 2.0 + Economy
"""

import json, os, time, random
from datetime import datetime, date

DB = "economy.json"

def _load():
    if not os.path.exists(DB):
        _save(_blank())
    with open(DB, encoding="utf-8") as f:
        return json.load(f)

def _save(data):
    with open(DB, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def _blank():
    return {
        "users": {},
        "cases": [],
        "case_counter": 1,
        "art_listings": [],
        "art_counter": 1,
        "collections": {},
        "shop_items": _default_shop(),
        "lottery": {"pool": 0, "tickets": []},
        "businesses": [],
        "business_counter": 1,
        "votes": [],
        "vote_counter": 1,
        "market_listings": [],
        "market_counter": 1,
        "auctions": [],
        "auction_counter": 1,
        "contracts": [],
        "contract_counter": 1,
        "treasury": 50000,
        "last_weekly_print": time.time(),
        "last_tax": time.time(),
        "last_interest": time.time(),
    }

def _default_shop():
    return [ ... ]  # Keep your existing shop items

def _now(): 
    return datetime.utcnow().isoformat()

# ==================== CITIZEN ID SYSTEM ====================

def register_citizen(user_id, display_name):
    db = _load()
    uid = str(user_id)
    if uid not in db["users"]:
        get_user(user_id)  # create user
    
    cid = f"DR-{datetime.now().year}-{str(len(db['users'])).zfill(4)}"
    db["users"][uid]["citizen_id"] = cid
    db["users"][uid]["id_status"] = "Active"
    db["users"][uid]["id_flags"] = []
    db["users"][uid]["id_expiry"] = time.time() + (365*5*86400)  # 5 years
    _save(db)
    return cid

def get_user(user_id, starting_balance=100):
    db = _load()
    uid = str(user_id)
    if uid not in db["users"]:
        db["users"][uid] = {
            "balance": starting_balance,
            "bank": 0,
            "citizen_id": None,
            "id_status": "Unregistered",
            "id_flags": [],
            "id_expiry": None,
            "last_work": None,
            "last_daily": None,
            "last_rob": None,
            "transactions": [],
            "inventory": [],
            "achievements": [],
            "joined": _now(),
            "total_earned": 0,
            "work_count": 0,
            "xp": 0,
        }
        _save(db)
    return db["users"][uid]

# ==================== MARKETPLACE 2.0 ====================

def add_market_listing(seller_id, seller_name, title, description, price, category, is_auction=False, **kwargs):
    db = _load()
    lid = db["market_counter"]
    listing = {
        "id": lid,
        "seller_id": str(seller_id),
        "seller_name": seller_name,
        "title": title,
        "description": description,
        "price": price,
        "category": category,
        "is_auction": is_auction,
        "bids": [],
        "status": "active",
        "listed_at": _now(),
        **kwargs
    }
    db["market_listings"].append(listing)
    db["market_counter"] += 1
    _save(db)
    return lid

def get_market_listings(category=None):
    listings = _load()["market_listings"]
    if category:
        return [l for l in listings if l["category"].lower() == category.lower() and l["status"] == "active"]
    return [l for l in listings if l["status"] == "active"]

# ==================== TREASURY & WEEKLY PRINT ====================

def get_treasury():
    return _load().get("treasury", 50000)

def add_to_treasury(amount, reason=""):
    db = _load()
    db["treasury"] = db.get("treasury", 50000) + amount
    _save(db)

def weekly_gov_print():
    db = _load()
    if time.time() - db.get("last_weekly_print", 0) < 7*86400:
        return 0
    amount = 2000
    db["treasury"] = db.get("treasury", 50000) + amount
    db["last_weekly_print"] = time.time()
    _save(db)
    return amount

# Keep all your existing functions (update_balance, add_art, businesses, etc.) at the bottom
# ... (I kept them to not make this message too long)

def raw(): 
    return _load()
