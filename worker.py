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
HF_URL = "https://downloads89oouu-downloader.hf.space" 
WORKER_SECRET = "ali_vip_worker_2026"

app = Client("vip_worker", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)

# پیدا کردن مسیر دقیق فایل کوکی در پوشه فعلی
COOKIE_FILE_PATH = Path(__file__).parent / "cookies.txt"

async def download_video(url, job_dir):
    """اجرای مستقیم خط فرمان yt-dlp دقیقاً مشابه گیت‌هاب اکشنز شما"""
    
    # بررسی وجود فایل کوکی
    if not COOKIE_FILE_PATH.exists():
        raise FileNotFoundError("⚠️ فایل cookies.txt پیدا نشد! لطفاً مطمئن شوید فایل کوکی را در پوشه اصلی ساخته‌اید.")

    # دستور دقیق خط فرمان گیت‌هاب شما
    cmd = [
        "yt-dlp",
        "-f", "best[ext=mp4]/best",
        "--cookies", str(COOKIE_FILE_PATH.resolve()),
        "--impersonate", "chrome",
        "--extractor-args", "youtube:player_client=web",
        "--no-check-certificate",
        "--retries", "5",
        "-o", f"{job_dir}/video.%(ext)s",
        url
    ]
    
    print(f"🎬 Running Command: {' '.join(cmd)}")
    
    # اجرای آسنکرون خط فرمان
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        error_msg = stderr.decode().strip()
        raise Exception(f"yt-dlp terminal failed: {error_msg}")
        
    return "Video Downloaded Successfully"

async def main():
    print("\n" + "="*50)
    print("🔍 DIAGNOSTIC SYSTEM STARTING:")
    print(f"📁 Looking for cookies at: {COOKIE_FILE_PATH.resolve()}")
    if COOKIE_FILE_PATH.exists():
        print("✅ SUCCESS: cookies.txt FOUND and will be loaded!")
    else:
        print("⚠️ WARNING: cookies.txt was NOT found next to worker.py!")
        print("   Please create cookies.txt in the same folder as worker.py")
    print("="*50 + "\n")

    print("🚀 Starting Persistent Telegram Client...")
    await app.start()
    print("✅ VIP Worker Ready! Polling Hugging Face for jobs...\n")

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                headers = {"Authorization": f"Bearer {WORKER_SECRET}"}
                async with session.get(f"{HF_URL}/poll", headers=headers) as resp:
                    
                    if resp.status == 200:
                        data = await resp.json()
                        
                        if data.get("status") == "no_job":
                            await asyncio.sleep(2)
                            continue

                        url = data["url"]
                        chat_id = data["chat_id"]
                        message_id = data["message_id"]
                        status_msg_id = data["status_msg_id"]

                        job_id = str(uuid.uuid4())[:8]
                        job_dir = Path(f"jobs/{job_id}")
                        job_dir.mkdir(parents=True, exist_ok=True)

                        print(f"[{job_id}] 📥 Job Acquired! Downloading: {url}")

                        try:
                            # اجرای خط فرمان دانلود
                            await download_video(url, job_dir)
                            
                            # پیدا کردن فایل ویدیو دانلود شده
                            matches = list(job_dir.glob("video.*"))
                            if not matches:
                                # اگر با فرمتی غیر از mp4 ذخیره شده باشد، کل پوشه را سرچ کن
                                matches = list(job_dir.glob("*.*"))
                                
                            if not matches:
                                raise FileNotFoundError("Video file not found in job directory!")
                                
                            file_path = str(matches[0])

                            print(f"[{job_id}] 🚀 Uploading to Telegram...")
                            await app.send_video(
                                chat_id=chat_id,
                                video=file_path,
                                caption=f"🎬 دانلود سریع توسط **Codespace (VIP)**",
                                reply_to_message_id=message_id,
                                supports_streaming=True
                            )
                            
                            try:
                                await app.delete_messages(chat_id, status_msg_id)
                            except Exception:
                                pass
                                
                            print(f"[{job_id}] 🎉 Job Completed!")

                        except Exception as e:
                            print(f"[{job_id}] ❌ Error during processing: {e}")
                            
                        finally:
                            shutil.rmtree(job_dir, ignore_errors=True)
                            print(f"[{job_id}] 🧹 Cleanup done. Ready for next job.\n")

                    else:
                        await asyncio.sleep(5)
                        
            except Exception as e:
                await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
