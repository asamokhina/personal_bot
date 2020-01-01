import csv
import datetime
import random
from collections import namedtuple

import telegram
from telegram.ext import CallbackContext


def set_topic(update: telegram.Update, context: CallbackContext):
    user_data = context.bot.user_data
    if not user_data["topic_change"]:
        return None

    reply = update.message.text

    # log topic
    with open(user_data["log_file"], "a") as log:
        writer = csv.writer(log, delimiter=";")
        writer.writerow([datetime.date.today() + datetime.timedelta(days=14), reply])

    # log dialog lines
    if user_data["current_topic"] != reply:
        topic_lists = {
            "topics_rest_list": user_data["data"]["thoughts"][reply],
            "topics_used_list": [],
        }

        for key, value in topic_lists.items():
            with open(f"{key}.csv", "w") as f:
                writer = csv.writer(f, delimiter=";")
                for row in value:
                    writer.writerow([row])

    reply_text = (
        f"Thank you. Results are saved. Topic for the next fortnight is {reply}"
    )
    context.bot.send_message(chat_id=update.effective_chat.id, text=reply_text)
    context.bot.user_data.pop("topic_change")


def topic_change_check(context: CallbackContext):
    user_data = context.bot.user_data

    if (
        datetime.datetime.strptime(user_data["change_date"], "%Y-%m-%d").date()
        == datetime.date.today()
    ):
        user_data["topic_change"] = True
        topics = [[topic] for topic in user_data["topics"]]
        reply_text = (
            f"It is time to choose a topic to focus for next two weeks. Here is a list:"
        )
        markup = telegram.ReplyKeyboardMarkup(topics, one_time_keyboard=True)
        #     choose_topic(bot, chat_id, data, reply, current_topic)
        context.bot.send_message(
            chat_id=context.bot.user_data["chat_id"],
            text=reply_text,
            reply_markup=markup,
        )


def give_human_something_to_think_about(context: CallbackContext):

    # build data structure
    track_used_lines = ["rest", "used"]
    rest_used = namedtuple("Rest_used", track_used_lines)
    today_answer = {}
    message_log_lists = {}
    for answer_part in ["topics", "traits"]:
        answer_part_content = []
        for lines_type in track_used_lines:
            content = list(
                csv.reader(open(f"{answer_part}_{lines_type}_list.csv"), delimiter=";")
            )
            if content:
                answer_part_content.append([line[0] for line in content])
            else:
                answer_part_content.append([])
        message_log_lists[answer_part] = rest_used(*answer_part_content)

        # update if no lines left
        if not message_log_lists[answer_part].rest:
            message_log_lists[answer_part] = rest_used(
                message_log_lists[answer_part].used, []
            )

        # select today's answer
        line_for_today = message_log_lists[answer_part].rest.pop(
            random.randint(0, len(message_log_lists[answer_part].rest) - 1)
        )

        today_answer[answer_part] = line_for_today

        # log results
        message_log_lists[answer_part].used.append(line_for_today)
        for lines_type in track_used_lines:
            with open(f"{answer_part}_{lines_type}_list.csv", "w") as f:
                writer = csv.writer(f, delimiter=";")
                for row in message_log_lists[answer_part]._asdict()[lines_type]:
                    writer.writerow([row])

    message = "\n\n".join(
        ["Good morning, human. I got something you might want to think about."]
        + [f"{k}: {v}" for k, v in today_answer.items()]
    )

    context.bot.send_message(chat_id=context.bot.user_data["chat_id"], text=message)


def read_log(context: CallbackContext):
    with open(context.bot.user_data["log_file"]) as log:
        change_date, current_topic = list(csv.reader(log, delimiter=";"))[-1]
    context.bot.user_data.update(
        {"change_date": change_date, "current_topic": current_topic}
    )
