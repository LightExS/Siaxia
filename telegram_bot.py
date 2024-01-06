# fmt:off
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from private_variables import TOKEN, BOT_USERNAME

import telegram_commands.timetable
import telegram_commands.bind
import telegram_commands.today
import telegram_commands.tomorrow

import sqlalchemy as db

FACULTY, GROUP, DATE, RESULT = range(4)

#commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text = f"ID: {update.effective_chat.id}")
    
def hande_response(text:str) ->str:
    if 'hello' in text:
        return "Hi!"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text:str = update.message.text
    print(f"User ({update.message.chat.id}) in {message_type}: {text}")

    if message_type == 'group':
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, "").strip()
            response: str = hande_response(new_text)
        else:
            return
    else:
        response: str = hande_response(text)
    print("Bot:", response)
    await update.message.reply_text(response)



async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')


if __name__ == '__main__':
    
    print("Connecting to database")
    engine = db.create_engine("sqlite:///telegram_data.db")
    connection = engine.connect()
    metadata = db.MetaData()
    user_data = db.Table("user_data", metadata, autoload_with=engine)
    
    print("Starting bot...")
    app = Application.builder().token(TOKEN).build()
    
    #Commands handlers
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(telegram_commands.today.get_handler(connection, user_data))
    
    app.add_handler(telegram_commands.tomorrow.get_handler(connection, user_data))

    #Conversation handlers
    timetable_conv_handler = telegram_commands.timetable.get_handler()
    app.add_handler(timetable_conv_handler)
    
    bind_conv_handler = telegram_commands.bind.get_handler(connection, user_data)
    app.add_handler(bind_conv_handler)
    
    
    #Message handlers
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    
    #Errors handlers
    app.add_error_handler(error)
    

    
    print("Polling...")
    app.run_polling(poll_interval=1)
