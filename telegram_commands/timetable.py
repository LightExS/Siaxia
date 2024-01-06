from telegram import Update
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
import timetable_puller

GROUP, DATE, RESULT = range(3)


async def timetable_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Оберіть групу")
    return GROUP


async def group_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Оберіть дату")
    context.user_data["group"] = update.message.text
    return DATE


async def date_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["date"] = update.message.text
    group = context.user_data["group"]
    date = context.user_data["date"]
    await update.message.reply_text(
        f"Факультет: \nГрупа: {group}\nДата: {date}\nВірно?"
    )
    return RESULT


async def result_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Так":
        group = context.user_data["group"]
        date = context.user_data["date"]

        timetables, dates = timetable_puller.get_timetable(group=group, sdate=date)

        response = ""
        for table, date in zip(timetables, dates):
            response += date + "\n\n" + timetable_puller.change_table_to_str(table)

        await update.message.reply_text(response)
        return -1
    elif update.message.text == "Ні":
        return -1
    else:
        return RESULT


def get_handler():
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("timetable", timetable_command)],
        states={
            GROUP: [MessageHandler(filters.TEXT, group_command)],
            DATE: [MessageHandler(filters.TEXT, date_command)],
            RESULT: [MessageHandler(filters.TEXT, result_command)],
        },
        fallbacks=[],
    )
    return conv_handler


if __name__ == "__main__":
    pass
