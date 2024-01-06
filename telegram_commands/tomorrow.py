from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
import timetable_puller
import sqlalchemy as db
from datetime import datetime, timedelta

# fmt: off
async def tomorow_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global con, user_data
    res = con.execute(db.select(user_data).where(user_data.c.id == update.effective_chat.id)).fetchall()


    if res == []:
        await update.message.reply_text("Для використання цієї команди потрібно прив'язати групу, скористайтесь командою /bind")
        return
    
    group = res[0][1]
    
    tomorrow = datetime.now() + timedelta(1)
    date = tomorrow.strftime("%d.%m.%Y")
    
    timetable, dates = timetable_puller.get_timetable(group=group, sdate=date)
    if timetable == []:
        out = date + "\n\nПар немає"
    else:
        out = dates[0] + "\n\n" + timetable_puller.change_table_to_str(timetable[0])
    
    await update.message.reply_text(out)


def get_handler(connection, user_table):
    global con, user_data
    con = connection
    user_data = user_table
    return CommandHandler("tomorrow", tomorow_command)
