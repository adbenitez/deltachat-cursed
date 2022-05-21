import configparser
import json
import os
import sys
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from typing import Any, Callable, Dict

from deltachat import Account, Message

APP_NAME = "Cursed Delta"
default_theme = {
    "background": ["", "", "", "", "g11"],
    "status_bar": ["", "", "", "white", "g23"],
    "separator": ["", "", "", "g15", "g15"],
    "date": ["", "", "", "#6f0", "g11"],
    "hour": ["", "", "", "dark gray", "g11"],
    "encrypted": ["", "", "", "dark gray", "g11"],
    "unencrypted": ["", "", "", "dark red", "g11"],
    "pending": ["", "", "", "dark gray", "g11"],
    "cur_chat": ["", "", "", "light blue", "g11"],
    "unread_chat": ["", "", "", "#6f0", "g11"],
    "reversed": ["", "", "", "g11", "white"],
    "quote": ["", "", "", "dark gray", "g11"],
    "mention": ["", "", "", "bold, light red", "g11"],
    "self_msg": ["", "", "", "dark green", "g11"],
    "self_color": ["bold, #6d0", "g11"],
    "users_color": [
        ["dark red", "g11"],
        ["dark green", "g11"],
        ["brown", "g11"],
        ["dark blue", "g11"],
        ["dark magenta", "g11"],
        ["dark cyan", "g11"],
        ["light red", "g11"],
        ["light green", "g11"],
        ["yellow", "g11"],
        ["light blue", "g11"],
        ["light magenta", "g11"],
        ["light cyan", "g11"],
        ["white", "g11"],
        ["#f80", "g11"],
        ["#06f", "g11"],
        ["#f08", "g11"],
        ["#f00", "g11"],
        ["#80f", "g11"],
        ["#8af", "g11"],
        ["#0f8", "g11"],
    ],
}
default_keymap = {
    "left": "h",
    "right": "l",
    "up": "k",
    "down": "j",
    "quit": "q",
    "insert_text": "i",
    "reply": "ctrl r",
    "open_file": "ctrl o",
    "send_msg": "enter",
    "insert_new_line": "meta enter",
    "next_chat": "meta up",
    "prev_chat": "meta down",
    "toggle_chatlist": "ctrl x",
}


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
                theme = json.load(fd)
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
    home_config = f"{os.path.expanduser('~')}/.{file_name}"
    confPriorityList = [file_name, home_config, "/etc/" + file_name]

    cfg = configparser.ConfigParser()

    for conffile in confPriorityList:
        if os.path.isfile(conffile):
            cfg.read(conffile)
            break
    else:
        cfg.add_section("general")

    cfg_full: Dict[str, dict] = {}
    cfg_full["general"] = {}

    home = os.path.expanduser("~")
    cfg_gen = cfg_full["general"]
    cfg_gen["account_path"] = cfg["general"].get(
        "account_path", home + "/.curseddelta/account/account.db"
    )
    cfg_gen["notification"] = cfg["general"].getboolean("notification", True)
    cfg_gen["open_file"] = (
        cfg["general"].getboolean("open_file", True) and "DISPLAY" in os.environ
    )
    cfg_gen["date_format"] = cfg["general"].get("date_format", "%x", raw=True)

    return cfg_full


def create_message(
    account: Account,
    text: str = None,
    html: str = None,
    viewtype: str = None,
    filename: str = None,
    bytefile=None,
    sender: str = None,
    quote: Message = None,
) -> Message:
    if bytefile:
        assert filename is not None, "bytefile given but filename not provided"
        blobdir = account.get_blobdir()
        parts = filename.split(".", maxsplit=1)
        if len(parts) == 2:
            prefix, suffix = parts
            prefix += "-"
            suffix = "." + suffix
        else:
            prefix = filename + "-"
            suffix = None
        with NamedTemporaryFile(
            dir=blobdir, prefix=prefix, suffix=suffix, delete=False
        ) as fp:
            filename = fp.name
        assert filename
        with open(filename, "wb") as f:
            with bytefile:
                f.write(bytefile.read())

    if not viewtype:
        if filename:
            viewtype = "file"
        else:
            viewtype = "text"
    msg = Message.new_empty(account, viewtype)

    if quote is not None:
        msg.quote = quote
    if text:
        msg.set_text(text)
    if html:
        msg.set_html(html)
    if filename:
        msg.set_file(filename)
    if sender:
        msg.set_override_sender_name(sender)

    return msg
