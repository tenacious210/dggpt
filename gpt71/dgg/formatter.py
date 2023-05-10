# Formats responses to make them DGG appropriate

import re
from gpt71.request import request_emotes


def format_dgg_message(message: str, nick: str = None) -> str:
    for emote in request_emotes():
        for punc in (".", ",", "?", "!", "'", '"', ">", "@", "#", "(", ")", "-", "*"):
            message = message.replace(f"{emote}{punc}", f"{emote} {punc}")
            message = message.replace(f"{punc}{emote}", f"{punc} {emote}")
    meme = "as an AI language model"
    message = re.sub(meme, f" BINGQILIN {meme}", message, flags=re.IGNORECASE)
    message = message.replace("\n", " ")
    if any((message.startswith(c) for c in (">", "!", "/me", "ඞ"))):
        return message
    elif nick and nick not in message:
        return f"{nick} {message}"
    else:
        return message
