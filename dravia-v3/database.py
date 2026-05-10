"""
database.py — Dravia v3 Data Layer
All data stored in economy.json — no external database needed.
"""

import json, os, time
from datetime import datetime, date

DB = "economy.json"

# ── Helpers ───────────────────────────────────────────────

def _load():
    if not os.path.exists(DB):
        _save(_blank())
    with open(DB) as f:
        return json.load(f)

def _save(data):
    with open(DB, "w") as f:
        json.dump(data, f, indent=2)

def _blank():
    return {
        "users":        {},
        "cases":        [],
        "case_counter": 1,
        "art_listings": [],
        "art_counter":  1,
        "collections":  {},
        "shop_items":   _default_shop(),
        "lottery":      {"pool": 0, "tickets": []},
    }

def _default_shop():
    return [
        {"id": 1, "name": "Citizen Badge",     "emoji": "🏅", "price": 50,   "description": "Official Dravia citizen badge",        "role_reward": None},
        {"id": 2, "name": "VIP Pass",           "emoji": "⭐", "price": 200,  "description": "VIP status in Dravia",                  "role_reward": None},
        {"id": 3, "name": "Business Licence",   "emoji": "📜", "price": 150,  "description": "Allows you to open a business",         "role_reward": None},
        {"id": 4, "name": "Lawyer Briefcase",   "emoji": "💼", "price": 100,  "description": "Represent clients in court",            "role_reward": None},
        {"id": 5, "name": "Gold Swan Trophy",   "emoji": "🦢", "price": 500,  "description": "Rare prestige item — very exclusive",   "role_reward": None},
        {"id": 6, "name": "Tax Exemption",      "emoji": "🛡️", "price": 300,  "description": "Exempt from one fine (single use)",     "role_reward": None},
    ]

def _now():
    return datetime.utcnow().isoformat()

def _today():
    return date.today().isoformat()

# ── Users ─────────────────────────────────────────────────

def get_user(user_id, starting_balance=100):
    db  = _load()
    uid = str(user_id)
    if uid not in db["users"]:
        db["users"][uid] = {
            "balance":      starting_balance,
            "bank":         0,
            "last_work":    None,
            "last_daily":   None,
            "last_rob":     None,
            "transactions": [],
            "inventory":    [],
            "joined":       _now(),
            "total_earned": 0,
            "total_spent":  0,
            "work_count":   0,
            "xp":           0,
        }
        _save(db)
    return db["users"][uid]

def update_balance(user_id, amount, reason="", starting_balance=100):
    db  = _load()
    uid = str(user_id)
    if uid not in db["users"]:
        get_user(uid, starting_balance)
        db = _load()

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
    db = _load()
    return db["users"].get(str(user_id), {}).get("balance", 0)

def set_last_work(user_id):
    db = _load()
    uid = str(user_id)
    if uid in db["users"]:
        db["users"][uid]["last_work"]  = time.time()
        db["users"][uid]["work_count"] = db["users"][uid].get("work_count", 0) + 1
        _save(db)

def set_last_daily(user_id):
    db = _load()
    uid = str(user_id)
    if uid in db["users"]:
        db["users"][uid]["last_daily"] = _today()
        _save(db)

def set_last_rob(user_id):
    db = _load()
    uid = str(user_id)
    if uid in db["users"]:
        db["users"][uid]["last_rob"] = time.time()
        _save(db)

def get_leaderboard(top=10):
    db = _load()
    return sorted(
        [{"id": uid, "balance": d["balance"], "xp": d.get("xp", 0)}
         for uid, d in db["users"].items()],
        key=lambda x: x["balance"], reverse=True
    )[:top]

def get_transactions(user_id):
    db = _load()
    return db["users"].get(str(user_id), {}).get("transactions", [])

# ── Inventory ─────────────────────────────────────────────

def add_to_inventory(user_id, item):
    db  = _load()
    uid = str(user_id)
    if uid not in db["users"]:
        get_user(uid)
        db = _load()
    db["users"][uid].setdefault("inventory", []).append({
        "item_id":    item["id"],
        "name":       item["name"],
        "emoji":      item["emoji"],
        "bought_at":  _now(),
    })
    _save(db)

def get_inventory(user_id):
    db = _load()
    return db["users"].get(str(user_id), {}).get("inventory", [])

# ── Shop ──────────────────────────────────────────────────

def get_shop():
    db = _load()
    return db.get("shop_items", _default_shop())

def get_shop_item(item_id):
    return next((i for i in get_shop() if i["id"] == item_id), None)

def add_shop_item(name, emoji, price, description):
    db = _load()
    items  = db.get("shop_items", [])
    new_id = max((i["id"] for i in items), default=0) + 1
    items.append({"id": new_id, "name": name, "emoji": emoji,
                  "price": price, "description": description, "role_reward": None})
    db["shop_items"] = items
    _save(db)
    return new_id

def remove_shop_item(item_id):
    db = _load()
    db["shop_items"] = [i for i in db.get("shop_items", []) if i["id"] != item_id]
    _save(db)

# ── Court ─────────────────────────────────────────────────

def add_case(plaintiff_id, defendant_id, reason, fee):
    db      = _load()
    case_id = db["case_counter"]
    db["cases"].append({
        "id":        case_id,
        "plaintiff": str(plaintiff_id),
        "defendant": str(defendant_id),
        "reason":    reason,
        "fee":       fee,
        "status":    "open",
        "filed":     _now(),
        "verdict":   None,
        "notes":     None,
    })
    db["case_counter"] = case_id + 1
    _save(db)
    return case_id

def close_case(case_id, winner, notes=""):
    db = _load()
    for c in db["cases"]:
        if c["id"] == case_id and c["status"] == "open":
            c.update(status="closed", verdict=winner,
                     notes=notes, closed_at=_now())
            _save(db)
            return c
    return None

def get_open_cases():
    db = _load()
    return [c for c in db["cases"] if c["status"] == "open"]

# ── Art ───────────────────────────────────────────────────

def add_art(seller_id, seller_name, title, price, image, description):
    db     = _load()
    art_id = db["art_counter"]
    db["art_listings"].append({
        "id": art_id, "seller_id": str(seller_id),
        "seller_name": seller_name, "title": title,
        "price": price, "image": image,
        "description": description, "listed_at": _now(),
    })
    db["art_counter"] = art_id + 1
    _save(db)
    return art_id

def get_art_listings():
    db = _load()
    return db.get("art_listings", [])

def get_art(art_id):
    return next((l for l in get_art_listings() if l["id"] == art_id), None)

def remove_art(art_id):
    db = _load()
    db["art_listings"] = [l for l in db["art_listings"] if l["id"] != art_id]
    _save(db)

def add_to_collection(user_id, listing):
    db  = _load()
    uid = str(user_id)
    db.setdefault("collections", {}).setdefault(uid, []).append({
        "title":       listing["title"],
        "seller_name": listing["seller_name"],
        "price":       listing["price"],
        "image":       listing["image"],
        "bought_at":   _now(),
    })
    _save(db)

def get_collection(user_id):
    db = _load()
    return db.get("collections", {}).get(str(user_id), [])

# ── Lottery ───────────────────────────────────────────────

def buy_lottery_ticket(user_id, cost):
    db  = _load()
    uid = str(user_id)
    db["lottery"]["pool"]    = db["lottery"].get("pool", 0) + cost
    db["lottery"]["tickets"] = db["lottery"].get("tickets", [])
    db["lottery"]["tickets"].append(uid)
    _save(db)
    return len(db["lottery"]["tickets"])

def get_lottery():
    db = _load()
    return db.get("lottery", {"pool": 0, "tickets": []})

def reset_lottery(winner_id=None):
    db = _load()
    old = db["lottery"].copy()
    db["lottery"] = {"pool": 0, "tickets": [], "last_winner": str(winner_id) if winner_id else None}
    _save(db)
    return old

def raw():
    return _load()
