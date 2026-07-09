import sys
import os
import asyncio
import time
import random
from pathlib import Path
from pyrogram import Client
from pyrogram.errors import FloodWait, AuthKeyDuplicated, AuthKeyInvalid
import redis.asyncio as redis

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
REDIS_URL = os.environ.get("REDIS_URL")

# دریافت 5 سشن از سکرت‌های گیت‌هاب
BOT_SESSIONS = os.environ.get("BOT_SESSIONS", "").split(",")

redis_client = redis.from_url(REDIS_URL, decode_responses=True)

async def acquire_semaphore(limit=3):
    print(f"🚦 Concurrency Control: Checking upload slots (Max {limit})...")
    while True:
        await redis_client.zremrangebyscore("upload_semaphore", "-inf", time.time() - 420)
        current_uploads = await redis_client.zcard("upload_semaphore")
        if current_uploads < limit:
            worker_id = os.urandom(8).hex()
            await redis_client.zadd("upload_semaphore", {worker_id: time.time()})
            print("🟢 Slot acquired! Ready to start upload.")
            return worker_id
        await asyncio.sleep(random.uniform(2.0, 5.0))

async def release_semaphore(worker_id):
    await redis_client.zrem("upload_semaphore", worker_id)
    print("🔴 Slot released successfully.")

async def main():
    chat_id = int(sys.argv[1])
    message_id = int(sys.argv[2])
    status_msg_id = int(sys.argv[3])
    title = sys.argv[4]

    matches = sorted(Path(".").glob("video.*"))
    if not matches:
        raise FileNotFoundError("❌ هیچ فایل ویدیویی پیدا نشد!")
    file_path = str(matches[0])

    worker_id = await acquire_semaphore(limit=3)

    try:
        # سیستم انتخاب سشن رندوم و تلاش مجدد در صورت تداخل
        upload_success = False
        for attempt in range(3):
            # انتخاب یکی از 5 سشن به صورت رندوم
            session_str = random.choice(BOT_SESSIONS)
            app = Client("uploader_bot", api_id=API_ID, api_hash=API_HASH, session_string=session_str, in_memory=True)
            
            try:
                async with app:
                    print(f"🚀 Attempt {attempt+1}: Uploading to Telegram...")
                    await asyncio.wait_for(
                        app.send_video(
                            chat_id=chat_id,
                            video=file_path,
                            caption=f"🎬 **{title}**\n\n⚡ دانلود موفق ****",
                            reply_to_message_id=message_id,
                            supports_streaming=True
                        ),
                        timeout=360
                    )
                    try:
                        await app.delete_messages(chat_id, status_msg_id)
                    except:
                        pass
                    print("🎉 Job finished successfully!")
                    upload_success = True
                    break # خروج از حلقه در صورت موفقیت
                    
            except (AuthKeyDuplicated, AuthKeyInvalid):
                print("⚠️ Session collision detected. Retrying with another session...")
                continue # سشن تکراری بود؟ برو بعدی!
            except FloodWait as e:
                print(f"🛑 Telegram Rate Limit: Must wait {e.value} seconds.")
                await asyncio.sleep(e.value + 2) # اینجا به جای کرش کردن، صبر می‌کند
                
        if not upload_success:
            print("❌ Upload failed after all retries.")

    except asyncio.TimeoutError:
         print("❌ Error: Upload execution exceeded 6 minutes (Timeout).")
    except Exception as e:
         print(f"❌ Upload failed: {e}")
    finally:
        await release_semaphore(worker_id)
        await redis_client.aclose()

if __name__ == "__main__":
    asyncio.run(main())
