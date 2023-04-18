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


def bad_word(message: str) -> bool:
    phrases, regex_phrases = get_phrases()
    return any(p.lower() in message.lower() for p in phrases) or any(
        regex.search(message) for regex in regex_phrases
    )


def bad_prompt(msg: Message):
    mod = openai.Moderation.create(input=msg.data)
    if mod["results"][0]["flagged"]:
        print(f"This prompt was flagged by openai: \n {msg.nick}: {msg.data}")
        return True
    return False
