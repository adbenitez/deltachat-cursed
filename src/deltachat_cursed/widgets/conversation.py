from datetime import datetime, timezone
from typing import Optional

import urwid
from deltachat import Chat
from emoji import demojize

from ..account import Account
from ..scli import LazyEvalListWalker, ListBoxPlus
from ..util import (
    get_contact_color,
    get_contact_name,
    get_sender_name,
    is_multiuser,
    shorten_text,
)


class ConversationWidget(ListBoxPlus):
    """Widget used to print the message list"""

    def __init__(  # noqa
        self,
        date_format: str,
        keymap: dict,
        theme: dict,
        account: Account,
        display_emoji: bool,
    ) -> None:
        self.date_format = date_format
        self.nick_bg = theme["background"][-1]
        self.keymap = keymap
        self.account = account
        self.display_emoji = display_emoji
        self.chat: Optional[Chat] = None
        super().__init__(
            LazyEvalListWalker(urwid.MonitoredList(), self._get_message_widget, -1)
        )

    def set_chat(self, chat: Optional[Chat]) -> None:
        self.chat = chat
        self.update_conversation()
        if chat:
            chat.mark_noticed()

    def update_conversation(self) -> None:
        self.contents = (
            self.chat.account.get_messages(self.chat.id) if self.chat else []
        )

    def _get_date(self, account: Account, position: int) -> Optional[datetime]:
        if 0 <= position < len(self.contents):
            return (
                account.get_message_by_id(self.contents[position])
                .time_sent.replace(tzinfo=timezone.utc)
                .astimezone()
            )
        return None

    def _get_message_widget(self, msg_id: int, position: int) -> urwid.Widget:
        msg = self.account.get_message_by_id(msg_id)
        sender = msg.get_sender_contact()

        cur_date = msg.time_sent.replace(tzinfo=timezone.utc).astimezone()
        if msg.is_encrypted() or sender.id < 10:
            timestamp = cur_date.strftime(" %H:%M ")
            timestamp_wgt = urwid.Text(("encrypted", timestamp))
        else:
            timestamp = cur_date.strftime("!%H:%M ")
            timestamp_wgt = urwid.Text(("unencrypted", timestamp))

        name = get_sender_name(msg)
        name = shorten_text(
            name if self.display_emoji else demojize(name),
            50,
        )
        components: list = [
            (urwid.AttrSpec(get_contact_color(sender), self.nick_bg), name)
        ]
        if msg.is_out_mdn_received():
            components.append(" ✓✓")
        elif msg.is_out_delivered():
            components.append(" ✓")
        elif msg.is_out_pending():
            components.append(" →")
        elif msg.is_out_failed():
            components.extend([" ", ("failed", " ! ")])
        header_wgt = urwid.Text(components)

        text = msg.text
        if msg.filename:
            text = f"[file://{msg.filename}]{' – ' if text else ''}{text}"
        if not self.display_emoji:
            text = demojize(text)
        lines = []
        quote_sender = msg.quote and msg.quote.get_sender_contact()
        if msg.quoted_text:
            if quote_sender:
                quote_color = urwid.AttrSpec(
                    get_contact_color(quote_sender), self.nick_bg
                )
                lines.append((quote_color, f"│ {get_sender_name(msg.quote)}\n"))
            else:
                quote_color = "quote"
            lines.append((quote_color, "│ "))
            lines.append(
                ("quote", f"{shorten_text(msg.quoted_text, 150, placeholder='[…]')}\n")
            )
        if msg.is_system_message():
            lines.append(("system_msg", text))
        else:
            self_contact = msg.account.get_self_contact()
            dname = get_contact_name(self_contact)
            if sender == self_contact:
                lines.append(("self_msg", text))
            elif is_multiuser(msg.chat) and (
                f"@{dname}" in text or (quote_sender and quote_sender == self_contact)
            ):
                lines.append(("mention", text))
            else:
                lines.append(text)
        body_wgt = urwid.Text(lines or "")

        msg_wgt = urwid.Columns(
            [(len(timestamp), timestamp_wgt), urwid.Pile([header_wgt, body_wgt])]
        )

        pdate = self._get_date(msg.account, position - 1)
        if not pdate or (pdate.year, pdate.month, pdate.day) != (
            cur_date.year,
            cur_date.month,
            cur_date.day,
        ):
            date = urwid.Text(("date", cur_date.strftime(f"\n  {self.date_format}  ")))
            divider = urwid.AttrMap(urwid.Divider("─", top=1, bottom=1), "date")
            date_wgt = urwid.Columns([divider, ("flow", date), divider])
            margin = ("fixed", 1, urwid.Text(" "))
            date_wgt = urwid.Columns([margin, date_wgt, margin])
            widget = urwid.Pile([date_wgt, msg_wgt])
        else:
            widget = msg_wgt

        msg.mark_seen()
        return widget

    def keypress(self, size: list, key: str) -> Optional[str]:
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
