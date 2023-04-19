from functools import cache
from typing import Union
import re

from dggbot import Message
import openai

import requests

vyneer_phrases = "https://vyneer.me/tools/phrases?ts=1"
tena_emotes = "https://tena.dev/api/emotes"
regex_check = re.compile(r"^/.*/$")


def is_regex(text: str) -> Union[re.Pattern, None]:
    if regex_check.search(text):
        try:
            return re.compile(text[1:-1], re.IGNORECASE)
        except re.error:
            pass


@cache
def get_phrases():
    r = requests.get(vyneer_phrases)
    data = r.json()["data"]
    regex_phrases = []
    phrases = []
    for item in data:
        if (regex := is_regex(phrase := item["phrase"])) is not None:
            regex_phrases.append(regex)
        else:
            phrases.append(phrase)
    return tuple(phrases), regex_phrases


@cache
def get_emotes():
    r = requests.get(tena_emotes).json()
    return [e for e in r.keys()]


def bad_prompt(msg: Message):
    mod = openai.Moderation.create(input=msg.data)
    if mod["results"][0]["flagged"]:
        print(f"This prompt was flagged by openai: \n {msg.nick}: {msg.data}")
        return True
    return False


def bot_filter(message: str) -> bool:
    def unique(message: str) -> bool:
        words_list = re.findall(r"[^, ]+", message.lower())

        if len(words_list) >= 8:
            total_words = len(words_list)
            unique_words = len(set(words_list))

            if total_words == 0:
                return False

            return unique_words / total_words <= 0.45

        return False

    def repeated(message: str) -> bool:
        if len(message) < 90 and len(message.split()) > 4:
            return False

        words = message.split()

        return not all(len(mess) < 90 / 1.5 or len(set(mess)) >= 9 for mess in words)

    def ascii(message: str) -> bool:
        non_ascii_count = len(re.findall(r"[^\x20-\x7F]", message))
        ascii_punct_count = len(re.findall(r"[\x21-\x2F\x3A-\x40]", message))
        return non_ascii_count > 20 or ascii_punct_count > 40

    def bad_word(message: str) -> bool:
        phrases, regex_phrases = get_phrases()
        return any(p.lower() in message.lower() for p in phrases) or any(
            regex.search(message) for regex in regex_phrases
        )

    return any(check(message) for check in (unique, repeated, ascii, bad_word))
