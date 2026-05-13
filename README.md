# 🦢 DRAVIA BOT v5.0 — ULTIMATE EDITION

Complete economy system with **achievements**, **businesses**, **voting**, **auto taxes**, **bank interest**, and **advanced gambling**!

---

## 🆕 What's New in v4.0

### 🏆 Achievement System
- 13 achievements to unlock (first work, 10 jobs, 100 jobs, 1000 Drav, 10k Drav, art sold, art bought, won case, rob success, lottery win, business owner, 7-day streak, crown owner)
- View with `/achievements` — unlocked achievements show on your profile

### 🏢 Business System
- `/business open` — open your own shop (needs Business Licence from shop or 200 Drav)
- `/business addproduct` — add items to sell
- `/business buy [business_id] [product_id]` — buy from any business
- `/business view` — see products and revenue
- Revenue tracks automatically to business owner

### 🗳️ Democratic Voting
- `/vote create` — admins create votes with 2-4 options (Admin)
- `/vote cast` — citizens vote (one vote per person)
- `/vote results` — see live bar chart results
- Auto-closes after duration

### 💰 Auto Economy Management
- **Taxes**: Automatically collected every 24 hours (5% from wallets)
- **Bank Interest**: 2% paid daily to vault holders
- Tax Exemption item protects you from one tax cycle
- Logs posted to log_channel_id

### ⚖️ Enhanced Court
- `/evidence [case_id]` — submit evidence to cases
- `/appeal [case_id]` — reopen closed cases (costs 5 Drav)
- `/caseinfo [case_id]` — view full case with all evidence
- Lawyer system — hire lawyers when filing

### 🎲 Advanced Gambling
- **Blackjack** — `/blackjack` then `/hit` or `/stand`
- **Dice** — `/dice` bet on 2-12 with multipliers (2x to 6x)
- **Slots** — `/slots` with 7 symbols, jackpot up to 50x
- **Coinflip** — `/coinflip` heads or tails
- **Lottery** — `/lottery` buy tickets, `/lotterydraw` to draw winner
- **Rob** — `/rob` 40% success, 2hr cooldown

---

## 📋 Full Command List

### 💰 Economy
| Command | Description |
|---|---|
| `/balance` | Check wallet + vault + level + XP |
| `/work` | Earn 20–50 Drav (1hr cooldown) |
| `/daily` | Claim 50–100 Drav (once per day) |
| `/pay @user 50` | Send Drav to someone |
| `/deposit 100` | Move Drav to vault (earns interest!) |
| `/withdraw 100` | Take Drav from vault |
| `/leaderboard` | Top 10 by balance/XP/earnings |
| `/history` | Last 10 transactions |

### 🪪 Profile
| Command | Description |
|---|---|
| `/profile` | Full card with achievements, business, stats |
| `/achievements` | View all 13 achievements |
| `/inventory` | Items you own |
| `/citizenid` | Official Dravia ID card |

### 🏪 Shop
| Command | Who | Description |
|---|---|---|
| `/shop browse` | Everyone | See government shop items |
| `/shop buy 1` | Everyone | Buy item #1 |
| `/shop add` | Admin | Add new item |
| `/shop remove 1` | Admin | Remove item |

### 🎨 Art
| Command | Description |
|---|---|
| `/art sell` | List artwork for sale |
| `/art browse` | See all art |
| `/art view 3` | View listing #3 |
| `/art buy 3` | Buy artwork #3 (5% tax) |
| `/art collection` | Your art collection |
| `/art remove 3` | Remove your listing |

### ⚖️ Court
| Command | Who | Description |
|---|---|---|
| `/complaint @user reason` | Everyone | File case (5 Drav fee) |
| `/evidence 1 "proof"` | Involved parties | Submit evidence |
| `/caseinfo 1` | Everyone | View full case details |
| `/appeal 1 "reason"` | Involved parties | Reopen closed case |
| `/fine @user 50 reason` | Judge | Fine a citizen |
| `/verdict 1 plaintiff` | Judge | Close case with winner |
| `/cases` | Everyone | View all open cases |

### 🏢 Business
| Command | Description |
|---|---|
| `/business open` | Start a business (200 Drav or licence) |
| `/business addproduct` | Add items to sell |
| `/business view [id]` | See business details |
| `/business buy [biz_id] [prod_id]` | Buy from a business |
| `/business list` | All open businesses |
| `/business close` | Permanently close your business |

### 🗳️ Voting
| Command | Who | Description |
|---|---|---|
| `/vote create` | Admin | Create a vote (2-4 options) |
| `/vote cast 1 2` | Everyone | Vote for option 2 in vote #1 |
| `/vote results 1` | Everyone | See current standings |
| `/vote list` | Everyone | All active votes |

### 🎲 Gambling
| Command | Description |
|---|---|
| `/coinflip 50 heads` | Bet on heads/tails |
| `/dice 50 7` | Bet on dice total (2-12) |
| `/slots 100` | Spin slot machine |
| `/blackjack 50` | Play blackjack → `/hit` `/stand` |
| `/lottery` | Buy ticket (20 Drav) |
| `/lotterydraw` | Draw winner (Admin) |
| `/rob @user` | 40% steal, 60% get fined |

### 🏛️ Government (Admin Only)
| Command | Description |
|---|---|
| `/gov give @user 100` | Give Drav (salary, reward) |
| `/gov take @user 50` | Remove Drav (fine, tax) |
| `/gov salary @role 30` | Pay everyone with a role |
| `/gov stats` | Full economy report |
| `/gov reset @user 100` | Reset balance to 100 |

---

## ⚙️ Setup Instructions

### 1. Fill in config.json
```json
{
    "token": "YOUR_BOT_TOKEN",
    "guild_id": "YOUR_SERVER_ID",
    "admin_role_id": "YOUR_ADMIN_ROLE_ID",
    "judge_role_id": "YOUR_JUDGE_ROLE_ID",
    "welcome_channel_id": "WELCOME_CHANNEL_ID",
    "log_channel_id": "LOG_CHANNEL_FOR_TAX_INTEREST"
}
```

### 2. Discord Developer Portal
- Go to **discord.com/developers/applications**
- **Bot** tab → turn ON all 3 Privileged Gateway Intents:
  - ✅ Presence Intent
  - ✅ Server Members Intent
  - ✅ Message Content Intent

### 3. Deploy on Railway
1. Push to GitHub
2. Connect to Railway
3. Add environment variable: `token = YOUR_BOT_TOKEN`
4. Deploy!

---

## 🎯 Key Features

- **13 Achievements** — unlockable milestones
- **Auto Tax & Interest** — runs every 24 hours
- **Business System** — citizens can open shops
- **Democratic Voting** — polls with live results
- **Advanced Court** — evidence submission and appeals
- **5 Gambling Games** — blackjack, dice, slots, coinflip, lottery
- **XP & Levels** — 11 ranks from Newcomer to Dravia Elite
- **Bank Vaults** — earn 2% interest daily, safe from robbery
- **Art Marketplace** — buy and sell art with 5% tax
- **Welcome System** — auto-greet new members with 100 Drav

---

*🦢 Dravia — Nation of Law and Unity. Est. 19__*
