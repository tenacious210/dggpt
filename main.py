from typing import Callable
from datetime import datetime, timedelta

from dggbot import DGGBot, Message
import openai

from moderation import get_phrases, get_emotes, bad_word, bad_prompt
from tools import read_cfg, save_cfg, base_history, count_tokens

cfg = read_cfg()
openai.api_key = cfg["openai_key"]
bot = DGGBot(cfg["dgg_key"])
bot._avoid_dupe = True

is_admin: Callable[[Message], bool] = lambda msg: msg.nick in cfg["admins"]
is_owner: Callable[[Message], bool] = lambda msg: msg.nick in ("tena")
user_msg: dict = lambda data: {"role": "user", "content": data}
gpt_msg: dict = lambda data: {"role": "assistant", "content": data}

last_sent: tuple[datetime, str] = (datetime.now() - timedelta(seconds=60), "obamna")
history = base_history()
print(f"base tokens: {count_tokens(history)}")
cooldown = 45
total_tokens = 0


def pre_msg_check(msg: Message):
    if is_admin(msg):
        return True
    if (datetime.now() - last_sent[0]).seconds < cooldown:
        print("on cooldown")
        return False
    if msg.nick == last_sent[1]:
        print("same user requested")
        return False
    if msg.nick in cfg["blacklist"]:
        print(f"{msg.nick} is blacklisted")
        return False
    if bad_word(msg.data) or bad_prompt(msg):
        return False
    return True


def format_response(rsp: str, nick: str):
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


@bot.command(cooldown=30)
def cost(msg: Message):
    amount = round(total_tokens / 1000 * 0.002, 4)
    msg.reply(f"tena has lost ${amount} so far LULW")


@bot.event()
def on_mention(msg: Message):
    global last_sent, total_tokens
    if not pre_msg_check(msg):
        return
    history.append(user_msg(f"{msg.nick}: {msg.data}"))
    while count_tokens(history) >= 1250:
        del history[15:17]
        print(f"trimmed prompt to {count_tokens(history)} tokens")
    print("Sending request to openai")
    last_sent = (datetime.now(), msg.nick)
    rsp = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=history)
    rsp = rsp["choices"][0]["message"]["content"]
    if not isinstance(rsp, str) or bad_word(rsp):
        print(f"{msg.nick}'s prompt made an invalid response:\n{rsp}")
        del history[-1]
        return
    history.append(gpt_msg(rsp))
    print(rsp)
    msg.reply(format_response(rsp, msg.nick))
    total_tokens += count_tokens(history)
    print(f"current tokens: {total_tokens}")


@bot.check(is_admin)
@bot.command()
def cc(msg: Message):
    get_phrases.cache_clear()
    get_emotes.cache_clear()
    msg.reply(f"{msg.nick} PepOk cleared caches")


@bot.check(is_admin)
@bot.command()
def wipe(msg: Message):
    global history
    history = base_history()
    msg.reply(f"{msg.nick} PepOk wiped history, tokens now at {count_tokens(history)}")


@bot.check(is_admin)
@bot.command()
def tokens(msg: Message):
    msg.reply(f"{msg.nick} PepoTurkey current tokens: {count_tokens(history)}")


@bot.check(is_admin)
@bot.command()
def bla(msg: Message, name: str, *_):
    if name not in cfg["blacklist"]:
        cfg["blacklist"].append(name)
    save_cfg(cfg)
    msg.reply(f"{msg.nick} PepOk {name} blacklisted")


@bot.check(is_admin)
@bot.command()
def blr(msg: Message, key: str, *_):
    if key in cfg["blacklist"]:
        cfg["blacklist"].remove(key)
    save_cfg(cfg)
    msg.reply(f"{msg.nick} PepOk {key} unblacklisted")


@bot.check(is_admin)
@bot.command()
def cd(msg: Message, seconds: str, *_):
    global cooldown
    try:
        cooldown = int(seconds)
    except ValueError:
        msg.reply(f"{msg.nick} that's not an integer MMMM")
        return
    msg.reply(f"{msg.nick} PepOk changed the cooldown to {cooldown}s")


if __name__ == "__main__":
    bot.run_forever()
