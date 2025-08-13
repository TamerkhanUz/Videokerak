import os
import asyncio
import yt_dlp as youtube_dl
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from concurrent.futures import ThreadPoolExecutor
import logging

# Sozlamalar
TOKEN = "8198686578:AAFDpwqt7yzTmH_KzXGZG-HBKhpDy5hOTxg"
CHANNEL = "@TamerkhanBlog"
MAX_WORKERS = 4
DOWNLOAD_TIMEOUT = 300  # 5 daqiqa

# Log konfiguratsiyasi
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global executor
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

async def download_media(url: str, chat_id: int):
    ydl_opts = {
        'cookiefile': 'cookies.txt',  # YouTube cookie fayli
        'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
        'outtmpl': f'downloads/{chat_id}/%(id)s.%(ext)s',
        'socket_timeout': 15,
        'retries': 3,
        'noprogress': True,
        'quiet': True,
        'no_cache_dir': True,
        'merge_output_format': 'mp4',
        'postprocessor_args': ['-preset', 'ultrafast'],
        'external_downloader': 'aria2c',
        'external_downloader_args': ['-x', '16', '-s', '16', '-k', '2M']
    }
    
    try:
        os.makedirs(f'downloads/{chat_id}', exist_ok=True)
        
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(executor, lambda: ydl.extract_info(url, download=True))
            filename = ydl.prepare_filename(info)
            
            file_size = os.path.getsize(filename) / (1024 * 1024)
            if file_size > 100:
                raise ValueError(f"Fayl hajmi {file_size:.1f}MB, maksimum 100MB ruxsat etilgan")
                
            return filename
            
    except Exception as e:
        logger.error(f"Yuklashda xato: {str(e)}")
        raise Exception(f"Yuklash jarayonida xato: {str(e)}")

async def stream_video(update: Update, filename: str):
    try:
        caption = "📥 @VideoKerakBot orqali yuklab olindi"
        with open(filename, 'rb') as file:
            await update.message.reply_video(
                video=file,
                caption=caption,
                supports_streaming=True
            )
    finally:
        if os.path.exists(filename):
            os.remove(filename)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not any(x in url for x in ["youtube.com", "youtu.be", "tiktok.com", "instagram.com"]):
        await update.message.reply_text("❌ Faqat YouTube, TikTok va Instagram linklari qabul qilinadi")
        return
    
    try:
        msg = await update.message.reply_text("⚡ Video tez yuklanmoqda...")
        filename = await download_media(url, update.message.chat_id)
        await msg.edit_text("✅ Yuklab olindi! 📤 Yuborilmoqda...")
        await stream_video(update, filename)
        
    except Exception as e:
        error_msg = str(e)[:100]
        await update.message.reply_text(f"❌ Xatolik: {error_msg}")
        if 'msg' in locals():
            await msg.delete()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📢 Kanalga obuna bo'lish", url=f"https://t.me/{CHANNEL[1:]}")],
        [InlineKeyboardButton("✅ Tekshirish", callback_data='check_sub')]
    ]
    await update.message.reply_text(
        "Botdan foydalanish uchun kanalga obuna bo'ling:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("✅ Siz obuna bo'ldingiz! Endi video linkini yuboring.")

if __name__ == '__main__':
    os.makedirs('downloads', exist_ok=True)
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_subscription, pattern='^check_sub$'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("⚡ Bot tez rejimda ishga tushdi...")
    app.run_polling()
