# Formats responses to make them DGG appropriate
import re
import logging
from gpt71.request import request_emotes

logger = logging.getLogger(__name__)


def format_dgg_message(message: str, nick: str = None) -> str:
    logger.debug(f'Before formatting:\n  "{message}"')
    for emote in request_emotes():
        for punc in (".", ",", "?", "!", "'", '"', ">", "@", "#", "(", ")", "-", "*"):
            message = message.replace(f"{emote}{punc}", f"{emote} {punc}")
            message = message.replace(f"{punc}{emote}", f"{punc} {emote}")
    meme = "as an AI language model"
    message = re.sub(meme, f" BINGQILIN {meme}", message, flags=re.IGNORECASE)
    message = message.replace("\n", " ")
    if (
        nick
        and nick not in message
        and not any((message.startswith(c) for c in (">", "!", "/me", "ඞ")))
    ):
        message = f"{nick} {message}"
    logger.debug(f'After formatting:\n  "{message}"')
    return message
