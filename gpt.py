import openai
from dggbot import Message

from moderation import bot_filter, get_emotes
from tools import count_tokens

user_msg: dict = lambda data: {"role": "user", "content": data}
gpt_msg: dict = lambda data: {"role": "assistant", "content": data}


def format_response(rsp: str, nick: str) -> str:
    for emote in get_emotes():
        for punc in (".", ",", "?", "!", "'", '"', ">", "@", "#", "(", ")", "-", "*"):
            rsp = rsp.replace(f"{emote}{punc}", f"{emote} {punc}")
            rsp = rsp.replace(f"{punc}{emote}", f"{punc} {emote}")
    rsp = rsp.replace("As an AI language model", " BINGQILIN As an AI language model")
    rsp = rsp.replace("as an AI language model", " BINGQILIN as an AI language model")
    rsp = rsp.replace("\n", "")
    if any((rsp.startswith(c) for c in (">", "!", "/me"))):
        return rsp
    elif nick not in rsp:
        return f"{nick} {rsp}"
    else:
        return rsp


def generate_response(msg: Message, history: list) -> tuple[str, list]:
    history.append(user_msg(f"{msg.nick}: {msg.data}"))
    while count_tokens(history) >= 1250:
        del history[15:17]
        print(f"trimmed prompt to {count_tokens(history)} tokens")
    print("Sending request to openai")
    rsp = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=history)
    rsp = rsp["choices"][0]["message"]["content"]
    if not isinstance(rsp, str) or bot_filter(rsp):
        print(f"{msg.nick}'s prompt made an invalid response:\n{rsp}")
        return None, None
    history.append(gpt_msg(rsp))
    return format_response(rsp, msg.nick), history
