"""Conversation area widget"""

from datetime import datetime
from typing import Any, Optional, Tuple

import urwid
from deltachat2 import (
    Client,
    Message,
    MessageState,
    SpecialContactId,
    SystemMessageType,
)

from .lazylistwaker import LazyListWalker
from .util import shorten_text


class DayMarker(urwid.Columns):
    """Day marker separating messages by day"""

    def __init__(self, timestamp: int):
        date = datetime.utcfromtimestamp(timestamp)  # timestamp is in local time already
        date_format = "%b %d, %Y"
        date_label = urwid.Text(("date", date.strftime(f"\n  {date_format}  ")))
        divider = urwid.AttrMap(urwid.Divider("─", top=1, bottom=1), "date")
        date_wgt = urwid.Columns([divider, ("flow", date_label), divider])
        margin = ("fixed", 1, urwid.Text(" "))
        super().__init__([margin, date_wgt, margin])


class MessageItem(urwid.AttrMap):
    """A single message item"""

    def __init__(self, msg: Any, nickbg: str) -> None:
        sender = msg.sender
        sent_date = datetime.fromtimestamp(msg.timestamp)
        if (
            msg.show_padlock
            or (sender.id <= SpecialContactId.LAST_SPECIAL and sender.id != SpecialContactId.SELF)
            or msg.system_message_type == SystemMessageType.WEBXDC_INFO_MESSAGE
        ):
            timestamp = sent_date.strftime(" %H:%M ")
            date_wgt = (len(timestamp), urwid.SelectableIcon(("encrypted", timestamp)))
        else:
            timestamp = sent_date.strftime("!%H:%M ")
            date_wgt = (len(timestamp), urwid.SelectableIcon(("unencrypted", timestamp)))

        header_wgt = get_sender_label(msg, nickbg)

        lines = []
        if msg.quote:
            if msg.quote.kind == "WithMessage":
                quote_sender = msg.quote.override_sender_name or msg.quote.author_display_name
                quote_color = urwid.AttrSpec(msg.quote.author_display_color, nickbg)
                lines.append((quote_color, f"│ {quote_sender}\n"))
            else:
                quote_color = "quote"
            lines.append((quote_color, "│ "))
            lines.append(("quote", f"{shorten_text(msg.quote.text, 150, placeholder='[…]')}\n"))
        text = msg.text
        if msg.file_name:
            text = f"[{msg.file_name}]{' – ' if text else ''}{text}"
        if msg.is_info:
            lines.append(("system_msg", text))
        else:
            if sender.id == SpecialContactId.SELF:
                lines.append(("self_msg", text))
            else:
                lines.append(text)
        body_wgt = urwid.Text(lines or "")

        cols = urwid.Columns([date_wgt, urwid.Pile([header_wgt, body_wgt])])
        super().__init__(cols, None, focus_map="focused_item")


class ConversationWidget(urwid.ListBox):
    """Display a list of messages"""

    def __init__(self, client: Client, nickbg: str) -> None:
        self.client = client
        self.nickbg = nickbg
        self.chat: Optional[Tuple[int, int]] = None
        super().__init__(LazyListWalker([], self._create_message_item))

    def set_chat(self, chat: Optional[Tuple[int, int]]) -> None:
        self.chat = chat
        if chat:
            self.client.rpc.marknoticed_chat(*chat)
        self._update_conversation()

    def messages_changed(self, _client: Client, accid: int, chatid: int, _msgid: int) -> None:
        if self.chat and accid == self.chat[0] and chatid in (self.chat[1], 0):
            self._update_conversation()

    def _update_conversation(self) -> None:
        self.body.clear_cache()
        if self.chat:
            items = self.client.rpc.get_message_list_items(*self.chat, False, True)
            self.body[:] = [
                (self.chat[0], item.kind, item.msg_id if item.kind == "message" else item.timestamp)
                for item in items
            ]
            if items:
                self.set_focus(len(items) - 1)
        else:
            self.body.clear()

    def _create_message_item(self, item: Tuple[int, str, int]) -> urwid.Widget:
        if item[1] == "message":
            self.client.rpc.markseen_msgs(item[0], [item[2]])
            return MessageItem(self.client.rpc.get_message(item[0], item[2]), self.nickbg)
        return DayMarker(item[2])


def get_sender_label(msg: Message, nickbg: str) -> urwid.Text:
    name = shorten_text(msg.override_sender_name or msg.sender.display_name, 50)
    components: list = [(urwid.AttrSpec(msg.sender.color, nickbg), name)]
    if msg.state == MessageState.OUT_MDN_RCVD:
        components.append(" ✓✓")
    elif msg.state == MessageState.OUT_DELIVERED:
        components.append(" ✓")
    elif msg.state == MessageState.OUT_PENDING:
        components.append(" →")
    elif msg.state == MessageState.OUT_FAILED:
        components.extend([" ", ("failed", " ! ")])
    return urwid.Text(components)
