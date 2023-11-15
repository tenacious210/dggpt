### Monkey patches
import re
from dggbot.user import User


def _name_regex(self) -> re.Pattern:
    return re.compile(rf"\b{self.name}\b", re.IGNORECASE)


User._name_regex = _name_regex
###

import os
import logging
from dggbot import Message, PrivateMessage
from dggpt import DGGPTBot

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
logging.getLogger("websocket").setLevel("CRITICAL")
for logger_name in ("dgg-bot", "openai", "urllib3"):
    logging.getLogger(logger_name).setLevel("INFO")

bot = DGGPTBot()


@bot.event()
def on_mention(msg: Message):
    bot.respond_to_mention(msg.nick, msg.data)


@bot.event()
def on_msg(msg: Message):
    bot.process_msg(msg.nick, msg.data)


@bot.event()
def on_privmsg(msg: Message):
    bot.process_privmsg(msg.nick, msg.data)


@bot.command(cooldown=30)
def search(msg: Message, user: str, term: str = None):
    bot.send_logs(user, term)


@bot.command(cooldown=30)
def cost(msg: Message):
    bot.send_cost()


@bot.command(cooldown=120)
def malaria(msg: Message):
    bot.send_charity_info()


@bot.check(bot.is_admin)
@bot.command(["send", "s"])
def repeat(msg: Message):
    bot.repeat(msg.data)


@bot.check(bot.is_admin)
@bot.command()
def summarize(msg: Message, user1: str, user2: str, amount: str = "10"):
    bot.send_summary(user1, user2, amount)


@bot.check(bot.is_admin)
@bot.command()
def solve(msg: Message):
    bot.send_solution()


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
def wipelast(msg: Message):
    bot.clear_last_prompt()


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
def maxtokens(msg: Message, limit: str, *_):
    bot.change_token_limit(limit)


@bot.check(bot.is_admin)
@bot.command()
def quickdraw(msg: Message):
    bot.start_quickdraw()


@bot.check(bot.is_admin)
@bot.command()
def simonsays(msg: Message):
    bot.start_simonsays()


if __name__ == "__main__":
    bot.run_forever()
