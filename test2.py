import os
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
    
    # Haqiqiy kanal obunasini tekshirish (Telegram API orqali)
    is_subscribed = await check_subscription(user_id, context)

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

# Kanalga obuna bo'lishni tekshirish
async def check_subscription(user_id: int, context):
    try:
        # Foydalanuvchining kanalga obuna bo‘lganini tekshirish
        chat_member = await context.bot.get_chat_member(CHANNEL, user_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Obuna tekshirishda xatolik: {e}")
        return False

# Video yuklash va yuborish
async def download_video(url, message, context, user_id):
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'cookiefile': 'cookie.txt',  # Cookie faylini ishlatish
        'quiet': True,
        'skip_download': True,  # Faqat ma'lumot olish, yuklamasdan
        'noplaylist': True,  # Playlistni o'tkazib yuborish
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
            direct_url = best_format['url']  # Video URL

        await message.edit_text("✅ Video manzili topildi! 📤 To‘g‘ridan-to‘g‘ri yuborilmoqda...")

        await context.bot.send_video(
            chat_id=message.chat_id,
            video=direct_url,
            caption="📽 @VideoKerakBot orqali yuklab olindi",
            supports_streaming=True  # Streamingni qo‘llab-quvvatlash
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
