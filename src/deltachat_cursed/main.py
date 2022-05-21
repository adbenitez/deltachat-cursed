import os
import sys
import time
from argparse import ArgumentParser, Namespace

import deltachat.const
from deltachat import Account
from deltachat.events import FFIEventLogger
from deltachat.tracker import ConfigureTracker

from .event import AccountPlugin
from .oauth2 import get_authz_code, is_oauth2
from .ui import CursedDelta
from .util import (
    APP_NAME,
    capture_keyboard_interrupt,
    create_message,
    fail,
    get_configuration,
    get_keymap,
    get_theme,
    online_account,
)


@capture_keyboard_interrupt
def main() -> None:
    app_path = os.path.join(os.path.expanduser("~"), ".curseddelta")
    if not os.path.exists(app_path):
        os.makedirs(app_path)
    cfg = get_configuration()
    args = get_parser(cfg).parse_args(sys.argv[1:])

    args.cfg = cfg
    args.acct = Account(os.path.expanduser(args.db))

    if args.show_ffi:
        args.acct.add_account_plugin(FFIEventLogger(args.acct))

    if "cmd" in args:
        args.cmd(args)
    else:
        start_ui(args)


def get_parser(cfg: dict) -> ArgumentParser:
    parser = ArgumentParser(prog="curseddelta")
    parser.add_argument(
        "--db",
        action="store",
        help="database file",
        default=cfg["general"]["account_path"],
    )
    parser.add_argument(
        "--show-ffi", action="store_true", help="show low level ffi events"
    )
    parser.add_argument(
        "--port",
        action="store",
        help="port to listen for oauth2 callback",
        type=int,
        default="8383",
    )

    subparsers = parser.add_subparsers(title="subcommands")

    init_parser = subparsers.add_parser("init", help="initialize your account")
    init_parser.add_argument("addr", help="your e-mail address")
    init_parser.add_argument(
        "password",
        help="your password, if not provided OAuth2 will be used",
        nargs="?",
    )
    init_parser.set_defaults(cmd=init_cmd)

    config_parser = subparsers.add_parser(
        "config", help="set or get account configuration options"
    )
    config_parser.add_argument(
        "option",
        help="option name",
        nargs="?",
    )
    config_parser.add_argument(
        "value",
        help="option value to set",
        nargs="?",
    )
    config_parser.set_defaults(cmd=config_cmd)

    send_parser = subparsers.add_parser("send", help="send message")
    send_parser.add_argument(
        "--chat",
        metavar="id",
        help="contact address or chat id where the message should be sent",
        required=True,
    )
    send_parser.add_argument(
        "-a", metavar="file", dest="filename", help="attach file to the message"
    )
    send_parser.add_argument("text", help="text message to send", nargs="?")
    send_parser.set_defaults(cmd=send_cmd)

    list_parser = subparsers.add_parser("list", help="print chat list")
    list_parser.set_defaults(cmd=list_cmd)

    return parser


def init_cmd(args: Namespace) -> None:
    if args.acct.is_configured():
        fail("Error: account already configured")

    args.acct.set_config("addr", args.addr)

    if args.password:
        args.acct.set_config("mail_pw", args.password)
    else:
        if is_oauth2(args.acct, args.addr):
            authz_code = get_authz_code(args.acct, args.addr, args.port)

            args.acct.set_config("mail_pw", authz_code)

            flags = args.acct.get_config("server_flags")
            flags = int(flags) if flags else 0
            flags |= deltachat.const.DC_LP_AUTH_OAUTH2  # noqa
            args.acct.set_config("server_flags", str(flags))
        else:
            fail(
                "Error: OAuth2 not supported for your provider, you must provide a password"
            )

    with args.acct.temp_plugin(ConfigureTracker(args.acct)) as tracker:
        args.acct.configure()
        try:
            tracker.wait_finish()
        except tracker.ConfigureFailed as ex:
            fail(f"Failed to configure: {ex}")
        else:
            print(f"Successfully configured {args.addr}")


def config_cmd(args: Namespace) -> None:
    if args.value:
        args.acct.set_config(args.option, args.value)

    if args.option:
        try:
            print(f"{args.option}={args.acct.get_config(args.option)!r}")
        except KeyError as err:
            fail("Error:", err.args[0])
    else:
        for key in args.acct.get_config("sys.config_keys").split():
            print(f"{key}={args.acct.get_config(key)!r}")


def send_cmd(args: Namespace) -> None:
    with online_account(args.acct) as acct:
        try:
            chat = acct.get_chat_by_id(int(args.chat))
        except ValueError:
            chat = acct.create_chat(args.chat)

        if not args.text and not args.filename:
            fail("Error: Empty message")

        print(f"Sending message to {chat.get_name()!r}")
        msg = chat.send_msg(
            create_message(args.acct, text=args.text, filename=args.filename)
        )
        while not msg.is_out_delivered():
            time.sleep(0.1)
        print("Message sent")


def list_cmd(args: Namespace) -> None:
    if not args.acct.is_configured():
        fail("Error: Account not configured yet")

    for chat in args.acct.get_chats():
        if chat.id >= 10:
            print(f"#{chat.id} - {chat.get_name()}")


def start_ui(args: Namespace) -> None:
    plugin = AccountPlugin(args.acct)
    args.acct.add_account_plugin(plugin)

    with online_account(args.acct):
        CursedDelta(args.cfg, get_keymap(), get_theme(), APP_NAME, plugin)
