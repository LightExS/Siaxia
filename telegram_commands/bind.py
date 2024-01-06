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
REWRITE, GROUP, CHECK, RESULT = range(4)


async def conv_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global con, user_data
        
    data = con.execute(db.select(user_data).where(user_data.c.id == update.effective_chat.id)).fetchall()
    
    if data != []:
        await update.message.reply_text("В даному чаті вже прив'язана інформація про групу, бажаєте її перезаписати?")
        return REWRITE

    await update.message.reply_text("Почнемо прив'язку?")
    return GROUP

async def rewrite_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resp = update.message.text.lower()
    if resp == "так":
        context.user_data["update"] = True
        return GROUP
    elif resp == "ні":
        await update.message.reply_text("Інформація залишилася без змін")
        return -1


async def group_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Оберіть групу")
    return CHECK


async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["group"] = update.message.text
    group = context.user_data["group"]

    await update.message.reply_text(f"Група: {group}\nВірно?")
    return RESULT


async def result_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global con, user_data
    resp = update.message.text.lower()
    if resp == "так":
        group = context.user_data["group"]
        
        if context.user_data.get('update') == True:
            query = db.update(user_data).values(id=update.effective_chat.id, group=group)
        else:
            query = db.insert(user_data).values(id=update.effective_chat.id, group=group)
        con.execute(query)
        con.commit()
        
        await update.message.reply_text("Дані оновлено")
        return -1
    elif resp == "ні":
        await update.message.reply_text("Почнемо спочатку")
        return GROUP
    else:
        await update.message.reply_text("ШО?")
        return RESULT


def get_handler(connection, user_table):
    global con, user_data
    con = connection
    user_data = user_table

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("bind", conv_start)],
        states={
            REWRITE: [MessageHandler(filters.TEXT, rewrite_question)],
            GROUP: [MessageHandler(filters.TEXT, group_command)],
            CHECK: [MessageHandler(filters.TEXT, check_command)],
            RESULT: [MessageHandler(filters.TEXT, result_command)],
        },
        fallbacks=[],
    )
    return conv_handler
