from utils import send_message, get_main_keyboard, get_admin_keyboard, get_main_inline, get_admin_inline, validate_code_from_url, api_request
from database.db import get_user, create_user, get_stats, get_remaining, is_code_used, use_code
from config import ADMINS, FREE_SEARCHES, FREE_DOWNLOADS, FREE_SEARCH_RESULTS

PURCHASE_LINK = "https://pay.avasam.ir/link/770140"

async def handle_start(chat_id: int, username: str = None, first_name: str = None):
    create_user(chat_id, username, first_name)
    is_admin = chat_id in ADMINS
    user = get_user(chat_id)
    remaining = get_remaining(chat_id)

    if is_admin:
        caption = f"👋 خوش آمدید ادمین {first_name or 'کاربر'}!"
        inline_kb = get_admin_inline()
    else:
        has_quota = remaining['searches'] > 0 or remaining['downloads'] > 0
        caption = f"""به ربات پینترست خوش آمدید.
امکانات :
۱ - دانلود هر نوع محتوای پینترست با لینک آن
۲ - امکان جستجو در پینترست
۳ - پیدا کردن تصاویر یا ویدیوهای مرتبط
---
آموزش استفاده :‌
- ابتدا برای شروع دستور /start را ارسال کنید
- در منوی اصلی از دکمه های جستجو و دانلود استفاده کنید برای دانلود باید لینک آن پست را داشته باشید.
- بصورت رایگان فقط ۲ بار میتوانید از ربات استفاده کنید بعد از آن باید کدفعالسازی خرید کنید.
---
امکانات درصورت خرید کدفعالسازی :
۱ - نتیجه جستجوی بهتر
۲ - عدم وجود محدودیت در دانلود
۳ - انتخاب میزان جستجو بین ۵ ۱۰ ۲۰ نتیجه
۴ - پیدا کردن پست های مرتبط نامحدود
۵ - دانلود کامل حتی فایل های بزرگ
"""
        if user and user["is_premium"]:
            caption += "\n✅ شما دسترسی ویژه دارید!"
        else:
            caption += f"\n🆓 رایگان: {remaining['searches']}/{FREE_SEARCHES} جستجو ({FREE_SEARCH_RESULTS} نتیجه)، {remaining['downloads']}/{FREE_DOWNLOADS} دانلود"
            if not has_quota:
                caption += f"\n\n🛒 خرید کد فعالسازی:\n{PURCHASE_LINK}"
        inline_kb = get_main_inline(user and user["is_premium"], has_quota)

    # Send photo with inline buttons
    import json
    with open("pinterest.jpg", "rb") as f:
        content = f.read()
    await api_request("sendPhoto", {"chat_id": chat_id, "caption": caption, "reply_markup": json.dumps(inline_kb)}, {"photo": ("pinterest.jpg", content, "image/jpeg")})

async def handle_profile(chat_id: int):
    user = get_user(chat_id)
    is_admin = chat_id in ADMINS
    remaining = get_remaining(chat_id)

    if is_admin:
        status = "ادمین"
        quota_text = "نامحدود"
    elif user and user["is_premium"]:
        status = "ویژه"
        quota_text = "نامحدود"
    else:
        status = "رایگان"
        quota_text = f"{remaining['searches']} جستجو، {remaining['downloads']} دانلود"

    text = f"""👤 پروفایل
━━━━━━━━━━━━━
🆔 شناسه: {chat_id}
📊 وضعیت: {status}
📈 باقیمانده: {quota_text}
📅 عضویت: {user['created_at'][:10] if user else 'N/A'}"""

    if not is_admin and not (user and user["is_premium"]):
        text += f"\n\n🛒 خرید کد فعالسازی:\n{PURCHASE_LINK}"

    has_quota = remaining['searches'] > 0 or remaining['downloads'] > 0
    kb = get_admin_keyboard() if is_admin else get_main_keyboard(user and user["is_premium"], has_quota)
    await send_message(chat_id, text, kb)

async def handle_activate(chat_id: int, key: str):
    user = get_user(chat_id)

    if user and user["is_premium"]:
        await send_message(chat_id, "✅ شما قبلا دسترسی ویژه دارید!", get_main_keyboard(True, True))
        return

    # Check if code already used
    if is_code_used(key):
        await send_message(chat_id, "❌ این کد قبلا استفاده شده است.", get_main_keyboard(False, True))
        return

    # Validate code from remote URL
    is_valid = await validate_code_from_url(key)

    if is_valid:
        use_code(chat_id, key)
        await send_message(chat_id, "✅ دسترسی ویژه با موفقیت فعال شد!\n\n🎉 اکنون دسترسی نامحدود دارید.", get_main_keyboard(True, True))
    else:
        remaining = get_remaining(chat_id)
        has_quota = remaining['searches'] > 0 or remaining['downloads'] > 0
        await send_message(chat_id, f"❌ کد نامعتبر است.\n\n🛒 خرید کد فعالسازی:\n{PURCHASE_LINK}", get_main_keyboard(False, has_quota))

async def handle_purchase(chat_id: int):
    user = get_user(chat_id)
    if user and user["is_premium"]:
        await send_message(chat_id, "✅ شما قبلا دسترسی ویژه دارید!", get_main_keyboard(True, True))
        return
    text = f"""🛒 خرید کد فعالسازی
━━━━━━━━━━━━━
برای خرید روی لینک زیر کلیک کنید:
{PURCHASE_LINK}

پس از خرید، از دکمه 🔑 فعالسازی استفاده کنید."""
    remaining = get_remaining(chat_id)
    has_quota = remaining['searches'] > 0 or remaining['downloads'] > 0
    await send_message(chat_id, text, get_main_keyboard(False, has_quota))

async def handle_stats(chat_id: int):
    if chat_id not in ADMINS:
        await send_message(chat_id, "❌ فقط ادمین.")
        return

    stats = get_stats()
    text = f"""📊 آمار
━━━━━━━━━━━━━
👥 کل کاربران: {stats['total_users']}
⭐ کاربران ویژه: {stats['premium_users']}
🔍 کل جستجوها: {stats['searches']}
📥 کل دانلودها: {stats['downloads']}"""
    await send_message(chat_id, text, get_admin_keyboard())

