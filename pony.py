# bot.py
# Pony Kingdom - Soroush Plus Official Bot API
# بازسازی شده بر اساس ربات Hamster Kingdom
#
# Install:
#   py -m pip install httpx fastapi uvicorn python-multipart
#
# Windows CMD:
#   set SPLUS_BOT_TOKEN=YOUR_BOT_TOKEN
#   set PONY_ADMIN_PASSWORD=YOUR_PANEL_PASSWORD
#   py bot.py
#
# Web panel:
#   http://127.0.0.1:8080

import asyncio
import json
import os
import random
import secrets
import threading
import time
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "users.json"

BOT_TOKEN = os.getenv("SPLUS_BOT_TOKEN", "").strip()

ADMIN_PASSWORD = os.getenv(
    "PONY_ADMIN_PASSWORD",
    "change-this-password"
)

WEB_HOST = os.getenv("PONY_WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("PONY_WEB_PORT", "8080"))

# هر 5 دقیقه یک پونی رایگان
PONY_REWARD = 50
PONY_COOLDOWN = 300

# درآمد خودکار
AUTO_INCOME_INTERVAL = 60
AUTO_SAVE_INTERVAL = 30

# جایزه روزانه
DAILY_COINS = 1000
DAILY_COOLDOWN = 86400

# گردونه
WHEEL_COOLDOWN = 3600


# ============================================================
# GAME DATA
# ============================================================

PONIES = {
    "twilight": {
        "name": "تایلایت اسپارکل",
        "emoji": "🦄",
        "price": 500,
        "income": 10,
    },
    "rainbow": {
        "name": "رینبو دش",
        "emoji": "🌈",
        "price": 5000,
        "income": 75,
    },
    "pinkie": {
        "name": "پینکی پای",
        "emoji": "🎀",
        "price": 25000,
        "income": 400,
    },
    "rarity": {
        "name": "رریتی",
        "emoji": "💎",
        "price": 100000,
        "income": 2000,
    },
    "applejack": {
        "name": "اپل‌جک",
        "emoji": "🍎",
        "price": 250000,
        "income": 6000,
    },
    "fluttershy": {
        "name": "فلاترشای",
        "emoji": "🦋",
        "price": 750000,
        "income": 18000,
    },
}

# به‌جای کارخانه، مکان‌های پادشاهی پونی
KINGDOMS = {
    "meadow": {
        "name": "چمنزار پونی‌ها",
        "emoji": "🌳",
        "price": 10000,
        "income": 150,
    },
    "crystal": {
        "name": "قصر کریستالی",
        "emoji": "🏰",
        "price": 50000,
        "income": 800,
    },
    "cloud": {
        "name": "شهر ابرها",
        "emoji": "☁️",
        "price": 250000,
        "income": 5000,
    },
    "canterlot": {
        "name": "کانترلوت",
        "emoji": "👑",
        "price": 1000000,
        "income": 25000,
    },
}

# دوستان/موجودات کمکی
FRIENDS = {
    "spike": {
        "name": "اسپایک",
        "emoji": "🐉",
        "price": 15000,
        "bonus": 0.05,
    },
    "angel": {
        "name": "انجل",
        "emoji": "🐰",
        "price": 30000,
        "bonus": 0.10,
    },
    "owl": {
        "name": "جغد تایلایت",
        "emoji": "🦉",
        "price": 75000,
        "bonus": 0.20,
    },
    "phoenix": {
        "name": "ققنوس",
        "emoji": "🔥",
        "price": 300000,
        "bonus": 0.50,
    },
}

MISSIONS = {
    "pony_5": {
        "name": "پیدا کردن ۵ پونی",
        "target": 5,
        "reward": 1000,
    },
    "pony_20": {
        "name": "پیدا کردن ۲۰ پونی",
        "target": 20,
        "reward": 5000,
    },
    "earn_10000": {
        "name": "کسب ۱۰٬۰۰۰ سکه",
        "target": 10000,
        "reward": 2500,
    },
    "earn_100000": {
        "name": "کسب ۱۰۰٬۰۰۰ سکه",
        "target": 100000,
        "reward": 15000,
    },
    "buy_kingdom": {
        "name": "خرید اولین مکان پادشاهی",
        "target": 1,
        "reward": 3000,
    },
    "buy_friend": {
        "name": "پیدا کردن اولین دوست",
        "target": 1,
        "reward": 2000,
    },
}

WHEEL_REWARDS = [
    (100, 35),
    (250, 25),
    (500, 18),
    (1000, 10),
    (2500, 7),
    (5000, 4),
    (10000, 1),
]


# ============================================================
# STORAGE
# ============================================================

LOCK = threading.RLock()
users = {}
web_sessions = set()
update_offset = None
running = True


def default_user(user_id, name="کاربر"):
    return {
        "id": str(user_id),
        "name": name,
        "coins": 0,
        "level": 1,
        "xp": 0,

        "last_pony": 0,
        "ponies": {},
        "pony_levels": {},

        "kingdoms": {},
        "kingdom_levels": {},

        "friends": {},

        "last_daily": 0,
        "daily_streak": 0,
        "last_spin": 0,

        "total_earned": 0,
        "total_spent": 0,
        "total_ponies_received": 0,

        "missions": {},
        "vip": False,
    }


def ensure_user_schema(user):
    """برای جلوگیری از خطا در users.json قدیمی."""
    defaults = default_user(
        user.get("id", "0"),
        user.get("name", "کاربر")
    )

    for key, value in defaults.items():
        if key not in user:
            user[key] = value.copy() if isinstance(value, dict) else value

    # اگر دیتای نسخه همستر وجود داشت، دارایی‌های قدیمی را پاک نمی‌کنیم
    # ولی ساختار پونی از اینجا به بعد استفاده می‌شود.
    return user


def load_users():
    global users

    if not USERS_FILE.exists():
        users = {}
        return

    try:
        data = json.loads(USERS_FILE.read_text(encoding="utf-8"))

        if isinstance(data, dict):
            users = data
            for user in users.values():
                ensure_user_schema(user)
        else:
            users = {}

    except Exception as e:
        print("users.json load error:", e)
        users = {}


def save_users():
    with LOCK:
        temp_file = USERS_FILE.with_suffix(".tmp")

        temp_file.write_text(
            json.dumps(
                users,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

        os.replace(temp_file, USERS_FILE)


def get_user(user_id, name="کاربر"):
    user_id = str(user_id)

    with LOCK:
        if user_id not in users:
            users[user_id] = default_user(user_id, name)
        else:
            ensure_user_schema(users[user_id])
            if name:
                users[user_id]["name"] = name

        return users[user_id]


# ============================================================
# GAME FUNCTIONS
# ============================================================

def xp_required(level):
    return 100 * level


def add_xp(user, amount):
    user["xp"] += amount

    while user["xp"] >= xp_required(user["level"]):
        user["xp"] -= xp_required(user["level"])
        user["level"] += 1


def calculate_income(user):
    base_income = 0

    for key, count in user.get("ponies", {}).items():
        if key not in PONIES:
            continue

        level = user.get("pony_levels", {}).get(key, 1)

        base_income += (
            PONIES[key]["income"]
            * count
            * level
        )

    for key, count in user.get("kingdoms", {}).items():
        if key not in KINGDOMS:
            continue

        level = user.get("kingdom_levels", {}).get(key, 1)

        base_income += (
            KINGDOMS[key]["income"]
            * count
            * level
        )

    friend_bonus = 0

    for key, count in user.get("friends", {}).items():
        if key in FRIENDS:
            friend_bonus += FRIENDS[key]["bonus"] * count

    vip_bonus = 0.20 if user.get("vip") else 0

    multiplier = 1 + friend_bonus + vip_bonus

    return int(base_income * multiplier)


def buy_item(user, catalog, key, collection, levels, xp):
    item = catalog.get(key)

    if not item:
        return False, "❌ مورد پیدا نشد."

    price = item["price"]

    if user["coins"] < price:
        return (
            False,
            f"❌ سکه کافی نیست.\nقیمت: {price:,}"
        )

    user["coins"] -= price
    user["total_spent"] += price

    user[collection][key] = (
        user[collection].get(key, 0) + 1
    )

    if levels is not None and key not in levels:
        levels[key] = 1

    add_xp(user, xp)

    return True, f"✅ {item['name']} به قلمرو تو اضافه شد!"


def upgrade_item(user, catalog, key, collection, levels, xp):
    item = catalog.get(key)

    if not item:
        return False, "❌ مورد پیدا نشد."

    if user[collection].get(key, 0) <= 0:
        return False, "❌ این مورد را نداری."

    current_level = levels.get(key, 1)
    price = item["price"] * current_level

    if user["coins"] < price:
        return (
            False,
            f"❌ سکه کافی نیست.\nهزینه ارتقا: {price:,}"
        )

    user["coins"] -= price
    user["total_spent"] += price
    levels[key] = current_level + 1

    add_xp(user, xp)

    return (
        True,
        f"⬆️ {item['name']} به سطح {current_level + 1} رسید!"
    )


def wheel_reward():
    values = [x[0] for x in WHEEL_REWARDS]
    weights = [x[1] for x in WHEEL_REWARDS]

    return random.choices(
        values,
        weights=weights,
        k=1
    )[0]


def mission_value(user, mission):
    if mission in ("pony_5", "pony_20"):
        return user["total_ponies_received"]

    if mission in ("earn_10000", "earn_100000"):
        return user["total_earned"]

    if mission == "buy_kingdom":
        return sum(user["kingdoms"].values())

    if mission == "buy_friend":
        return sum(user["friends"].values())

    return 0


def claim_mission(user, mission):
    data = MISSIONS.get(mission)

    if not data:
        return False, "❌ مأموریت پیدا نشد."

    if user["missions"].get(mission):
        return False, "ℹ️ این مأموریت قبلاً دریافت شده."

    value = mission_value(user, mission)

    if value < data["target"]:
        return (
            False,
            f"❌ مأموریت کامل نشده.\n"
            f"پیشرفت: {value}/{data['target']}"
        )

    user["missions"][mission] = True
    user["coins"] += data["reward"]
    user["total_earned"] += data["reward"]

    add_xp(user, 50)

    return (
        True,
        f"🎯 مأموریت کامل شد!\n"
        f"💰 جایزه: {data['reward']:,} سکه"
    )


# ============================================================
# TEXT
# ============================================================

def profile_text(user):
    vip = "فعال" if user.get("vip") else "غیرفعال"

    return (
        f"🦄 پروفایل {user['name']}\n\n"
        f"💰 سکه: {user['coins']:,}\n"
        f"⭐ سطح: {user['level']}\n"
        f"✨ XP: {user['xp']}/{xp_required(user['level'])}\n"
        f"📈 درآمد در دقیقه: {calculate_income(user):,}\n"
        f"💎 VIP: {vip}\n"
        f"💵 کل درآمد: {user['total_earned']:,}\n"
        f"🛒 کل خرج: {user['total_spent']:,}"
    )


def inventory_text(user):
    lines = [
        "🎒 دارایی‌های پادشاهی تو",
        "",
        "🦄 پونی‌ها:"
    ]

    found = False

    for key, data in PONIES.items():
        count = user["ponies"].get(key, 0)

        if count:
            found = True
            level = user["pony_levels"].get(key, 1)

            lines.append(
                f"{data['emoji']} {data['name']}: "
                f"{count} عدد | سطح {level}"
            )

    if not found:
        lines.append("هنوز پونی نداری.")

    lines += ["", "🏰 مکان‌های پادشاهی:"]

    found = False

    for key, data in KINGDOMS.items():
        count = user["kingdoms"].get(key, 0)

        if count:
            found = True
            level = user["kingdom_levels"].get(key, 1)

            lines.append(
                f"{data['emoji']} {data['name']}: "
                f"{count} عدد | سطح {level}"
            )

    if not found:
        lines.append("هنوز مکانی در پادشاهی نداری.")

    lines += ["", "🤝 دوستان:"]

    found = False

    for key, data in FRIENDS.items():
        count = user["friends"].get(key, 0)

        if count:
            found = True
            lines.append(
                f"{data['emoji']} {data['name']}: {count}"
            )

    if not found:
        lines.append("هنوز دوستی پیدا نکرده‌ای.")

    return "\n".join(lines)


def shop_text():
    lines = [
        "🛍 فروشگاه Pony Kingdom",
        "",
        "🦄 پونی‌ها:"
    ]

    for data in PONIES.values():
        lines.append(
            f"{data['emoji']} {data['name']} — "
            f"{data['price']:,} سکه | "
            f"+{data['income']:,}/دقیقه"
        )

    lines += ["", "🏰 مکان‌های پادشاهی:"]

    for data in KINGDOMS.values():
        lines.append(
            f"{data['emoji']} {data['name']} — "
            f"{data['price']:,} سکه | "
            f"+{data['income']:,}/دقیقه"
        )

    lines += ["", "🤝 دوستان:"]

    for data in FRIENDS.values():
        lines.append(
            f"{data['emoji']} {data['name']} — "
            f"{data['price']:,} سکه | "
            f"+{int(data['bonus'] * 100)}% درآمد"
        )

    return "\n".join(lines)


def missions_text(user):
    lines = ["🎯 مأموریت‌های پونی‌ها", ""]

    for key, data in MISSIONS.items():
        value = mission_value(user, key)

        if user["missions"].get(key):
            status = "✅ دریافت شد"
        else:
            status = (
                f"{value}/{data['target']} "
                f"— جایزه {data['reward']:,}"
            )

        lines.append(
            f"• {data['name']}: {status}"
        )

    return "\n".join(lines)


def leaderboard_text():
    ranking = []

    with LOCK:
        for user in users.values():
            ensure_user_schema(user)

            score = (
                user["coins"]
                + calculate_income(user) * 100
                + user["level"] * 1000
            )

            ranking.append((score, user))

    ranking.sort(
        key=lambda x: x[0],
        reverse=True
    )

    if not ranking:
        return "🏆 هنوز بازیکنی وجود ندارد."

    lines = ["🏆 برترین پونی‌سوارها", ""]

    medals = ["🥇", "🥈", "🥉"]

    for index, (_, user) in enumerate(ranking[:10], 1):
        medal = medals[index - 1] if index <= 3 else f"{index}."

        lines.append(
            f"{medal} {user['name']} — "
            f"💰 {user['coins']:,} | "
            f"⭐ {user['level']}"
        )

    return "\n".join(lines)


def help_text():
    return (
        "❓ راهنمای Pony Kingdom\n\n"

        "🦄 رنگین کمون\n"
        "هر ۵ دقیقه پاداش پونی بگیر\n\n"

        "💰 موجودی\n"
        "نمایش سکه‌های تو\n\n"

        "👤 پروفایل\n"
        "نمایش اطلاعات بازیکن\n\n"

        "🎒 دارایی‌ها\n"
        "نمایش پونی‌ها، مکان‌ها و دوستان\n\n"

        "🛍 فروشگاه\n"
        "خرید پونی، مکان و دوست\n\n"

        "🎁 جایزه روزانه\n"
        "دریافت جایزه روزانه و استریک\n\n"

        "🎡 گردونه\n"
        "شانس گرفتن سکه بیشتر\n\n"

        "🎯 مأموریت‌ها\n"
        "انجام مأموریت و گرفتن جایزه\n\n"

        "🏆 رتبه\n"
        "دیدن ۱۰ بازیکن برتر"
    )


# ============================================================
# SOROUSH PLUS API
# ============================================================

class SPlusAPI:
    def __init__(self, token):
        self.token = token
        self.base_url = "https://api.splus.ir/bot" + token

        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                40.0,
                connect=10.0
            )
        )

    async def call(self, method, data=None):
        if not self.token:
            raise RuntimeError(
                "SPLUS_BOT_TOKEN تنظیم نشده."
            )

        response = await self.client.post(
            f"{self.base_url}/{method}",
            json=data or {}
        )

        response.raise_for_status()

        result = response.json()

        if not result.get("ok"):
            raise RuntimeError(
                result.get(
                    "description",
                    "SPlus API error"
                )
            )

        return result.get("result")

    async def get_me(self):
        return await self.call("getMe")

    async def get_updates(
        self,
        offset=None,
        timeout=30,
        limit=100
    ):
        data = {
            "limit": limit,
            "timeout": timeout
        }

        if offset is not None:
            data["offset"] = offset

        return await self.call(
            "getUpdates",
            data
        )

    async def send_message(
        self,
        chat_id,
        text,
        reply_markup=None,
        parse_mode=None
    ):
        data = {
            "chat_id": chat_id,
            "text": text
        }

        if reply_markup is not None:
            data["reply_markup"] = reply_markup

        if parse_mode:
            data["parse_mode"] = parse_mode

        return await self.call(
            "sendMessage",
            data
        )

    async def edit_message_text(
        self,
        chat_id,
        message_id,
        text,
        reply_markup=None
    ):
        data = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text
        }

        if reply_markup is not None:
            data["reply_markup"] = reply_markup

        return await self.call(
            "editMessageText",
            data
        )

    async def answer_callback_query(
        self,
        callback_query_id,
        text=None,
        show_alert=False
    ):
        data = {
            "callback_query_id": callback_query_id,
            "show_alert": show_alert
        }

        if text:
            data["text"] = text

        return await self.call(
            "answerCallbackQuery",
            data
        )

    async def set_my_commands(self):
        commands = [
            {
                "command": "start",
                "description": "شروع بازی"
            },
            {
                "command": "help",
                "description": "راهنما"
            },
            {
                "command": "balance",
                "description": "موجودی"
            },
            {
                "command": "profile",
                "description": "پروفایل"
            },
            {
                "command": "shop",
                "description": "فروشگاه"
            },
        ]

        return await self.call(
            "setMyCommands",
            {"commands": commands}
        )


api = SPlusAPI(BOT_TOKEN)


# ============================================================
# KEYBOARDS
# ============================================================

def button(text, callback_data):
    return {
        "text": text,
        "callback_data": callback_data
    }


def keyboard(rows):
    return {
        "inline_keyboard": rows
    }


def main_keyboard():
    return keyboard([
        [
            button("🦄 پونی", "pony"),
            button("💰 موجودی", "balance"),
        ],
        [
            button("👤 پروفایل", "profile"),
            button("🎒 دارایی‌ها", "inventory"),
        ],
        [
            button("🛍 فروشگاه", "shop"),
            button("🎯 مأموریت‌ها", "missions"),
        ],
        [
            button("🎁 روزانه", "daily"),
            button("🎡 گردونه", "wheel"),
        ],
        [
            button("🏆 رتبه", "leaderboard"),
            button("❓ راهنما", "help"),
        ],
    ])


def shop_keyboard():
    rows = []

    for key, data in PONIES.items():
        rows.append([
            button(
                f"{data['emoji']} {data['name']} | {data['price']:,}",
                f"buy_pony:{key}"
            )
        ])

    for key, data in KINGDOMS.items():
        rows.append([
            button(
                f"{data['emoji']} {data['name']} | {data['price']:,}",
                f"buy_kingdom:{key}"
            )
        ])

    for key, data in FRIENDS.items():
        rows.append([
            button(
                f"{data['emoji']} {data['name']} | {data['price']:,}",
                f"buy_friend:{key}"
            )
        ])

    rows.append([
        button("⬅️ برگشت", "home")
    ])

    return keyboard(rows)


def mission_keyboard(user):
    rows = []

    for key, data in MISSIONS.items():
        if not user["missions"].get(key):
            rows.append([
                button(
                    f"🎯 {data['name']}",
                    f"claim_m:{key}"
                )
            ])

    rows.append([
        button("⬅️ برگشت", "home")
    ])

    return keyboard(rows)


# ============================================================
# MESSAGE HANDLING
# ============================================================

async def send(chat_id, text, markup=None):
    return await api.send_message(
        chat_id,
        text,
        markup
    )


def user_from_sender(sender, chat_id):
    user_id = sender.get("id", chat_id)

    name = (
        sender.get("first_name")
        or sender.get("username")
        or "کاربر"
    )

    return get_user(user_id, name)


async def give_pony(chat_id, user, edit=False, message_id=None):
    now = time.time()

    remaining = (
        PONY_COOLDOWN
        - (now - user["last_pony"])
    )

    if remaining > 0:
        minutes = int(remaining) // 60
        seconds = int(remaining) % 60

        text = (
            f"⏳ هنوز {minutes} دقیقه و "
            f"{seconds} ثانیه مونده."
        )

        if edit:
            await api.answer_callback_query(
                None,
                text,
                True
            )
        else:
            await send(chat_id, text)

        return

    reward = PONY_REWARD

    if user.get("vip"):
        reward = int(reward * 1.5)

    user["last_pony"] = now
    user["coins"] += reward
    user["total_earned"] += reward
    user["total_ponies_received"] += 1

    add_xp(user, 10)

    # یک پونی تصادفی برای ثبت در مجموعه
    pony_key = random.choice(list(PONIES.keys()))
    user["ponies"][pony_key] = (
        user["ponies"].get(pony_key, 0) + 1
    )

    pony = PONIES[pony_key]

    text = (
        f"{pony['emoji']} {pony['name']} پیدا کردی!\n\n"
        f"💰 +{reward:,} سکه\n"
        f"⭐ +10 XP\n"
        f"🦄 یک {pony['name']} به مجموعه‌ات اضافه شد!"
    )

    if edit and message_id is not None:
        await api.edit_message_text(
            chat_id,
            message_id,
            text,
            main_keyboard()
        )
    else:
        await send(
            chat_id,
            text,
            main_keyboard()
        )


async def handle_message(message):
    if not message:
        return

    chat = message.get("chat", {})
    sender = message.get("from", {})

    chat_id = chat.get("id")

    if chat_id is None:
        return

    user = user_from_sender(sender, chat_id)

    text = (
        message.get("text") or ""
    ).strip()

    command = text.lower()

    # START
    if command in ("/start", "start"):
        await send(
            chat_id,
            f"🦄 سلام {user['name']}!\n\n"
            "به Pony Kingdom خوش اومدی!\n"
            "پادشاهی خودت رو بساز، پونی جمع کن و ثروتمند شو 👑\n\n"
            "از منوی زیر شروع کن 👇",
            main_keyboard()
        )
        return

    # PONY
    if command in ("رنگین کمون", "/pony"):
        await give_pony(chat_id, user)
        return

    # BALANCE
    if command in ("موجودی", "/balance"):
        await send(
            chat_id,
            f"💰 موجودی شما:\n\n"
            f"{user['coins']:,} سکه",
            main_keyboard()
        )
        return

    # PROFILE
    if command in ("پروفایل", "/profile"):
        await send(
            chat_id,
            profile_text(user),
            main_keyboard()
        )
        return

    # INVENTORY
    if command in ("دارایی‌ها", "دارایی ها", "دارایی"):
        await send(
            chat_id,
            inventory_text(user),
            main_keyboard()
        )
        return

    # SHOP
    if command in ("فروشگاه", "/shop"):
        await send(
            chat_id,
            shop_text(),
            shop_keyboard()
        )
        return

    # MISSIONS
    if command in (
        "ماموریت",
        "ماموریت‌ها",
        "ماموریت ها"
    ):
        await send(
            chat_id,
            missions_text(user),
            mission_keyboard(user)
        )
        return

    # LEADERBOARD
    if command in (
        "رتبه",
        "رتبه‌بندی",
        "رتبه بندی"
    ):
        await send(
            chat_id,
            leaderboard_text(),
            main_keyboard()
        )
        return

    # DAILY
    if command in (
        "جایزه روزانه",
        "روزانه",
        "/daily"
    ):
        now = time.time()

        remaining = (
            DAILY_COOLDOWN
            - (now - user["last_daily"])
        )

        if remaining > 0:
            hours = int(remaining) // 3600
            minutes = (int(remaining) % 3600) // 60

            await send(
                chat_id,
                f"⏳ جایزه روزانه آماده نیست.\n"
                f"زمان باقی‌مانده: "
                f"{hours} ساعت و {minutes} دقیقه"
            )
            return

        if (
            now - user["last_daily"]
            <= DAILY_COOLDOWN * 2
        ):
            user["daily_streak"] += 1
        else:
            user["daily_streak"] = 1

        reward = min(
            5000,
            DAILY_COINS
            + (user["daily_streak"] - 1) * 250
        )

        user["last_daily"] = now
        user["coins"] += reward
        user["total_earned"] += reward

        add_xp(user, 25)

        await send(
            chat_id,
            f"🎁 جایزه روزانه!\n\n"
            f"💰 +{reward:,} سکه\n"
            f"🔥 استریک: {user['daily_streak']}",
            main_keyboard()
        )
        return

    # WHEEL
    if command in ("گردونه", "wheel", "/wheel"):
        now = time.time()

        if now - user["last_spin"] < WHEEL_COOLDOWN:
            await send(
                chat_id,
                "⏳ گردونه هنوز آماده نیست."
            )
            return

        reward = wheel_reward()

        user["last_spin"] = now
        user["coins"] += reward
        user["total_earned"] += reward

        add_xp(user, 10)

        await send(
            chat_id,
            f"🎡 گردونه چرخید!\n\n"
            f"💰 +{reward:,} سکه",
            main_keyboard()
        )
        return

    # HELP
    if command in ("راهنما", "/help"):
        await send(
            chat_id,
            help_text(),
            main_keyboard()
        )
        return

    await send(
        chat_id,
        "🤔 این دستور رو نمی‌شناسم.\n"
        "از /help استفاده کن.",
        main_keyboard()
    )


# ============================================================
# CALLBACK HANDLING
# ============================================================

async def handle_callback(callback):
    if not callback:
        return

    callback_id = callback.get("id")
    data = callback.get("data", "")

    message = callback.get("message", {})
    chat = message.get("chat", {})
    sender = callback.get("from", {})

    chat_id = chat.get("id")
    message_id = message.get("message_id")

    if chat_id is None:
        return

    user = user_from_sender(sender, chat_id)

    if callback_id:
        try:
            await api.answer_callback_query(callback_id)
        except Exception as e:
            print("Callback ACK error:", e)

    # HOME
    if data == "home":
        await api.edit_message_text(
            chat_id,
            message_id,
            f"🦄 Pony Kingdom\n\n"
            f"💰 {user['coins']:,} سکه\n"
            f"📈 درآمد: {calculate_income(user):,}/دقیقه",
            main_keyboard()
        )
        return

    # PONY
    if data == "pony":
        now = time.time()

        remaining = (
            PONY_COOLDOWN
            - (now - user["last_pony"])
        )

        if remaining > 0:
            await api.answer_callback_query(
                callback_id,
                f"⏳ {int(remaining)} ثانیه باقی مانده.",
                True
            )
            return

        reward = PONY_REWARD

        if user.get("vip"):
            reward = int(reward * 1.5)

        user["last_pony"] = now
        user["coins"] += reward
        user["total_earned"] += reward
        user["total_ponies_received"] += 1

        add_xp(user, 10)

        pony_key = random.choice(list(PONIES.keys()))
        user["ponies"][pony_key] = (
            user["ponies"].get(pony_key, 0) + 1
        )

        pony = PONIES[pony_key]

        await api.edit_message_text(
            chat_id,
            message_id,
            f"{pony['emoji']} {pony['name']} پیدا کردی!\n\n"
            f"💰 +{reward:,} سکه\n"
            f"⭐ +10 XP\n"
            f"🦄 یک {pony['name']} به مجموعه‌ات اضافه شد!",
            main_keyboard()
        )
        return

    # BALANCE
    if data == "balance":
        await api.edit_message_text(
            chat_id,
            message_id,
            f"💰 موجودی:\n\n"
            f"{user['coins']:,} سکه",
            main_keyboard()
        )
        return

    # PROFILE
    if data == "profile":
        await api.edit_message_text(
            chat_id,
            message_id,
            profile_text(user),
            main_keyboard()
        )
        return

    # INVENTORY
    if data == "inventory":
        await api.edit_message_text(
            chat_id,
            message_id,
            inventory_text(user),
            main_keyboard()
        )
        return

    # SHOP
    if data == "shop":
        await api.edit_message_text(
            chat_id,
            message_id,
            shop_text(),
            shop_keyboard()
        )
        return

    # MISSIONS
    if data == "missions":
        await api.edit_message_text(
            chat_id,
            message_id,
            missions_text(user),
            mission_keyboard(user)
        )
        return

    # LEADERBOARD
    if data == "leaderboard":
        await api.edit_message_text(
            chat_id,
            message_id,
            leaderboard_text(),
            main_keyboard()
        )
        return

    # HELP
    if data == "help":
        await api.edit_message_text(
            chat_id,
            message_id,
            help_text(),
            main_keyboard()
        )
        return

    # DAILY
    if data == "daily":
        now = time.time()

        if now - user["last_daily"] < DAILY_COOLDOWN:
            await api.answer_callback_query(
                callback_id,
                "⏳ جایزه روزانه هنوز آماده نیست.",
                True
            )
            return

        if (
            now - user["last_daily"]
            <= DAILY_COOLDOWN * 2
        ):
            user["daily_streak"] += 1
        else:
            user["daily_streak"] = 1

        reward = min(
            5000,
            DAILY_COINS
            + (user["daily_streak"] - 1) * 250
        )

        user["last_daily"] = now
        user["coins"] += reward
        user["total_earned"] += reward

        add_xp(user, 25)

        await api.edit_message_text(
            chat_id,
            message_id,
            f"🎁 جایزه روزانه!\n\n"
            f"💰 +{reward:,} سکه\n"
            f"🔥 استریک: {user['daily_streak']}",
            main_keyboard()
        )
        return

    # WHEEL
    if data == "wheel":
        now = time.time()

        if now - user["last_spin"] < WHEEL_COOLDOWN:
            await api.answer_callback_query(
                callback_id,
                "⏳ گردونه آماده نیست.",
                True
            )
            return

        reward = wheel_reward()

        user["last_spin"] = now
        user["coins"] += reward
        user["total_earned"] += reward

        add_xp(user, 10)

        await api.edit_message_text(
            chat_id,
            message_id,
            f"🎡 برنده شدی!\n\n"
            f"💰 +{reward:,} سکه",
            main_keyboard()
        )
        return

    # BUY PONY
    if data.startswith("buy_pony:"):
        key = data[len("buy_pony:"):]

        ok, text = buy_item(
            user,
            PONIES,
            key,
            "ponies",
            user["pony_levels"],
            25
        )

        await api.answer_callback_query(
            callback_id,
            text[:200],
            not ok
        )

        await api.edit_message_text(
            chat_id,
            message_id,
            f"{text}\n\n"
            f"💰 موجودی: {user['coins']:,}",
            shop_keyboard()
        )
        return

    # BUY KINGDOM
    if data.startswith("buy_kingdom:"):
        key = data[len("buy_kingdom:"):]

        ok, text = buy_item(
            user,
            KINGDOMS,
            key,
            "kingdoms",
            user["kingdom_levels"],
            100
        )

        await api.answer_callback_query(
            callback_id,
            text[:200],
            not ok
        )

        await api.edit_message_text(
            chat_id,
            message_id,
            f"{text}\n\n"
            f"💰 موجودی: {user['coins']:,}",
            shop_keyboard()
        )
        return

    # BUY FRIEND
    if data.startswith("buy_friend:"):
        key = data[len("buy_friend:"):]

        ok, text = buy_item(
            user,
            FRIENDS,
            key,
            "friends",
            None,
            50
        )

        await api.answer_callback_query(
            callback_id,
            text[:200],
            not ok
        )

        await api.edit_message_text(
            chat_id,
            message_id,
            f"{text}\n\n"
            f"💰 موجودی: {user['coins']:,}",
            shop_keyboard()
        )
        return

    # CLAIM MISSION
    if data.startswith("claim_m:"):
        key = data[len("claim_m:"):]

        ok, text = claim_mission(
            user,
            key
        )

        await api.answer_callback_query(
            callback_id,
            text[:200],
            not ok
        )

        await api.edit_message_text(
            chat_id,
            message_id,
            missions_text(user),
            mission_keyboard(user)
        )
        return


# ============================================================
# UPDATE LOOP
# ============================================================

async def process_update(update):
    if update.get("message"):
        await handle_message(
            update["message"]
        )

    if update.get("callback_query"):
        await handle_callback(
            update["callback_query"]
        )


async def bot_loop():
    global update_offset

    if not BOT_TOKEN:
        print("\nERROR: SPLUS_BOT_TOKEN is not set.")
        return

    try:
        me = await api.get_me()

        print("================================")
        print("Soroush Plus Bot Connected")
        print("Pony Kingdom")
        print("Bot:", me)
        print("================================")

    except Exception as e:
        print("getMe failed:", e)
        return

    try:
        await api.set_my_commands()
        print("Bot commands configured.")
    except Exception as e:
        print("setMyCommands warning:", e)

    while running:
        try:
            updates = await api.get_updates(
                offset=update_offset,
                timeout=30,
                limit=100
            )

            for update in updates or []:
                update_offset = (
                    int(update["update_id"]) + 1
                )

                try:
                    await process_update(update)
                except Exception as e:
                    print(
                        "Update processing error:",
                        repr(e)
                    )

            save_users()

        except Exception as e:
            print("Polling error:", repr(e))
            await asyncio.sleep(3)


# ============================================================
# AUTO INCOME
# ============================================================

async def auto_income_loop():
    while running:
        await asyncio.sleep(
            AUTO_INCOME_INTERVAL
        )

        with LOCK:
            for user in users.values():
                ensure_user_schema(user)

                income = calculate_income(user)

                if income <= 0:
                    continue

                user["coins"] += income
                user["total_earned"] += income

        save_users()


# ============================================================
# WEB PANEL
# ============================================================

app = FastAPI(title="Pony Kingdom Admin")


def is_logged_in(request: Request):
    session = request.cookies.get("pony_admin")
    return session in web_sessions


def html_page(title, content):
    return f"""
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
* {{ box-sizing: border-box; }}

body {{
    margin: 0;
    font-family: Tahoma, Arial, sans-serif;
    background: #17132b;
    color: #fff;
}}

nav {{
    background: #241b42;
    padding: 18px 25px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
}}

nav a {{
    color: #fff;
    text-decoration: none;
    margin: 0 8px;
}}

main {{
    max-width: 1200px;
    margin: 30px auto;
    padding: 0 15px;
}}

.grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 15px;
}}

.card {{
    background: #272044;
    padding: 20px;
    border-radius: 18px;
    margin-bottom: 15px;
    box-shadow: 0 8px 30px rgba(0,0,0,.18);
}}

.card h2 {{
    margin: 8px 0 0;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    background: #272044;
    border-radius: 15px;
    overflow: hidden;
}}

th, td {{
    padding: 12px;
    border-bottom: 1px solid #3b315e;
    text-align: right;
}}

input, button {{
    padding: 11px;
    border: 1px solid #514572;
    border-radius: 9px;
    background: #17132b;
    color: white;
}}

button {{
    cursor: pointer;
    background: #3b2e61;
}}

a {{
    color: #d8c9ff;
}}

form.inline {{
    display: inline;
}}
</style>
</head>
<body>
<nav>
<b>🦄 Pony Kingdom</b>
<div>
<a href="/">داشبورد</a>
<a href="/users">کاربران</a>
<a href="/logout">خروج</a>
</div>
</nav>
<main>
{content}
</main>
</body>
</html>
"""


LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pony Kingdom</title>
<style>
body {
    margin: 0;
    background: #17132b;
    color: white;
    font-family: Tahoma, Arial;
}
.box {
    width: 90%;
    max-width: 400px;
    margin: 100px auto;
    padding: 30px;
    background: #272044;
    border-radius: 20px;
}
input, button {
    width: 100%;
    padding: 13px;
    margin-top: 10px;
    box-sizing: border-box;
    border-radius: 10px;
    border: 1px solid #514572;
    background: #17132b;
    color: white;
}
button {
    cursor: pointer;
    background: #3b2e61;
}
</style>
</head>
<body>
<div class="box">
<h1>🦄 Pony Kingdom</h1>
<p>پنل مدیریت</p>
<form method="post" action="/login">
<input type="password" name="password" placeholder="رمز پنل" required>
<button>ورود</button>
</form>
</div>
</body>
</html>
"""


@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return LOGIN_PAGE


@app.post("/login")
async def login(
    request: Request,
    password: str = Form(...)
):
    if password != ADMIN_PASSWORD:
        return HTMLResponse(
            "<h2 style='direction:rtl'>❌ رمز اشتباه است</h2>"
            "<a href='/login'>برگشت</a>",
            status_code=401
        )

    session = secrets.token_urlsafe(32)
    web_sessions.add(session)

    response = RedirectResponse(
        url="/",
        status_code=303
    )

    response.set_cookie(
        key="pony_admin",
        value=session,
        httponly=True,
        samesite="lax"
    )

    return response


@app.get("/logout")
async def logout(request: Request):
    session = request.cookies.get("pony_admin")

    if session:
        web_sessions.discard(session)

    response = RedirectResponse(
        "/login",
        status_code=303
    )

    response.delete_cookie("pony_admin")

    return response


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    if not is_logged_in(request):
        return RedirectResponse(
            "/login",
            status_code=303
        )

    with LOCK:
        for user in users.values():
            ensure_user_schema(user)

        total_coins = sum(
            u["coins"] for u in users.values()
        )

        total_ponies = sum(
            sum(u["ponies"].values())
            for u in users.values()
        )

        total_kingdoms = sum(
            sum(u["kingdoms"].values())
            for u in users.values()
        )

        total_friends = sum(
            sum(u["friends"].values())
            for u in users.values()
        )

        vip_users = sum(
            1 for u in users.values()
            if u.get("vip")
        )

        total_income = sum(
            calculate_income(u)
            for u in users.values()
        )

    content = f"""
<h1>📊 داشبورد Pony Kingdom</h1>

<div class="grid">

<div class="card">
👥 کاربران
<h2>{len(users):,}</h2>
</div>

<div class="card">
💰 کل سکه
<h2>{total_coins:,}</h2>
</div>

<div class="card">
🦄 پونی‌ها
<h2>{total_ponies:,}</h2>
</div>

<div class="card">
🏰 مکان‌های پادشاهی
<h2>{total_kingdoms:,}</h2>
</div>

<div class="card">
🤝 دوستان
<h2>{total_friends:,}</h2>
</div>

<div class="card">
💎 کاربران VIP
<h2>{vip_users:,}</h2>
</div>

<div class="card">
📈 درآمد کل در دقیقه
<h2>{total_income:,}</h2>
</div>

</div>
"""

    return html_page(
        "Dashboard",
        content
    )


@app.get("/users", response_class=HTMLResponse)
async def users_page(
    request: Request,
    q: str = ""
):
    if not is_logged_in(request):
        return RedirectResponse(
            "/login",
            status_code=303
        )

    q = q.strip().lower()
    rows = []

    with LOCK:
        for user_id, user in users.items():
            ensure_user_schema(user)

            name = str(user.get("name", ""))

            if q:
                if (
                    q not in user_id.lower()
                    and q not in name.lower()
                ):
                    continue

            rows.append(
                f"""
<tr>
<td>{user_id}</td>
<td>{name}</td>
<td>{user['coins']:,}</td>
<td>{user['level']}</td>
<td>{calculate_income(user):,}</td>
<td>{'✅' if user.get('vip') else '❌'}</td>
<td><a href="/user/{user_id}">مدیریت</a></td>
</tr>
"""
            )

    content = f"""
<h1>👥 کاربران</h1>

<form>
<input name="q" value="{q}" placeholder="جستجو با ID یا نام">
<button>جستجو</button>
</form>

<br>

<table>
<tr>
<th>ID</th>
<th>نام</th>
<th>سکه</th>
<th>سطح</th>
<th>درآمد</th>
<th>VIP</th>
<th>مدیریت</th>
</tr>

{''.join(rows)}

</table>
"""

    return html_page(
        "Users",
        content
    )


@app.get(
    "/user/{user_id}",
    response_class=HTMLResponse
)
async def user_page(
    request: Request,
    user_id: str
):
    if not is_logged_in(request):
        return RedirectResponse(
            "/login",
            status_code=303
        )

    with LOCK:
        user = users.get(user_id)

        if user:
            ensure_user_schema(user)

    if not user:
        return HTMLResponse(
            "کاربر پیدا نشد.",
            status_code=404
        )

    vip_button = (
        "غیرفعال کردن VIP"
        if user.get("vip")
        else
        "فعال کردن VIP"
    )

    content = f"""
<h1>👤 {user['name']}</h1>

<div class="card">

<p>🆔 ID: <b>{user_id}</b></p>
<p>💰 سکه: <b>{user['coins']:,}</b></p>
<p>⭐ سطح: <b>{user['level']}</b></p>
<p>📈 درآمد: <b>{calculate_income(user):,}</b> در دقیقه</p>
<p>🦄 تعداد پونی: <b>{user['total_ponies_received']:,}</b></p>
<p>💎 VIP: <b>{'فعال' if user.get('vip') else 'غیرفعال'}</b></p>

</div>

<div class="grid">

<div class="card">
<h3>💰 مدیریت سکه</h3>

<form method="post" action="/user/{user_id}/coins">

<input
type="number"
name="amount"
placeholder="مقدار"
required
>

<br>

<button name="action" value="add">افزایش</button>
<button name="action" value="remove">کاهش</button>
<button name="action" value="set">تنظیم</button>

</form>
</div>

<div class="card">
<h3>💎 VIP</h3>

<form method="post" action="/user/{user_id}/vip">
<button>{vip_button}</button>
</form>

</div>

<div class="card">
<h3>⚠️ ریست</h3>

<form method="post" action="/user/{user_id}/reset">
<button>ریست کامل کاربر</button>
</form>

</div>

</div>
"""

    return html_page(
        "User",
        content
    )


@app.post("/user/{user_id}/coins")
async def change_coins(
    request: Request,
    user_id: str,
    amount: int = Form(...),
    action: str = Form(...)
):
    if not is_logged_in(request):
        return RedirectResponse(
            "/login",
            status_code=303
        )

    with LOCK:
        user = users.get(user_id)

        if user:
            ensure_user_schema(user)

            amount = max(0, amount)

            if action == "add":
                user["coins"] += amount

            elif action == "remove":
                user["coins"] = max(
                    0,
                    user["coins"] - amount
                )

            elif action == "set":
                user["coins"] = amount

    save_users()

    return RedirectResponse(
        f"/user/{user_id}",
        status_code=303
    )


@app.post("/user/{user_id}/vip")
async def toggle_vip(
    request: Request,
    user_id: str
):
    if not is_logged_in(request):
        return RedirectResponse(
            "/login",
            status_code=303
        )

    with LOCK:
        if user_id in users:
            ensure_user_schema(users[user_id])

            users[user_id]["vip"] = not users[
                user_id
            ].get("vip", False)

    save_users()

    return RedirectResponse(
        f"/user/{user_id}",
        status_code=303
    )


@app.post("/user/{user_id}/reset")
async def reset_user(
    request: Request,
    user_id: str
):
    if not is_logged_in(request):
        return RedirectResponse(
            "/login",
            status_code=303
        )

    with LOCK:
        if user_id in users:
            name = users[user_id].get(
                "name",
                "کاربر"
            )

            users[user_id] = default_user(
                user_id,
                name
            )

    save_users()

    return RedirectResponse(
        f"/user/{user_id}",
        status_code=303
    )


# ============================================================
# SAVE LOOP
# ============================================================

async def save_loop():
    while running:
        await asyncio.sleep(
            AUTO_SAVE_INTERVAL
        )

        try:
            save_users()
        except Exception as e:
            print("Save error:", e)


# ============================================================
# WEB SERVER
# ============================================================

def start_web_server():
    uvicorn.run(
        app,
        host=WEB_HOST,
        port=WEB_PORT,
        log_level="info"
    )


# ============================================================
# MAIN
# ============================================================

async def main_async():
    await asyncio.gather(
        bot_loop(),
        auto_income_loop(),
        save_loop()
    )


def main():
    load_users()

    print("========================================")
    print("🦄 Pony Kingdom")
    print("Soroush Plus Official API")
    print("========================================")

    if not BOT_TOKEN:
        print("ERROR: SPLUS_BOT_TOKEN is not set.")
        print()
        print("Windows CMD:")
        print("set SPLUS_BOT_TOKEN=YOUR_TOKEN")
        print("set PONY_ADMIN_PASSWORD=YOUR_PASSWORD")
        print("py bot.py")
        return

    web_thread = threading.Thread(
        target=start_web_server,
        daemon=True
    )

    web_thread.start()

    print(
        f"🌐 Web Panel: http://127.0.0.1:{WEB_PORT}"
    )

    print("🦄 Pony Kingdom starting...")

    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        save_users()


if __name__ == "__main__":
    main()
