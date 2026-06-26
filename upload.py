import sys
import os
import asyncio
from pyrogram import Client

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]

async def main():
    chat_id = int(sys.argv[1])
    message_id = int(sys.argv[2])
    status_msg_id = int(sys.argv[3])
    file_path = sys.argv[4]
    title = sys.argv[5]

    # ساخت کلاینت موقت روی گیت‌هاب برای ارسال فایل به کاربر
    app = Client("uploader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)
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
        except Exception:
            pass

if __name__ == "__main__":
    asyncio.run(main())
