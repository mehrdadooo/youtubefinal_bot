import os
import asyncio
import aiohttp
import shutil
import uuid
from pathlib import Path
from pyrogram import Client

# ─── تنظیمات اختصاصی شما ───
API_ID = 39884025
API_HASH = "24ce21160fcabd7e7c0de00a77b45ef3"
BOT_TOKEN = "8813125038:AAFZinXNwq9rdNq4B8LaRzQjMFIvj3ZZNvs"

# آدرس ربات هگینگ‌فیس شما 
HF_URL = "https://downloads89oouu-downloader.hf.space" 

# رمز امنیتی بین کارگر و هگینگ‌فیس
WORKER_SECRET = "ali_vip_worker_2026"

# کلاینت تلگرام (فقط یک بار استارت می‌شود)
app = Client("vip_worker", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)

async def download_video(url, job_dir):
    """عملیات دانلود با yt-dlp در یک ترد مجزا که حلقه اصلی را قفل نکند"""
    import yt_dlp
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': f'{job_dir}/%(id)s.%(ext)s',
        'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
        'quiet': True
    }
    def _run():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return info.get('title', 'Unknown Title')
            
    return await asyncio.to_thread(_run)

async def main():
    print("🚀 Starting Persistent Telegram Client...")
    await app.start()
    print("✅ VIP Worker Ready! Polling Hugging Face for jobs...\n")

    # باز کردن یک نشست (Session) دائمی اینترنتی برای مصرف کمتر منابع
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                # پرسش از هگینگ فیس (الگوی PULL)
                headers = {"Authorization": f"Bearer {WORKER_SECRET}"}
                async with session.get(f"{HF_URL}/poll", headers=headers) as resp:
                    
                    if resp.status == 200:
                        data = await resp.json()
                        
                        # اگر کاری نبود، 2 ثانیه می‌خوابد و دوباره می‌پرسد
                        if data.get("status") == "no_job":
                            await asyncio.sleep(2)
                            continue

                        # 🚨 کار دریافت شد!
                        url = data["url"]
                        chat_id = data["chat_id"]
                        message_id = data["message_id"]
                        status_msg_id = data["status_msg_id"]

                        job_id = str(uuid.uuid4())[:8]
                        job_dir = Path(f"jobs/{job_id}")
                        job_dir.mkdir(parents=True, exist_ok=True)

                        print(f"[{job_id}] 📥 Job Acquired! Downloading: {url}")

                        try:
                            # ۱. دانلود
                            title = await download_video(url, job_dir)
                            
                            # پیدا کردن فایل دانلود شده
                            matches = list(job_dir.glob("*.*"))
                            if not matches:
                                raise FileNotFoundError("Video not found!")
                            file_path = str(matches[0])

                            # ۲. آپلود
                            print(f"[{job_id}] 🚀 Uploading to Telegram...")
                            await app.send_video(
                                chat_id=chat_id,
                                video=file_path,
                                caption=f"🎬 **{title}**\n\n⚡ دانلود سریع توسط **Codespace (VIP)**",
                                reply_to_message_id=message_id,
                                supports_streaming=True
                            )
                            
                            # ۳. پاک کردن پیام "در حال انتظار" کاربر
                            try:
                                await app.delete_messages(chat_id, status_msg_id)
                            except Exception:
                                pass
                                
                            print(f"[{job_id}] 🎉 Job Completed!")

                        except Exception as e:
                            print(f"[{job_id}] ❌ Error during processing: {e}")
                            
                        finally:
                            # در هر شرایطی (موفقیت یا شکست) پوشه موقت را پاک کن
                            shutil.rmtree(job_dir, ignore_errors=True)
                            print(f"[{job_id}] 🧹 Cleanup done. Ready for next job.\n")

                    else:
                        # اگر HF ارور 500 داد یا آماده نبود
                        await asyncio.sleep(5)
                        
            except Exception as e:
                # اگر کلاً اینترنت قطع شد یا HF در دسترس نبود
                await asyncio.sleep(5)

if __name__ == "__main__":
    # اجرای حلقه بی‌نهایت
    asyncio.run(main())
