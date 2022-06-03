import logging
import os
import sys
import time
from argparse import ArgumentParser, Namespace
from getpass import getpass

import deltachat.const
from deltachat.tracker import ConfigureTracker, ImexFailed

from . import __version__
from .account import Account
from .application import Application
from .oauth2 import get_authz_code, is_oauth2
from .util import (
    FFIEventLogger,
    abspath,
    capture_keyboard_interrupt,
    fail,
    get_configuration,
    get_keymap,
    get_theme,
    make_logger,
    online_account,
)


@capture_keyboard_interrupt
def main() -> None:
    cfg = get_configuration()
    args = get_parser(cfg).parse_args(sys.argv[1:])

    args.cfg = cfg
    try:
        args.acct = Account(args.db, closed=True)
    except ValueError:
        fail(f"Error: couldn't open account's database: {args.db!r}")

    args.logger = make_logger(args.log)
    if args.log == "debug":
        core_logger = logging.Logger("Core", logging.DEBUG)
        core_logger.parent = args.logger
        args.acct.add_account_plugin(FFIEventLogger(args.acct, core_logger))

    is_new = not os.path.exists(args.db)
    opened = False
    if args.db_prompt:
        if is_new:
            prompt = "Enter new database password:"
        else:
            prompt = "Enter database password:"
        args.db_pass = getpass(prompt)
        if is_new:
            if args.db_pass != getpass("Enter database password again:"):
                fail("Error: passwords don't match")
    elif not args.db_pass and not is_new:
        opened = args.acct.open()
        if not opened:
            args.db_pass = getpass("Enter database password:")
    if not opened:
        if not args.acct.open(args.db_pass):
            fail("Error: failed to open database, is the password correct?")

    if "cmd" in args:
        args.cmd(args)
    else:
        start_ui(args)


def get_parser(cfg: dict) -> ArgumentParser:
    parser = ArgumentParser(prog="delta")
    parser.add_argument("-v", "--version", action="version", version=__version__)
    parser.add_argument(
        "--db",
        help="account's database file",
        default=cfg["global"]["account_path"],
        type=abspath,
    )
    parser.add_argument(
        "--password",
        help="password to open an encrypted database, if the database doesn't exist it will be created and encrypted with the given password",
        default="",
        dest="db_pass",
        metavar="PASSWORD",
    )
    parser.add_argument(
        "--prompt",
        "-p",
        action="store_true",
        dest="db_prompt",
        help="prompt for password to open/create encrypted database",
    )
    parser.add_argument(
        "--log",
        help="set the severity level of what should be saved in the log file (default: %(default)s)",
        choices=["debug", "info", "warn", "error", "disabled"],
        default="warn",
        type=str.lower,
    )

    subparsers = parser.add_subparsers(title="subcommands")

    init_parser = subparsers.add_parser("init", help="initialize your account")
    init_parser.add_argument(
        "--port",
        help="port to listen for oauth2 callback (default: %(default)s)",
        type=int,
        default="8383",
    )
    init_parser.add_argument("addr", help="your e-mail address")
    init_parser.add_argument(
        "password",
        help="your password, if not provided you will be requested to enter it, if empty, OAuth2 will be used",
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
        "-a",
        metavar="file",
        dest="filename",
        help="attach file to the message",
        type=abspath,
    )
    send_parser.add_argument("text", help="text message to send", nargs="?")
    send_parser.set_defaults(cmd=send_cmd)

    list_parser = subparsers.add_parser("list", help="print chat list")
    list_parser.set_defaults(cmd=list_cmd)

    import_parser = subparsers.add_parser("import", help="import keys or full backup")
    import_parser.add_argument(
        "--password",
        help="if provided, this passphrase will be used to access an encrypted backup",
    )
    import_parser.add_argument(
        "--prompt",
        "-p",
        action="store_true",
        help="prompt for password to access an encrypted backup",
    )
    import_parser.add_argument(
        "path",
        help="path to a backup file or path to a directory containing keys to import",
        type=abspath,
    )
    import_parser.set_defaults(cmd=import_cmd)

    export_parser = subparsers.add_parser("export", help="export full backup or keys")
    export_parser.add_argument(
        "--keys-only",
        "-k",
        action="store_true",
        help="export only the public and private keys",
    )
    export_parser.add_argument(
        "--password",
        help="if provided, this passphrase will be used to encrypt the exported backup",
    )
    export_parser.add_argument(
        "--prompt",
        "-p",
        action="store_true",
        help="prompt for password to encrypt backup",
    )
    export_parser.add_argument(
        "folder",
        help="path to the directory where the files should be saved, if not given, current working directory is used",
        nargs="?",
        default=os.curdir,
        type=abspath,
    )
    export_parser.set_defaults(cmd=export_cmd)

    return parser


def init_cmd(args: Namespace) -> None:
    if args.acct.is_configured():
        fail("Error: account already configured")

    args.acct.set_config("addr", args.addr)

    if args.password is None:
        args.password = getpass("Enter account password:")

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
            args.acct.create_message(text=args.text, filename=args.filename)
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


def import_cmd(args: Namespace) -> None:
    if os.path.isdir(args.path):
        if args.password or args.prompt:
            fail(
                "Error: can't import keys, only full backups support password protection"
            )
        try:
            args.acct.import_self_keys(args.path)
            print("Keys imported successfully")
        except ImexFailed:
            fail(f"Error: no valid keys found in {args.path!r}")
    elif os.path.isfile(args.path):
        if args.acct.is_configured():
            fail("Error: can't import backup into an already configured account")

        if args.prompt:
            args.password = getpass("Enter backup password:")

        try:
            args.acct.import_all(args.path, args.password)
            print("Backup imported successfully")
        except ImexFailed:
            fail(f"Error: invalid password or backup file {args.path!r}")
    else:
        fail(f"Error: file doesn't exists {args.path!r}")


def export_cmd(args: Namespace) -> None:
    try:
        if args.keys_only:
            if args.password or args.prompt:
                fail(
                    "Error: can't export keys, only full backups support password protection"
                )
            paths = args.acct.export_self_keys(args.folder)
        else:
            if args.prompt:
                args.password = getpass("Enter new backup password:")
                if args.password != getpass("Enter backup password again:"):
                    fail("Error: passwords don't match")
            paths = [args.acct.export_all(args.folder, args.password)]
        print("Exported files:")
        for path in paths:
            print(path)
    except ImexFailed:
        fail(f"Error: failed to export to {args.folder!r}")


def start_ui(args: Namespace) -> None:
    theme = get_theme(args.logger)
    keymap = get_keymap(args.logger)
    app = Application(args.acct, args.cfg, keymap, theme, args.logger)
    with online_account(args.acct):
        app.run()
