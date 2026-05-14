"""
database.py — Dravia v4 Full Data Layer
"""

import json, os, time
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
        "users": {}, "cases": [], "case_counter": 1,
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
        {"id": 1, "name": "Citizen Badge",    "emoji": "🏅", "price": 50,  "description": "Official Dravia citizen badge"},
        {"id": 2, "name": "VIP Pass",          "emoji": "⭐", "price": 200, "description": "VIP status in Dravia"},
        {"id": 3, "name": "Business Licence",  "emoji": "📜", "price": 200, "description": "Allows you to open a business"},
        {"id": 4, "name": "Lawyer Briefcase",  "emoji": "💼", "price": 100, "description": "Represent clients in court"},
        {"id": 5, "name": "Gold Swan Trophy",  "emoji": "🦢", "price": 500, "description": "Rare prestige item"},
        {"id": 6, "name": "Tax Exemption",     "emoji": "🛡️", "price": 300, "description": "Exempt from one tax cycle"},
        {"id": 7, "name": "Dravia Crown",      "emoji": "👑", "price": 1000,"description": "Ultimate prestige — only for the elite"},
    ]

def _now(): return datetime.utcnow().isoformat()
def _today(): return date.today().isoformat()

# ── Users ─────────────────────────────────────────────────

def get_user(user_id, starting_balance=100):
    db  = _load()
    uid = str(user_id)
    if uid not in db["users"]:
        db["users"][uid] = {
            "balance": starting_balance, "bank": 0,
            "last_work": None, "last_daily": None, "last_rob": None,
            "transactions": [], "inventory": [], "achievements": [],
            "joined": _now(), "total_earned": 0, "total_spent": 0,
            "work_count": 0, "xp": 0, "citizen_id": len(db["users"]) + 1,
            "job_title": None, "tax_exempt": False,
        }
        _save(db)
    return db["users"][uid]

def update_balance(user_id, amount, reason="", starting_balance=100):
    db  = _load()
    uid = str(user_id)
    if uid not in db["users"]:
        get_user(uid, starting_balance); db = _load()
    db["users"][uid]["balance"] = max(0, db["users"][uid]["balance"] + amount)
    if amount > 0:
        db["users"][uid]["total_earned"] = db["users"][uid].get("total_earned", 0) + amount
        db["users"][uid]["xp"]           = db["users"][uid].get("xp", 0) + max(1, amount // 10)
    else:
        db["users"][uid]["total_spent"]  = db["users"][uid].get("total_spent", 0) + abs(amount)
    log = db["users"][uid].get("transactions", [])
    log.append({"amount": amount, "reason": reason, "date": _now()})
    db["users"][uid]["transactions"] = log[-30:]
    _save(db)
    return db["users"][uid]["balance"]

def get_balance(user_id):
    return _load()["users"].get(str(user_id), {}).get("balance", 0)

def set_last_work(user_id):
    db = _load(); uid = str(user_id)
    if uid in db["users"]:
        db["users"][uid]["last_work"]  = time.time()
        db["users"][uid]["work_count"] = db["users"][uid].get("work_count", 0) + 1
        _save(db)

def set_last_daily(user_id):
    db = _load(); uid = str(user_id)
    if uid in db["users"]:
        db["users"][uid]["last_daily"] = _today(); _save(db)

def set_last_rob(user_id):
    db = _load(); uid = str(user_id)
    if uid in db["users"]:
        db["users"][uid]["last_rob"] = time.time(); _save(db)

def get_leaderboard(top=10):
    db = _load()
    return sorted(
        [{"id": uid, "balance": d["balance"], "xp": d.get("xp", 0),
          "total_earned": d.get("total_earned", 0)}
         for uid, d in db["users"].items()],
        key=lambda x: x["balance"], reverse=True
    )[:top]

def get_transactions(user_id):
    return _load()["users"].get(str(user_id), {}).get("transactions", [])

def set_job_title(user_id, title):
    db = _load(); uid = str(user_id)
    if uid in db["users"]:
        db["users"][uid]["job_title"] = title; _save(db)

# ── Bank & Interest ───────────────────────────────────────

def apply_bank_interest(rate_percent):
    db = _load()
    paid = {}
    for uid, data in db["users"].items():
        bank = data.get("bank", 0)
        if bank > 0:
            interest = max(1, int(bank * rate_percent / 100))
            db["users"][uid]["bank"] += interest
            db["users"][uid]["total_earned"] = db["users"][uid].get("total_earned", 0) + interest
            log = db["users"][uid].get("transactions", [])
            log.append({"amount": interest, "reason": f"Bank interest ({rate_percent}%)", "date": _now()})
            db["users"][uid]["transactions"] = log[-30:]
            paid[uid] = interest
    db["last_interest"] = time.time()
    _save(db)
    return paid

def apply_taxes(rate_percent):
    db = _load()
    collected = {}
    for uid, data in db["users"].items():
        if data.get("tax_exempt"):
            data["tax_exempt"] = False
            continue
        bal = data.get("balance", 0)
        if bal > 0:
            tax = max(1, int(bal * rate_percent / 100))
            db["users"][uid]["balance"] = max(0, bal - tax)
            log = db["users"][uid].get("transactions", [])
            log.append({"amount": -tax, "reason": f"Weekly tax ({rate_percent}%)", "date": _now()})
            db["users"][uid]["transactions"] = log[-30:]
            collected[uid] = tax
    db["last_tax"] = time.time()
    _save(db)
    return collected

# ── Inventory ─────────────────────────────────────────────

def add_to_inventory(user_id, item):
    db = _load(); uid = str(user_id)
    if uid not in db["users"]: get_user(uid); db = _load()
    if item["name"] == "Tax Exemption":
        db["users"][uid]["tax_exempt"] = True
    db["users"][uid].setdefault("inventory", []).append({
        "item_id": item["id"], "name": item["name"],
        "emoji": item["emoji"], "bought_at": _now(),
    })
    _save(db)

def get_inventory(user_id):
    return _load()["users"].get(str(user_id), {}).get("inventory", [])

# ── Shop ──────────────────────────────────────────────────

def get_shop():
    return _load().get("shop_items", _default_shop())

def get_shop_item(item_id):
    return next((i for i in get_shop() if i["id"] == item_id), None)

def add_shop_item(name, emoji, price, description):
    db = _load(); items = db.get("shop_items", [])
    new_id = max((i["id"] for i in items), default=0) + 1
    items.append({"id": new_id, "name": name, "emoji": emoji,
                  "price": price, "description": description})
    db["shop_items"] = items; _save(db)
    return new_id

def remove_shop_item(item_id):
    db = _load()
    db["shop_items"] = [i for i in db.get("shop_items", []) if i["id"] != item_id]
    _save(db)

# ── Achievements ──────────────────────────────────────────

ACHIEVEMENTS = {
    "first_work":     {"name": "First Day",        "emoji": "🌅", "desc": "Completed your first job"},
    "work_10":        {"name": "Hard Worker",       "emoji": "💪", "desc": "Worked 10 times"},
    "work_100":       {"name": "Grinder",           "emoji": "⚙️", "desc": "Worked 100 times"},
    "balance_1000":   {"name": "Thousandaire",      "emoji": "💰", "desc": "Reached 1,000 Drav"},
    "balance_10000":  {"name": "Tycoon",            "emoji": "🏦", "desc": "Reached 10,000 Drav"},
    "art_sold":       {"name": "Artist",            "emoji": "🎨", "desc": "Sold your first artwork"},
    "art_bought":     {"name": "Collector",         "emoji": "🖼️", "desc": "Bought your first artwork"},
    "won_case":       {"name": "Justice Served",    "emoji": "⚖️", "desc": "Won a court case"},
    "rob_success":    {"name": "Criminal",          "emoji": "🦹", "desc": "Successfully robbed someone"},
    "lottery_win":    {"name": "Lucky",             "emoji": "🎰", "desc": "Won the lottery"},
    "business_owner": {"name": "Entrepreneur",      "emoji": "🏢", "desc": "Opened a business"},
    "daily_7":        {"name": "Streak",            "emoji": "🔥", "desc": "Claimed daily 7 days in a row"},
    "crown_owner":    {"name": "Dravia Elite",      "emoji": "👑", "desc": "Owns the Dravia Crown"},
}

def unlock_achievement(user_id, achievement_id):
    db  = _load(); uid = str(user_id)
    if uid not in db["users"]: return False
    achieved = db["users"][uid].get("achievements", [])
    if achievement_id not in achieved:
        achieved.append(achievement_id)
        db["users"][uid]["achievements"] = achieved
        _save(db)
        return True
    return False

def check_achievements(user_id):
    db   = _load(); uid = str(user_id)
    data = db["users"].get(uid, {})
    unlocked = []
    checks = {
        "first_work":    data.get("work_count", 0) >= 1,
        "work_10":       data.get("work_count", 0) >= 10,
        "work_100":      data.get("work_count", 0) >= 100,
        "balance_1000":  data.get("balance", 0) >= 1000,
        "balance_10000": data.get("balance", 0) >= 10000,
    }
    for aid, condition in checks.items():
        if condition and unlock_achievement(user_id, aid):
            unlocked.append(aid)
    return unlocked

# ── Court ─────────────────────────────────────────────────

def add_case(plaintiff_id, defendant_id, reason, fee, lawyer_id=None):
    db = _load()
    case_id = db["case_counter"]
    db["cases"].append({
        "id": case_id, "plaintiff": str(plaintiff_id),
        "defendant": str(defendant_id), "reason": reason,
        "fee": fee, "status": "open", "filed": _now(),
        "verdict": None, "notes": None,
        "lawyer_plaintiff": str(lawyer_id) if lawyer_id else None,
        "evidence": [],
    })
    db["case_counter"] = case_id + 1; _save(db)
    return case_id

def add_evidence(case_id, user_id, evidence_text):
    db = _load()
    for c in db["cases"]:
        if c["id"] == case_id and c["status"] == "open":
            c.setdefault("evidence", []).append({
                "user": str(user_id), "text": evidence_text, "date": _now()
            })
            _save(db); return True
    return False

def close_case(case_id, winner, notes=""):
    db = _load()
    for c in db["cases"]:
        if c["id"] == case_id and c["status"] == "open":
            c.update(status="closed", verdict=winner, notes=notes, closed_at=_now())
            _save(db); return c
    return None

def appeal_case(case_id, reason):
    db = _load()
    for c in db["cases"]:
        if c["id"] == case_id and c["status"] == "closed":
            c["status"]  = "appealed"
            c["appeal"]  = reason
            c["appealed_at"] = _now()
            _save(db); return c
    return None

def get_open_cases():
    return [c for c in _load()["cases"] if c["status"] in ("open", "appealed")]

def get_case(case_id):
    return next((c for c in _load()["cases"] if c["id"] == case_id), None)

# ── Art ───────────────────────────────────────────────────

def add_art(seller_id, seller_name, title, price, image, description):
    db = _load(); art_id = db["art_counter"]
    db["art_listings"].append({
        "id": art_id, "seller_id": str(seller_id),
        "seller_name": seller_name, "title": title,
        "price": price, "image": image,
        "description": description, "listed_at": _now(),
    })
    db["art_counter"] = art_id + 1; _save(db)
    return art_id

def get_art_listings(): return _load().get("art_listings", [])
def get_art(art_id): return next((l for l in get_art_listings() if l["id"] == art_id), None)

def remove_art(art_id):
    db = _load()
    db["art_listings"] = [l for l in db["art_listings"] if l["id"] != art_id]
    _save(db)

def add_to_collection(user_id, listing):
    db = _load(); uid = str(user_id)
    db.setdefault("collections", {}).setdefault(uid, []).append({
        "title": listing["title"], "seller_name": listing["seller_name"],
        "price": listing["price"], "image": listing["image"], "bought_at": _now(),
    })
    _save(db)

def get_collection(user_id):
    return _load().get("collections", {}).get(str(user_id), [])

# ── Businesses ────────────────────────────────────────────

def open_business(owner_id, name, description, category):
    db = _load()
    bid = db.get("business_counter", 1)
    db.setdefault("businesses", []).append({
        "id": bid, "owner_id": str(owner_id),
        "name": name, "description": description,
        "category": category, "opened_at": _now(),
        "employees": [], "revenue": 0, "status": "open",
        "products": [],
    })
    db["business_counter"] = bid + 1; _save(db)
    return bid

def get_businesses(): return _load().get("businesses", [])
def get_business(bid): return next((b for b in get_businesses() if b["id"] == bid), None)

def get_user_business(owner_id):
    return next((b for b in get_businesses() if b["owner_id"] == str(owner_id)), None)

def add_business_product(bid, name, price, description):
    db = _load()
    for b in db["businesses"]:
        if b["id"] == bid:
            pid = max((p["id"] for p in b.get("products", [])), default=0) + 1
            b.setdefault("products", []).append({
                "id": pid, "name": name, "price": price,
                "description": description, "sales": 0,
            })
            _save(db); return pid
    return None

def buy_business_product(buyer_id, bid, product_id, starting_balance=100):
    db = _load()
    for b in db["businesses"]:
        if b["id"] == bid:
            for p in b.get("products", []):
                if p["id"] == product_id:
                    buyer_bal = db["users"].get(str(buyer_id), {}).get("balance", 0)
                    if buyer_bal < p["price"]: return None, "broke"
                    update_balance(buyer_id,    -p["price"], f"Bought {p['name']} from {b['name']}", starting_balance)
                    update_balance(b["owner_id"], p["price"], f"Sale: {p['name']} in {b['name']}", starting_balance)
                    p["sales"] = p.get("sales", 0) + 1
                    b["revenue"] = b.get("revenue", 0) + p["price"]
                    _save(db); return p, "ok"
    return None, "not_found"

def close_business(bid):
    db = _load()
    for b in db["businesses"]:
        if b["id"] == bid:
            b["status"] = "closed"; _save(db); return True
    return False

# ── Lottery ───────────────────────────────────────────────

def buy_lottery_ticket(user_id, cost):
    db = _load()
    db["lottery"]["pool"] = db["lottery"].get("pool", 0) + cost
    db["lottery"].setdefault("tickets", []).append(str(user_id))
    _save(db)
    return len(db["lottery"]["tickets"])

def get_lottery(): return _load().get("lottery", {"pool": 0, "tickets": []})

def reset_lottery(winner_id=None):
    db = _load(); old = db["lottery"].copy()
    db["lottery"] = {"pool": 0, "tickets": [],
                     "last_winner": str(winner_id) if winner_id else None}
    _save(db); return old

# ── Votes ─────────────────────────────────────────────────

def create_vote(creator_id, title, description, options, duration_hours=24):
    db = _load()
    vid = db.get("vote_counter", 1)
    import time
    db.setdefault("votes", []).append({
        "id": vid, "creator": str(creator_id),
        "title": title, "description": description,
        "options": [{"text": o, "votes": [], } for o in options],
        "created_at": _now(),
        "ends_at": time.time() + duration_hours * 3600,
        "status": "open",
    })
    db["vote_counter"] = vid + 1; _save(db); return vid

def cast_vote(vote_id, user_id, option_index):
    db = _load()
    for v in db.get("votes", []):
        if v["id"] == vote_id and v["status"] == "open":
            uid = str(user_id)
            for opt in v["options"]:
                if uid in opt["votes"]: return "already_voted"
            if option_index >= len(v["options"]): return "invalid"
            v["options"][option_index]["votes"].append(uid)
            _save(db); return "ok"
    return "not_found"

def get_active_votes():
    import time
    votes = _load().get("votes", [])
    now   = time.time()
    result = []
    for v in votes:
        if v["status"] == "open":
            if now > v["ends_at"]: v["status"] = "closed"
            else: result.append(v)
    return result

def get_vote(vote_id):
    return next((v for v in _load().get("votes", []) if v["id"] == vote_id), None)

#── Citizen ID System ─────────────────────────────────────
def get_citizen_year():
    from datetime import datetime
    return datetime.utcnow().year

def register_citizen(user_id, full_name, address, occupation):
    db = _load()
    cid = str(user_id)
    if cid in db.get("citizens", {}):
        return None  # Already registered
    
    year = datetime.utcnow().year
    db.setdefault("citizens", {})
    db.setdefault("citizen_counter", 1)
    
    new_id = f"DR-{year}-{str(db['citizen_counter']).zfill(4)}"
    
    # Calculate expiry: 5 years from now
    from datetime import timedelta
    expires = (datetime.utcnow() + timedelta(days=5*365)).isoformat()
    
    db["citizens"][cid] = {
        "id_number": new_id,
        "full_name": full_name,
        "address": address,
        "occupation": occupation,
        "status": "active",
        "tier": "full",
        "flags": [],
        "issued_at": _now(),
        "expires_at": expires,
        "is_lost": False
    }
    db["citizen_counter"] += 1
    # Link to user
    if cid in db["users"]:
        db["users"][cid]["citizen_id"] = new_id
    _save(db)
    return new_id
