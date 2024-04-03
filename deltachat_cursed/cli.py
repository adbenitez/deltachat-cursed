"""Command line arguments parsing"""

import sys
from argparse import ArgumentParser, Namespace
from typing import Callable

from appdirs import user_config_dir
from deltachat2 import Client, JsonRpcError

from . import APP_NAME
from ._version import __version__
from .util import abspath, get_account, get_or_create_account, parse_docstring


class Cli:
    """Command line argument parser"""

    def __init__(self) -> None:
        self._parser = ArgumentParser()
        self._subcommands = self._parser.add_subparsers(title="subcommands")

        self._parser.add_argument("-v", "--version", action="version", version=__version__)

        self._parser.add_argument(
            "--program-folder",
            "-f",
            help="program configuration folder (default: %(default)s)",
            metavar="PATH",
            default=user_config_dir(APP_NAME),
            type=abspath,
        )

        self._parser.add_argument(
            "--account",
            "-a",
            help="operate only over the given account when running any subcommand",
            metavar="ADDR",
        )

        self._parser.add_argument(
            "--log",
            help=(
                "set the severity level of what should be saved in the log file"
                " (default: %(default)s)"
            ),
            choices=["debug", "info", "warning", "error", "disabled"],
            default="warning",
            type=str.lower,
        )

        init_parser = self.add_subcommand(init_cmd, name="init")
        init_parser.add_argument("addr", help="your e-mail address")
        init_parser.add_argument("password", help="your password")

        config_parser = self.add_subcommand(config_cmd, name="config")
        config_parser.add_argument("option", help="option name", nargs="?")
        config_parser.add_argument("value", help="option value to set", nargs="?")

    def add_subcommand(
        self,
        func: Callable[["Cli", Namespace], None],
        **kwargs,
    ) -> ArgumentParser:
        """Add a subcommand to the CLI."""
        if not kwargs.get("name"):
            kwargs["name"] = func.__name__
        if not kwargs.get("help") and not kwargs.get("description"):
            kwargs["help"], kwargs["description"] = parse_docstring(func.__doc__)
        subparser = self._subcommands.add_parser(**kwargs)
        subparser.set_defaults(cmd=func)
        return subparser

    def parse_args(self) -> Namespace:
        """Parse command line arguments"""
        return self._parser.parse_args()


def init_cmd(client: Client, args: Namespace) -> None:
    """initialize an account"""
    if args.account:
        accid = get_account(client.rpc, args.account)
        if not accid or accid not in client.rpc.get_all_account_ids():
            print(f"Error: unknown account: {args.account!r}")
            sys.exit(1)
    else:
        accid = get_or_create_account(client.rpc, args.addr)

    try:
        client.configure(accid, email=args.addr, password=args.password)
        print("Account configured successfully.")
    except JsonRpcError as err:
        print("ERROR: Configuration failed:", err)
        sys.exit(1)


def config_cmd(client: Client, args: Namespace) -> None:
    """set or get account configuration values"""
    accounts = client.rpc.get_all_account_ids()
    if not args.account and len(accounts) == 1:
        args.account = accounts[0]

    if args.account:
        accid = get_account(client.rpc, args.account)
        if not accid or accid not in accounts:
            print(f"Error: unknown account: {args.account!r}")
            sys.exit(1)

        keys = (client.rpc.get_config(accid, "sys.config_keys") or "").split()
        if args.option and not args.option.startswith("ui.") and args.option not in keys:
            print(f"Error: unknown configuration option: {args.option}")
            sys.exit(1)

        if args.value:
            client.rpc.set_config(accid, args.option, args.value)

        if args.option:
            try:
                value = client.rpc.get_config(accid, args.option)
                print(f"{args.option}={value!r}")
            except JsonRpcError:
                print(f"Error: unknown configuration option: {args.option}")
                sys.exit(1)
        else:
            for key in keys:
                value = client.rpc.get_config(accid, key)
                print(f"{key}={value!r}")
    else:
        print(
            "Error: you must use --account option to set what account to set/get"
            " configuration values"
        )
        sys.exit(1)
