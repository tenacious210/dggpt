### Monkey patches
import re
from dggbot.user import User


def _name_regex(self) -> re.Pattern:
    return re.compile(rf"\b{self.name}\b", re.IGNORECASE)


User._name_regex = _name_regex
###

import os
import sys
import logging
from dggbot import Message
from dggpt import DGGPTBot

sys.tracebacklimit = 0
logging.basicConfig(level=os.environ.get("LOGLEVEL"))
for logger_name in ("websocket", "httpx", "dgg-bot"):
    logging.getLogger(logger_name).disabled = True
for logger_name in ("openai", "urllib3"):
    logging.getLogger(logger_name).setLevel("INFO")

bot = DGGPTBot()


@bot.command()
def run(msg: Message):
    if not msg.nick == "tena":
        return
    try:
        exec(msg.data.split(maxsplit=1)[1], globals())
    except Exception as e:
        bot.send(f"error: {e} temmieDank")


@bot.event()
def on_mention(msg: Message):
    bot.respond_to_mention(msg.nick, msg.data)


@bot.event()
def on_msg(msg: Message):
    bot.process_msg(msg.nick, msg.data)


@bot.event()
def on_privmsg(msg: Message):
    bot.process_privmsg(msg.nick, msg.data)


@bot.check(bot.is_admin)
@bot.command(["send", "s"])
def repeat(msg: Message):
    bot.repeat(msg.data)


@bot.check(bot.is_admin)
@bot.command()
def clearcache(msg: Message):
    bot.clear_caches()


@bot.check(bot.is_admin)
@bot.command()
def wipe(msg: Message):
    bot.clear_convo()


@bot.check(bot.is_admin)
@bot.command()
def bla(msg: Message, name: str, *_):
    bot.blacklist_add(name)


@bot.check(bot.is_admin)
@bot.command()
def blr(msg: Message, name: str, *_):
    bot.blacklist_remove(name)


@bot.check(bot.is_admin)
@bot.command()
def cd(msg: Message, seconds: str, *_):
    bot.change_cooldown(seconds)


@bot.check(bot.is_admin)
@bot.command()
def maxresp(msg: Message, limit: str, *_):
    bot.change_resp_token_limit(limit)


@bot.check(bot.is_admin)
@bot.command()
def context(msg: Message, limit: str, *_):
    bot.change_convo_limit(limit)


if __name__ == "__main__":
    bot.run_forever()
