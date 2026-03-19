# Handles all requests that use the requests module
import logging
from functools import cache
import re
import requests

logger = logging.getLogger(__name__)

PHRASE_LINK = "https://vyneer.me/tools/phrases?ts=1"
EMOTE_LINK = "https://cdn.destiny.gg/emotes/emotes.json"
STREAM_STATUS_LINK = "https://www.destiny.gg/api/info/stream"


@cache
def request_phrases() -> tuple[tuple[str], tuple[re.Pattern]]:
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
    logger.debug("Phrases loaded from vyneer.me")
    return tuple(phrases), tuple(regex_phrases)


@cache
def request_emotes() -> tuple:
    """Returns a tuple of all current emotes"""
    emote_json = requests.get(EMOTE_LINK).json()
    logger.debug("Emotes loaded from destiny.gg")
    return tuple([e["prefix"] for e in emote_json])
