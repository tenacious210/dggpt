import logging
from collections import deque
from random import choice
from datetime import datetime, timedelta
from time import sleep
from dggbot import DGGBot, Message
from .config import (
    BASE_CONVO,
    BASE_SUMMARY,
    read_config,
    save_config,
    read_qd_record,
    write_qd_record,
)
from .gpt import generate_response, generate_summary, generate_solution
from .gpt.convo import delete_last_prompt, trim_tokens
from .gpt.tokens import get_cost_from_tokens, count_tokens
from .gpt.moderation import flag_check
from .dgg import format_dgg_message, will_trigger_bot_filter
from .dgg.moderation import SPAM_SEARCH_AMOUNT
from .request import (
    request_debate,
    request_emotes,
    request_phrases,
    request_charity_info,
    request_logs,
)

logger = logging.getLogger(__name__)


class DGGPTBot(DGGBot):
    """Base form of the bot with no commands"""

    def __init__(self):
        # gpt_config keys: "dgg_key", "openai_key", "admins", "blacklist"
        self.gpt_config = read_config()
        super().__init__(self.gpt_config["dgg_key"])
        self._avoid_dupe = True
        self.last_sent: datetime = datetime.now() - timedelta(seconds=60)
        self.convo: list[dict] = list(BASE_CONVO)
        self.summaries: list[dict] = list(BASE_SUMMARY)
        self.message_history: deque[str] = deque(maxlen=SPAM_SEARCH_AMOUNT)
        self.cooldown = 30
        self.max_tokens = 1400
        self.max_resp_tokens = 65
        self.quickdraw = {
            "waiting": False,
            "time_started": datetime.now(),
            "record": read_qd_record(),
        }
        logger.info(f"Bot initialized, prompt tokens: {count_tokens(self.convo)}")

    def send(self, data: str):
        logger.info(f"Sending message:\n{data}")
        if len(data) < 512:
            super().send(data)
        else:
            for substring in [data[i : i + 512] for i in range(0, len(data), 512)]:
                super().send(substring)
                sleep(2)

    def _convert_to_int(self, value):
        try:
            return int(value)
        except ValueError as e:
            self.send("that's not an integer MMMM")
            raise e

    def check_cooldown(self) -> int:
        last_sent_delta = (datetime.now() - self.last_sent).seconds
        remaining = self.cooldown - last_sent_delta
        return 0 if remaining < 0 else remaining

    def is_admin(self, msg: Message) -> bool:
        return msg.nick in self.gpt_config["admins"]

    def process_msg(self, nick: str, data: str):
        responses = (
            "me",
            "yup, that's me...",
            "I can't even deny it, that's me LULW",
            "me tbh...",
            "LITERALLY ME LULW",
            "me PepoTurkey",
            "me? hmmm.. yup, that's me",
        )
        self.message_history.append(data)
        if self.quickdraw["waiting"] and (data == "YEEHAW" or data == "PARDNER"):
            self.end_quickdraw(nick, data)
        if (
            data.startswith(">")
            and "next chatter" in data.lower()
            and not self.check_cooldown()
        ):
            self.send(choice(responses))
            self.last_sent = datetime.now()

    def respond_with_flags(self, nick: str, data: str):
        if flags := flag_check(data, raise_error=False):
            self.send(
                f"{nick} Congrats, your prompt was flagged"
                + f" by openai for: {', '.join(flags)} GIGACHAD"
            )
        self.last_sent = datetime.now()
        return flags

    def pre_response_check(self, nick: str, data: str) -> bool:
        if data.startswith(self.prefix):
            logger.info("Check fail: Name and command used at the same time")
            return False
        if self.convo[-1]["role"] == "user":
            logger.info("Check fail: Still waiting on the last completion")
            return False
        if nick in self.gpt_config["admins"]:
            if self.respond_with_flags(nick, data):
                logger.info(f"Check fail: Admin prompt was flagged")
                return False
            logger.info("Check pass: Admin requested")
            return True
        if remaining := self.check_cooldown():
            logger.info(f"Check fail: On cooldown for another {remaining}s")
            return False
        if nick in self.gpt_config["blacklist"]:
            logger.info(f"Check fail: {nick} is blacklisted")
            return False
        if self.respond_with_flags(nick, data):
            logger.info(f"Check fail: Prompt was flagged")
            return False
        logger.info("Check pass")
        return True

    def respond_to_mention(self, nick: str, data: str):
        logger.debug(f"Bot was mentioned:\n  {nick}: {data}")
        if not self.pre_response_check(nick, data):
            return
        self.last_sent = datetime.now()
        self.convo = trim_tokens(self.convo, self.max_tokens)
        generate_response(nick, data, self.convo, self.max_resp_tokens)
        formatted = format_dgg_message(self.convo[-1]["content"], nick)
        if will_trigger_bot_filter(formatted, self.message_history):
            logger.info("Filter check failed")
            self.send("nah, I don't feel like it MMMM")
            delete_last_prompt(self.convo)
            return
        self.send(formatted)

    def send_cost(self):
        logger.info(f"!cost was called")
        cost = get_cost_from_tokens()
        self.send(f"tena has lost ${cost} this month LULW")

    def send_summary(self, user1: str, user2: str, amount: str | int):
        logger.info(f"!summarize was used on {user1} & {user2}")
        self.last_sent = datetime.now()
        self.summaries = list(BASE_SUMMARY)
        debate = request_debate(user1, user2, amount)
        if isinstance(debate, str):
            self.send(debate)
            return
        generate_summary("\n".join(debate), self.summaries)
        self.send(self.summaries[-1]["content"])

    def send_solution(self):
        logger.info("!solve was called")
        if self.summaries == list(BASE_SUMMARY):
            self.send("I don't have a summary stored MMMM")
            return
        generate_solution(self.summaries)
        self.last_sent = datetime.now()
        self.send(self.summaries[-1]["content"])
        self.summaries = list(BASE_SUMMARY)

    def clear_caches(self):
        logger.info("!clearcache was called")
        request_phrases.cache_clear()
        request_emotes.cache_clear()
        self.send("PepOk cleared caches")

    def clear_convo(self):
        logger.info("!wipe was called")
        self.convo = list(BASE_CONVO)
        logger.info(f"Convo wiped, tokens at {count_tokens(self.convo)}")

    def clear_last_prompt(self):
        logger.info("!wipelast was called")
        delete_last_prompt(self.convo)
        self.send(f"PepOk deleted the last prompt")

    def blacklist_add(self, name: str):
        logger.info(f"!bla was used on {name}")
        if name not in self.gpt_config["blacklist"]:
            self.gpt_config["blacklist"].append(name)
        save_config(self.gpt_config)
        self.send(f"PepOk {name} blacklisted")

    def blacklist_remove(self, name: str):
        logger.info(f"!blr was used on {name}")
        if name in self.gpt_config["blacklist"]:
            self.gpt_config["blacklist"].remove(name)
        save_config(self.gpt_config)
        self.send(f"PepOk {name} unblacklisted")

    def change_cooldown(self, seconds: str):
        logger.info("!cd was used")
        self.cooldown = self._convert_to_int(seconds)
        self.send(f"PepOk changed the cooldown to {self.cooldown}s")

    def change_token_limit(self, limit: str):
        logger.info("!maxtokens was used")
        limit = self._convert_to_int(limit)
        base_tokens = count_tokens(list(BASE_CONVO))
        if limit > 3996 or limit < base_tokens:
            self.send(f"token limit must be between {base_tokens} and 3996 MMMM")
            return
        self.max_tokens = limit
        self.send(f"PepOk changed the max tokens to {self.max_tokens}")

    def change_resp_token_limit(self, limit: str):
        logger.info("!maxresp was used")
        limit = self._convert_to_int(limit)
        if limit < 1:
            self.send(f"must be positive MMMM")
            return
        self.max_resp_tokens = limit
        self.send(f"PepOk changed the max response length to {self.max_resp_tokens}")

    def start_quickdraw(self):
        logger.info("Starting quickdraw")
        self.send("> QUICKDRAW! PARDNER vs YEEHAW")
        self.quickdraw["waiting"] = True
        self.quickdraw["time_started"] = datetime.now()
        return

    def end_quickdraw(self, nick: str, data: str):
        logger.info(f"Quickdraw ended by {nick}")
        self.quickdraw["waiting"] = False
        delta = datetime.now() - self.quickdraw["time_started"]
        response_time = round(delta.total_seconds(), 2)
        ending_message = (
            f"{data} {nick} shot first! Response time: {response_time} seconds. "
        )
        if response_time < self.quickdraw["record"]["time"]:
            ending_message += "New record!"
            self.quickdraw["record"]["time"] = response_time
            self.quickdraw["record"]["holder"] = nick
            write_qd_record(self.quickdraw["record"])
        else:
            ending_message += f'Record time: {self.quickdraw["record"]["time"]} by {self.quickdraw["record"]["holder"]}'
        self.send(ending_message)

    def send_charity_info(self):
        logger.info(f"!malaria was called")
        charity_info = request_charity_info()
        response = (
            f'Total raised: ${charity_info["amount_raised"]} dggL '
            + f'Last donor: {charity_info["last_donor"]["name"]} dggL '
            + f'Amount: {charity_info["last_donor"]["amount"]} dggL '
            + f'Comment: {charity_info["last_donor"]["comment"]} dggL '
            + "www.againstmalaria.com/destiny"
        )
        if will_trigger_bot_filter(response, self.message_history):
            self.send("nah, I don't feel like it MMMM")
            return
        self.send(response)

    def send_logs(self, user: str, term: str = None):
        log_info = request_logs(user, term)
        if term:
            response = f'Results: {log_info["hits"]} {log_info["log_link"]}'
        else:
            response = f'Last seen {log_info["last_seen"]} ago {log_info["log_link"]}'
        if will_trigger_bot_filter(response, self.message_history):
            self.send("nah, I don't feel like it MMMM")
            return
        self.send(response)
