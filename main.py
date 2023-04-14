from typing import Callable
from datetime import datetime, timedelta

from dggbot import DGGBot, Message
import openai

from moderation import get_phrases, get_emotes, bad_word, bad_prompt
from tools import read_cfg, save_cfg, base_convo, count_tokens

cfg = read_cfg()
openai.api_key = cfg["openai_key"]
bot = DGGBot(cfg["dgg_key"])
bot._avoid_dupe = True

is_admin: Callable[[Message], bool] = lambda msg: msg.nick in cfg["admins"]
is_owner: Callable[[Message], bool] = lambda msg: msg.nick in ("tena")
user_msg: dict = lambda data: {"role": "user", "content": data}
gpt_msg: dict = lambda data: {"role": "assistant", "content": data}

last_sent: tuple[datetime, str] = (datetime.now() - timedelta(seconds=60), "obamna")
convos: dict[str, list[dict]] = {}
cooldown = 30


def pre_msg_check(msg: Message):
    if bad_word(msg.data) or bad_prompt(msg):
        return False
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
    if not msg.nick in convos.keys():
        convos[msg.nick] = base_convo()
    if len(convos[msg.nick]) >= 2:
        print(f"sent to {msg.nick} twice already")
        return False
    return True


@bot.event()
@bot.check(pre_msg_check)
def on_mention(msg: Message):
    global last_sent
    convos[msg.nick].append(user_msg(msg.data))
    while count_tokens(convos[msg.nick]) > 4096:
        print("Trimming the prompt")
        convos[msg.nick].pop(1)
    print("Sending request to openai")
    last_sent = (datetime.now(), msg.nick)
    rsp = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=convos[msg.nick])
    rsp = rsp["choices"][0]["message"]["content"]
    if not isinstance(rsp, str) or bad_word(rsp):
        print(rsp)
        convos[msg.nick].pop(-1)
        return
    convos[msg.nick].append(gpt_msg(rsp))
    for emote in get_emotes():
        for punc in (".", ",", "?", "!", "'", '"', ">"):
            rsp = rsp.replace(f"{emote}{punc}", f"{emote} {punc}")
            rsp = rsp.replace(f"{punc}{emote}", f"{punc} {emote}")
    rsp = rsp.replace("As an AI language model", " BINGQILIN As an AI language model")
    rsp = rsp.replace("as an AI language model", " BINGQILIN as an AI language model")
    if ">" in rsp:
        msg.reply(f"> {rsp}")
    elif "/me" in rsp:
        msg.reply(f"/me {rsp}")
    else:
        msg.reply(f"{msg.nick} {rsp}")
    print(rsp)


@bot.command()
@bot.check(is_admin)
def cc(msg: Message):
    get_phrases.cache_clear()
    get_emotes.cache_clear()
    msg.reply(f"{msg.nick} PepOk cleared caches")


@bot.command()
@bot.check(is_admin)
def clear(msg: Message, name: str, *_):
    if name not in convos.keys():
        msg.reply(f"{msg.nick} I have no convo with {name} MMMM")
    convos[name] = base_convo()
    msg.reply(f"{msg.nick} PepOk cleared convo for {name}")


@bot.command()
@bot.check(is_admin)
def bla(msg: Message, name: str, *_):
    if name not in cfg["blacklist"]:
        cfg["blacklist"].append(name)
    save_cfg(cfg)
    msg.reply(f"{msg.nick} PepOk {name} blacklisted")


@bot.command()
@bot.check(is_admin)
def blr(msg: Message, key: str, *_):
    if key in cfg["blacklist"]:
        cfg["blacklist"].remove(key)
    save_cfg(cfg)
    msg.reply(f"{msg.nick} PepOk {key} unblacklisted")


@bot.command()
@bot.check(is_admin)
def cd(msg: Message, seconds: str, *_):
    global cooldown
    try:
        cooldown = int(seconds)
    except ValueError:
        msg.reply(f"{msg.nick} that's not an integer MMMM")
        return
    msg.reply(f"{msg.nick} PepOk changed the cooldown to {cooldown}s")


# if __name__ == "__main__":
#     bot.run_forever()


def test(question):
    if not "tena" in convos.keys():
        convos["tena"] = base_convo()
    convos["tena"].append(user_msg(question))
    print(convos)
    print("Sending request to openai")
    rsp = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=convos["tena"])
    rsp = rsp["choices"][0]["message"]["content"]
    convos["tena"].append(gpt_msg(rsp))
    print(f"tena {rsp}")


if __name__ == "__main__":
    while True:
        test(input("Say something: "))
