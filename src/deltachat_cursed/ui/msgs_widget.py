import textwrap
from datetime import timezone
from typing import Optional

import urwid
from emoji import demojize

from ..event import ChatListMonitor
from .scli import LazyEvalListWalker, ListBoxPlus


class MessagesWidget(ListBoxPlus, ChatListMonitor):
    """Widget used to print the message list"""

    def __init__(  # noqa
        self, date_format: str, keymap: dict, theme: dict, account, display_emoji: bool
    ) -> None:
        self.DATE_FORMAT = date_format
        self.theme = theme
        self.keymap = keymap
        self.model = account
        self.display_emoji = display_emoji
        self.updating = False
        super().__init__(
            LazyEvalListWalker(urwid.MonitoredList(), self.get_message_widget, -1)
        )
        self.model.add_chatlist_monitor(self)

    def chatlist_changed(self, current_chat_index: Optional[int], chats: list) -> None:
        self.update(current_chat_index, chats)
        if current_chat_index is not None:
            chats[current_chat_index].mark_noticed()

    def chat_selected(self, index: Optional[int], chats: list) -> None:
        self.update(index, chats)
        if index is not None:
            chats[index].mark_noticed()

    def update(self, current_chat_index: Optional[int], chats: list) -> None:
        if self.updating:
            return

        self.updating = True

        if current_chat_index is None:
            msgs = []
        else:
            msgs = self.model.account.get_messages(chats[current_chat_index].id)
        self.contents = urwid.MonitoredList(msgs)

        self.updating = False

    def get_message_widget(self, msg_id, _position=None) -> urwid.Widget:
        msg = self.model.account.get_message_by_id(msg_id)
        local_date = msg.time_sent.replace(tzinfo=timezone.utc).astimezone()
        sender = msg.get_sender_contact()
        color = self.get_name_color(sender.id)
        name = (
            sender.display_name if self.display_emoji else demojize(sender.display_name)
        )

        hour = local_date.strftime(" %H:%M ")

        size_name = len(name)
        if size_name > 9:
            name = name[0:9] + "..."
            size_name = len(name)

        status = "encrypted" if msg.is_encrypted() else "unencrypted"
        message_meta = urwid.Text(
            [("hour", hour), (urwid.AttrSpec(*color), name), (status, " > ")]
        )

        text = msg.text
        if msg.filename:
            text = f"[file://{msg.filename}]{' – ' if text else ''}{text}"

        if not self.display_emoji:
            text = demojize(text)

        if msg.is_out_mdn_received():
            text = text + "  ✓✓"
        elif msg.is_out_delivered():
            text = text + "  ✓"
        elif msg.is_out_failed():
            text = text + "  ✖"

        lines = []
        quote_sender = msg.quote and msg.quote.get_sender_contact()
        if msg.quoted_text:
            if quote_sender:
                quote_color = urwid.AttrSpec(*self.get_name_color(quote_sender.id))
                lines.append((quote_color, f"│ {quote_sender.display_name}\n"))
            else:
                quote_color = "quote"
            lines.append((quote_color, "│ "))
            lines.append(("quote", f"{textwrap.shorten(msg.quoted_text, 150)}\n"))
        if msg.is_out_pending() or msg.is_out_failed():
            lines.append(("pending", text))
        elif msg.is_system_message():
            lines.append(("system_msg", text))
        else:
            me = self.model.account.get_self_contact()
            dname = self.model.account.get_config("displayname")
            if sender == me:
                lines.append(("self_msg", text))
            elif msg.account.is_multiuser(msg.chat) and (
                (dname and f"@{dname}" in text) or (quote_sender and quote_sender == me)
            ):
                lines.append(("mention", text))
            else:
                lines.append(text)

        return urwid.Columns([(size_name + 10, message_meta), urwid.Text(lines or "")])

    def get_name_color(self, id_: int) -> list:
        if id_ == self.model.account.get_self_contact().id:
            return self.theme["self_color"]

        users_color = self.theme["users_color"]
        color = id_ % len(users_color)
        return users_color[color]

    def keypress(self, size, key: str) -> Optional[str]:
        key = super().keypress(size, key)
        if key == self.keymap["down"]:
            self.keypress(size, "down")
        elif key == self.keymap["up"]:
            self.keypress(size, "up")
        else:
            return key
        return None

    def mouse_event(self, size, event, button, col, row, focus) -> None:
        if button == 4:
            self.keypress(size, "up")
            self.keypress(size, "up")
        if button == 5:
            self.keypress(size, "down")
            self.keypress(size, "down")
