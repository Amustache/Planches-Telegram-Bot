#!/usr/bin/env python

# pylint: disable=unused-argument, wrong-import-position

# This program is dedicated to the public domain under the CC0 license.


import logging


from peewee import CharField, IntegerField, Model, SqliteDatabase
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, filters, MessageHandler
import requests


from secret import TOKEN


# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

logger = logging.getLogger(__name__)

ENDPOINT = "https://planches.arnalo.ch/api/{board}/{op}"
BOARDS = ["b", "n", "c", "smol"]
OPS = ["", "ops", "post/{num}"]

DB = SqliteDatabase("./main.db")


class BaseModel(Model):
    class Meta:
        database = DB


class Subscription(BaseModel):
    userid = IntegerField()
    board = CharField()


def subuser(userid, board):
    sub, created = Subscription.get_or_create(userid=userid, board=board)
    return created


def unsubuser(userid, board):
    sub = Subscription.get_or_none(userid=userid, board=board)
    if sub:
        sub.delete_instance()
        return True
    else:
        return False


def subsfromuser(userid):
    subs = Subscription.select().where(Subscription.userid == userid)
    return [sub.board for sub in subs]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""

    user = update.effective_user

    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""

    await update.message.reply_text("Help!")


async def sub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:
        board = context.args[0]
        if board not in BOARDS:
            await update.message.reply_text(f"Board not available: {board}.")
            return
        subbed = subuser(update.effective_user.id, board)
        if not subbed:
            await update.message.reply_text(f"You were already subscribed to the board {board}.")
    else:
        boards = ", ".join(BOARDS)
        await update.message.reply_text(f"Usage: /sub <board>\nAvailable boards: {boards}.")


async def unsub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:
        board = context.args[0]
        if board not in BOARDS:
            await update.message.reply_text(f"Board not available: {board}.")
            return
        unsubbed = unsubuser(update.effective_user.id, board)
        if not unsubbed:
            await update.message.reply_text(f"You were not subscribed to the board {board}.")
    else:
        boards = ", ".join(subsfromuser(update.effective_user.id)) or "none"
        await update.message.reply_text(f"Usage: /unsub <board>\nYour boards: {boards}.")


async def list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    boards = ", ".join(subsfromuser(update.effective_user.id)) or "none"
    await update.message.reply_text(f"Your boards: {boards}.")


async def read(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:
        board = context.args[0]
        if board not in BOARDS:
            await update.message.reply_text(f"Board not available: {board}.")
            return
        data = requests.get(ENDPOINT.format(board=board, op="ops")).json()
        text = f"Last 5 ops from {board}\n"
        for post in data[:5]:
            number = post["fields"]["seq"]
            # img = "https://planches.arnalo.ch/media/{}".format(post["fields"]["img"])
            last_bump = post["fields"]["bump_timestamp"]
            content = post["fields"]["content"].replace("\r\n", " ")
            link = f"https://planches.arnalo.ch/{board}/thread/{number}"
            text += f"[<a href=\"{link}\">#{number}</a>] {content[:128]}{'[...]' if len(content) > 128 else ''} (Last bump: {last_bump})\n"
        await update.message.reply_text(text, disable_web_page_preview=True, parse_mode="HTML")
    else:
        boards = ", ".join(BOARDS)
        await update.message.reply_text(f"Usage: /read <board>\nAvailable boards: {boards}.")


async def catalog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:
        board = context.args[0]
        if board not in BOARDS:
            await update.message.reply_text(f"Board not available: {board}.")
    else:
        boards = ", ".join(BOARDS)
        await update.message.reply_text(f"Usage: /read <board>\nAvailable boards: {boards}.")


def main() -> None:
    """Start the bot."""
    DB.connect()
    DB.create_tables([Subscription])

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("sub", sub))
    application.add_handler(CommandHandler("unsub", unsub))
    application.add_handler(CommandHandler("list", list))
    application.add_handler(CommandHandler("read", read))
    application.add_handler(CommandHandler("catalog", catalog))

    # on non command i.e message - echo the message on Telegram
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
