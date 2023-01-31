#!/usr/bin/env python

# pylint: disable=unused-argument, wrong-import-position

# This program is dedicated to the public domain under the CC0 license.
import logging


from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


from helpers import BOARDS, ENDPOINT, get_last_op_from_board, get_latest_op, get_latest_ops
from models import DB, Subscription, subsfromuser, subuser, unsubuser
from secret import TOKEN


# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

logger = logging.getLogger(__name__)

LAST_OPS = {}


async def update_from_board(context):
    job = context.job
    board = job.data
    last = get_last_op_from_board(board)  # Because the API is broken lmao
    if last > LAST_OPS[board]:
        LAST_OPS[board] = last
        subs = Subscription.select().where(Subscription.board == board)
        post = get_latest_op(board)
        text = f"Update from board {board}!\n\nThread #{post['number']}\n{post['content']}\nLink: {post['link']}\nLast bump: {post['last_bump']}\n"
        for sub in subs:
            if post["img"]:
                await context.bot.send_photo(sub.userid, post["img"], caption=text)
            else:
                await context.bot.send_message(sub.userid, text=text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""

    await update.message.reply_text(
        "Telegram bot for https://planches.arnalo.ch/\n\n"
        "- /sub \<board>: Get new updates from a board\n"
        "- /unsub \<board>: Unsub from a board\n"
        "- /list: Show currently subscribed boards\n"
        "- /read \<board>: List last five OPs of a board\n"
    )


async def sub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:
        board = context.args[0]
        if board not in BOARDS:
            await update.message.reply_text(f"Board not available: {board}.")
            return
        subbed = subuser(update.effective_user.id, board)
        if not subbed:
            await update.message.reply_text(f"You were already subscribed to the board {board}.")
            return
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
            return
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
        text = f"Last 5 ops from {board}\n"
        for post in get_latest_ops(board, 5):
            text += f"[<a href=\"{post['link']}\">#{post['number']}</a>] {post['content'][:128]}{'[...]' if len(post['content']) > 128 else ''} (Last bump: {post['last_bump']})\n"
        await update.message.reply_text(text, disable_web_page_preview=True, parse_mode="HTML")
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
    application.add_handler(CommandHandler(["start", "help"], help_command))
    application.add_handler(CommandHandler("sub", sub))
    application.add_handler(CommandHandler("unsub", unsub))
    application.add_handler(CommandHandler("list", list))
    application.add_handler(CommandHandler("read", read))

    # on non command i.e message - echo the message on Telegram
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    for board in BOARDS:
        LAST_OPS[board] = get_last_op_from_board(board)
        application.job_queue.run_repeating(update_from_board, 60, data=board, name=str(board))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
