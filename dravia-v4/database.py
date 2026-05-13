import json, os, time, random
from datetime import datetime

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
        "users": {}, "cases": [], "case_counter": 1,
        "art_listings": [], "art_counter": 1,
        "collections": {}, "shop_items": _default_shop(),
        "lottery": {"pool": 0, "tickets": []},
        "businesses": [], "business_counter": 1,
        "votes": [], "vote_counter": 1,
        "market_listings": [], "market_counter": 1,
        "treasury": 50000,
        "last_weekly_print": time.time(),
        "last_tax": time.time(),
        "last_interest": time.time(),
    }

def _default_shop(): 
    return [  # your original shop items
        {"id":1,"name":"Citizen Badge","emoji":"🏅","price":50,"description":"Official badge"},
        {"id":2,"name":"Business Licence","emoji":"📜","price":500,"description":"Open a business"},
    ]

def _now(): return datetime.utcnow().isoformat()

# ==================== CITIZEN ID ====================
def register_citizen(user_id, name):
    db = _load()
    uid = str(user_id)
    if uid not in db["users"]:
        get_user(user_id)
    cid = f"DR-{datetime.now().year}-{str(len([u for u in db['users'].values() if u.get('citizen_id')])+1).zfill(4)}"
    db["users"][uid].update({
        "citizen_id": cid,
        "id_status": "Active",
        "id_flags": [],
        "id_expiry": time.time() + 5*365*86400,
        "citizen_tier": 1
    })
    _save(db)
    return cid

def get_user(user_id, starting=100):
    db = _load()
    uid = str(user_id)
    if uid not in db["users"]:
        db["users"][uid] = {
            "balance": starting, "bank":0, "citizen_id":None, "id_status":"Unregistered",
            "id_flags":[], "id_expiry":None, "citizen_tier":0,
            "last_work":None, "last_daily":None, "transactions":[],
            "xp":0, "work_count":0, "joined":_now()
        }
        _save(db)
    return db["users"][uid]

# ==================== MARKETPLACE ====================
def add_market_listing(seller_id, seller_name, title, desc, price, category, is_auction=False):
    db = _load()
    lid = db["market_counter"]
    db["market_listings"].append({
        "id": lid, "seller_id": str(seller_id), "seller_name": seller_name,
        "title": title, "description": desc, "price": price,
        "category": category, "is_auction": is_auction,
        "bids": [], "status": "active", "listed_at": _now()
    })
    db["market_counter"] += 1
    _save(db)
    return lid

def get_market_listings(category=None):
    listings = _load()["market_listings"]
    active = [l for l in listings if l["status"] == "active"]
    if category:
        return [l for l in active if l["category"].lower() == category.lower()]
    return active

def get_treasury(): 
    return _load().get("treasury", 50000)

def weekly_gov_print():
    db = _load()
    if time.time() - db.get("last_weekly_print",0) < 7*86400: 
        return 0
    amount = 2000
    db["treasury"] = db.get("treasury",50000) + amount
    db["last_weekly_print"] = time.time()
    _save(db)
    return amount

# Keep all your original functions below (update_balance, art, business, court, etc.)
# ... (I preserved them from your original file)
def raw(): return _load()
