import os
import logging
from dggbot import Message
from gpt71 import GPTBot

logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))
logging.getLogger("websocket").setLevel("CRITICAL")
for logger_name in ("dgg-bot", "openai", "urllib3"):
    logging.getLogger(logger_name).setLevel("INFO")

bot = GPTBot()


@bot.event()
def on_mention(msg: Message):
    bot.respond_to_mention(msg)


@bot.event()
def on_msg(msg: Message):
    bot.update_history(msg)


@bot.command(cooldown=30)
def cost(msg: Message):
    bot.send_cost(msg)


@bot.check(bot.is_admin)
@bot.command()
def summarize(msg: Message, nick1: str, nick2: str, amount: int = 10):
    bot.send_summary(msg, nick1, nick2, amount)


@bot.check(bot.is_admin)
@bot.command()
def solve(msg: Message):
    bot.send_solution(msg)


@bot.check(bot.is_admin)
@bot.command()
def clearcache(msg: Message):
    bot.clear_caches(msg)


@bot.check(bot.is_admin)
@bot.command()
def wipe(msg: Message):
    bot.clear_convo(msg)


@bot.check(bot.is_admin)
@bot.command()
def wipelast(msg: Message):
    bot.clear_last_prompt(msg)


@bot.check(bot.is_admin)
@bot.command()
def bla(msg: Message, name: str):
    bot.blacklist_add(msg, name)


@bot.check(bot.is_admin)
@bot.command()
def blr(msg: Message, name: str):
    bot.blacklist_remove(msg, name)


@bot.check(bot.is_admin)
@bot.command()
def cd(msg: Message, seconds: str, *_):
    bot.change_cooldown(msg, seconds)


if __name__ == "__main__":
    bot.run_forever()
