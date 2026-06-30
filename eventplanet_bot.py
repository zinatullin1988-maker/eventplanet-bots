"""
Event-planet Telegram Bot
───────────────────────
Приветствует пользователя, рассказывает о сервисе,
спрашивает роль (заказчик / исполнитель) и отправляет
в Mini App с нужным параметром.

Установка зависимостей:
  pip install python-telegram-bot==20.7

Запуск:
  python eventplanet_bot.py

Переменные окружения (создайте файл .env или задайте вручную):
  BOT_TOKEN   — токен от @BotFather
  MINIAPP_URL — URL вашего задеплоенного Mini App
                (например https://yourapp.netlify.app)
"""

import os
import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ─── CONFIG ───────────────────────────────────────────────
BOT_TOKEN  = os.getenv("BOT_TOKEN", "AAGL5F4q2FMscF5VIk683_DBRHRiJz9jK9g")
MINIAPP_URL = os.getenv("MINIAPP_URL", "https://your-eventplanet-app.netlify.app")

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─── TEXTS ────────────────────────────────────────────────
WELCOME_TEXT = """
👋 Привет, {name}! Добро пожаловать в *Event-planet* — профессиональную портал специалистов event-индустрии.

🎪 *Что такое Event-planet?*
Платформа, где заказчики мероприятий находят проверенных специалистов: ведущих, DJ, звукорежиссёров, фотографов, декораторов и всю команду — быстро и надёжно.
Платформа, где можно контролировать проект: создавать рабочие чаты для всех сотрудников и для каждой , создавать задачи по проекту

⚡ *Как это работает:*
• Заказчики размещают заявки с датой, городом и нужными специалистами
• Исполнители откликаются на релевантные заявки
• Стороны договариваются и оставляют друг другу отзывы

🚀 *Сейчас — бесплатный бета-тест.* Регистрируйтесь и занимайте место первым!

━━━━━━━━━━━━━━━
Кто вы на платформе?
"""

ROLE_CLIENT = "client"
ROLE_EXEC   = "exec"


# ─── HANDLERS ─────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    name = user.first_name or "друг"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎯 Я заказчик",    callback_data=ROLE_CLIENT),
            InlineKeyboardButton("🎭 Я исполнитель", callback_data=ROLE_EXEC),
        ]
    ])

    await update.message.reply_text(
        WELCOME_TEXT.format(name=name),
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


async def role_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    role = query.data  # "client" or "exec"
    user = query.from_user

    if role == ROLE_CLIENT:
        role_label = "заказчика"
        role_emoji = "🎯"
        role_desc  = (
            "Теперь вы можете:\n"
            "• Размещать заявки на поиск специалистов\n"
            "• Просматривать отклики и профили\n"
            "• Оставлять отзывы после мероприятия"
        )
    else:
        role_label = "исполнителя"
        role_emoji = "🎭"
        role_desc  = (
            "Теперь вы можете:\n"
            "• Заполнить анкету со своей специализацией\n"
            "• Откликаться на релевантные заявки\n"
            "• Получать контакты заказчиков"
        )

    # URL с параметром роли — Mini App откроет нужный экран
    app_url = f"{MINIAPP_URL}?role={role}"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"{role_emoji} Открыть Event-planet",
                web_app=WebAppInfo(url=app_url),
            )
        ],
        [
            InlineKeyboardButton("◀️ Выбрать другую роль", callback_data="back"),
        ],
    ])

    text = (
        f"✅ Отлично! Вы зарегистрированы как *{role_label}*.\n\n"
        f"{role_desc}\n\n"
        "Нажмите кнопку ниже, чтобы открыть платформу 👇"
    )

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=keyboard,
    )

    logger.info(f"User {user.id} ({user.username}) chose role: {role}")


async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = query.from_user
    name = user.first_name or "друг"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎯 Я заказчик",    callback_data=ROLE_CLIENT),
            InlineKeyboardButton("🎭 Я исполнитель", callback_data=ROLE_EXEC),
        ]
    ])

    await query.edit_message_text(
        WELCOME_TEXT.format(name=name),
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "ℹ️ *Event-planet* — биржа специалистов для event-индустрии.\n\n"
        "Команды:\n"
        "/start — начать / сменить роль\n"
        "/help  — эта справка\n"
        "/support — связаться с поддержкой\n",
        parse_mode="Markdown",
    )


async def support_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎧 Написать в поддержку", url="https://t.me/eventplanet_support_bot")]
    ])
    await update.message.reply_text(
        "Если у вас вопрос, проблема или жалоба — напишите боту поддержки. "
        "Сообщения там читает живой человек и отвечает в течение дня.",
        reply_markup=keyboard,
    )


# ─── MAIN ─────────────────────────────────────────────────

def main() -> None:
    if not BOT_TOKEN or BOT_TOKEN == "AAGL5F4q2FMscF5VIk683_DBRHRiJz9jK9g":
        logger.error("❌ Укажите BOT_TOKEN в переменных окружения!")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help",  help_cmd))
    app.add_handler(CommandHandler("support", support_cmd))
    app.add_handler(CallbackQueryHandler(back_to_start, pattern="^back$"))
    app.add_handler(CallbackQueryHandler(role_chosen,   pattern=f"^({ROLE_CLIENT}|{ROLE_EXEC})$"))

    logger.info("🚀 Event-planet бот запущен")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
