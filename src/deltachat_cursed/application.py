import os
import subprocess
import sys
from logging import Logger
from typing import Optional

import urwid
from deltachat import Chat
from emoji import emojize

from .account import Account
from .events import EventCenter
from .util import (
    COMMANDS,
    Container,
    Throttle,
    get_contact_name,
    is_mailing_list,
    is_multiuser,
    is_pinned,
    set_chat_visibility,
    shorten_text,
)
from .widgets.chatlist import ChatListWidget
from .widgets.composer import ComposerWidget
from .widgets.conversation import ConversationWidget


class Application:
    def __init__(
        self,
        account: Account,
        conf: dict,
        keymap: dict,
        theme: dict,
        logger: Logger,
    ) -> None:
        self.conf = conf
        self.keymap = keymap
        self.account = account
        self.evcenter = EventCenter(account, logger, conf["global"]["notification"])
        self.main_loop: urwid.MainLoop = urwid.MainLoop(
            None,
            [(key, *value) for key, value in theme.items()],
            unhandled_input=self._unhandle_key,
            screen=urwid.raw_display.Screen(),
        )
        self.main_loop.screen.set_terminal_properties(colors=256)
        self.main_loop.draw_screen = Throttle(self.main_loop.draw_screen, interval=0.1)
        display_emoji = conf["global"]["display_emoji"]

        # Chatlist
        self.chatlist = ChatListWidget(keymap, display_emoji)
        urwid.connect_signal(self.evcenter, "chatlist_changed", self.chatlist.set_chats)
        chatlist_container = Container(self.chatlist, self._chatlist_keypress)

        # Conversation messages
        conversation_widget = ConversationWidget(
            conf["global"]["date_format"], keymap, theme, self.account, display_emoji
        )
        urwid.connect_signal(
            self.chatlist, "chat_selected", conversation_widget.set_chat
        )
        urwid.connect_signal(
            self.evcenter,
            "conversation_changed",
            conversation_widget.update_conversation,
        )
        conversation_container = Container(
            conversation_widget, self._conversation_keypress
        )

        # message writing + status bar widget
        self.composer = ComposerWidget(keymap, display_emoji)
        urwid.connect_signal(self.chatlist, "chat_selected", self.composer.set_chat)
        urwid.connect_signal(
            self.evcenter,
            "chat_changed",
            lambda _chat: self.composer.update_status_bar(),
        )
        composer_container = Container(
            self.composer, self._composer_keypress, process_unhandled=True
        )

        # Right pannel
        self.right_side = urwid.Pile([conversation_container, (2, composer_container)])

        vert_separator = urwid.AttrMap(urwid.Filler(urwid.Columns([])), "separator")

        # Final arrangements
        self.main_columns = urwid.Columns(
            [
                ("weight", 1, chatlist_container),
                (1, vert_separator),
                ("weight", 4, self.right_side),
            ]
        )
        self.main_loop.widget = urwid.AttrMap(self.main_columns, "background")

        urwid.connect_signal(
            self.evcenter, "chatlist_changed", self.on_chatlist_changed
        )
        urwid.connect_signal(
            self.evcenter, "conversation_changed", self.main_loop.draw_screen
        )
        urwid.connect_signal(self.chatlist, "chat_selected", self.on_chat_selected)
        # call listeners with initial chatlist
        self.evcenter.chatlist_changed(None)

    def run(self) -> None:
        try:
            self.main_loop.run()
        except KeyboardInterrupt:
            try:
                self.exit()
            except urwid.ExitMainLoop:
                pass

    def exit(self) -> None:
        if self.chatlist.selected_chat:
            self.composer.save_draft()
        sys.stdout.write("\x1b]2;\x07")
        raise urwid.ExitMainLoop

    def on_chatlist_changed(self, _chats) -> None:
        self._print_title(self.account.get_fresh_messages_cnt())
        self.main_loop.draw_screen()

    def on_chat_selected(self, _chat) -> None:
        self.main_columns.focus_position = 2
        self.right_side.focus_position = 1

    def _print_title(self, badge: int) -> None:
        name = shorten_text(get_contact_name(self.account.get_self_contact()), 30)
        if badge > 0:
            text = f"\x1b]2;({badge if badge < 999 else '+999'}) {name}\x07"
        else:
            text = f"\x1b]2;{name}\x07"
        sys.stdout.write(text)

    def _unhandle_key(self, key: str) -> None:
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
            self.chatlist.select_previous_chat()
        elif key == self.keymap["next_chat"]:
            self.chatlist.select_next_chat()
        elif key == self.keymap["insert_text"]:
            self.main_columns.focus_position = 2
            self.right_side.focus_position = 1
        elif key == self.keymap["open_file"]:
            if not self.conf["global"]["open_file"]:
                return
            selected_chat = self.chatlist.selected_chat
            if selected_chat:
                msgs = selected_chat.get_messages()
                if msgs:
                    for msg in reversed(msgs[-20:]):
                        if msg.filename:
                            subprocess.Popen(  # noqa
                                ["xdg-open", msg.filename],
                                stderr=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL,
                            )
                            break

    def _chatlist_keypress(self, _size: list, key: str) -> Optional[str]:
        if key == self.keymap["right"]:
            self.main_columns.focus_position = 2
            self.right_side.focus_position = 1
        elif key == self.keymap["toggle_chatlist"]:
            self.main_columns.focus_position = 2
            self.right_side.focus_position = 1
        else:
            return key
        return None

    def _conversation_keypress(self, _size: list, key: str) -> Optional[str]:
        if key == self.keymap["left"]:
            self.main_columns.focus_position = 0
            return None
        return key

    def _composer_keypress(self, size: list, key: str) -> Optional[str]:
        # send message
        if key == self.keymap["send_msg"]:
            edit = self.composer.widgetEdit
            text = edit.get_edit_text().strip()
            if not text:
                return None
            selected_chat = self.chatlist.selected_chat
            if text.startswith("//"):
                text = text[1:]
            elif text.startswith("/"):
                edit.set_edit_text("")
                text = self._process_command(selected_chat, text)
                if text:
                    edit.set_edit_text(text)
                edit.set_edit_pos(len(edit.get_edit_text()))
                self._resize_zone(size)
                return None
            if selected_chat.is_contact_request():
                # accept contact requests automatically until UI allows to accept/block
                selected_chat.accept()
            try:
                selected_chat.send_text(emojize(text))
                edit.set_edit_text("")
            except ValueError:
                edit.set_edit_text(
                    "Error: message could not be sent, are you a member of the chat?"
                )
            edit.set_edit_pos(len(edit.get_edit_text()))
            self._resize_zone(size)
        # give the focus to the chat list
        elif key == self.keymap["left"]:
            self.main_columns.focus_position = 0
        # give the focus to the message list
        elif key in ("up", "page up", "esc"):
            self.right_side.focus_position = 0
        else:
            self._resize_zone(size)
            return key
        return None

    def _process_command(self, chat: Chat, cmd: str) -> str:
        acct = chat.account if chat else self.account
        args = cmd.split(maxsplit=1)

        text = ""
        processed = True
        if args[0] not in COMMANDS:
            text = f"Error: Unknown command {args[0]}"
        elif args[0] == COMMANDS["/query"]:
            try:
                self.chatlist.select_chat(acct.create_chat(args[1].strip()))
            except AssertionError:
                text = "Error: invalid email address"
            except ValueError as ex:
                text = f"Error: {ex}"
        elif args[0] == COMMANDS["/join"]:
            self.chatlist.select_chat(acct.create_group_chat(args[1].strip()))
        elif args[0] == COMMANDS["/nick"]:
            if len(args) == 2:
                acct.set_config("displayname", args[1].strip())
                self._print_title(acct.get_fresh_messages_cnt())
            else:
                text = f"Nick: {acct.get_config('displayname')!r}"
        else:
            processed = False

        # commands that require a chat to be selected come next
        if processed:
            pass
        elif not chat:
            text = "Error: select a chat before using that command"
        elif args[0] == COMMANDS["/delete"]:
            chat.delete()
        elif args[0] == COMMANDS["/names"]:
            text = "\n".join(c.addr for c in chat.get_contacts())
        elif args[0] == COMMANDS["/add"]:
            try:
                for addr in args[1].split(","):
                    chat.add_contact(addr.strip())
            except ValueError as ex:
                text = f"Error: {ex}"
        elif args[0] == COMMANDS["/kick"]:
            try:
                for addr in args[1].split(","):
                    chat.remove_contact(addr.strip())
            except AttributeError:
                text = "Error: invalid email address"
            except ValueError as ex:
                text = f"Error: {ex}"
        elif args[0] == COMMANDS["/part"]:
            try:
                chat.remove_contact(acct.get_self_contact())
            except ValueError as ex:
                text = f"Error: {ex}"
        elif args[0] == COMMANDS["/id"]:
            text = str(chat.id)
        elif args[0] == COMMANDS["/send"]:
            try:
                path = os.path.expanduser(args[1].strip())
                chat.send_msg(acct.create_message(filename=path))
            except ValueError as ex:
                text = f"Error: {ex}"
        elif args[0] == COMMANDS["/pin"]:
            set_chat_visibility(chat, "pinned")
        elif args[0] == COMMANDS["/unpin"]:
            if is_pinned(chat):
                set_chat_visibility(chat, "normal")
        elif args[0] == COMMANDS["/mute"]:
            chat.mute()
        elif args[0] == COMMANDS["/unmute"]:
            chat.unmute()
        elif args[0] == COMMANDS["/topic"]:
            name = args[1].strip() if len(args) == 2 else ""
            if name:
                if is_multiuser(chat):
                    if is_mailing_list(chat) or chat.can_send():
                        chat.set_name(name)
                    else:
                        text = "Error: can't change chat name"
                else:
                    chat.account.create_contact(chat.get_contacts()[0], name)
            else:
                text = "Error: Command expects one argument but none was given"
        elif args[0] == COMMANDS["/clear"]:
            msgs = chat.account.get_messages(chat.id)
            if msgs:
                chat.account.delete_messages(msgs)

        return text

    def _resize_zone(self, size: list) -> None:
        text_caption = self.composer.text_caption
        text = self.composer.widgetEdit.get_edit_text()
        rows_needed = 1
        for line in text.split("\n"):
            rows_needed += int((len(line) + len(text_caption)) / size[0]) + 1
        rows_needed = min(rows_needed, 10)
        contents = self.right_side.contents
        if rows_needed != size[1]:
            contents[1] = (contents[1][0], ("given", rows_needed))
