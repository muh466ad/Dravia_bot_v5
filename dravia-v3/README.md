# 🦢 DRAVIA BOT v3.0 — Setup Guide

---

## 📁 Files Explained
```
dravia-v3/
├── bot.py          ← Start the bot with this
├── database.py     ← Stores all data (economy.json created automatically)
├── utils.py        ← Shared helpers
├── config.json     ← YOUR settings — fill this in first!
├── requirements.txt
└── cogs/
    ├── economy.py  ← /balance /work /pay /daily /deposit /withdraw /leaderboard /history
    ├── profile.py  ← /profile /inventory
    ├── shop.py     ← /shop browse/buy/add/remove
    ├── art.py      ← /art sell/browse/view/buy/collection/remove
    ├── court.py    ← /complaint /fine /verdict /cases
    ├── gov.py      ← /gov give/take/salary/stats/reset
    └── fun.py      ← /coinflip /lottery /lotterydraw /rob
```

---

## ✅ Setup Steps

### 1. Install Python
- Download from **python.org/downloads**
- ⚠️ Check **"Add Python to PATH"** during install!

### 2. Install the library
Open Command Prompt / Terminal and run:
```
pip install discord.py
```

### 3. Create your bot on Discord
1. Go to **discord.com/developers/applications**
2. Click **New Application** → name it **Dravia Bot**
3. Go to **Bot** tab → **Reset Token** → copy the token
4. Turn ON: **Server Members Intent** + **Message Content Intent**

### 4. Invite bot to your server
1. Go to **OAuth2** → **URL Generator**
2. Check: `bot` + `applications.commands`
3. Permissions: Send Messages, Embed Links, Read Message History, Use Slash Commands
4. Copy the URL → paste in browser → add to Dravia server

### 5. Get your IDs (need Developer Mode on)
- Discord Settings → Advanced → turn on **Developer Mode**
- **Server ID**: right-click server icon → Copy Server ID
- **Admin Role ID**: Server Settings → Roles → right-click Admin → Copy Role ID
- **Judge Role ID**: same for Judge role

### 6. Fill in config.json
Open config.json in Notepad and replace the placeholders:
```json
{
    "token":               "YOUR BOT TOKEN",
    "guild_id":            "YOUR SERVER ID",
    "admin_role_id":       "YOUR ADMIN ROLE ID",
    "judge_role_id":       "YOUR JUDGE ROLE ID",
    "welcome_channel_id":  "CHANNEL ID FOR WELCOME MSGS (optional)"
}
```

### 7. Run it!
```
python bot.py
```
You should see **🦢 DRAVIA BOT v3.0 — ONLINE**

---

## 🎮 All Commands

### 💰 Economy (Everyone)
| Command | What it does |
|---|---|
| `/balance` | Check wallet + bank + level |
| `/work` | Earn 20–50 Drav (1hr cooldown) |
| `/daily` | Claim 50–100 Drav daily reward |
| `/pay @user 50` | Send Drav to someone |
| `/deposit 100` | Move Drav to your safe bank vault |
| `/withdraw 100` | Take Drav back from vault |
| `/leaderboard` | Richest citizens top 10 |
| `/history` | Your last 10 transactions |

### 🪪 Profile (Everyone)
| Command | What it does |
|---|---|
| `/profile` | Full citizen card with level, XP bar, stats |
| `/inventory` | Items you own from the shop |

### 🏪 Shop (Everyone to buy, Admin to manage)
| Command | What it does |
|---|---|
| `/shop browse` | See all items for sale |
| `/shop buy 1` | Buy item #1 |
| `/shop add` | Add item (Admin only) |
| `/shop remove 1` | Remove item #1 (Admin only) |

### 🎨 Art Marketplace (Everyone)
| Command | What it does |
|---|---|
| `/art sell` | List your art for sale |
| `/art browse` | See all art for sale |
| `/art view 3` | View listing #3 in detail |
| `/art buy 3` | Buy listing #3 |
| `/art collection` | Your art collection |
| `/art remove 3` | Remove your listing |

### ⚖️ Court (Everyone to file, Judge/Admin to rule)
| Command | Who | What it does |
|---|---|---|
| `/complaint @user reason` | Everyone | File a case (costs 5 Drav) |
| `/cases` | Everyone | See open cases |
| `/fine @user 50 reason` | Judge/Admin | Fine a citizen |
| `/verdict 1 plaintiff` | Judge | Close case #1 |

### 🏛️ Government (Admin only)
| Command | What it does |
|---|---|
| `/gov give @user 100` | Give Drav (salary, reward) |
| `/gov take @user 50` | Remove Drav (tax) |
| `/gov salary @role 30` | Pay everyone with a role |
| `/gov stats` | Full economy report |
| `/gov reset @user` | Reset someone's balance |

### 🎲 Fun (Everyone)
| Command | What it does |
|---|---|
| `/coinflip 50 heads` | Bet Drav on heads or tails |
| `/lottery` | Buy a lottery ticket (20 Drav) |
| `/lotterydraw` | Draw the winner (Admin only) |
| `/rob @user` | Try to steal Drav (risky!) |

---

## 🆕 New in v3.0
- ✅ **Daily reward** — claim free Drav every day
- ✅ **Bank vault** — safe storage that can't be robbed
- ✅ **Citizen levels** — XP system with titles (Newcomer → Dravia Elite)
- ✅ **Profile cards** — full stats, XP bar, inventory, art collection
- ✅ **Government shop** — buy items and badges
- ✅ **Coinflip gambling** — bet your Drav
- ✅ **Lottery system** — jackpot pool grows with every ticket
- ✅ **Rob command** — steal from citizens (40% success rate)
- ✅ **Welcome message** — auto greets new members with starter Drav
- ✅ **Salary command** — pay entire roles at once

---

*🦢 Dravia — Nation of Law and Unity. Est. 19__*
