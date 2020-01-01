import datetime
from enum import Enum, auto

import telegram
from telegram.ext import CallbackContext, ConversationHandler


class States(Enum):
    ENTRY = auto()


def diary(update: telegram.Update, context: CallbackContext):
    update.message.reply_text("I am ready to save an entry.",)

    return States.ENTRY


def received_humans_blabla(update: telegram.Update, context: CallbackContext):
    text = update.message.text

    with open(context.bot.user_data["diary_file"], "a") as diary:
        diary.write(
            "\n"
            + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            + "\n"
            + text
            + "\n"
            + "".join(["*"] * 10)
        )
    # TODO parse entry

    update.message.reply_text("Your entry is saved. Anything else?")

    return States.ENTRY


def done(update: telegram.Update, context: CallbackContext):
    update.message.reply_text("Great! Stay tuned, human.")

    return ConversationHandler.END
