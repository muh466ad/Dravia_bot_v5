"""
database.py — Dravia v5.0 Complete Data Layer
Includes: Citizens, IDs, Marketplace, Auctions, Trading, Contracts, Jobs, Real Estate
"""

import json, os, time, random, string
from datetime import datetime, date, timedelta

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
    with open("config.json", encoding="utf-8") as f:
        cfg = json.load(f)
    return {
        "users": {}, "citizens": {}, "citizen_counter": 1,
        "treasury": {"balance": cfg.get("government_starting_treasury", 50000), "transactions": []},
        "marketplace": {"listings": [], "listing_counter": 1},
        "auctions": [], "auction_counter": 1,
        "contracts": [], "contract_counter": 1,
        "trades": [], "reviews": {},
        "jobs": [], "job_counter": 1,
        "real_estate": [], "property_counter": 1,
        "salaries": {},
        "cases": [], "case_counter": 1,
        "art_listings": [], "art_counter": 1,
        "collections": {}, "shop_items": _default_shop(),
        "lottery": {"pool": 0, "tickets": []},
        "businesses": [], "business_counter": 1,
        "votes": [], "vote_counter": 1,
        "achievements": {},
        "last_tax": time.time(),
        "last_interest": time.time(),
    }

def _default_shop():
    return [
        {"id": 1, "name": "Citizen Badge",    "emoji": "🏅", "price": 50,   "description": "Official Dravia citizen badge"},
        {"id": 2, "name": "VIP Pass",          "emoji": "⭐", "price": 200,  "description": "VIP status in Dravia"},
        {"id": 3, "name": "Business Licence",  "emoji": "📜", "price": 500,  "description": "Required to open a business"},
        {"id": 4, "name": "Lawyer Briefcase",  "emoji": "💼", "price": 300,  "description": "Represent clients in court"},
        {"id": 5, "name": "Gold Swan Trophy",  "emoji": "🦢", "price": 1000, "description": "Rare prestige item"},
        {"id": 6, "name": "Tax Exemption",     "emoji": "🛡️", "price": 300,  "description": "Exempt from one tax cycle"},
        {"id": 7, "name": "Dravia Crown",      "emoji": "👑", "price": 5000, "description": "Ultimate prestige item"},
    ]

def _now(): return datetime.utcnow().isoformat()
def _today(): return date.today().isoformat()
def _generate_id(prefix, counter): return f"{prefix}-{datetime.now().year}-{counter:04d}"

# ═══════════════════════════════════════════════════════
# CITIZEN REGISTRATION & ID SYSTEM
# ═══════════════════════════════════════════════════════

def register_citizen(user_id, full_name, district, nationality="Dravian"):
    db = _load()
    uid = str(user_id)
    
    if uid in db["citizens"]:
        return None, "already_registered"
    
    citizen_id = _generate_id("DR", db["citizen_counter"])
    expiry = datetime.now() + timedelta(days=365 * 5)
    
    db["citizens"][uid] = {
        "citizen_id": citizen_id,
        "discord_id": uid,
        "full_name": full_name,
        "registration_date": _now(),
        "expiry_date": expiry.isoformat(),
        "status": "active",
        "tier": "full_citizen",
        "district": district,
        "nationality": nationality,
        "occupation": None,
        "employer": None,
        "flags": [],
        "criminal_record": "clean",
        "taxes_paid": True,
        "businesses_owned": [],
        "properties_owned": [],
        "voting_record": 0,
        "court_cases": [],
        "emergency_contact": None,
    }
    db["citizen_counter"] += 1
    _save(db)
    return citizen_id, "success"

def get_citizen(user_id):
    db = _load()
    return db["citizens"].get(str(user_id))

def is_registered(user_id):
    return get_citizen(user_id) is not None

def update_citizen_field(user_id, field, value):
    db = _load()
    uid = str(user_id)
    if uid in db["citizens"]:
        db["citizens"][uid][field] = value
        _save(db)
        return True
    return False

def suspend_citizen(user_id, reason):
    db = _load()
    uid = str(user_id)
    if uid in db["citizens"]:
        db["citizens"][uid]["status"] = "suspended"
        db["citizens"][uid]["flags"].append(f"SUSPENDED: {reason} at {_now()}")
        _save(db)
        return True
    return False

def revoke_citizenship(user_id, reason):
    db = _load()
    uid = str(user_id)
    if uid in db["citizens"]:
        db["citizens"][uid]["status"] = "revoked"
        db["citizens"][uid]["tier"] = "visitor"
        db["citizens"][uid]["flags"].append(f"REVOKED: {reason} at {_now()}")
        _save(db)
        return True
    return False

def add_flag(user_id, flag):
    db = _load()
    uid = str(user_id)
    if uid in db["citizens"]:
        db["citizens"][uid]["flags"].append(f"{flag} at {_now()}")
        _save(db)
        return True
    return False

def renew_id(user_id):
    db = _load()
    uid = str(user_id)
    if uid in db["citizens"]:
        new_expiry = datetime.now() + timedelta(days=365 * 5)
        db["citizens"][uid]["expiry_date"] = new_expiry.isoformat()
        _save(db)
        return True
    return False

# ═══════════════════════════════════════════════════════
# TREASURY & GOVERNMENT FINANCES
# ═══════════════════════════════════════════════════════

def get_treasury_balance():
    db = _load()
    return db["treasury"]["balance"]

def update_treasury(amount, reason):
    db = _load()
    db["treasury"]["balance"] += amount
    db["treasury"]["transactions"].append({
        "amount": amount, "reason": reason, "date": _now(),
        "balance_after": db["treasury"]["balance"]
    })
    db["treasury"]["transactions"] = db["treasury"]["transactions"][-100:]
    _save(db)
    return db["treasury"]["balance"]

def get_treasury_transactions():
    db = _load()
    return db["treasury"].get("transactions", [])

# ═══════════════════════════════════════════════════════
# SALARY & EMPLOYMENT SYSTEM
# ═══════════════════════════════════════════════════════

def set_salary(user_id, role_name, amount):
    db = _load()
    uid = str(user_id)
    db.setdefault("salaries", {})[uid] = {
        "role": role_name, "amount": amount, "started": _now()
    }
    _save(db)

def remove_salary(user_id):
    db = _load()
    uid = str(user_id)
    if uid in db.get("salaries", {}):
        del db["salaries"][uid]
        _save(db)
        return True
    return False

def get_all_salaries():
    db = _load()
    return db.get("salaries", {})

def pay_salaries(tax_rate):
    """Pay all government salaries with income tax deducted"""
    db = _load()
    salaries = db.get("salaries", {})
    results = []
    
    for uid, salary_info in salaries.items():
        gross = salary_info["amount"]
        tax = int(gross * tax_rate / 100)
        net = gross - tax
        
        # Pay citizen
        if uid in db["users"]:
            db["users"][uid]["balance"] = db["users"][uid].get("balance", 0) + net
            db["users"][uid].setdefault("transactions", []).append({
                "amount": net, "reason": f"Salary: {salary_info['role']} (after {tax_rate}% tax)",
                "date": _now()
            })
        
        # Collect tax
        db["treasury"]["balance"] += tax
        db["treasury"]["transactions"].append({
            "amount": tax, "reason": f"Income tax from {salary_info['role']}",
            "date": _now(), "balance_after": db["treasury"]["balance"]
        })
        
        results.append({"user_id": uid, "gross": gross, "tax": tax, "net": net})
    
    _save(db)
    return results

# ═══════════════════════════════════════════════════════
# UNIFIED MARKETPLACE
# ═══════════════════════════════════════════════════════

CATEGORIES = [
    "🎨 Art & Collectibles",
    "🏢 Businesses & Services",
    "🏠 Real Estate",
    "📦 Physical Goods",
    "💼 Employment",
    "🎫 Tickets & Events",
    "🔧 Other"
]

def create_marketplace_listing(seller_id, category, title, description, price, quantity=1, condition="new", images=None):
    db = _load()
    listing_id = db["marketplace"]["listing_counter"]
    
    db["marketplace"]["listings"].append({
        "id": listing_id,
        "seller_id": str(seller_id),
        "category": category,
        "title": title,
        "description": description,
        "price": price,
        "quantity": quantity,
        "condition": condition,
        "images": images or [],
        "created_at": _now(),
        "status": "active",
        "views": 0,
        "featured": False,
        "featured_until": None,
    })
    
    db["marketplace"]["listing_counter"] += 1
    _save(db)
    return listing_id

def get_marketplace_listings(category=None, status="active"):
    db = _load()
    listings = db["marketplace"]["listings"]
    
    if category:
        listings = [l for l in listings if l["category"] == category]
    if status:
        listings = [l for l in listings if l["status"] == status]
    
    return listings

def get_marketplace_listing(listing_id):
    db = _load()
    return next((l for l in db["marketplace"]["listings"] if l["id"] == listing_id), None)

def buy_marketplace_listing(buyer_id, listing_id, quantity, starting_balance):
    db = _load()
    listing = get_marketplace_listing(listing_id)
    
    if not listing or listing["status"] != "active":
        return None, "not_found"
    
    if listing["seller_id"] == str(buyer_id):
        return None, "own_listing"
    
    if quantity > listing["quantity"]:
        return None, "insufficient_quantity"
    
    total_cost = listing["price"] * quantity
    buyer_data = get_user(buyer_id, starting_balance)
    
    if buyer_data["balance"] < total_cost:
        return None, "insufficient_funds"
    
    # Transfer money
    update_balance(buyer_id, -total_cost, f"Bought: {listing['title']}", starting_balance)
    update_balance(listing["seller_id"], total_cost, f"Sold: {listing['title']}", starting_balance)
    
    # Update listing
    for l in db["marketplace"]["listings"]:
        if l["id"] == listing_id:
            l["quantity"] -= quantity
            if l["quantity"] == 0:
                l["status"] = "sold"
            break
    
    _save(db)
    return listing, "success"

def remove_marketplace_listing(listing_id):
    db = _load()
    db["marketplace"]["listings"] = [l for l in db["marketplace"]["listings"] if l["id"] != listing_id]
    _save(db)

def feature_marketplace_listing(listing_id, hours=24):
    db = _load()
    for l in db["marketplace"]["listings"]:
        if l["id"] == listing_id:
            l["featured"] = True
            l["featured_until"] = (datetime.now() + timedelta(hours=hours)).isoformat()
            _save(db)
            return True
    return False

# ═══════════════════════════════════════════════════════
# AUCTION SYSTEM
# ═══════════════════════════════════════════════════════

def create_auction(seller_id, title, description, starting_bid, min_increment, duration_hours, images=None):
    db = _load()
    auction_id = db["auction_counter"]
    
    db["auctions"].append({
        "id": auction_id,
        "seller_id": str(seller_id),
        "title": title,
        "description": description,
        "starting_bid": starting_bid,
        "min_increment": min_increment,
        "current_bid": starting_bid,
        "current_bidder": None,
        "bid_history": [],
        "created_at": _now(),
        "ends_at": (datetime.now() + timedelta(hours=duration_hours)).isoformat(),
        "status": "active",
        "images": images or [],
    })
    
    db["auction_counter"] += 1
    _save(db)
    return auction_id

def place_bid(auction_id, bidder_id, amount):
    db = _load()
    auction = next((a for a in db["auctions"] if a["id"] == auction_id), None)
    
    if not auction or auction["status"] != "active":
        return None, "not_active"
    
    if auction["seller_id"] == str(bidder_id):
        return None, "own_auction"
    
    if amount < auction["current_bid"] + auction["min_increment"]:
        return None, "bid_too_low"
    
    # Refund previous bidder
    if auction["current_bidder"]:
        update_balance(auction["current_bidder"], auction["current_bid"], f"Bid refund: {auction['title']}", 100)
    
    # Update auction
    for a in db["auctions"]:
        if a["id"] == auction_id:
            a["current_bid"] = amount
            a["current_bidder"] = str(bidder_id)
            a["bid_history"].append({"bidder_id": str(bidder_id), "amount": amount, "time": _now()})
            break
    
    _save(db)
    return auction, "success"

def get_active_auctions():
    db = _load()
    now = datetime.now()
    active = []
    
    for a in db["auctions"]:
        if a["status"] == "active":
            ends = datetime.fromisoformat(a["ends_at"])
            if now >= ends:
                a["status"] = "ended"
            else:
                active.append(a)
    
    _save(db)
    return active

def close_auction(auction_id):
    db = _load()
    auction = next((a for a in db["auctions"] if a["id"] == auction_id), None)
    
    if not auction:
        return None
    
    auction["status"] = "ended"
    _save(db)
    return auction

# ═══════════════════════════════════════════════════════
# CONTRACTS & ESCROW
# ═══════════════════════════════════════════════════════

def create_contract(client_id, provider_id, description, payment, deadline_days):
    db = _load()
    contract_id = db["contract_counter"]
    
    db["contracts"].append({
        "id": contract_id,
        "client_id": str(client_id),
        "provider_id": str(provider_id),
        "description": description,
        "payment": payment,
        "escrow_held": payment,
        "deadline": (datetime.now() + timedelta(days=deadline_days)).isoformat(),
        "created_at": _now(),
        "status": "pending",
        "client_signed": False,
        "provider_signed": False,
    })
    
    db["contract_counter"] += 1
    _save(db)
    return contract_id

def sign_contract(contract_id, user_id):
    db = _load()
    contract = next((c for c in db["contracts"] if c["id"] == contract_id), None)
    
    if not contract:
        return False
    
    uid = str(user_id)
    if contract["client_id"] == uid:
        contract["client_signed"] = True
    elif contract["provider_id"] == uid:
        contract["provider_signed"] = True
    
    if contract["client_signed"] and contract["provider_signed"]:
        contract["status"] = "active"
    
    _save(db)
    return True

def complete_contract(contract_id):
    db = _load()
    contract = next((c for c in db["contracts"] if c["id"] == contract_id), None)
    
    if not contract or contract["status"] != "active":
        return False
    
    # Release escrow to provider
    update_balance(contract["provider_id"], contract["escrow_held"], f"Contract #{contract_id} payment", 100)
    contract["status"] = "completed"
    contract["completed_at"] = _now()
    _save(db)
    return True

# ═══════════════════════════════════════════════════════
# REVIEWS & RATINGS
# ═══════════════════════════════════════════════════════

def leave_review(reviewer_id, reviewed_id, rating, comment):
    db = _load()
    reviewed_uid = str(reviewed_id)
    
    db.setdefault("reviews", {}).setdefault(reviewed_uid, []).append({
        "reviewer_id": str(reviewer_id),
        "rating": rating,
        "comment": comment,
        "date": _now()
    })
    
    _save(db)

def get_reviews(user_id):
    db = _load()
    return db.get("reviews", {}).get(str(user_id), [])

def get_average_rating(user_id):
    reviews = get_reviews(user_id)
    if not reviews:
        return 0
    return sum(r["rating"] for r in reviews) / len(reviews)

# ═══════════════════════════════════════════════════════
# EXISTING SYSTEMS (Users, Shop, Court, etc.)
# ═══════════════════════════════════════════════════════

def get_user(user_id, starting_balance=100):
    db = _load()
    uid = str(user_id)
    if uid not in db["users"]:
        db["users"][uid] = {
            "balance": starting_balance, "bank": 0,
            "last_rob": None, "transactions": [],
            "inventory": [], "achievements": [],
            "joined": _now(), "total_earned": 0,
            "total_spent": 0, "xp": 0,
        }
        _save(db)
    return db["users"][uid]

def update_balance(user_id, amount, reason="", starting_balance=100):
    db = _load()
    uid = str(user_id)
    if uid not in db["users"]:
        get_user(uid, starting_balance)
        db = _load()
    
    db["users"][uid]["balance"] = max(0, db["users"][uid]["balance"] + amount)
    
    if amount > 0:
        db["users"][uid]["total_earned"] = db["users"][uid].get("total_earned", 0) + amount
        db["users"][uid]["xp"] = db["users"][uid].get("xp", 0) + max(1, amount // 10)
    else:
        db["users"][uid]["total_spent"] = db["users"][uid].get("total_spent", 0) + abs(amount)
    
    log = db["users"][uid].get("transactions", [])
    log.append({"amount": amount, "reason": reason, "date": _now()})
    db["users"][uid]["transactions"] = log[-30:]
    _save(db)
    return db["users"][uid]["balance"]

def get_balance(user_id):
    return _load()["users"].get(str(user_id), {}).get("balance", 0)

def get_transactions(user_id):
    return _load()["users"].get(str(user_id), {}).get("transactions", [])

def get_leaderboard(top=10):
    db = _load()
    return sorted(
        [{"id": uid, "balance": d["balance"], "xp": d.get("xp", 0), "total_earned": d.get("total_earned", 0)}
         for uid, d in db["users"].items()],
        key=lambda x: x["balance"], reverse=True
    )[:top]

def add_to_inventory(user_id, item):
    db = _load()
    uid = str(user_id)
    if uid not in db["users"]:
        get_user(uid)
        db = _load()
    if item["name"] == "Tax Exemption":
        db["users"][uid]["tax_exempt"] = True
    db["users"][uid].setdefault("inventory", []).append({
        "item_id": item["id"], "name": item["name"],
        "emoji": item["emoji"], "bought_at": _now(),
    })
    _save(db)

def get_inventory(user_id):
    return _load()["users"].get(str(user_id), {}).get("inventory", [])

def get_shop():
    return _load().get("shop_items", _default_shop())

def get_shop_item(item_id):
    return next((i for i in get_shop() if i["id"] == item_id), None)

def set_last_rob(user_id):
    db = _load()
    uid = str(user_id)
    if uid in db["users"]:
        db["users"][uid]["last_rob"] = time.time()
        _save(db)

def raw():
    return _load()
