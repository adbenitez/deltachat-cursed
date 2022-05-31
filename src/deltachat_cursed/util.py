import configparser
import json
import logging.handlers
import os
import queue
import sys
import time
from collections import deque
from contextlib import contextmanager
from threading import Event, Thread
from typing import Any, Callable, Dict, Optional

import urwid
from deltachat import Account, Chat, Contact, Message, const
from deltachat.capi import lib
from deltachat.cutil import from_dc_charpointer
from deltachat.events import FFIEvent
from deltachat.hookspec import account_hookimpl

APP_NAME = "Cursed Delta"
APP_FOLDER = os.path.abspath(os.path.join(os.path.expanduser("~"), ".curseddelta"))
if not os.path.exists(APP_FOLDER):
    os.makedirs(APP_FOLDER)
LOGS_FOLDER = os.path.join(APP_FOLDER, "logs")
COMMANDS = {
    key: key
    for key in [
        "/query",
        "/join",
        "/delete",
        "/names",
        "/add",
        "/kick",
        "/part",
        "/id",
        "/send",
        "/nick",
        "/pin",
        "/unpin",
        "/mute",
        "/unmute",
        "/topic",
        "/clear",
        "//",
    ]
}
fg_color = "white"
bg_color = "g11"
default_theme = {
    "background": ["", "", "", fg_color, bg_color],
    "status_bar": ["", "", "", "white", "g23"],
    "separator": ["", "", "", "g15", "g15"],
    "date": ["", "", "", "#6f0", bg_color],
    "encrypted": ["", "", "", "dark gray", bg_color],
    "unencrypted": ["", "", "", "dark red", bg_color],
    "failed": ["", "", "", "dark red", bg_color],
    "cur_chat": ["", "", "", "black", "light blue"],
    "unread_chat": ["", "", "", "#000", "#6f0"],
    "reversed": ["", "", "", bg_color, fg_color],
    "quote": ["", "", "", "dark gray", bg_color],
    "mention": ["", "", "", "bold, light red", bg_color],
    "system_msg": ["", "", "", "dark gray", bg_color],
    "self_msg": ["", "", "", "dark green", bg_color],
    "pinned_marker": ["", "", "", "dark gray", bg_color],
}
default_keymap = {
    "left": "h",
    "right": "l",
    "up": "k",
    "down": "j",
    "quit": "q",
    "insert_text": "i",
    "open_file": "ctrl o",
    "send_msg": "enter",
    "insert_new_line": "meta enter",
    "next_chat": "meta up",
    "prev_chat": "meta down",
    "toggle_chatlist": "ctrl x",
}


class Container(urwid.WidgetPlaceholder):
    def __init__(
        self,
        widget: urwid.Widget,
        keypress_callback: Callable,
        process_unhandled: bool = False,
    ) -> None:
        self._keypress_callback = keypress_callback
        self._process_unhandled = process_unhandled
        super().__init__(widget)

    def keypress(self, size: list, key: str) -> Optional[str]:
        if self._process_unhandled:
            key = super().keypress(size, key)
            return self._keypress_callback(size, key)
        key = self._keypress_callback(size, key)
        return super().keypress(size, key)


class Throttle:
    """Do at most one call (the most recent) in the given interval"""

    def __init__(self, func: Callable[..., None], interval: float = 1) -> None:
        self.func = func
        self.interval = interval
        self._tasks: deque = deque(maxlen=1)
        self._event = Event()
        self._worker = Thread(target=self._loop, daemon=True)
        self._worker.start()

    def _loop(self) -> None:
        while True:
            try:
                args, kwargs = self._tasks.pop()
                start = time.time()
                try:
                    self.func(*args, **kwargs)
                except Exception:  # noqa
                    pass
                time.sleep(max(self.interval - time.time() + start, 0))
            except IndexError:
                self._event.wait()
                self._event.clear()

    def __call__(self, *args, **kwargs) -> None:
        self._tasks.append((args, kwargs))
        self._event.set()


class BatchThrottle:
    """Group calls arguments into a single function call at the given interval"""

    def __init__(self, func: Callable[..., None], interval: float = 1) -> None:
        self.func = func
        self.interval = interval
        self._args: queue.Queue = queue.Queue()
        self._worker = Thread(target=self._loop, daemon=True)
        self._worker.start()

    def _loop(self) -> None:
        while True:
            args = [*self._args.get()]
            cooldown = self.interval
            start = time.time()
            while cooldown > 0:
                try:
                    args.extend(self._args.get(timeout=cooldown))
                    cooldown -= time.time() - start
                except queue.Empty:
                    break
            try:
                self.func(*args)
            except Exception:  # noqa
                pass

    def __call__(self, *args) -> None:
        self._args.put(args)


class FFIEventLogger:
    def __init__(self, account: Account, logger: logging.Logger) -> None:
        self.account = account
        self.logger = logger

    @account_hookimpl
    def ac_process_ffi_event(self, ffi_event: FFIEvent) -> None:
        self.account.log(str(ffi_event))

    @account_hookimpl
    def ac_log_line(self, message: str) -> None:
        self.logger.debug(message)


@contextmanager
def online_account(acct: Account) -> Account:
    if not acct.is_configured():
        fail("Error: Account not configured yet")
    acct.start_io()
    yield acct
    acct.shutdown()


def capture_keyboard_interrupt(func: Callable) -> Any:
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            print("Closing, operation canceled by user")
            sys.exit(0)

    return wrapper


def make_logger(log_level: str) -> logging.Logger:
    logger = logging.Logger(APP_NAME)
    logger.parent = None

    if log_level == "disabled":
        logger.disabled = True
        return logger

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    log_path = os.path.join(LOGS_FOLDER, "log.txt")
    if not os.path.exists(LOGS_FOLDER):
        os.makedirs(LOGS_FOLDER)

    fhandler = logging.handlers.RotatingFileHandler(
        log_path, backupCount=2, maxBytes=2000000
    )
    fhandler.setLevel(log_level.upper())
    fhandler.setFormatter(formatter)
    logger.addHandler(fhandler)

    return logger


def shorten_text(text: str, width: int, placeholder: str = "…") -> str:
    text = " ".join(text.split())
    if len(text) > width:
        width -= len(placeholder)
        assert width > 0, "placeholder can't be bigger than width"
        text = text[:width].strip() + placeholder
    return text


def get_theme() -> dict:
    file_name = "theme.json"
    themes = [
        "curseddelta-" + file_name,
        os.path.join(APP_FOLDER, file_name),
        "/etc/curseddelta/" + file_name,
    ]

    for path in themes:
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fd:
                theme = {**default_theme, **json.load(fd)}
            break
    else:
        theme = default_theme
        with open(themes[1], "w", encoding="utf-8") as fd:
            json.dump(theme, fd, indent=2)

    return theme


def get_keymap() -> dict:
    file_name = "keymap.json"
    keymaps = [
        "curseddelta-" + file_name,
        os.path.join(APP_FOLDER, file_name),
        "/etc/curseddelta/" + file_name,
    ]

    for path in keymaps:
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fd:
                keymap = {**default_keymap, **json.load(fd)}
                # hack to fix keymap for users of v0.3.1:
                if keymap["send_msg"] == keymap["insert_new_line"]:
                    keymap["send_msg"] = "enter"
                    with open(path, "w", encoding="utf-8") as fd:
                        json.dump(keymap, fd, indent=1)
            break
    else:
        keymap = default_keymap
        with open(keymaps[1], "w", encoding="utf-8") as fd:
            json.dump(keymap, fd, indent=1)

    return keymap


def fail(*args, **kwargs) -> None:
    print(*args, **kwargs)
    sys.exit(1)


def get_configuration() -> dict:
    file_name = "curseddelta.conf"
    home_config = os.path.join(APP_FOLDER, file_name)
    confPriorityList = [file_name, home_config, "/etc/curseddelta/" + file_name]

    cfg = configparser.ConfigParser()

    for conffile in confPriorityList:
        if os.path.isfile(conffile):
            cfg.read(conffile)
            break
    else:
        cfg.add_section("global")

    cfg_full: Dict[str, dict] = {"global": {}}

    cfg_gbl = cfg_full["global"]
    cfg_gbl["account_path"] = cfg["global"].get(
        "account_path", os.path.join(APP_FOLDER, "account", "account.db")
    )
    cfg_gbl["notification"] = cfg["global"].getboolean("notification", True)
    cfg_gbl["open_file"] = (
        cfg["global"].getboolean("open_file", True) and "DISPLAY" in os.environ
    )
    cfg_gbl["date_format"] = cfg["global"].get("date_format", "%b %d, %Y", raw=True)
    cfg_gbl["display_emoji"] = cfg["global"].getboolean("display_emoji", True)

    return cfg_full


def get_sender_name(msg: Message) -> str:
    sender = msg.override_sender_name
    if sender:
        return f"~{sender}"
    return get_contact_name(msg.get_sender_contact())


def get_contact_name(contact: Contact) -> str:
    if contact == contact.account.get_self_contact():
        return contact.account.get_config("displayname") or contact.addr
    return contact.display_name


def get_contact_color(contact: Contact) -> str:
    return f"#{lib.dc_contact_get_color(contact._dc_contact):06X}"  # noqa


def get_summarytext(msg: Message, width: int) -> str:
    return from_dc_charpointer(lib.dc_msg_get_summarytext(msg._dc_msg, width))  # noqa


def is_self_talk(chat: Chat) -> bool:
    return bool(lib.dc_chat_is_self_talk(chat._dc_chat))  # noqa


def is_device_talk(chat: Chat) -> bool:
    return bool(lib.dc_chat_is_device_talk(chat._dc_chat))  # noqa


def is_multiuser(chat: Chat) -> bool:
    return chat.get_type() in (
        const.DC_CHAT_TYPE_GROUP,
        const.DC_CHAT_TYPE_MAILINGLIST,
        const.DC_CHAT_TYPE_BROADCAST,
    )


def is_mailing_list(chat: Chat) -> bool:
    return chat.get_type() != const.DC_CHAT_TYPE_MAILINGLIST


def is_pinned(chat: Chat) -> bool:
    visibility = lib.dc_chat_get_visibility(chat._dc_chat)  # noqa
    return visibility == const.DC_CHAT_VISIBILITY_PINNED


def set_chat_visibility(chat: Chat, visibility: str) -> None:
    if visibility == "normal":
        _visibility = const.DC_CHAT_VISIBILITY_NORMAL
    elif visibility == "pinned":
        _visibility = const.DC_CHAT_VISIBILITY_PINNED
    elif visibility == "archived":
        _visibility = const.DC_CHAT_VISIBILITY_ARCHIVED
    else:
        raise ValueError(f"Invalid visibility: {visibility!r}")
    lib.dc_set_chat_visibility(chat.account._dc_context, chat.id, _visibility)  # noqa


def get_subtitle(chat: Chat) -> str:
    chat_type = chat.get_type()
    contacts = chat.get_contacts()
    if chat_type == const.DC_CHAT_TYPE_MAILINGLIST:
        subtitle = "Mailing List"
    if chat_type == const.DC_CHAT_TYPE_BROADCAST:
        count = len(contacts)
        subtitle = "1 recipient" if count == 1 else f"{count} recipients"
    elif is_multiuser(chat):
        count = len(contacts)
        subtitle = "1 member" if count == 1 else f"{count} members"
    elif len(contacts) >= 1:
        if is_self_talk(chat):
            subtitle = "Messages I sent to myself"
        elif is_device_talk(chat):
            subtitle = "Locally generated messages"
        else:
            subtitle = contacts[0].addr
    else:
        subtitle = ""

    return subtitle


def abspath(path: str) -> str:
    return os.path.abspath(os.path.expanduser(path))
