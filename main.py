from typing import Callable
from datetime import datetime, timedelta

from dggbot import DGGBot, Message
import openai

from moderation import get_phrases, get_emotes, bad_prompt, bot_filter
from tools import read_cfg, save_cfg, base_history, count_tokens
from gpt import generate_response

cfg = read_cfg()
openai.api_key = cfg["openai_key"]
bot = DGGBot(cfg["dgg_key"])
bot._avoid_dupe = True

is_admin: Callable[[Message], bool] = lambda msg: msg.nick in cfg["admins"]

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
    if bad_prompt(msg) or bot_filter(msg.data):
        return False
    return True


def gpt_respond(msg: Message):
    global history, total_tokens, last_sent
    last_sent = (datetime.now(), msg.nick)
    rsp = generate_response(msg, history)
    if rsp[0] is None:
        return
    print(rsp[0])
    msg.reply(rsp[0])
    history = rsp[1]
    total_tokens += count_tokens(history)
    print(f"current tokens: {total_tokens}")


@bot.event()
def on_mention(msg: Message):
    if not pre_msg_check(msg):
        return
    gpt_respond(msg)


@bot.event()
def on_privmsg(msg: Message):
    if not is_admin(msg):
        return
    gpt_respond(msg)


@bot.command(cooldown=30)
def cost(msg: Message):
    amount = round(total_tokens / 1000 * 0.002, 4)
    msg.reply(f"tena has lost ${amount} so far LULW")


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
