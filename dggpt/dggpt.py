import logging
from threading import Thread
from collections import deque, Counter
from random import choice
from datetime import datetime, timedelta
from time import sleep
from dggbot import DGGBot, DGGLive, Message, StreamInfo
from .config import (
    BASE_CONVO,
    BASE_SUMMARY,
    read_config,
    save_config,
    read_qd_record,
    write_qd_record,
)
from .gpt import generate_response, generate_summary, generate_solution, generate_image
from .gpt.convo import delete_last_prompt, trim_tokens
from .gpt.tokens import get_cost_from_tokens, count_tokens
from .gpt.moderation import flag_check
from .tts import generate_tts
from .tts.formatter import format_tts_message
from .dgg import format_dgg_message, will_trigger_bot_filter
from .dgg.moderation import SPAM_SEARCH_AMOUNT
from .request import (
    request_debate,
    request_emotes,
    request_phrases,
    request_latest_log,
)

logger = logging.getLogger(__name__)


class DGGPTBot(DGGBot):
    """Base form of the bot with no commands"""

    def __init__(self):
        # gpt_config keys: "dgg_key", "openai_key", "admins", "blacklist"
        self.gpt_config = read_config()
        super().__init__(self.gpt_config["dgg_key"])
        self._avoid_dupe = True
        self.stream_is_live: bool = False
        self.tts_mode: bool = False
        self.last_sent: datetime = datetime.now() - timedelta(seconds=60)
        self.convo: list[dict] = list(BASE_CONVO)
        self.summaries: list[dict] = list(BASE_SUMMARY)
        self.message_history: deque[str] = deque(maxlen=SPAM_SEARCH_AMOUNT)
        self.cooldown = 30
        self.max_tokens = 2500
        self.max_resp_tokens = 80
        self.simonsays = {
            "emote": None,
            "winners": [],
            "time_started": datetime.now(),
        }
        self.quickdraw = {
            "waiting": False,
            "time_started": datetime.now(),
            "record": read_qd_record(),
        }
        Thread(target=self.update_live_status).start()
        logger.info(f"Bot initialized, prompt tokens: {count_tokens(self.convo)}")

    def send(self, data: str):
        logger.debug(f"Sending message:\n{data}")
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

    def process_privmsg(self, nick: str, data: str):
        logger.info(f"Got whispered: {nick}: {data}")
        if nick in self.gpt_config["admins"]:
            self.respond_to_mention(nick, data)
            sleep(3)
            self.send_privmsg(nick, "PepOk")

    def process_msg(self, nick: str, data: str):
        self.message_history.append(data)
        if self.quickdraw["waiting"] and (data == "YEEHAW" or data == "PARDNER"):
            self.end_quickdraw(nick, data)
        if self.simonsays["emote"] and data == self.simonsays["emote"]:
            self.end_simonsays(nick)

    def respond_with_flags(self, nick: str, data: str):
        if flags := flag_check(data, raise_error=False):
            response = (
                f"{nick} Congrats, your prompt was flagged"
                + f" by openai for: {', '.join(flags)} GIGACHAD"
            )
            if "sexual/minors" in response:
                response = response.replace("GIGACHAD", "HUH")
            if will_trigger_bot_filter(response, self.message_history):
                self.send_filter_response(nick)
            else:
                self.send(response)
        self.last_sent = datetime.now()
        return flags

    def pre_response_check(self, nick: str, data: str) -> bool:
        if data.startswith(self.prefix):
            logger.debug("Check fail: Name and command used at the same time")
            return False
        if self.convo[-1]["role"] == "user":
            logger.warning("Check fail: Still waiting on the last completion")
            return False
        if "#kick/gpt71" in data:
            logger.debug(f"Check fail: Name used in Kick embed")
            return False
        if nick in self.gpt_config["admins"]:
            if nick == "tena" or nick == "Destiny":
                logger.debug("Check pass: Owner requested")
                return True
            if self.check_cooldown() and self.tts_mode:
                logger.debug(f"Check fail: Admin prompt on cooldown during tts mode")
                return False
            if self.respond_with_flags(nick, data):
                logger.debug(f"Check fail: Admin prompt was flagged")
                return False
            logger.debug("Check pass: Admin requested")
            return True
        if self.stream_is_live:
            logger.debug("Check fail: Stream is live")
            return False
        if remaining := self.check_cooldown():
            logger.debug(f"Check fail: On cooldown for another {remaining}s")
            return False
        if nick in self.gpt_config["blacklist"]:
            logger.debug(f"Check fail: {nick} is blacklisted")
            return False
        if self.respond_with_flags(nick, data):
            logger.debug(f"Check fail: Prompt was flagged")
            return False
        logger.debug("Check pass")
        return True

    def send_filter_response(self, user: str):
        responses = (
            f"{user} nah, I don't feel like it MMMM",
            f"/me ignores {user}'s request TF",
            f"/me doesn't understand {user}'s request temmieDank",
            f"/me ignores {user} MMMM",
        )
        self.send(choice(responses))
        return

    def respond_to_mention(self, nick: str, data: str):
        logger.debug(f"Bot was mentioned:\n  {nick}: {data}")
        if not self.pre_response_check(nick, data):
            return
        self.last_sent = datetime.now()
        self.convo = trim_tokens(self.convo, self.max_tokens)
        generate_response(nick, data, self.convo, self.max_resp_tokens)
        if self.tts_mode:
            resp = self.convo[-1]["content"]
            if nick.lower() not in resp:
                formatted = f"{nick}, {resp}"
            resp = format_tts_message(resp)
            generate_tts(resp)
        else:
            formatted = format_dgg_message(self.convo[-1]["content"], nick)
            if will_trigger_bot_filter(formatted, self.message_history):
                logger.debug("Filter check failed")
                self.send_filter_response(nick)
                delete_last_prompt(self.convo)
                return
            if formatted.isspace() or formatted == "":
                self.send_filter_response(nick)
                return
            self.send(formatted)

    def respond_to_log(self, nick: str):
        logger.debug("!respond was called")
        log_info = request_latest_log(nick)
        self.last_sent = datetime.now()
        self.convo = trim_tokens(self.convo, self.max_tokens)
        generate_response(nick, log_info["text"], self.convo, self.max_resp_tokens)
        formatted = format_dgg_message(self.convo[-1]["content"], nick)
        if nick.lower() not in formatted.lower():
            formatted = f"{nick} {formatted}"
        if will_trigger_bot_filter(formatted, self.message_history):
            logger.debug("Filter check failed")
            self.send_filter_response(nick)
            delete_last_prompt(self.convo)
            return
        self.send(formatted)

    def repeat(self, data: str):
        self.send(data.split(maxsplit=1)[1])
        self.last_sent = datetime.now()

    def send_cost(self):
        logger.debug(f"!cost was called")
        cost = get_cost_from_tokens()
        dollars = "{:,.2f}".format(cost)
        self.send(f"tena has lost ${dollars} this month LULW")

    def send_summary(self, user1: str, user2: str, amount: str | int):
        logger.debug(f"!summarize was used on {user1} & {user2}")
        self.last_sent = datetime.now()
        self.summaries = list(BASE_SUMMARY)
        debate = request_debate(user1, user2, amount)
        if isinstance(debate, str):
            self.send(debate)
            return
        generate_summary("\n".join(debate), self.summaries)
        self.send(self.summaries[-1]["content"])

    def send_solution(self):
        logger.debug("!solve was called")
        if self.summaries == list(BASE_SUMMARY):
            self.send("I don't have a summary stored MMMM")
            return
        generate_solution(self.summaries)
        self.last_sent = datetime.now()
        self.send(self.summaries[-1]["content"])
        self.summaries = list(BASE_SUMMARY)

    def clear_caches(self):
        logger.debug("!clearcache was called")
        request_phrases.cache_clear()
        request_emotes.cache_clear()
        self.send("PepOk cleared caches")

    def clear_convo(self):
        self.convo = list(BASE_CONVO)
        logger.debug(f"Convo wiped, tokens at {count_tokens(self.convo)}")

    def clear_last_prompt(self):
        logger.debug("!wipelast was called")
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
        self.cooldown = self._convert_to_int(seconds)
        logger.info(f"cooldown set to {seconds}")
        self.send(f"PepOk changed the cooldown to {self.cooldown}s")

    def change_token_limit(self, limit: str):
        logger.debug("!maxtokens was used")
        limit = self._convert_to_int(limit)
        base_tokens = count_tokens(list(BASE_CONVO))
        if limit > 3996 or limit < base_tokens:
            self.send(f"token limit must be between {base_tokens} and 3996 MMMM")
            return
        self.max_tokens = limit
        self.send(f"PepOk changed the max tokens to {self.max_tokens}")

    def change_resp_token_limit(self, limit: str):
        logger.debug("!maxresp was used")
        limit = self._convert_to_int(limit)
        if limit < 1:
            self.send(f"must be positive MMMM")
            return
        self.max_resp_tokens = limit
        self.send(f"PepOk changed the max response length to {self.max_resp_tokens}")

    def toggle_tts_mode(self):
        self.tts_mode = not self.tts_mode
        word = "enabled" if self.tts_mode else "disabled"
        logger.info(f"TTS mode was {word}")
        self.send(f"PepOk TTS mode {word}")

    def start_quickdraw(self):
        logger.debug("Starting quickdraw")
        self.send("> QUICKDRAW! PARDNER vs YEEHAW")
        self.quickdraw["waiting"] = True
        self.quickdraw["time_started"] = datetime.now()
        return

    def end_quickdraw(self, nick: str, data: str):
        logger.debug(f"Quickdraw ended by {nick}")
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

    def simonsays_thread(self):
        emotes = request_emotes()
        i = 0
        while i < 4:
            self.simonsays["emote"] = choice(emotes)
            self.send(f"> Simon says... {self.simonsays['emote']}")
            self.simonsays["time_started"] = datetime.now()
            self.last_sent = datetime.now()
            while self.simonsays["emote"] != None:
                sleep(0.5)
            i += 1
            sleep(5)
        winners = Counter(self.simonsays["winners"]).most_common()
        winners_list = [f"{name}: {count}" for name, count in winners]
        self.send("Final scores Klappa " + ", ".join(winners_list))
        self.simonsays["winners"] = []

    def start_simonsays(self):
        logger.debug("Starting simon says")
        Thread(target=self.simonsays_thread).start()

    def end_simonsays(self, nick: str):
        logger.debug(f"Simon says ended by {nick}")
        delta = datetime.now() - self.simonsays["time_started"]
        response_time = round(delta.total_seconds() * 1000)
        self.send(f"{nick} got it in {response_time} ms Klappa")
        self.last_sent = datetime.now()
        self.simonsays["emote"] = None
        self.simonsays["winners"].append(nick)

    def spam_check(self, nick: str, data: str):
        if will_trigger_bot_filter(data, self.message_history):
            self.send_privmsg(nick, "This will get you muted MMMM")
        else:
            self.send_privmsg(nick, "This is safe to post MMMM")

    def send_coinflip(self):
        self.send(f"You got {choice(['heads', 'tails'])}")

    def send_image(self, prompt):
        logger.debug(f"!image was used with prompt: {prompt}")
        self.last_sent = datetime.now()
        self.send(f"{generate_image(prompt)} MMMM")

    def update_live_status(self):
        """Runs as a thread, updates stream status"""
        live = DGGLive()

        @live.event()
        def on_streaminfo(streaminfo: StreamInfo):
            self.stream_is_live = streaminfo.is_live()
            logger.debug(f"Live status: {self.stream_is_live}")

        live.run_forever()
