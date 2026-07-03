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

async def download_video(url, job_dir):
    """عملیات دانلود با جا زدن به عنوان آیفون و تلویزیون (ایده عالی شما)"""
    import yt_dlp
    
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': f'{job_dir}/%(id)s.%(ext)s',
        'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
        'impersonate': 'chrome', 
        # 🚨 این همان تکنیک طلایی شماست: جا زدن به عنوان آیفون و تلویزیون 🚨
        'extractor_args': {'youtube': {'player_client': ['ios,tv']}}, 
        'quiet': True,
        'no_warnings': True
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
                            title = await download_video(url, job_dir)
                            
                            matches = list(job_dir.glob("*.*"))
                            if not matches:
                                raise FileNotFoundError("Video not found!")
                            file_path = str(matches[0])

                            print(f"[{job_id}] 🚀 Uploading to Telegram...")
                            await app.send_video(
                                chat_id=chat_id,
                                video=file_path,
                                caption=f"🎬 **{title}**\n\n⚡ دانلود سریع توسط **Codespace (VIP)**",
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
