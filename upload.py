import sys
import os
import asyncio
import time
import random
from pathlib import Path
from pyrogram import Client
from pyrogram.errors import FloodWait
import redis.asyncio as redis

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
REDIS_URL = os.environ.get("REDIS_URL")

# ساخت نمونه کلاینت ردیس
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

async def acquire_semaphore(limit=3):
    """
    سیستم مدیریت ترافیک: نهایتاً ۳ کانتینر همزمان اجازه آپلود دارند.
    این تابع تضمین می‌کند که تلگرام پکت‌های شبکه را دراپ نکند.
    """
    print(f"🚦 Concurrency Control: Checking upload slots (Max {limit} concurrent)...")
    while True:
        # پاک کردن رکوردهای قدیمی یا سوخته (اگر اکشن‌های قبلی بدون باز کردن قفل کرش کردند)
        # هر ورکر بعد از ۴۲۰ ثانیه (۷ دقیقه) خود به خود منقضی می‌شود
        await redis_client.zremrangebyscore("upload_semaphore", "-inf", time.time() - 420)
        
        current_uploads = await redis_client.zcard("upload_semaphore")
        if current_uploads < limit:
            worker_id = os.urandom(8).hex()
            # ثبت شناسه ورکر در پایگاه داده ردیس
            await redis_client.zadd("upload_semaphore", {worker_id: time.time()})
            print("🟢 Slot acquired! Ready to start upload.")
            return worker_id
        
        # اگر خط شلوغ بود، ۲ تا ۵ ثانیه صبر کرده و مجدد بررسی می‌کند
        sleep_time = random.uniform(2.0, 5.0)
        await asyncio.sleep(sleep_time)

async def release_semaphore(worker_id):
    """آزاد کردن اسلات برای ورکرهای بعدی در صف"""
    await redis_client.zrem("upload_semaphore", worker_id)
    print("🔴 Slot released successfully.")

async def main():
    chat_id = int(sys.argv[1])
    message_id = int(sys.argv[2])
    status_msg_id = int(sys.argv[3])
    title = sys.argv[4]

    # پیدا کردن فایل ویدیو
    matches = sorted(Path(".").glob("video.*"))
    if not matches:
        raise FileNotFoundError("❌ هیچ فایل ویدیویی پیدا نشد!")
    
    file_path = str(matches[0])

    # 🚦 دریافت اجازه آپلود از ردیس قبل از اتصال به تلگرام
    worker_id = await acquire_semaphore(limit=3)

    try:
        app = Client(
            "uploader_bot", 
            api_id=API_ID, 
            api_hash=API_HASH, 
            bot_token=BOT_TOKEN, 
            in_memory=True
        )

        async with app:
            print("🚀 Uploading to Telegram...")
            # استفاده از wait_for برای جلوگیری از فریز شدن ابدی فرآیند آپلود
            # از آنجا که محدودیت کل اکشن 7 دقیقه است، تایم‌اوت را روی 6 دقیقه (360 ثانیه) می‌گذاریم
            await asyncio.wait_for(
                app.send_video(
                    chat_id=chat_id,
                    video=file_path,
                    caption=f"🎬 **{title}**\n\n⚡ دانلود شده با موفقیت!",
                    reply_to_message_id=message_id,
                    supports_streaming=True
                ),
                timeout=360
            )
            
            # پاک کردن پیام انتظار لایه هگینگ‌فیس
            try:
                await app.delete_messages(chat_id, status_msg_id)
            except Exception:
                pass
            print("🎉 Job finished successfully!")

    except asyncio.TimeoutError:
         print("❌ Error: Upload execution exceeded 6 minutes (Timeout).")
    except FloodWait as e:
         print(f"🛑 Telegram Rate Limit: Must wait {e.value} seconds.")
    except Exception as e:
         print(f"❌ Upload failed: {e}")
    finally:
        # 🟢 مهم نیست کارگر با موفقیت کارش تمام شد یا کرش کرد، در هر صورت قفل باید باز شود
        await release_semaphore(worker_id)
        await redis_client.aclose()

if __name__ == "__main__":
    asyncio.run(main())
