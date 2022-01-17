import subprocess
import sys
from typing import Optional

import urwid
from deltachat import account_hookimpl

from ..event import ChatListMonitor
from .chatlist_widget import ChatListWidget
from .containers import ChatListContainer, MessagesContainer, MessageSendContainer
from .msgs_widget import MessagesWidget
from .msgsend_widget import MessageSendWidget
from .notifications import notify_msg


class CursedDelta(ChatListMonitor):
    def __init__(
        self, conf: dict, keymap: dict, theme: dict, app_name: str, account
    ) -> None:
        self.conf = conf
        self.keymap = keymap
        self.app_name = app_name
        self.account = account

        palette = [
            ("bg", *theme["background"]),
            ("status_bar", *theme["status_bar"]),
            ("separator", *theme["separator"]),
            ("date", *theme["date"]),
            ("hour", *theme["hour"]),
            ("encrypted", *theme["encrypted"]),
            ("unencrypted", *theme["unencrypted"]),
            ("pending", *theme["pending"]),
            ("cur_chat", *theme["cur_chat"]),
            ("reversed", *theme["reversed"]),
            ("quote", *theme["quote"]),
            ("mention", *theme["mention"]),
            ("self_msg", *theme["self_msg"]),
            ("unread_chat", *theme["unread_chat"]),
        ]

        self.chatlist_container = ChatListContainer(
            self, ChatListWidget(keymap, self.account)
        )

        # message list
        dformat = conf["general"]["date_format"]
        self.msgs_container = MessagesContainer(
            self, MessagesWidget(dformat, keymap, theme, self.account)
        )

        # message writing + status bar widget
        self.msg_send_widget = MessageSendWidget(keymap, self.account)
        self.msg_send_container = MessageSendContainer(self, self.msg_send_widget)

        # Right pannel
        self.right_side = urwid.Pile(
            [self.msgs_container, (2, self.msg_send_container)]
        )

        vert_separator = urwid.AttrMap(urwid.Filler(urwid.Columns([])), "separator")

        # Final arrangements
        self.main_columns = urwid.Columns(
            [
                ("weight", 1, self.chatlist_container),
                (1, vert_separator),
                ("weight", 4, self.right_side),
            ]
        )

        self.account.add_chatlist_monitor(self)
        self.account.account.add_account_plugin(self)

        bg = urwid.AttrMap(self.main_columns, "bg")
        self.main_loop = urwid.MainLoop(
            bg,
            palette,
            unhandled_input=self.unhandle_key,
            screen=urwid.raw_display.Screen(),
        )
        self.main_loop.screen.set_terminal_properties(colors=256)
        self.main_loop.run()

    def print_title(self, messages_count: int) -> None:
        if messages_count > 0:
            text = f"\x1b]2;{self.app_name} ({messages_count})\x07"
        else:
            text = f"\x1b]2;{self.app_name}\x07"
        sys.stdout.write(text)

    def exit(self) -> None:
        if self.account.current_chat:
            self.msg_send_widget.save_draft(self.account.current_chat)
        sys.stdout.write("\x1b]2;\x07")
        raise urwid.ExitMainLoop

    def unhandle_key(self, key: str) -> None:
        if key == self.keymap["quit"]:
            self.exit()
        elif key == self.keymap["toggle_chatlist"]:
            # check if already hidden
            if self.main_columns.contents[0][1][1] == 1:
                cols_contents = self.main_columns.contents
                # hidding
                cols_contents[0] = (cols_contents[0][0], ("given", 0, False))
                cols_contents[1] = (cols_contents[1][0], ("given", 0, False))
            else:
                self.main_columns.contents[0] = (
                    self.main_columns.contents[0][0],
                    ("weight", 1, True),
                )
                self.main_columns.contents[1] = (
                    self.main_columns.contents[1][0],
                    ("given", 1, False),
                )
                self.main_columns.focus_position = 0
        elif key == self.keymap["prev_chat"]:
            self.account.select_previous_chat()
        elif key == self.keymap["next_chat"]:
            self.account.select_next_chat()
        elif key == self.keymap["insert_text"]:
            self.main_columns.focus_position = 2
            self.right_side.focus_position = 1
        elif key == self.keymap["open_file"]:
            if not self.conf["general"]["open_file"]:
                return
            current_chat = self.account.current_chat
            if current_chat:
                msgs = current_chat.get_messages()
                if msgs:
                    for msg in reversed(msgs[-20:]):
                        if msg.filename:
                            subprocess.Popen(  # noqa
                                ["xdg-open", msg.filename],
                                stderr=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL,
                            )
                            break

    def chatlist_changed(self, current_chat_index: Optional[int], chats: list) -> None:
        new_messages = 0
        for chat in chats:
            new_messages += chat.count_fresh_messages()
        self.print_title(new_messages)

        if hasattr(self, "main_loop"):
            self.main_loop.draw_screen()

    def chat_selected(self, index: Optional[int], chats: list) -> None:
        self.main_columns.focus_position = 2
        self.right_side.focus_position = 1

    @account_hookimpl
    def ac_incoming_message(self, message) -> None:
        if not self.conf["general"]["notification"]:
            return
        sender = message.get_sender_contact()
        acc = self.account.account
        me = acc.get_self_contact()
        if sender == me:
            return
        name = acc.get_config("displayname") or me.addr
        if not message.chat.is_group() or ("@" + name in message.text):
            notify_msg(message)
