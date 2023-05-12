import logging
from collections import deque
from datetime import datetime, timedelta
from dggbot import DGGBot, Message
from .config import BASE_CONVO, BASE_SUMMARY, read_config, save_config
from .gpt import generate_response, generate_summary, generate_solution
from .gpt.convo import delete_last_prompt
from .gpt.tokens import get_cost_from_tokens, count_tokens
from .dgg import format_dgg_message, will_trigger_bot_filter
from .dgg.moderation import SPAM_SEARCH_AMOUNT
from .request import request_debate, request_emotes, request_phrases

logger = logging.getLogger(__name__)


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
        self.message_history: deque[str] = deque(maxlen=SPAM_SEARCH_AMOUNT)
        self.cooldown = 45
        logger.info("Bot initialized")

    def is_admin(self, msg: Message) -> bool:
        return msg.nick in self.gpt_config["admins"]

    def update_history(self, msg: Message):
        self.message_history.append(msg.data)

    def pre_response_check(self, msg: Message) -> bool:
        if self.is_command(msg):
            logger.info("Check fail: Name and command used at the same time")
            return False
        if self.is_admin(msg):
            logger.info("Check pass: Admin requested")
            return True
        last_sent_delta = (datetime.now() - self.last_sent[0]).seconds
        if last_sent_delta < self.cooldown:
            remaining = self.cooldown - last_sent_delta
            logger.info(f"Check fail: On cooldown for another {remaining}s")
            return False
        if msg.nick == self.last_sent[1]:
            logger.info(f"Check fail: {msg.nick} requested twice")
            return False
        if msg.nick in self.gpt_config["blacklist"]:
            logger.info(f"Check fail: {msg.nick} is blacklisted")
            return False
        logger.info("Check pass")
        return True

    def respond_to_mention(self, msg: Message):
        logger.debug(f"Bot was mentioned:\n  {msg.nick}: {msg.data}")
        if not self.pre_response_check(msg):
            return
        self.last_sent = (datetime.now(), msg.nick)
        generate_response(msg, self.convo)
        formatted = format_dgg_message(self.convo[-1]["content"], msg.nick)
        if will_trigger_bot_filter(formatted, self.message_history):
            delete_last_prompt(self.convo)
            logger.info("Filter check failed, response cancelled")
            return
        logger.info("Sending response")
        msg.reply(formatted)

    def send_cost(self, msg: Message):
        logger.info(f"{msg.nick} used !cost")
        cost = get_cost_from_tokens()
        logger.info(f"Sending cost ({cost})")
        msg.reply(f"tena has lost ${cost} this month LULW")

    def send_summary(self, msg: Message, nick1: str, nick2: str, amount: str | int):
        logger.info(f"{msg.nick} used !summarize on {nick1} & {nick2}")
        self.last_sent = (datetime.now(), msg.nick)
        self.summaries = list(BASE_SUMMARY)
        debate = request_debate(nick1, nick2, amount)
        if isinstance(debate, str):
            msg.reply(debate)
            return
        generate_summary("\n".join(debate), self.summaries)
        logger.info("Sending summary")
        msg.reply(self.summaries[-1]["content"])

    def send_solution(self, msg: Message):
        logger.info(f"{msg.nick} used !solve")
        if self.summaries == list(BASE_SUMMARY):
            logger.info(f"No summary stored, response cancelled")
            msg.reply("I don't have a summary stored MMMM")
            return
        self.last_sent = (datetime.now(), msg.nick)
        generate_solution(self.summaries)
        logger.info("Sending solution")
        msg.reply(self.summaries[-1]["content"])
        self.summaries = list(BASE_SUMMARY)

    def clear_caches(self, msg: Message):
        logger.info(f"{msg.nick} used !clearcache")
        request_phrases.cache_clear()
        request_emotes.cache_clear()
        logger.info(f"Cleared caches for request_phrases & request_emotes")
        msg.reply(f"{msg.nick} PepOk cleared caches")

    def clear_convo(self, msg: Message):
        logger.info(f"{msg.nick} used !wipe")
        self.convo = list(BASE_CONVO)
        logger.info(f"Convo wiped, tokens at {count_tokens(self.convo)}")
        msg.reply(f"{msg.nick} PepOk wiped my memory FeelsDankMan")

    def clear_last_prompt(self, msg: Message):
        logger.info(f"{msg.nick} used !wipelast")
        delete_last_prompt(self.convo)
        msg.reply(f"{msg.nick} PepOk deleted the last prompt")

    def blacklist_add(self, msg: Message, name: str):
        logger.info(f"{msg.nick} used !bla")
        if name not in self.gpt_config["blacklist"]:
            self.gpt_config["blacklist"].append(name)
        save_config(self.gpt_config)
        logger.info(f'"{name}" was added to the blacklist')
        msg.reply(f"{msg.nick} PepOk {name} blacklisted")

    def blacklist_remove(self, msg: Message, name: str):
        logger.info(f"{msg.nick} used !blr")
        if name in self.gpt_config["blacklist"]:
            self.gpt_config["blacklist"].remove(name)
        save_config(self.gpt_config)
        logger.info(f'"{name}" was removed from the blacklist')
        msg.reply(f"{msg.nick} PepOk {name} unblacklisted")

    def change_cooldown(self, msg: Message, seconds: str):
        logger.info(f"{msg.nick} used !cd")
        try:
            self.cooldown = int(seconds)
        except ValueError:
            logger.info(f"Cooldown wasn't an integer")
            msg.reply(f"{msg.nick} that's not an integer MMMM")
            return
        logger.info(f"Cooldown changed to {self.cooldown}s")
        msg.reply(f"{msg.nick} PepOk changed the cooldown to {self.cooldown}s")
