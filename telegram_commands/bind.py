from telegram import Update
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
import sqlalchemy as db

# fmt: off
REWRITE, FACULTY, GROUP, CHECK, RESULT = range(5)


async def conv_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global con, user_data, group_data, cur_table

    message_type: str = update.message.chat.type
    if message_type == "group":
        cur_table = group_data
    else:
        cur_table = user_data
        
    data = con.execute(db.select(cur_table).where(cur_table.c.id == update.effective_chat.id)).fetchall()
    
    if data != []:
        await update.message.reply_text("В даному чаті вже прив'язана інформація про групу, бажаєте її перезаписати?")
        return REWRITE

    await update.message.reply_text("Почнемо прив'язку?")
    return FACULTY

async def rewrite_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resp = update.message.text.lower()
    if resp == "так":
        return FACULTY
    elif resp == "ні":
        await update.message.reply_text("Інформація залишилася без змін")
        return -1

async def faculty_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Оберіть факультет")
    return GROUP

async def group_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Оберіть групу")
    context.user_data["faculty"] = update.message.text
    return CHECK


async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["group"] = update.message.text
    faculty = context.user_data["faculty"]
    group = context.user_data["group"]

    await update.message.reply_text(f"Факультет: {faculty}\nГрупа: {group}\nВірно?")
    return RESULT


async def result_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global con, cur_table
    resp = update.message.text.lower()
    if resp == "так":
        faculty = context.user_data["faculty"]
        group = context.user_data["group"]

        values = {"id":update.effective_chat.id, "faculty": faculty, "group":group}
        query = db.insert(cur_table)
        con.execute(query, values)
        
        await update.message.reply_text("Дані оновлено")
        return -1
    elif resp == "ні":
        await update.message.reply_text("Почнемо спочатку")
        return FACULTY
    else:
        await update.message.reply_text("ШО?")
        return RESULT


def get_handler(connection, user_table, group_table):
    global con, user_data, group_data
    con = connection
    user_data = user_table
    group_data = group_table

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("bind", conv_start)],
        states={
            REWRITE: [MessageHandler(filters.TEXT, rewrite_question)],
            FACULTY: [MessageHandler(filters.TEXT, faculty_command)],
            GROUP: [MessageHandler(filters.TEXT, group_command)],
            CHECK: [MessageHandler(filters.TEXT, check_command)],
            RESULT: [MessageHandler(filters.TEXT, result_command)],
        },
        fallbacks=[],
    )
    return conv_handler
