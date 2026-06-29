import sys
import os
import asyncio
import random
from pathlib import Path
from pyrogram import Client
from pyrogram.errors import FloodWait

# دریافت متغیرهای محیطی
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]

async def main():
    # دریافت پارامترها از اکشن گیت‌هاب
    chat_id = int(sys.argv[1])
    message_id = int(sys.argv[2])
    status_msg_id = int(sys.argv[3])
    title = sys.argv[4]

    # 🔎 جستجوی خودکار فایل ویدیو با هر پسوندی در پوشه اصلی
    matches = sorted(Path(".").glob("video.*"))
    if not matches:
        raise FileNotFoundError("❌ هیچ فایل ویدیویی در پوشه اصلی پیدا نشد!")
    
    file_path = str(matches[0])

    # 🛡 سپر اول: Jitter (تأخیر تصادفی)
    # اگر 20 اکشن همزمان به این خط برسند، هر کدام بین 1 تا 8 ثانیه تاخیر متفاوت می‌گیرند
    # تا به صورت رگباری به سرور تلگرام API ریکوئست نزنند.
    delay = random.uniform(1.0, 8.0)
    print(f"⏱ Jitter active: Waiting {delay:.2f} seconds before connecting to Telegram...")
    await asyncio.sleep(delay)

    # ساخت کلاینت موقت روی گیت‌هاب (in_memory=True برای جلوگیری از ساخت فایل سشن)
    app = Client(
        "uploader_bot", 
        api_id=API_ID, 
        api_hash=API_HASH, 
        bot_token=BOT_TOKEN, 
        in_memory=True,
        sleep_threshold=60 # مدیریت خودکار توقف‌های زیر 1 دقیقه توسط پایروگرام
    )

    # 🛡 سپر دوم و سوم: مکانیزم Retry و شکار FloodWait
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"🚀 Attempt {attempt + 1}/{max_retries}: Uploading to Telegram...")
            
            # استفاده از async with به صورت خودکار app.start() و app.stop() را مدیریت می‌کند
            async with app:
                # ۱. ارسال ویدیو به عنوان ریپلای به پیام اصلی کاربر
                await app.send_video(
                    chat_id=chat_id,
                    video=file_path,
                    caption=f"🎬 **{title}**\n\n⚡ دانلود شده توسط گیت‌هاب با موفقیت و بر بستر کلودفلر WARP!",
                    reply_to_message_id=message_id,
                    supports_streaming=True
                )
                
                # ۲. پاک کردن پیام وضعیت قبلی هگینگ فیس
                try:
                    await app.delete_messages(chat_id, status_msg_id)
                    print("✅ Status message deleted.")
                except Exception as e:
                    print(f"⚠️ Could not delete status message: {e}")
            
            print("🎉 Video uploaded successfully!")
            break  # خروج از حلقه چون آپلود موفقیت‌آمیز بود

        except FloodWait as e:
            # اگر با وجود Jitter تلگرام باز هم حساس شد، اسکریپت کرش نمی‌کند!
            wait_time = e.value + 2  # 2 ثانیه برای اطمینان بیشتر
            print(f"🛑 Telegram Rate Limit (FloodWait) Hit! Sleeping for {wait_time} seconds...")
            await asyncio.sleep(wait_time)
            # بعد از بیداری، حلقه دوباره تلاش می‌کند

        except Exception as e:
            print(f"❌ Fatal Upload Error: {e}")
            break # در صورت بروز خطاهای غیر از لیمیت، حلقه شکسته می‌شود

if __name__ == "__main__":
    asyncio.run(main())
