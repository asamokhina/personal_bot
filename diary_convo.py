import datetime
import json
from enum import Enum, auto

import telegram
from telegram.ext import CallbackContext, ConversationHandler

from emoparser import identify_emotions


class States(Enum):
    ENTRY = auto()


def diary(update: telegram.Update, context: CallbackContext):
    update.message.reply_text("I am ready to save an entry.",)

    return States.ENTRY


def write_entry(file_name, text):
    with open(file_name, "a") as diary:
        diary.write(
            "\n"
            + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            + "\n"
            + text
            + "\n"
            + "".join(["*"] * 10)
        )


def received_humans_blabla(update: telegram.Update, context: CallbackContext):
    text = update.message.text
    diary_file = context.bot.user_data["diary_file"]
    write_entry(diary_file, text)

    try:
        emo_dict = context.bot.user_data["emo_dict"]
        parsed_emotions = identify_emotions.score_emotions(emo_dict, text)
        write_entry(
            diary_file.replace(".txt", "_score.txt"), json.dumps(parsed_emotions)
        )

    except KeyError:
        pass

    finally:
        update.message.reply_text("Your entry is saved. Anything else?")

        return States.ENTRY


def done(update: telegram.Update, context: CallbackContext):
    update.message.reply_text("Great! Stay tuned, human.")

    return ConversationHandler.END
