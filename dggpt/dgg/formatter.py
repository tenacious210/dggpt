# Formats responses to make them DGG appropriate
import re
import logging
from dggpt.request import request_emotes

logger = logging.getLogger(__name__)
PUNCS = tuple(". , ? ! ' \" > @ # ( ) - * :".split())


def format_dgg_message(message: str, nick: str = None) -> str:
    for emote in request_emotes():
        for punc in PUNCS:
            message = message.replace(f"{emote}{punc}", f"{emote} {punc}")
            message = message.replace(f"{punc}{emote}", f"{punc} {emote}")
    message = message.replace("\n", " ")
    if (
        nick
        and nick not in message
        and not any((message.startswith(c) for c in (">", "!", "/me", "ඞ")))
    ):
        message = f"{nick} {message}"
    if len(message) > 512:
        message = message[:511]
    return message
