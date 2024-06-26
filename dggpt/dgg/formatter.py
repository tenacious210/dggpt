# Formats responses to make them DGG appropriate
import re
import logging
from emoji import replace_emoji
from dggpt.request import request_emotes

logger = logging.getLogger(__name__)
PUNCS = tuple(". , ? ! ' \" > @ # ( ) - * :".split())


def format_dgg_message(message: str, nick: str = None) -> str:
    for emote in request_emotes():
        for punc in PUNCS:
            message = message.replace(f"{emote}{punc}", f"{emote} {punc}")
            message = message.replace(f"{punc}{emote}", f"{punc} {emote}")
    message = message.replace("\n", " ")
    message = replace_emoji(message, replace="")
    return message
