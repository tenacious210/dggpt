from typing import Callable
from datetime import datetime, timedelta
import json

from dggbot import DGGBot, Message
import openai

from moderation import get_phrases, count_tokens, bad_word, bad_prompt

with open("config.json", "r") as cfg_json:
    cfg = json.loads(cfg_json.read())

admins = cfg["admins"]
blacklist: list = cfg["blacklist"]
bot = DGGBot(cfg["dgg_key"])
openai.api_key = cfg["openai_key"]

with open("system.txt", "r") as sys_txt:
    system = sys_txt.read()

with open("base.json", "r") as base_json:
    base = json.loads(base_json.read())

base_convo: list[dict] = lambda: [{"role": "system", "content": system}] + base
user_msg: dict = lambda data: {"role": "user", "content": data}
gpt_msg: dict = lambda data: {"role": "assistant", "content": data}

with open("convos.json", "r") as cnv_json:
    convos: dict[str, list] = json.loads(cnv_json.read())

for convo in convos.values():
    for i in reversed(base_convo()):
        convo.insert(0, i)

is_admin: Callable[[Message], bool] = lambda msg: msg.nick in admins
last_sent = datetime.now() - timedelta(seconds=60)


def save_files():
    to_cfg_json = {
        "dgg_key": cfg["dgg_key"],
        "openai_key": cfg["openai_key"],
        "admins": admins,
        "blacklist": blacklist,
    }
    to_cnv_json = {n: c[17:] for n, c in convos.items()}
    with open("config.json", "w") as cfg_json:
        cfg_json.write(json.dumps(to_cfg_json, indent=1))
    with open("convos.json", "w") as cnv_json:
        cnv_json.write(json.dumps(to_cnv_json, indent=1))


@bot.command()
@bot.check(is_admin)
def update_bans(msg: Message):
    get_phrases.cache_clear()
    msg.reply("Cleared the banned phrase cache")


@bot.command()
@bot.check(is_admin)
def clear(msg: Message, key: str):
    if key not in convos.keys():
        msg.reply("Invalid username")
    convos[key] = base_convo()
    save_files()
    msg.reply(f"Cleared convo for {key}")


@bot.command()
@bot.check(is_admin)
def bla(msg: Message, key: str):
    global blacklist
    blacklist.append(key)
    save_files()
    msg.reply(f"{key} blacklisted")


@bot.command()
@bot.check(is_admin)
def blr(msg: Message, key: str):
    global blacklist
    if key in blacklist:
        blacklist.remove(key)
    save_files()
    msg.reply(f"{key} unblacklisted")


@bot.event()
def on_mention(msg: Message):
    global last_sent
    if not is_admin(msg) and (datetime.now() - last_sent).seconds < 60:
        print("on cooldown")
        return
    if bad_word(msg.data) or bad_prompt(msg):
        print(f"bad msg: {msg.data}")
        return
    if msg.nick in blacklist:
        print(f"{msg.nick} blacklisted")
        return
    if not msg.nick in convos.keys():
        convos[msg.nick] = base_convo()
    convos[msg.nick].append(user_msg(msg.data))
    while count_tokens(convos[msg.nick]) > 4096:
        print("Trimming the prompt")
        convos[msg.nick].pop(1)
    print("Sending request to openai")
    rsp = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=convos[msg.nick])
    rsp = rsp["choices"][0]["message"]["content"]
    if not isinstance(rsp, str) or bad_word(rsp):
        convos[msg.nick].pop(-1)
        return
    convos[msg.nick].append(gpt_msg(rsp))
    bot.send(f"{msg.nick} {rsp}")
    last_sent = datetime.now()
    save_files()


# def test(question):
#     if not "tena" in convos.keys():
#         convos["tena"] = base_convo()
#     convos["tena"].append({"role": "user", "content": question})
#     print("Sending request to openai")
#     rsp = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=convos["tena"])
#     rsp = rsp["choices"][0]["message"]["content"]
#     convos["tena"].append(gpt_msg(rsp))
#     print(f"tena {rsp}")
#     save_files()


# if __name__ == "__main__":
#     while True:
#         test(input("Say something: "))

if __name__ == "__main__":
    bot.run_forever()
