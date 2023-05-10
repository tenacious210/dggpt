from datetime import datetime, timedelta
from dggbot import DGGBot, Message
from .config import BASE_CONVO, BASE_SUMMARY, read_config, save_config
from .gpt import generate_response, generate_summary, generate_solution
from .gpt.convo import delete_last_prompt
from .gpt.tokens import get_cost_from_tokens
from .dgg import format_dgg_message, bot_filter
from .request import request_debate, request_emotes, request_phrases


class GPTBot(DGGBot):
    """Base form of the bot with no commands"""

    def __init__(self):
        # gpt_config keys: "dgg_key", "openai_key", "admins", "blacklist"
        self.gpt_config = read_config()
        super().__init__(self.gpt_config["dgg_key"])
        self._avoid_dupe = True
        self.last_sent: tuple[datetime, str] = (
            datetime.now() - timedelta(seconds=60),
            "tena",
        )
        self.convo: list[dict] = list(BASE_CONVO)
        self.summaries: list[dict] = list(BASE_SUMMARY)
        self.cooldown = 45

    def is_admin(self, msg: Message) -> bool:
        return msg.nick in self.gpt_config["admins"]

    def pre_response_check(self, msg: Message) -> bool:
        if self.is_admin(msg):
            return True
        if (datetime.now() - self.last_sent[0]).seconds < self.cooldown:
            return False
        if msg.nick == self.last_sent[1]:
            return False
        if msg.nick in self.gpt_config["blacklist"]:
            return False
        return True

    def respond_to_mention(self, msg: Message):
        if not self.pre_response_check(msg):
            return
        self.last_sent = (datetime.now(), msg.nick)
        generate_response(msg, self.convo)
        if bot_filter(self.convo[-1]["content"]):
            delete_last_prompt(self.convo)
            return
        msg.reply(format_dgg_message(self.convo[-1]["content"], msg.nick))

    def send_cost(self, msg: Message):
        msg.reply(f"tena has lost ${get_cost_from_tokens()} this month LULW")

    def send_summary(self, msg: Message, nick1: str, nick2: str, amount: int):
        self.summaries = list(BASE_SUMMARY)
        debate = request_debate(nick1, nick2, amount)
        generate_summary(debate, self.summaries)
        msg.reply(self.summaries[-1]["content"])

    def send_solution(self, msg: Message):
        if self.summaries == list(BASE_SUMMARY):
            msg.reply("I don't have a summary stored MMMM")
            return
        generate_solution(self.summaries)
        msg.reply(self.summaries[-1]["content"])
        self.summaries = list(BASE_SUMMARY)

    def clear_caches(self, msg: Message):
        request_phrases.cache_clear()
        request_emotes.cache_clear()
        msg.reply(f"{msg.nick} PepOk cleared caches")

    def clear_convo(self, msg: Message):
        self.convo = list(BASE_CONVO)
        msg.reply(f"{msg.nick} PepOk wiped my memory FeelsDankMan")

    def clear_last_prompt(self, msg: Message):
        delete_last_prompt(self.convo)
        msg.reply(f"{msg.nick} PepOk deleted the last prompt")

    def blacklist_add(self, msg: Message, name: str):
        if name not in self.gpt_config["blacklist"]:
            self.gpt_config["blacklist"].append(name)
        save_config(self.gpt_config)
        msg.reply(f"{msg.nick} PepOk {name} blacklisted")

    def blacklist_remove(self, msg: Message, name: str):
        if name in self.gpt_config["blacklist"]:
            self.gpt_config["blacklist"].remove(name)
        save_config(self.gpt_config)
        msg.reply(f"{msg.nick} PepOk {name} unblacklisted")

    def change_cooldown(self, msg: Message, seconds: str):
        try:
            self.cooldown = int(seconds)
        except ValueError:
            msg.reply(f"{msg.nick} that's not an integer MMMM")
            return
        msg.reply(f"{msg.nick} PepOk changed the cooldown to {seconds}s")
