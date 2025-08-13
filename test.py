import os
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "8198686578:AAFDpwqt7yzTmH_KzXGZG-HBKhpDy5hOTxg"
CHANNEL = "@TamerkhanBlog"

# Video yuklash
async def download_video(url, message, context, user_id):
    ydl_opts = {
        'format': 'best',
        'cookiefile': 'cookie.txt',  # Cookie fayli yo'li
        'quiet': True,
        'noplaylist': True,  # Playlistni yuklamaslik
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        await message.edit_text("✅ Video yuklandi! 📤 Yuborilmoqda...")

        with open(filename, 'rb') as video_file:
            await context.bot.send_video(
                chat_id=message.chat_id,
                video=video_file,
                caption="📽 @VideoKerakBot orqali yuklab olindi"
            )

        os.remove(filename)  # Faylni o'chirish

    except Exception as e:
        print(f"Video yuklashda xatolik: {e}")
        await message.edit_text("❌ Video yuklashda xatolik yuz berdi, iltimos keyinroq urinib ko‘ring.")

# Foydalanuvchi yuborgan linkni tekshirish
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    user_id = update.message.from_user.id

    if any(x in url for x in ["youtube.com", "youtu.be", "tiktok.com", "instagram.com"]):
        msg = await update.message.reply_text("📥 Video yuklanmoqda, kuting...")
        await download_video(url, msg, context, user_id)
    else:
        await update.message.reply_text("❌ Faqat YouTube, TikTok va Instagram videolarini yuklash mumkin.")

# Bot ishga tushishi
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot ishga tushdi...")
    app.run_polling()

