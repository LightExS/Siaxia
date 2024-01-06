# fmt:off
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import timetable_puller
from private_variables import TOKEN, BOT_USERNAME

import telegram_commands.timetable
import telegram_commands.bind

import sqlalchemy as db

buttons = [[InlineKeyboardButton("btn1", callback_data="1")],[InlineKeyboardButton("btn2", callback_data="2")]]
FACULTY, GROUP, DATE, RESULT = range(4)

#commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text = f"ID: {update.effective_chat.id}",reply_markup = InlineKeyboardMarkup(buttons))
    

async def timetable_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Оберіть факультет")
    return FACULTY

async def faculty_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Оберіть групу")
    context.user_data['faculty'] = update.message.text
    return GROUP

async def group_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Оберіть з якого числа")
    context.user_data['group'] = update.message.text
    return DATE

async def date_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['date'] = update.message.text
    faculty = context.user_data['faculty']
    group = context.user_data['group']
    date = context.user_data['date']
    await update.message.reply_text(f"Факультет: {faculty}\nГрупа: {group}\nДата: {date}\nВірно?")
    return RESULT

async def result_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Так":
        faculty = context.user_data['faculty']
        group = context.user_data['group']
        date = context.user_data['date']

        
        timetables, dates = timetable_puller.get_timetable(faculty=faculty, group=group, sdate=date)

        #Temporary output, to be changed
        response = "" 
        for table, date in zip(timetables,dates):
            response += date +"\n\n"+ timetable_puller.change_table_to_str(table)
        
        await update.message.reply_text(response)
        return -1
    elif update.message.text == "Ні":
        return -1
    else:
        return RESULT


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
    chat_data = db.Table("group_data", metadata, autoload_with=engine)
    
    print("Starting bot...")
    app = Application.builder().token(TOKEN).build()
    
    #Commands handlers
    app.add_handler(CommandHandler('start', start_command))

    #Conversation handlers
    timetable_conv_handler = telegram_commands.timetable.get_handler()
    app.add_handler(timetable_conv_handler)
    
    bind_conv_handler = telegram_commands.bind.get_handler(connection, user_data, chat_data)
    app.add_handler(bind_conv_handler)
    
    
    #Message handlers
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    
    #Errors handlers
    app.add_error_handler(error)
    

    
    print("Polling...")
    app.run_polling(poll_interval=1)
