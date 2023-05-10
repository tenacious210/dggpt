# Handles all requests that use the requests module

from functools import cache
from datetime import datetime
import re
import requests


LOG_LINK = "https://api-v2.rustlesearch.dev/anon/search"
PHRASE_LINK = "https://vyneer.me/tools/phrases?ts=1"
EMOTE_LINK = "https://tena.dev/api/emotes"


@cache
def request_phrases() -> tuple[tuple]:
    def is_regex(text: str):
        if re.search(r"^/.*/$", text):
            try:
                return re.compile(text[1:-1], re.IGNORECASE)
            except re.error:
                pass

    raw_phrases = requests.get(PHRASE_LINK)
    regex_phrases = []
    phrases = []
    for item in raw_phrases.json()["data"]:
        if (regex := is_regex(phrase := item["phrase"])) is not None:
            regex_phrases.append(regex)
        else:
            phrases.append(phrase)
    return tuple(phrases), tuple(regex_phrases)


@cache
def request_emotes() -> tuple:
    """Returns a tuple of all current emotes on tena.dev"""
    emotes = requests.get(EMOTE_LINK).json().keys()
    return (emote_name for emote_name in emotes)


def request_debate(nick1: str, nick2: str, amount: int, day: str = None) -> str:
    """Returns messages from 2 users on rustlesearch.dev where they mention eachother."""
    if not day:
        day = datetime.utcnow().strftime("%Y-%m-%d")
    r_link = (
        f"{LOG_LINK}?username={nick1}%20%7C%20{nick2}"
        f"&start_date={day}&end_date={day}&channel=Destinygg"
        f"&text=%22{nick1}%22%20%7C%20%22{nick2}%22"
    )
    raw = requests.get(r_link).json()
    if not raw["data"] or not raw["data"]["messages"]:
        return "No messages found."
    i, debate = 0, []
    for message in reversed(raw["data"]["messages"]):
        if i == amount:
            break
        debate.append(f'{message["username"]}: {message["text"]}')
        i += 1
    return "\n".join(debate)
