import argparse
import configparser
import json
import os
import sys

import deltachat.const
from deltachat import Account, events
from deltachat.tracker import ConfigureTracker

from .event import AccountPlugin
from .oauth2 import get_authz_code, is_oauth2
from .ui import CursedDelta

app_name = "Cursed Delta"
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
    "send_msg": "meta enter",
    "next_chat": "meta up",
    "prev_chat": "meta down",
    "toggle_chatlist": "ctrl x",
}


def get_theme():
    file_name = "theme.json"
    themes = [
        "curseddelta-" + file_name,
        "{}/.curseddelta/{}".format(os.path.expanduser("~"), file_name),
        "/etc/curseddelta/" + file_name,
    ]

    for theme in themes:
        if os.path.isfile(theme):
            with open(theme) as fd:
                theme = json.load(fd)
            break
    else:
        theme = default_theme
        with open(themes[1], "w") as fd:
            json.dump(theme, fd, indent=2)

    return theme


def get_keymap():
    file_name = "keymap.json"
    keymaps = [
        "curseddelta-" + file_name,
        "{}/.curseddelta/{}".format(os.path.expanduser("~"), file_name),
        "/etc/curseddelta/" + file_name,
    ]

    for keymap in keymaps:
        if os.path.isfile(keymap):
            with open(keymap) as fd:
                keymap = json.load(fd)
            break
    else:
        keymap = default_keymap
        with open(keymaps[1], "w") as fd:
            json.dump(keymap, fd, indent=1)

    return keymap


def get_configuration():
    file_name = "curseddelta.conf"
    home_config = "{}/.{}".format(os.path.expanduser("~"), file_name)
    confPriorityList = [file_name, home_config, "/etc/" + file_name]

    cfg = configparser.ConfigParser()

    for conffile in confPriorityList:
        if os.path.isfile(conffile):
            cfg.read(conffile)
            break
    else:
        cfg.add_section("general")

    cfg_full = {}
    cfg_full["general"] = {}

    home = os.path.expanduser("~")
    cfg_gen = cfg_full["general"]
    cfg_gen["account_path"] = cfg["general"].get(
        "account_path", home + "/.curseddelta/account/account.db"
    )
    cfg_gen["notification"] = cfg["general"].getboolean("notification", True)
    cfg_gen["open_file"] = cfg["general"].getboolean("open_file", True)
    cfg_gen["date_format"] = cfg["general"].get("date_format", "%x", raw=True)

    if "DISPLAY" not in os.environ:
        cfg_gen["notification"] = False
        cfg_gen["open_file"] = False

    if cfg_gen["notification"]:
        try:
            import gi

            gi.require_version("Notify", "0.7")
            from gi.repository import Notify
        except:
            cfg_gen["notification"] = False

    return cfg_full


def main():
    sys.argv[0] = "curseddelta"
    argv = sys.argv
    app_path = os.path.join(os.path.expanduser("~"), ".curseddelta")
    if not os.path.exists(app_path):
        os.makedirs(app_path)
    cfg = get_configuration()

    parser = argparse.ArgumentParser(prog=argv[0])
    parser.add_argument(
        "--db",
        action="store",
        help="database file",
        default=cfg["general"]["account_path"],
    )
    parser.add_argument(
        "--show-ffi", action="store_true", help="show low level ffi events"
    )
    parser.add_argument("--email", action="store", help="email address")
    parser.add_argument("--password", action="store", help="password")
    parser.add_argument("--set-conf", action="store", help="set config option", nargs=2)
    parser.add_argument("--get-conf", action="store", help="get config option")
    parser.add_argument(
        "--port",
        action="store",
        help="port to listen for oauth2 callback",
        type=int,
        default="8383",
    )

    args = parser.parse_args(argv[1:])

    ac = Account(os.path.expanduser(args.db))

    if args.get_conf:
        print(ac.get_config(args.get_conf))
        return

    if args.show_ffi:
        log = events.FFIEventLogger(ac, "CursedDelta")
        ac.add_account_plugin(log)

    if not ac.is_configured():
        assert args.email, (
            "you must specify --email once" " to configure this database/account"
        )
        ac.set_config("addr", args.email)

        if not args.password and is_oauth2(ac, args.email):
            authz_code = get_authz_code(ac, args.email, args.port)

            ac.set_config("mail_pw", authz_code)

            flags = ac.get_config("server_flags")
            flags = int(flags) if flags else 0
            flags |= deltachat.const.DC_LP_AUTH_OAUTH2
            ac.set_config("server_flags", str(flags))
        else:
            assert args.password, (
                "you must specify --password once" " to configure this database/account"
            )
            ac.set_config("mail_pw", args.password)

        with ac.temp_plugin(ConfigureTracker(ac)) as tracker:
            ac.configure()
            tracker.wait_finish()

    if args.set_conf:
        ac.set_config(*args.set_conf)

    account = AccountPlugin(ac)
    ac.add_account_plugin(account)

    ac.start_io()

    keymap = get_keymap()
    theme = get_theme()
    CursedDelta(cfg, keymap, theme, app_name, account)
    ac.shutdown()
