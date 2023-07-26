import logging
from collections import deque
from datetime import datetime, timedelta
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
)

logger = logging.getLogger(__name__)


class DGGPTBot(DGGBot):
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
        self.cooldown = 30
        self.max_tokens = 1400
        self.max_resp_tokens = 65
        self.quickdraw = {
            "waiting": False,
            "time_started": datetime.now(),
            "record": read_qd_record(),
        }
        logger.info(f"Bot initialized, prompt tokens: {count_tokens(self.convo)}")

    def is_admin(self, msg: Message) -> bool:
        return msg.nick in self.gpt_config["admins"]

    def update_history(self, data: str):
        self.message_history.append(data)

    def respond_with_flags(self, nick: str, data: str):
        if flags := flag_check(data, raise_error=False):
            self.send(
                f"{nick} Congrats, your prompt was flagged"
                + f" by openai for: {', '.join(flags)} GIGACHAD"
            )
        self.last_sent = (datetime.now(), nick)
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
        last_sent_delta = (datetime.now() - self.last_sent[0]).seconds
        if last_sent_delta < self.cooldown:
            remaining = self.cooldown - last_sent_delta
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
        self.last_sent = (datetime.now(), nick)
        self.convo = trim_tokens(self.convo, self.max_tokens)
        generate_response(nick, data, self.convo)
        formatted = format_dgg_message(self.convo[-1]["content"], nick)
        if will_trigger_bot_filter(formatted, self.message_history):
            delete_last_prompt(self.convo)
            logger.info("Filter check failed, response cancelled")
            return
        logger.info("Sending response")
        self.send(formatted)

    def send_cost(self):
        logger.info(f"!cost was called")
        cost = get_cost_from_tokens()
        logger.info(f"Sending cost ({cost})")
        self.send(f"tena has lost ${cost} this month LULW")

    def send_summary(self, user1: str, user2: str, amount: str | int):
        logger.info(f"!summarize was used on {user1} & {user2}")
        self.last_sent = (datetime.now(), "")
        self.summaries = list(BASE_SUMMARY)
        debate = request_debate(user1, user2, amount)
        if isinstance(debate, str):
            self.send(debate)
            return
        generate_summary("\n".join(debate), self.summaries)
        logger.info("Sending summary")
        self.send(self.summaries[-1]["content"])

    def send_solution(self):
        logger.info("!solve was called")
        if self.summaries == list(BASE_SUMMARY):
            logger.info("No summary stored, response cancelled")
            self.send("I don't have a summary stored MMMM")
            return
        generate_solution(self.summaries)
        self.last_sent = (datetime.now(), "")
        logger.info("Sending solution")
        self.send(self.summaries[-1]["content"])
        self.summaries = list(BASE_SUMMARY)

    def clear_caches(self):
        logger.info("!clearcache was called")
        request_phrases.cache_clear()
        request_emotes.cache_clear()
        logger.info(f"Cleared caches for request_phrases & request_emotes")
        self.send("PepOk cleared caches")

    def clear_convo(self):
        logger.info("!wipe was called")
        self.convo = list(BASE_CONVO)
        logger.info(f"Convo wiped, tokens at {count_tokens(self.convo)}")
        self.send("PepOk wiped my memory FeelsDankMan")

    def clear_last_prompt(self):
        logger.info("!wipelast was called")
        delete_last_prompt(self.convo)
        self.send(f"PepOk deleted the last prompt")

    def blacklist_add(self, name: str):
        logger.info(f"!bla was used on {name}")
        if name not in self.gpt_config["blacklist"]:
            self.gpt_config["blacklist"].append(name)
        save_config(self.gpt_config)
        logger.info(f'"{name}" was added to the blacklist')
        self.send(f"PepOk {name} blacklisted")

    def blacklist_remove(self, name: str):
        logger.info(f"!blr was used on {name}")
        if name in self.gpt_config["blacklist"]:
            self.gpt_config["blacklist"].remove(name)
        save_config(self.gpt_config)
        logger.info(f'"{name}" was removed from the blacklist')
        self.send(f"PepOk {name} unblacklisted")

    def change_cooldown(self, seconds: str):
        logger.info("!cd was used")
        try:
            self.cooldown = int(seconds)
        except ValueError:
            logger.info(f"Cooldown wasn't an integer")
            self.send("that's not an integer MMMM")
            return
        logger.info(f"Cooldown changed to {self.cooldown}s")
        self.send(f"PepOk changed the cooldown to {self.cooldown}s")

    def change_token_limit(self, limit: str):
        logger.info("!maxtokens was used")
        try:
            limit = int(limit)
        except ValueError:
            logger.info(f"Token amount wasn't an integer")
            self.send("that's not an integer MMMM")
            return
        base_tokens = count_tokens(list(BASE_CONVO))
        if limit > 3996 or limit < base_tokens:
            logger.info(f"Token amount was outside the limits")
            self.send(f"token limit must be between {base_tokens} and 3996 MMMM")
            return
        self.max_tokens = limit
        logger.info(f"Max tokens changed to {self.max_tokens}")
        self.send(f"PepOk changed the max tokens to {self.max_tokens}")

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
        self.send(
            f'Total raised: ${charity_info["amount_raised"]} dggL '
            + f'Last donor: {charity_info["last_donor"]["name"]} dggL '
            + f'Amount: {charity_info["last_donor"]["amount"]} dggL '
            + f'Comment: {charity_info["last_donor"]["comment"]} dggL '
            + "www.againstmalaria.com/destiny"
        )
