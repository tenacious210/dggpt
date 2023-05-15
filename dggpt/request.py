# Handles all requests that use the requests module
import logging
from functools import cache
from datetime import datetime
import re
import requests

logger = logging.getLogger(__name__)

LOG_LINK = "https://api-v2.rustlesearch.dev/anon/search"
PHRASE_LINK = "https://vyneer.me/tools/phrases?ts=1"
EMOTE_LINK = "https://tena.dev/api/emotes"


@cache
def request_phrases() -> tuple[tuple[str], tuple[re.Pattern]]:
    def is_regex(text: str):
        if re.search(r"^/.*/$", text):
            try:
                return re.compile(text[1:-1], re.IGNORECASE)
            except re.error:
                pass

    logger.debug("Getting phrases from vyneer.me ...")
    raw_phrases = requests.get(PHRASE_LINK)
    regex_phrases = []
    phrases = []
    for item in raw_phrases.json()["data"]:
        if (regex := is_regex(phrase := item["phrase"])) is not None:
            regex_phrases.append(regex)
        else:
            phrases.append(phrase)
    logger.debug("Phrases loaded from vyneer.me")
    return tuple(phrases), tuple(regex_phrases)


@cache
def request_emotes() -> tuple:
    """Returns a tuple of all current emotes on tena.dev"""
    logger.debug("Getting emotes from tena.dev ...")
    emotes = requests.get(EMOTE_LINK).json().keys()
    logger.debug("Emotes loaded from tena.dev")
    return tuple([emote_name for emote_name in emotes])


def request_debate(
    nick1: str, nick2: str, amount: str | int, day: str = None
) -> list | str:
    """Returns messages from 2 users on rustlesearch.dev where they mention eachother."""
    try:
        amount = int(amount)
    except ValueError:
        logger.info('"amount" was given a non-int value')
        return "Message amount wasn't an integer MMMM"
    if not day:
        day = datetime.utcnow().strftime("%Y-%m-%d")
    r_link = (
        f"{LOG_LINK}?username={nick1}%20%7C%20{nick2}"
        f"&start_date={day}&end_date={day}&channel=Destinygg"
        f"&text=%22{nick1}%22%20%7C%20%22{nick2}%22"
    )
    logger.debug(f"Getting messages from rustlesearch.dev ...")
    raw = requests.get(r_link).json()
    if not raw["data"] or not raw["data"]["messages"]:
        logger.info("No messages found from rustlesearch.dev")
        return "No messages found MMMM"
    i, debate = 0, []
    for message in reversed(raw["data"]["messages"]):
        if i == amount:
            break
        debate.append(f'{message["username"]}: {message["text"]}')
        i += 1
    logger.info(f"{amount} messages loaded from rustlesearch.dev")
    return debate
