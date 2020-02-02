#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import json
from collections import namedtuple

import telegram
import yaml
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    Filters,
    JobQueue,
    MessageHandler,
    PicklePersistence,
    Updater,
)

from diary_convo import States, diary, done, received_humans_blabla
from food_for_thought_convo import (
    give_human_something_to_think_about,
    read_log,
    set_topic,
    topic_change_check,
)


class PersonalBot(telegram.Bot):
    """Because I am a special snowflake"""

    def __init__(self, token, owner):
        super().__init__(token=token)
        self.user_data = {}
        self.owner = owner
        self.persistence = None

    def check_user(self, user_id):
        if user_id != self.owner:
            self.send_message(chat_id=user_id, text="Sorry, you are not my owner")
            return False


def set_up_bot(config_file):
    with open(config_file) as f:
        config = yaml.safe_load(f)

    with open(config["data_file"]) as j:
        data = json.load(j)
        topics = list(data["thoughts"].keys())

    bot = PersonalBot(config["token"], owner=config["owner"])
    bot.persistence = PicklePersistence(config["history"])
    bot.user_data = {
        "log_file": config["log_file"],
        "diary_file": config["diary_file"],
        "chat_id": config["chat_id"],
        "emo_dict": config.get("emo_dict"),
        "data": data,
        "topics": topics,
    }

    return bot


def alive(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'm alive!")


def nastyas_chat(config_file):
    # set up
    bot = set_up_bot(config_file)
    updater = Updater(bot=bot, use_context=True, persistence=bot.persistence)
    dp = updater.dispatcher
    queue = updater.job_queue

    # handlers
    dp.add_handler(CommandHandler("alive", alive))
    topic_answer = MessageHandler(
        filters=(
            Filters.regex(f"{'|'.join(bot.user_data['topics'])}")
            & Filters.chat(username=[bot.owner])
        ),
        callback=set_topic,
    )
    dp.add_handler(topic_answer)

    diary_handler = ConversationHandler(
        entry_points=[CommandHandler("diary", diary)],
        states={
            States.ENTRY: [
                MessageHandler(
                    filters=(Filters.text & Filters.chat(username=[bot.owner])),
                    callback=received_humans_blabla,
                )
            ],
        },
        fallbacks=[CommandHandler("done", done)],
        allow_reentry=True,
        persistent=True,
        name="diary",
    )

    dp.add_handler(diary_handler)

    # job queue
    queue.run_daily(
        read_log, time=datetime.time(6, 58, 00),
    )

    queue.run_daily(
        give_human_something_to_think_about, time=datetime.time(7, 00, 00),
    )
    queue.run_daily(
        topic_change_check, time=datetime.time(7, 1, 00),
    )

    # polling
    updater.start_polling()


nastyas_chat("config.yaml")
