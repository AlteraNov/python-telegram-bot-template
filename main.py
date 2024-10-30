#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import os
import logging
from typing import Dict, List

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    PicklePersistence,
    filters,
)

#Включение логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

#Состояния разговора
NOTES, SHOPPING_LIST, CHOOSING, DELETE_NOTE, DELETE_ITEM, MARK_ITEM = range(6)

#Клавиатура для выбора действий
reply_keyboard = [
    ["Добавить заметку", "Просмотреть заметки"],
    ["Добавить товар", "Просмотреть список покупок"],
    ["Удалить заметку", "Удалить товар"],
    ["Готово"],
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

def facts_to_str(user_data: Dict[str, List[str]]) -> str:
    """Функция для форматирования собранной информации."""
    facts = [f"{key}: {', '.join(values)}" for key, values in user_data.items() if values]
    return "\n".join(facts).join(["\n", "\n"])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало разговора и показ опций."""
    user = update.message.from_user
    logger.info(f"Пользователь {user.full_name} начал разговор.")
    
    await update.message.reply_text(
        "Добро пожаловать! Я могу помочь вам управлять вашими заметками и списком покупок. Что бы вы хотели сделать?",
        reply_markup=markup
    )

    return CHOOSING

async def choosing_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Выбор действия на основе ввода пользователя."""
    user_choice = update.message.text
    if user_choice == "Добавить заметку":
        await update.message.reply_text("Пожалуйста, отправьте мне вашу заметку.")
        return NOTES
    elif user_choice == "Просмотреть заметки":
        notes = context.user_data.get("notes", [])
        if notes:
            await update.message.reply_text(f"Ваши заметки:\n{''.join(notes)}")
        else:
            await update.message.reply_text("У вас пока нет заметок.")
        return CHOOSING
    elif user_choice == "Добавить товар":
        await update.message.reply_text("Пожалуйста, отправьте мне товар для вашего списка покупок.")
        return SHOPPING_LIST
    elif user_choice == "Просмотреть список покупок":
        shopping_list = context.user_data.get("shopping_list", [])
        if shopping_list:
            await update.message.reply_text(f"Ваш список покупок:\n{''.join(shopping_list)}")
        else:
            await update.message.reply_text("Ваш список покупок пуст.")
        return CHOOSING
    elif user_choice == "Удалить заметку":
        await update.message.reply_text("Пожалуйста, отправьте мне заметку, которую вы хотите удалить.")
        return DELETE_NOTE
    elif user_choice == "Удалить товар":
        await update.message.reply_text("Пожалуйста, отправьте мне товар, который вы хотите удалить.")
        return DELETE_ITEM
    elif user_choice == "Готово":
        await update.message.reply_text("До свидания!", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

async def add_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Добавить заметку в данные пользователя."""
    note = update.message.text
    context.user_data.setdefault("notes", []).append(note + "\n")
    await update.message.reply_text("Заметка добавлена! Что бы вы хотели сделать дальше?")
    return CHOOSING

async def add_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Добавить товар в список покупок."""
    item = update.message.text
    context.user_data.setdefault("shopping_list", []).append(item + "\n")
    await update.message.reply_text("Товар добавлен! Что бы вы хотели сделать дальше?")
    return CHOOSING

async def delete_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Удалить заметку из данных пользователя."""
    note = update.message.text
    notes = context.user_data.get("notes", [])
    
    if note + "\n" in notes:
        notes.remove(note + "\n")
        context.user_data["notes"] = notes
        await update.message.reply_text("Заметка удалена! Что бы вы хотели сделать дальше?")
    else:
        await update.message.reply_text("Эта заметка не найдена.")
    
    return CHOOSING

async def delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Удалить товар из списка покупок."""
    item = update.message.text
    shopping_list = context.user_data.get("shopping_list", [])
    
    if item + "\n" in shopping_list:
        shopping_list.remove(item + "\n")
        context.user_data["shopping_list"] = shopping_list
        await update.message.reply_text("Товар удален! Что бы вы хотели сделать дальше?")
    else:
        await update.message.reply_text("Этот товар не найден в списке покупок.")
    
    return CHOOSING

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменить разговор."""
    await update.message.reply_text("Пока! Если захотите поговорить снова, просто введите /start.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Функция для регистрации команд бота
async def post_init(application: Application) -> None:
    bot_commands = [
        BotCommand("start", "Начать беседу"),
        BotCommand("cancel", "Отменить текущую операцию"),
    ]
    await application.bot.set_my_commands(bot_commands)

def main() -> None:
    """Запустить бота."""
    #Создание приложения и передача токена бота.
    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    #Добавление обработчика разговора с состояниями
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [
                MessageHandler(filters.TEXT & ~(filters.COMMAND), choosing_action),
            ],
            NOTES: [
                MessageHandler(filters.TEXT & ~(filters.COMMAND), add_note),
            ],
            SHOPPING_LIST: [
                MessageHandler(filters.TEXT & ~(filters.COMMAND), add_item),
            ],
            DELETE_NOTE: [
                MessageHandler(filters.TEXT & ~(filters.COMMAND), delete_note),
            ],
            DELETE_ITEM: [
                MessageHandler(filters.TEXT & ~(filters.COMMAND), delete_item),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        name="my_conversation"
    )

    application.add_handler(conv_handler)

    #Запустить бота, пока пользователь не нажмет Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()