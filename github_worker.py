import os
import sys
import asyncio
import aiohttp
import random
import json
import uuid  # 👈 این کلمه فراموش شده بود!
import urllib.parse
from pathlib import Path
from pyrogram import Client
from pyrogram.errors import FloodWait, AuthKeyDuplicated, AuthKeyInvalid

def print_log(msg):
    print(msg, flush=True)
    sys.stdout.flush()

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]

bot_sessions_env = os.getenv("BOT_SESSIONS")
if bot_sessions_env:
    try: BOT_SESSIONS = json.loads(bot_sessions_env)
    except: BOT_SESSIONS = [s.strip() for s in bot_sessions_env.split(",") if s.strip()]
else:
    BOT_SESSIONS = [
        "BAJglPkAO0RCs_NW3uELJV95CRa17odKleHTrosLpwhRpmfX3N1K7SqQobP1kJvc6czR6E1z5j9TChl_X5_hHlAtx5RZH-xdFiOfJ_CrTMrTRKY2wzpe9dC2E9CitkBqwgZQDyHbiLZC-mrJPoXgDZ2tGeNwMMbWd3kHal3me4N8HloJcvwbR93nopWSZaO1VE9OGol8iczRSPovbqMcexgkquu7yb8EO2U6aeHZOqiExD8Vdibnj8W4QUQLA60bdhNhZGSC4EmdKXKCq32DfZHFtNNxC3RMmh3h1xJdS6Jf4W9IJaR32E5mS8pM-COP9N9pCoLWlw-2XjQiSu5KM9AQjGcs5wAAAAINTZ2uAQ",
        "BAJglPkAEIHq7qQmQFqUMINW5U6OolhKB8sxXd5mn0pLpwl6mB5fRnvM8UFmd2wf-7N0oDZ0-Rms2QlSr9JMkRoXAAGxKTp0tj0kK_mUobjFlOtS8hctWZgSwNjcsEDXprLU4f7CMQLvRskRzpPkShd1TxsEuzjtjg2sq9_Ed1hBQan1-BFBdAJ2wVNGSfg6zOAUBgV1XUU1_SAl7LywJJQUmSeQEB8dBX_-tmUqJVzpJI6iorwqPxYu8n5k2bPnXdtRB-vbZf-Oi2Cv-1wl-cvG_0vTVPcVUnTiIJjigDpXRz_Eu0lmVIiRhSNtxJvtSj_4u1z-Ze9qnQOCfTNQ3dRQQHYO1wAAAAINTZ2uAQ",
        "BAJglPkAq5Ab9cqjvp2qvWWxpgmw7wOq2W6wlOC6EUCD9QOu5mAtsAyr7CaY9eOTUCpjB1yuYvE9UyQy6EpZdh-AupsQ6wwQPGjxe6b6wkv7gVm8z0vdO5f54I_dh8erfAY1Lz-186zlCumDcV63EZwm2MO27qKdzbjOocILR4SKECgrvxk1bEqfLHlp5D8nFyTBZeAko4iPWhh8O6d9WMdLQDodXMG-dJCNwQzqE6Vyui1BRNxFIXKoz1XGnZ6iPPuf3eKJH-ayZ3FHJJUei0kYO4MKl_gy3Uv1WFzvTEuvTZtbjyKFKMSp4YH39_OdTdUwXbHca-lQhGwukSztM10quL9_xAAAAAINTZ2uAQ",
        "BAJglPkAag83pxlJ7YpaNRtvcskvrUSiHrWl0HfkNboMFQuljSaFf6rieC84VjbF5aq9Pxrqrplls6jlfm7f4HC9D7JWa7bKqH9WjSplofQTsSbRYmkvQbUk2lmC7obeze9Unblo0VFc9kXXYG5No0hojvU4DCWTH3ZsY8uveLe8hVTSvlHCQiPcU0cJfnTZT9E2yK__EnlPojvEyavyi1h0pFzGWAybMlegSoHnLcX9VGU08qiRgkKOYdF3i5CV3heSijJiFlwI35wu-XYnqKm60zK2lMTJr2lfid6ssTcdy90brCa9C1BzAcnSGPQMy-GaoZo0ESsHEgGR4R7Z9smYtDFSTgAAAAINTZ2uAQ",
        "BAJglPkAnFvYFhSl3hlS4GIGt1SE-9C07UeeF0iteez4skX9hDjV3v_MpG7XN50rodIXGUghdjN_s_ePRYiY2_0d7cOROP1EvEhbcNp1c7FaJzYzRNbC4ejWuqdVF88yRh7Y1_1frOzsrEKlFF8UWq2bl6jeOPcTyl0OZGkosKhuXXIVbnM9h_-X96MLqvRCPlvW9IrBjby-HXHlE_RFAw-68JViTuVNZz6zEFsDWV0M-D5-L8nRfedqEFP0Y1pg_7JZQnCggHKYUJ7lvhCa9-XCo1PJQZjbj9ukDM53B7WoZgpfKGjtnuRfp0kHEuZYrZGtXUHs_N7wmLdrZfeolKQ6RNa1nAAAAAINTZ2uAQ"
    ]

COOKIE_FILE_PATH = Path("cookies.txt")

async def download_video_via_ytdlp(url, job_dir, quality="max"):
    is_youtube = "youtube.com" in url.lower() or "youtu.be" in url.lower()
    absolute_job_dir = str(job_dir.resolve()) 
    
    if is_youtube:
        if quality == "1080": format_str = "bv*[height>=1080]+ba" 
        elif quality == "720": format_str = "bv*[height>=720]+ba"
        elif quality == "480": format_str = "bv*[height>=480]+ba"
        elif quality == "audio": format_str = "ba/b"
        else: format_str = "bv*+ba/b"
    else:
        format_str = "b"
        if quality == "1080": format_str = "best[height<=1080]/best"
        elif quality == "720": format_str = "best[height<=720]/best"
        elif quality == "480": format_str = "best[height<=480]/best"
        elif quality == "audio": format_str = "ba/b"
    
    cmd = [
        "yt-dlp", "--rm-cache-dir", "-f", format_str, 
        "--write-info-json", "--write-thumbnail", "--convert-thumbnails", "jpg",
        "--no-check-certificate", "--retries", "10", "--fragment-retries", "infinite",
        "-o", f"{absolute_job_dir}/video.%(ext)s"
    ]
    
    if quality == "audio":
        cmd.extend(["--extract-audio", "--audio-format", "mp3"])
    else:
        cmd.extend(["--merge-output-format", "mp4", "--postprocessor-args", "ffmpeg:-movflags +faststart"])

    print_log("🥷 Trying Ninja Mode (Direct Connection + iOS Client)...")
    ninja_cmd = list(cmd)
    if is_youtube:
        ninja_cmd.extend(["--extractor-args", "youtube:player_client=ios,android", "--remote-components", "ejs:github", "--impersonate", "chrome"])
    ninja_cmd.append(url)
    
    process = await asyncio.create_subprocess_exec(*ninja_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    
    if process.returncode == 0:
        print_log("✅ Ninja Mode Success!")
        return True
        
    print_log(f"⚠️ Ninja Mode failed. Initiating Tank Mode fallback...")

    print_log("🛡️ Trying Tank Mode (VLESS Proxy + Cookies + WEB_CREATOR Client)...")
    
    tank_cmd = list(cmd)
    if os.getenv("VLESS_LINK"):
        tank_cmd.extend(["--proxy", "socks5h://127.0.0.1:10808"])
    if COOKIE_FILE_PATH.exists():
        tank_cmd.extend(["--cookies", str(COOKIE_FILE_PATH.resolve())])
        
    if is_youtube:
        tank_cmd.extend([
            "--extractor-args", "youtube:player_client=web_creator,tv_downgraded,android_vr;player_skip=webpage", 
            "--remote-components", "ejs:github", 
            "--impersonate", "chrome", 
            "--force-ipv4"
        ])
    tank_cmd.append(url)
    
    process = await asyncio.create_subprocess_exec(*tank_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    
    if process.returncode == 0:
        print_log("✅ Tank Mode Success!")
        return True
        
    error_msg = stderr.decode('utf-8', errors='ignore').strip()
    raise Exception(f"yt-dlp failed completely. Last error: {error_msg}")

async def download_via_cobalt(url, job_dir, quality="max"):
    print_log(f"🌟 Starting Cobalt API fallback for: {url} | Quality: {quality}")
    api_urls = ["https://api.cobalt.tools/api/json", "https://co.wuk.sh/api/json", "https://cobalt.q0.pm/api/json"]
    headers = {
        "Accept": "application/json", "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }
    
    payload = {"url": url, "vQuality": quality if quality != "audio" else "max"}
    if quality == "audio": payload["isAudioOnly"] = True

    async with aiohttp.ClientSession() as session:
        video_url = None
        for api in api_urls:
            try:
                async with session.post(api, headers=headers, json=payload, timeout=15) as resp:
                    if resp.status in [200, 202]:
                        data = await resp.json()
                        if data.get("status") in ["redirect", "stream", "success", "picker"]:
                            video_url = data.get("url")
                            if video_url: break
            except: continue

        if not video_url: raise Exception("❌ All Cobalt APIs failed.")

        ext = "mp3" if quality == "audio" else "mp4"
        file_path = f"{job_dir.resolve()}/video.{ext}"
        print_log(f"📥 Downloading raw media from Cobalt to: {file_path}")
        async with session.get(video_url) as video_resp:
            if video_resp.status != 200: raise Exception("Download from Cobalt stream failed.")
            with open(file_path, 'wb') as f:
                while True:
                    chunk = await video_resp.content.read(2 * 1024 * 1024)
                    if not chunk: break
                    f.write(chunk)
        print_log("✅ Successfully downloaded via Cobalt!")
        return True

async def main():
    url = sys.argv[1]
    chat_id = int(sys.argv[2])
    message_id = int(sys.argv[3])
    status_msg_id = int(sys.argv[4])
    quality = sys.argv[5]

    job_dir = Path(".")
    
    print_log(f"📥 GITHUB Job Started: {url} | Quality: {quality}")

    try:
        download_success = False
        try:
            await download_video_via_ytdlp(url, job_dir, quality)
            download_success = True
        except Exception as e:
            print_log(f"⚠️ yt-dlp failed: {e}")
        
        if not download_success:
            print_log("🔄 Falling back to Cobalt API for heavy extraction...")
            try:
                await download_via_cobalt(url, job_dir, quality)
                download_success = True
            except Exception as cobalt_err:
                print_log(f"❌ Cobalt API also failed: {cobalt_err}")
                raise Exception("All download methods (yt-dlp & Cobalt) failed.")

        matches = list(job_dir.glob("video.mp4")) or list(job_dir.glob("video.mp3")) or [m for m in job_dir.glob("video.*") if m.suffix.lower() not in ['.jpg', '.json']]
        if not matches or not download_success: raise FileNotFoundError("Video/Audio file not found on disk!")
        file_path = str(matches[0].resolve())

        thumb_path = None
        thumb_matches = list(job_dir.glob("*.jpg"))
        if thumb_matches: thumb_path = str(thumb_matches[0].resolve())

        width, height, duration, title = 0, 0, 0, "Video"
        info_matches = list(job_dir.glob("*.info.json"))
        if info_matches:
            try:
                with open(info_matches[0], 'r', encoding='utf-8') as f:
                    info = json.load(f)
                    width, height, duration, title = info.get('width', 0), info.get('height', 0), info.get('duration', 0), info.get('title', 'Video')
            except: pass

        is_audio = quality == "audio"
        quality_text = "صدا (MP3)" if is_audio else f"{quality}p" if quality != "max" else "بهترین کیفیت"
        upload_kwargs = {
            "chat_id": chat_id, 
            "caption": f"🎬 **{title}**\n\n⚙️ کیفیت: `{quality_text}`\n🔥 دریافت سریع از ارتش گیت‌هاب", 
            "reply_to_message_id": message_id
        }
        
        if is_audio:
            upload_kwargs["audio"] = file_path
            if thumb_path: upload_kwargs["thumb"] = thumb_path
            if duration: upload_kwargs["duration"] = int(duration)
        else:
            upload_kwargs["video"] = file_path
            upload_kwargs["supports_streaming"] = True
            if thumb_path: upload_kwargs["thumb"] = thumb_path
            if width: upload_kwargs["width"] = width
            if height: upload_kwargs["height"] = height
            if duration: upload_kwargs["duration"] = int(duration)

        upload_success = False
        for attempt in range(3):
            chosen_session = random.choice(BOT_SESSIONS)
            upload_app = Client(f"gh_{uuid.uuid4().hex[:8]}", api_id=API_ID, api_hash=API_HASH, session_string=chosen_session, in_memory=True)
            try:
                async with upload_app:
                    print_log(f"🚀 Attempt {attempt+1}: Uploading to Telegram...")
                    if is_audio: await upload_app.send_audio(**upload_kwargs)
                    else: await upload_app.send_video(**upload_kwargs)
                    try: await upload_app.delete_messages(chat_id, status_msg_id)
                    except: pass
                print_log("🎉 Job Completed!")
                upload_success = True
                break
            except (AuthKeyDuplicated, AuthKeyInvalid): continue
            except FloodWait as e: await asyncio.sleep(e.value + 2)
                
        if not upload_success: print_log("❌ Upload failed after all retries.")

    except Exception as e: 
        print_log(f"❌ Error during processing: {e}")
        try:
            err_app = Client("err_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)
            async with err_app:
                await err_app.edit_message_text(chat_id, status_msg_id, f"❌ متاسفانه دانلود با خطا مواجه شد:\n`{e}`")
        except: pass

if __name__ == "__main__":
    asyncio.run(main())
