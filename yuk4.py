import os
import time
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from telegram.error import TimedOut

TOKEN = "8198686578:AAFDpwqt7yzTmH_KzXGZG-HBKhpDy5hOTxg"
CHANNEL = "@TamerkhanBlog"

# User tilini saqlash
user_lang = {}
last_update_time = {}

# Til tanlash
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇺🇿 O'zbek", callback_data='lang_uz')],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data='lang_ru')],
        [InlineKeyboardButton("🇬🇧 English", callback_data='lang_en')],
        [InlineKeyboardButton("🇩🇪 Deutsch", callback_data='lang_de')]
    ]
    await update.message.reply_text(
        "Tilni tanlang / Choose language / Выберите язык / Sprache auswählen:", 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Til callback
async def lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split('_')[1]
    user_lang[query.from_user.id] = lang

    keyboard = [
        [InlineKeyboardButton("📢 Kanalga obuna bo'lish", url=f"https://t.me/{CHANNEL[1:]}")],
        [InlineKeyboardButton("✅ Tekshirish", callback_data='check_sub')]
    ]

    texts = {
        "uz": "Botdan foydalanish uchun kanalga obuna bo‘ling va tekshirish tugmasini bosing.",
        "ru": "Для использования бота подпишитесь на канал и нажмите кнопку Проверить.",
        "en": "To use the bot, subscribe to the channel and click Check button.",
        "de": "Um den Bot zu benutzen, abonniere den Kanal und klicke auf 'Überprüfen'."
    }

    await query.edit_message_text(
        text=texts[lang], 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Obuna tekshirish
async def check_sub_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = user_lang.get(user_id, "uz")
    
    # TODO: Haqiqiy kanal obunasini tekshirish (Telegram API orqali)
    is_subscribed = True  # Hozircha true qildik

    texts_success = {
        "uz": "✅ Siz obuna bo‘ldingiz! Endi videoni yuboring.",
        "ru": "✅ Вы подписаны! Теперь отправьте видео.",
        "en": "✅ You are subscribed! Now send a video.",
        "de": "✅ Du hast abonniert! Jetzt schicke ein Video."
    }
    texts_fail = {
        "uz": "❌ Iltimos kanalga obuna bo‘ling.",
        "ru": "❌ Пожалуйста, подпишитесь на канал.",
        "en": "❌ Please subscribe to the channel.",
        "de": "❌ Bitte abonniere den Kanal."
    }

    if is_subscribed:
        await query.edit_message_text(text=texts_success[lang])
    else:
        await query.answer(text=texts_fail[lang], show_alert=True)

# Video progress hook
async def progress_hook(d, message, context, user_id):
    if d['status'] == 'downloading':
        now = time.time()
        if user_id not in last_update_time:
            last_update_time[user_id] = 0
        if now - last_update_time[user_id] < 1:
            return
        last_update_time[user_id] = now

        percent = d.get('_percent_str', '').strip()
        speed = d.get('_speed_str', 'Noma’lum')
        eta = d.get('_eta_str', '???')
        text = f"⬇ Yuklanmoqda: {percent} | 📡 Tezlik: {speed} | ⏳ Qolgan vaqt: {eta}"
        try:
            await message.edit_text(text)
        except TimedOut:
            await message.edit_text("⏳ Bir necha soniyada sizga yetib boradi, sabrli bo‘ling...")
        except:
            pass

# Video yuklash
async def download_video(url, message, context, user_id):
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'quiet': True,
        'cookiefile': 'cookie.txt',  # Cookie faylni ulash
        'skip_download': True,  # Yuklamasdan faqat ma'lumot olish
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [info])
            # Eng yaxshi mp4 formatni tanlash
            best_format = max(
                (f for f in formats if f.get('ext') == 'mp4' and f.get('url')),
                key=lambda f: f.get('filesize') or 0,
                default=formats[0]
            )
            direct_url = best_format['url']

        await message.edit_text("✅ Video manzili topildi! 📤 To‘g‘ridan-to‘g‘ri yuborilmoqda...")

        await context.bot.send_video(
            chat_id=message.chat_id,
            video=direct_url,
            caption="📽 @VideoKerakBot orqali yuklab olindi",
            supports_streaming=True
        )

    except Exception as e:
        print(f"Video yuklashda xatolik: {e}")
        await message.edit_text("❌ Video yuklashda xatolik yuz berdi, iltimos keyinroq urinib ko‘ring.")

# Foydalanuvchi yuborgan link
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    user_id = update.message.from_user.id
    lang = user_lang.get(user_id, "uz")

    if any(x in url for x in ["youtube.com", "youtu.be", "tiktok.com", "instagram.com"]):
        msg = await update.message.reply_text("📥 Video yuklanmoqda, kuting...")
        await download_video(url, msg, context, user_id)
    else:
        texts_invalid = {
            "uz": "❌ Bu faqat YouTube, TikTok va Instagram videolari uchun ishlaydi.",
            "ru": "❌ Работает только с видео YouTube, TikTok и Instagram.",
            "en": "❌ Only works for YouTube, TikTok, and Instagram videos.",
            "de": "❌ Funktioniert nur mit YouTube-, TikTok- und Instagram-Videos."
        }
        await update.message.reply_text(texts_invalid[lang])

# Bot ishga tushishi
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(lang_callback, pattern=r'lang_'))
    app.add_handler(CallbackQueryHandler(check_sub_callback, pattern=r'check_sub'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot ishga tushdi...")
    app.run_polling()
