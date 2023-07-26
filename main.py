import os
import logging
from dggbot import Message
from dggpt import DGGPTBot

logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))
logging.getLogger("websocket").setLevel("CRITICAL")
for logger_name in ("dgg-bot", "openai", "urllib3"):
    logging.getLogger(logger_name).setLevel("INFO")

bot = DGGPTBot()


@bot.event()
def on_mention(msg: Message):
    bot.respond_to_mention(msg.nick, msg.data)


@bot.event()
def on_msg(msg: Message):
    bot.update_history(msg.data)
    if bot.quickdraw["waiting"] and (msg.data == "YEEHAW" or msg.data == "PARDNER"):
        bot.end_quickdraw(msg.nick, msg.data)


@bot.command(cooldown=30)
def cost(msg: Message):
    bot.send_cost()


@bot.command(cooldown=120)
def malaria(msg: Message):
    bot.send_charity_info()


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
def maxtokens(msg: Message, limit: str, *_):
    bot.change_token_limit(limit)


@bot.check(bot.is_admin)
@bot.command()
def quickdraw(msg: Message):
    bot.start_quickdraw()


if __name__ == "__main__":
    bot.run_forever()
