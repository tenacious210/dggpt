import json
import re
from threading import Timer
from datetime import datetime


from dggbot import DGGBot, Message
import requests
import openai


with open("config.json", "r") as cfg_json:
    cfg = json.loads(cfg_json.read())

with open("system.txt", "r") as sys_txt:
    system = sys_txt.read()

bot = DGGBot(cfg["dgg_key"])
openai.api_key = cfg["openai_key"]

convos = {"tena": [{"role": "system", "content": system}]}
# v_phrases = requests.get("https://vyneer.me/tools/phrases").json()
# ban_phrases = [re.compile(p["phrase"]) for p in v_phrases]


("tena", "tena_", "Cake", "mori", "Fritz", "Destiny", "vyneer")


@bot.event()
def on_mention(msg: Message):
    if not msg.nick in ("tena", "tena_", "Cake", "mori", "Fritz", "Destiny", "vyneer"):
        return
    mod = openai.Moderation.create(input=msg.data)
    if mod["results"][0]["flagged"]:
        print(f"This prompt was flagged by openai: \n {msg.nick}: {msg.data}")
        return
    if not msg.nick in convos.keys():
        convos[msg.nick] = [{"role": "system", "content": system}]
    convos[msg.nick].append({"role": "user", "content": msg.data})
    print("Sending request to openai")
    rsp = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=convos[msg.nick])
    rsp = rsp["choices"][0]["message"]["content"]
    # for phrase in ban_phrases:
    #     if re.search(phrase, rsp):
    #         convos[msg.nick].pop()
    #         return
    convos[msg.nick].append({"role": "assistant", "content": rsp})
    bot.send(f"{msg.nick} {rsp}")


if __name__ == "__main__":
    bot.run_forever()
