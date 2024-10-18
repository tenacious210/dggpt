# Formats responses to make them TTS appropriate
import re
import logging
from emoji import replace_emoji
from dggpt.request import request_emotes

logger = logging.getLogger(__name__)


def format_tts_message(message: str, nick: str = None) -> str:
    for emote in request_emotes():
        if message.endswith(emote):
            message.rstrip(emote)
    message = message.replace("\n", " ")
    message = replace_emoji(message, replace="")
    return message
