import asyncio
import json
import logging
import os
import random

from splusthon import SoroushClient, events

logging.basicConfig(
    format="[%(levelname)s] %(message)s",
    level=logging.WARNING
)

DATA_FILE = "data.json"
SESSION_FILE = "splus.session"


# -----------------------------
# Data
# -----------------------------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "enemies": {},
            "replies": [],
            "enabled": True,
            "magazine": {}
        }

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        data.setdefault("enemies", {})
        data.setdefault("replies", [])
        data.setdefault("enabled", True)
        data.setdefault("magazine", {})

        return data

    except Exception:
        return {
            "enemies": {},
            "replies": [],
            "enabled": True,
            "magazine": {}
        }


def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


data = load_data()


# -----------------------------
# Runtime state
# -----------------------------

spam_state = {}
magazine_state = {}
auto_reply_state = {"running": False, "task": None}
purge_state = {}


# -----------------------------
# Client
# -----------------------------

client = SoroushClient(SESSION_FILE)


# -----------------------------
# Helper
# -----------------------------

def enemy_key(chat_id, user_id):
    return f"{chat_id}:{user_id}"


def get_enemy(chat_id, user_id):
    return enemy_key(chat_id, user_id) in data["enemies"]


# -----------------------------
# Enemy / Friend
# -----------------------------

@client.on(events.NewMessage(outgoing=True))
async def manage_enemy(event):

    text = (event.raw_text or "").strip()

    if text not in ("دشمن", "دوست"):
        return

    if not event.is_reply:
        await event.reply("باید روی پیام شخص ریپلای کنی.")
        return

    replied = await event.get_reply_message()

    if replied is None:
        return

    user_id = replied.sender_id
    chat_id = event.chat_id

    if user_id is None:
        await event.reply("شناسه کاربر پیدا نشد.")
        return

    key = enemy_key(chat_id, user_id)

    if text == "دشمن":

        if key in data["enemies"]:
            await event.reply("این شخص از قبل دشمن است.")
            return

        data["enemies"][key] = {
            "chat_id": chat_id,
            "user_id": user_id
        }

        save_data()

        await event.reply("این شخص به لیست دشمنان اضافه شد.")

    elif text == "دوست":

        if key not in data["enemies"]:
            await event.reply("این شخص در لیست دشمنان نیست.")
            return

        del data["enemies"][key]

        save_data()

        await event.reply("این شخص از لیست دشمنان حذف شد.")


# -----------------------------
# Pin / Delete / Ban / Unban (by reply)
# -----------------------------

@client.on(events.NewMessage(outgoing=True))
async def pin_ban_delete(event):

    text = (event.raw_text or "").strip()

    if text not in ("پین", "حذف", "بن", "آنبن"):
        return

    if not event.is_reply:
        await event.reply("باید روی یه پیام ریپلای کنی.")
        return

    replied = await event.get_reply_message()

    if replied is None:
        await event.reply("پیام مورد نظر پیدا نشد.")
        return

    chat_id = event.chat_id

    # ---- پین ----
    if text == "پین":
        try:
            await client.pin_message(chat_id, replied.id)
            await event.reply("پیام پین شد.")
        except Exception as e:
            logging.warning(f"Pin error: {e}")
            await event.reply(f"خطا در پین کردن:\n{e}")
        return

    # ---- حذف ----
    if text == "حذف":
        try:
            await client.delete_messages(
                chat_id,
                [replied.id],
                revoke=True
            )
            # پیام دستور حذف هم پاک بشه
            try:
                await client.delete_messages(
                    chat_id,
                    [event.id],
                    revoke=True
                )
            except Exception:
                pass
        except Exception as e:
            logging.warning(f"Delete error: {e}")
            await event.reply(f"خطا در حذف:\n{e}")
        return

    # ---- بن ----
    if text == "بن":
        user_id = replied.sender_id
        if user_id is None:
            await event.reply("شناسه کاربر پیدا نشد.")
            return

        try:
            await client.edit_permissions(
                chat_id,
                user_id,
                view_messages=False
            )
            await event.reply("کاربر بن شد.")
        except Exception as e:
            logging.warning(f"Ban error: {e}")
            await event.reply(f"خطا در بن کردن:\n{e}")
        return

    # ---- آنبن ----
    if text == "آنبن":
        user_id = replied.sender_id
        if user_id is None:
            await event.reply("شناسه کاربر پیدا نشد.")
            return

        try:
            await client.edit_permissions(
                chat_id,
                user_id,
                view_messages=True
            )
            await event.reply("کاربر آنبن شد.")
        except Exception as e:
            logging.warning(f"Unban error: {e}")
            await event.reply(f"خطا در آنبن:\n{e}")
        return


# -----------------------------
# Enemy Auto Reply (incoming)
# -----------------------------

@client.on(events.NewMessage(incoming=True))
async def enemy_handler(event):

    if not data["enabled"]:
        return

    user_id = event.sender_id
    chat_id = event.chat_id

    if user_id is None or chat_id is None:
        return

    if not get_enemy(chat_id, user_id):
        return

    if not data["replies"]:
        return

    response = random.choice(data["replies"])

    try:
        await event.reply(response)
    except Exception as e:
        logging.warning(f"Reply error: {e}")


# -----------------------------
# Auto Reply Loop (رگباری دیوانه‌وار بدون دیلی)
# -----------------------------

# تنظیمات رگبار - حالت دیوانه‌وار
BURST_COUNT = 100         # تعداد ریپلای در هر رگبار
BURST_DELAY = 0           # بدون هیچ دیلی
ROUND_DELAY = 0           # بدون مکث بین دورها


async def auto_reply_loop():
    """
    به صورت رگباری دیوانه‌وار بدون دیلی روی آخرین پیام هر دشمن ریپلای می‌زنه.
    """
    while auto_reply_state["running"]:
        try:
            if not data["enabled"] or not data["replies"] or not data["enemies"]:
                await asyncio.sleep(0.5)
                continue

            enemies_snapshot = list(data["enemies"].values())

            for enemy in enemies_snapshot:
                if not auto_reply_state["running"]:
                    break

                chat_id = enemy["chat_id"]
                user_id = enemy["user_id"]

                last_enemy_msg = None

                try:
                    async for msg in client.iter_messages(chat_id, limit=10):
                        if msg.sender_id == user_id:
                            last_enemy_msg = msg
                            break
                except Exception as e:
                    logging.warning(
                        f"iter_messages error {chat_id}:{user_id} -> {e}"
                    )
                    continue

                if last_enemy_msg is None:
                    continue

                # ---- رگبار دیوانه‌وار بدون دیلی ----
                for _ in range(BURST_COUNT):
                    if not auto_reply_state["running"]:
                        break

                    response = random.choice(data["replies"])

                    try:
                        await client.send_message(
                            chat_id,
                            response,
                            reply_to=last_enemy_msg.id
                        )
                    except TypeError:
                        try:
                            await last_enemy_msg.reply(response)
                        except Exception as e:
                            logging.warning(
                                f"Auto reply error {chat_id}:{user_id} -> {e}"
                            )
                    except Exception as e:
                        err = str(e).lower()
                        if "flood" in err or "wait" in err:
                            logging.warning(
                                f"Flood detected, sleeping 60s: {e}"
                            )
                            await asyncio.sleep(60)
                        else:
                            logging.warning(
                                f"Auto reply error {chat_id}:{user_id} -> {e}"
                            )

                    if BURST_DELAY > 0:
                        await asyncio.sleep(BURST_DELAY)

            if ROUND_DELAY > 0:
                await asyncio.sleep(ROUND_DELAY)

        except asyncio.CancelledError:
            break
        except Exception as e:
            logging.warning(f"Auto reply loop error: {e}")
            await asyncio.sleep(0.5)


# -----------------------------
# Panel
# -----------------------------

PANEL = """
پنل سلف‌بات

دستورات:

افزودن پاسخ
مثال:
افزودن پاسخ سلام

حذف پاسخ
مثال:
حذف پاسخ 2

لیست پاسخ‌ها

لیست دشمنان

حذف لیست دشمنان

روشن
(شروع پاسخ خودکار + ریپ رگباری دیوانه‌وار روی آخرین پیام دشمن)

خاموش

شمارش
مثال:
شمارش 0 تا 10

خشاب
خشاب خاموش

اسپم
مثال:
اسپم سلام
اسپم سلام 20
اسپم خاموش

پاکسازی
پاکسازی پیام های گپ

پاکسازی 700
پاکسازی ۷۰۰ پیام

پاکسازی خاموش
توقف پاکسازی

پین
پین یک پیام

حذف
حذف یک پیام

بن
حذف یک شخص از گفتگو

آنبن
حذف شخص از لیست حذف شده ها

راهنما


splus.ir/hlrud
t.me/hlrud
"""


@client.on(events.NewMessage(outgoing=True))
async def panel(event):

    text = (event.raw_text or "").strip()

    # -------------------------
    # پنل
    # -------------------------

    if text == "پنل" or text == "راهنما":

        await event.reply(PANEL)
        return

    # -------------------------
    # روشن
    # -------------------------

    if text == "روشن":

        data["enabled"] = True
        save_data()

        if not data["replies"]:
            await event.reply(
                "سیستم روشن شد ولی لیست پاسخ‌ها خالیه.\n"
                "اول با «افزودن پاسخ سلام» پاسخ اضافه کن."
            )
            return

        if not data["enemies"]:
            await event.reply(
                "سیستم روشن شد ولی لیست دشمنان خالیه.\n"
                "اول روی پیام شخص ریپلای کن و بنویس «دشمن»."
            )
            return

        if not auto_reply_state["running"]:
            auto_reply_state["running"] = True
            task = asyncio.create_task(auto_reply_loop())
            auto_reply_state["task"] = task

            await event.reply(
                "سیستم روشن شد.\n"
            )
            return

        await event.reply("سیستم پاسخ خودکار روشن شد.")
        return

    # -------------------------
    # خاموش
    # -------------------------

    if text == "خاموش":

        data["enabled"] = False
        save_data()

        if auto_reply_state["running"]:
            auto_reply_state["running"] = False
            task = auto_reply_state.get("task")
            if task and not task.done():
                task.cancel()
            auto_reply_state["task"] = None

        await event.reply("سیستم پاسخ خودکار و ریپ رگباری خاموش شد.")
        return

    # -------------------------
    # شمارش
    # -------------------------

    if text.startswith("شمارش "):

        parts = text[len("شمارش "):].strip().split(" تا ")

        if len(parts) != 2:
            await event.reply("مثال:\nشمارش 0 تا 10")
            return

        try:
            start = int(parts[0].strip())
            end = int(parts[1].strip())
        except ValueError:
            await event.reply("فقط عدد وارد کن.\nمثال:\nشمارش 0 تا 10")
            return

        if start > end:
            await event.reply("عدد شروع باید کوچک‌تر از عدد پایان باشد.")
            return

        if end - start > 100:
            await event.reply("حداکثر بازه شمارش 100 عدد است.")
            return

        chat_id = event.chat_id

        async def count_task():
            try:
                for i in range(start, end + 1):
                    await client.send_message(chat_id, str(i))
            except Exception as e:
                logging.warning(f"Count error: {e}")

        asyncio.create_task(count_task())
        return

    # -------------------------
    # خشاب
    # -------------------------

    if text == "خشاب":

        if not data["replies"]:
            await event.reply("لیست پاسخ‌ها خالی است. اول پاسخ اضافه کن.")
            return

        chat_id = event.chat_id

        if chat_id in magazine_state:
            old = magazine_state[chat_id]
            old["running"] = False
            old_task = old.get("task")
            if old_task and not old_task.done():
                old_task.cancel()

        state = {"running": True, "task": None}
        magazine_state[chat_id] = state

        async def magazine_task():
            try:
                while state["running"]:
                    if not data["replies"]:
                        break
                    response = random.choice(data["replies"])
                    try:
                        await client.send_message(chat_id, response)
                    except Exception as e:
                        logging.warning(f"Magazine send error: {e}")
                        break
            except asyncio.CancelledError:
                pass
            finally:
                state["running"] = False

        task = asyncio.create_task(magazine_task())
        state["task"] = task

        await event.reply(
            "خشاب فعال شد.\n"
            "پاسخ‌ها بدون ریپلای ارسال می‌شن.\n"
            "برای توقف: خشاب خاموش"
        )
        return

    if text == "خشاب خاموش":

        chat_id = event.chat_id

        if chat_id in magazine_state:
            state = magazine_state[chat_id]
            state["running"] = False

            task = state.get("task")
            if task and not task.done():
                task.cancel()

            del magazine_state[chat_id]

        await event.reply("خشاب خاموش شد.")
        return

    # -------------------------
    # اسپم خاموش
    # -------------------------

    if text == "اسپم خاموش":

        chat_id = event.chat_id

        if chat_id in spam_state:
            state = spam_state[chat_id]
            state["running"] = False

            task = state.get("task")
            if task and not task.done():
                task.cancel()

            del spam_state[chat_id]

        await event.reply("اسپم خاموش شد.")
        return

    # -------------------------
    # اسپم
    # -------------------------

    if text.startswith("اسپم "):

        content = text[len("اسپم "):].strip()

        if not content:
            await event.reply("مثال:\nاسپم سلام\nاسپم سلام 20")
            return

        count = None
        message_text = content

        parts = content.rsplit(" ", 1)

        if len(parts) == 2 and parts[1].isdigit():
            count = int(parts[1])
            message_text = parts[0].strip()

        if not message_text:
            await event.reply("متن اسپم خالی است.")
            return

        chat_id = event.chat_id

        if chat_id in spam_state:
            old = spam_state[chat_id]
            old["running"] = False
            old_task = old.get("task")
            if old_task and not old_task.done():
                old_task.cancel()

        state = {"running": True, "task": None}
        spam_state[chat_id] = state

        async def spam_task():
            try:
                if count is not None:
                    for _ in range(count):
                        if not state["running"]:
                            break
                        await client.send_message(chat_id, message_text)
                else:
                    while state["running"]:
                        await client.send_message(chat_id, message_text)
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logging.warning(f"Spam error: {e}")
            finally:
                state["running"] = False

        task = asyncio.create_task(spam_task())
        state["task"] = task

        if count is not None:
            await event.reply(f"اسپم شروع شد ({count} بار):\n{message_text}")
        else:
            await event.reply(
                f"اسپم نامحدود شروع شد:\n{message_text}\n\n"
                "برای توقف: اسپم خاموش"
            )

        return

    # -------------------------
    # پاکسازی خاموش
    # -------------------------

    if text == "پاکسازی خاموش":

        chat_id = event.chat_id

        if chat_id in purge_state:
            state = purge_state[chat_id]
            state["running"] = False

            task = state.get("task")
            if task and not task.done():
                task.cancel()

            del purge_state[chat_id]

        await event.reply("پاکسازی متوقف شد.")
        return

    # -------------------------
    # پاکسازی (عادی و عددی) - فقط پاکسازی خالی یا پاکسازی عدد
    # -------------------------

    is_purge_cmd = False
    limit = None

    if text == "پاکسازی":
        is_purge_cmd = True
    elif text.startswith("پاکسازی "):
        num_part = text[len("پاکسازی "):].strip()
        if num_part.isdigit():
            is_purge_cmd = True
            limit = int(num_part)

    if is_purge_cmd:

        if limit is not None and limit <= 0:
            await event.reply("عدد باید بزرگ‌تر از صفر باشه.")
            return

        chat_id = event.chat_id

        if chat_id in purge_state:
            old = purge_state[chat_id]
            old["running"] = False
            old_task = old.get("task")
            if old_task and not old_task.done():
                old_task.cancel()

        try:
            purge_cmd_msg_id = event.id
        except Exception:
            purge_cmd_msg_id = None

        try:
            start_msg = await event.reply("شروع پاکسازی...")
            start_msg_id = start_msg.id
        except Exception:
            start_msg_id = None

        state = {"running": True, "task": None}
        purge_state[chat_id] = state

        async def purge_task():
            total = 0
            protect_ids = set()
            stopped_by_user = False
            limit_reached = False

            if purge_cmd_msg_id is not None:
                protect_ids.add(purge_cmd_msg_id)
            if start_msg_id is not None:
                protect_ids.add(start_msg_id)

            try:
                while state["running"]:
                    if limit is not None and total >= limit:
                        limit_reached = True
                        break

                    ids = []

                    batch_limit = 100
                    if limit is not None:
                        remaining = limit - total
                        if remaining <= 0:
                            limit_reached = True
                            break
                        batch_limit = min(batch_limit, remaining)

                    async for message in client.iter_messages(
                        chat_id, limit=batch_limit
                    ):
                        if message.id in protect_ids:
                            continue
                        ids.append(message.id)

                        if limit is not None and len(ids) >= (limit - total):
                            break

                    if not ids:
                        break

                    try:
                        await client.delete_messages(
                            chat_id,
                            ids,
                            revoke=True
                        )
                        total += len(ids)

                        await asyncio.sleep(0.5)

                    except Exception as e:
                        logging.warning(f"Delete error: {e}")
                        break

            except asyncio.CancelledError:
                stopped_by_user = True
            except Exception as e:
                logging.warning(f"Purge error: {e}")

            state["running"] = False

            try:
                if stopped_by_user:
                    final = (
                        f"پاکسازی متوقف شد.\n"
                        f"تعداد پیام‌های پاک شده: {total}"
                    )
                else:
                    final = (
                        f"پاکسازی تموم شد.\n"
                        f"تعداد پیام‌های پاک شده: {total}"
                    )

                await client.send_message(chat_id, final)
            except Exception as e:
                logging.warning(f"Final msg error: {e}")

            if chat_id in purge_state:
                del purge_state[chat_id]

        task = asyncio.create_task(purge_task())
        state["task"] = task

        if limit is not None:
            await event.reply(
                f"پاکسازی شروع شد.\n"
                f"حداکثر {limit} پیام پاک می‌شه.\n"
                f"برای توقف: پاکسازی خاموش"
            )
        else:
            await event.reply(
                "پاکسازی شروع شد.\n"
                "همه پیام‌ها پاک می‌شن.\n"
                "برای توقف: پاکسازی خاموش"
            )
        return

    # -------------------------
    # افزودن پاسخ
    # -------------------------

    prefix = "افزودن پاسخ "

    if text.startswith(prefix):

        reply_text = text[len(prefix):].strip()

        if not reply_text:
            await event.reply("متن پاسخ خالی است.")
            return

        data["replies"].append(reply_text)
        save_data()

        await event.reply("پاسخ اضافه شد.")
        return

    # -------------------------
    # لیست پاسخ‌ها
    # -------------------------

    if text == "لیست پاسخ‌ها":

        if not data["replies"]:
            await event.reply("هنوز هیچ پاسخی اضافه نشده.")
            return

        result = "لیست پاسخ‌ها:\n\n"

        for i, reply in enumerate(data["replies"], 1):
            result += f"{i}. {reply}\n"

        await event.reply(result)
        return

    # -------------------------
    # حذف پاسخ
    # -------------------------

    prefix = "حذف پاسخ "

    if text.startswith(prefix):

        number = text[len(prefix):].strip()

        try:
            index = int(number) - 1
        except ValueError:
            await event.reply("مثال:\nحذف پاسخ 2")
            return

        if index < 0 or index >= len(data["replies"]):
            await event.reply("چنین شماره‌ای وجود ندارد.")
            return

        removed = data["replies"].pop(index)
        save_data()

        await event.reply(f"پاسخ حذف شد:\n{removed}")
        return

    # -------------------------
    # حذف لیست دشمنان
    # -------------------------

    if text == "حذف لیست دشمنان":

        if not data["enemies"]:
            await event.reply("لیست دشمنان از قبل خالی است.")
            return

        count = len(data["enemies"])
        data["enemies"] = {}
        save_data()

        await event.reply(f"{count} دشمن از لیست حذف شد.")
        return

    # -------------------------
    # لیست دشمنان
    # -------------------------

    if text == "لیست دشمنان":

        if not data["enemies"]:
            await event.reply("لیست دشمنان خالی است.")
            return

        result = "دشمنان:\n\n"

        for key, enemy in data["enemies"].items():
            result += (
                f"چت: {enemy['chat_id']} | "
                f"کاربر: {enemy['user_id']}\n"
            )

        await event.reply(result)
        return


# -----------------------------
# Start
# -----------------------------

print("================================")
print(" Soroush Self Bot")
print("================================")
print("Session:", SESSION_FILE)
print("Data:", DATA_FILE)
print("================================")
print("splus.ir/hlrud • @hlrud")
print("t.me/hlrud • @hlrud")
print("================================")

client.start()
print("Bot is running...")
client.run_until_disconnected()