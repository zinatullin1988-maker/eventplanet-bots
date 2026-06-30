"""
Event-planet Support Bot
─────────────────────────
Отдельный бот для обратной связи. Пользователи пишут сюда вопросы и жалобы,
сообщения пересылаются администратору. Администратор отвечает прямо в этом же
чате (реплаем на пересланное сообщение) — ответ автоматически уходит пользователю.

Установка:
  pip install python-telegram-bot==20.7

Запуск:
  ADMIN_CHAT_ID=ваш_telegram_id python eventplanet_support_bot.py

Как узнать свой ADMIN_CHAT_ID:
  1. Напишите любое сообщение боту @userinfobot в Telegram
  2. Он пришлёт ваш числовой ID — это и есть ADMIN_CHAT_ID
"""

import os
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ─── CONFIG ───────────────────────────────────────────────
BOT_TOKEN     = os.getenv("SUPPORT_BOT_TOKEN", "ВСТАВЬТЕ_ТОКЕН_БОТА_ПОДДЕРЖКИ")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "ВСТАВЬТЕ_ВАШ_TELEGRAM_ID")

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# В реальной версии замените на базу данных (Supabase/PostgreSQL).
# Сейчас — простой словарь в памяти: {id пересланного сообщения у админа: id пользователя}
forwarded_map = {}


# ─── HANDLERS ─────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Это поддержка *Event-planet*.\n\n"
        "Опишите вашу проблему или вопрос одним сообщением — "
        "мы ответим вам прямо здесь в течение дня.\n\n"
        "Если у вас жалоба на другого пользователя, укажите:\n"
        "• Имя/username нарушителя\n"
        "• Что произошло\n"
        "• Номер заявки или проекта (если есть)",
        parse_mode="Markdown",
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "ℹ️ Просто напишите ваш вопрос или проблему — мы получим сообщение и ответим.\n\n"
        "Команды:\n"
        "/start — начать заново"
    )


async def forward_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Пересылает сообщение пользователя администратору."""
    user = update.effective_user
    message = update.message

    # Если пишет сам админ — не пересылаем (избегаем дублирования)
    if str(update.effective_chat.id) == str(ADMIN_CHAT_ID):
        return

    header = (
        f"📩 *Новое обращение*\n"
        f"От: {user.first_name} {user.last_name or ''}\n"
        f"Username: @{user.username or 'нет'}\n"
        f"ID: `{user.id}`\n"
        f"{'─'*20}"
    )

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=header,
        parse_mode="Markdown",
    )

    # Пересылаем оригинальное сообщение (работает для текста, фото, файлов и т.д.)
    forwarded = await context.bot.forward_message(
        chat_id=ADMIN_CHAT_ID,
        from_chat_id=update.effective_chat.id,
        message_id=message.message_id,
    )

    # Запоминаем связь: пересланное сообщение → пользователь
    forwarded_map[forwarded.message_id] = user.id

    await message.reply_text(
        "✅ Ваше сообщение получено! Мы ответим вам здесь в ближайшее время."
    )

    logger.info(f"Forwarded message from user {user.id} ({user.username})")


async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Когда админ отвечает реплаем на пересланное сообщение —
    бот пересылает этот ответ обратно пользователю.
    """
    if str(update.effective_chat.id) != str(ADMIN_CHAT_ID):
        return

    message = update.message
    if not message.reply_to_message:
        return

    replied_id = message.reply_to_message.message_id
    user_id = forwarded_map.get(replied_id)

    if not user_id:
        await message.reply_text(
            "⚠️ Не могу определить, кому отправить ответ. "
            "Отвечайте реплаем (Reply) именно на пересланное сообщение пользователя."
        )
        return

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"💬 *Ответ от поддержки Event-planet:*\n\n{message.text}",
            parse_mode="Markdown",
        )
        await message.reply_text("✅ Ответ отправлен пользователю")
        logger.info(f"Admin replied to user {user_id}")
    except Exception as e:
        await message.reply_text(f"❌ Не удалось отправить: {e}")
        logger.error(f"Failed to send reply to user {user_id}: {e}")


# ─── MAIN ─────────────────────────────────────────────────

def main() -> None:
    if BOT_TOKEN == "8990858708:AAFIQ9GoarkK2m7tXlgU0kf9UFuIrp2nPSs":
        logger.error("❌ Укажите SUPPORT_BOT_TOKEN!")
        return
    if ADMIN_CHAT_ID == "380685081":
        logger.error("❌ Укажите ADMIN_CHAT_ID!")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))

    # Сообщения от админа (реплай) — обрабатываем первыми, более специфичный фильтр
    app.add_handler(MessageHandler(
        filters.TEXT & filters.REPLY & filters.Chat(chat_id=int(ADMIN_CHAT_ID)) if ADMIN_CHAT_ID.lstrip('-').isdigit() else filters.TEXT & filters.REPLY,
        reply_to_user
    ))

    # Все остальные сообщения — пересылаем админу
    app.add_handler(MessageHandler(
        filters.TEXT | filters.PHOTO | filters.Document.ALL,
        forward_to_admin
    ))

    logger.info("🎧 Event-planet Support Bot запущен")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
