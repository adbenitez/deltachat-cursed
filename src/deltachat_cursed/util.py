import configparser
import json
import os
import sys
from contextlib import contextmanager
from typing import Any, Callable, Dict, Optional

import urwid
from deltachat import Account, Chat, Contact, Message, const
from deltachat.capi import lib
from deltachat.cutil import from_dc_charpointer

APP_NAME = "Cursed Delta"
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
    "cur_chat": ["", "", "", "light blue", bg_color],
    "unread_chat": ["", "", "", "#6f0", bg_color],
    "reversed": ["", "", "", bg_color, fg_color],
    "quote": ["", "", "", "dark gray", bg_color],
    "mention": ["", "", "", "bold, light red", bg_color],
    "system_msg": ["", "", "", "dark gray", bg_color],
    "self_msg": ["", "", "", "dark green", bg_color],
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
        f"{os.path.expanduser('~')}/.curseddelta/{file_name}",
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
        f"{os.path.expanduser('~')}/.curseddelta/{file_name}",
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
    home_config = f"{os.path.expanduser('~')}/.curseddelta/{file_name}"
    confPriorityList = [file_name, home_config, "/etc/curseddelta/" + file_name]

    cfg = configparser.ConfigParser()

    for conffile in confPriorityList:
        if os.path.isfile(conffile):
            cfg.read(conffile)
            break
    else:
        cfg.add_section("global")

    cfg_full: Dict[str, dict] = {"global": {}}

    home = os.path.expanduser("~")
    cfg_gbl = cfg_full["global"]
    cfg_gbl["account_path"] = cfg["global"].get(
        "account_path", home + "/.curseddelta/account/account.db"
    )
    cfg_gbl["notification"] = cfg["global"].getboolean("notification", True)
    cfg_gbl["open_file"] = (
        cfg["global"].getboolean("open_file", True) and "DISPLAY" in os.environ
    )
    cfg_gbl["date_format"] = cfg["global"].get("date_format", "%b %d, %Y", raw=True)
    cfg_gbl["display_emoji"] = cfg["global"].getboolean("display_emoji", False)

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


def is_multiuser(chat: Chat) -> bool:
    return chat.get_type() != const.DC_CHAT_TYPE_SINGLE


def is_pinned(chat: Chat) -> bool:
    visibility = lib.dc_chat_get_visibility(chat._dc_chat)  # noqa
    return visibility == const.DC_CHAT_VISIBILITY_PINNED


def get_subtitle(chat: Chat) -> str:
    if chat.get_type() == const.DC_CHAT_TYPE_MAILINGLIST:
        return "Mailing List"
    members = chat.get_contacts()
    if chat.get_type() == const.DC_CHAT_TYPE_SINGLE and members:
        return members[0].addr
    count = len(members)
    if chat.get_type() == const.DC_CHAT_TYPE_BROADCAST:
        if count == 1:
            return "1 recipient"
        return f"{count} recipients"
    if count == 1:
        return "1 member"
    return f"{count} members"
