"""Chat list widget"""

from typing import Any, Callable, Optional, Tuple

import urwid
from deltachat2 import ChatlistFlag, Client

from .lazylistwaker import LazyListWalker
from .util import shorten_text

CHAT_SELECTED = "chat_selected"


class ChatListItem(urwid.Button):
    """A single chatlist item"""

    def __init__(
        self,
        accid: int,
        item: Any,
        selected: bool,
        callback: Callable[["ChatListItem"], None],
    ) -> None:
        super().__init__("", callback)
        self.accid = accid
        self.id = item.id
        elements: list = []

        if item.is_self_talk:
            color = "#0af"
            icon = "*"
        elif item.is_device_talk:
            color = "#888"
            icon = "i"
        else:
            color = item.color
            icon = "@" if item.dm_chat_contact else "#"
        elements.append((urwid.AttrSpec("#fff", color), f" {icon} "))

        if item.is_pinned:
            elements.append("*")
        else:
            elements.append(" ")

        name = shorten_text(item.name, 40)
        elements.append(("selected_chat", name) if selected else name)

        if item.fresh_message_counter > 0:
            elements.append(" ")
            style = "unread_badge_muted" if item.is_muted else "unread_badge"
            elements.append((style, f"({item.fresh_message_counter})"))

        self._w = urwid.AttrMap(urwid.SelectableIcon(elements, 3), None, focus_map="focused_item")


class ChatListWidget(urwid.ListBox):
    """Display a list of chats"""

    signals = [CHAT_SELECTED]

    def __init__(self, client: Client) -> None:
        self.client = client
        self.accid: Optional[int] = None
        self.selected_chat: Optional[Tuple[int, int]] = None
        super().__init__(LazyListWalker([], self._create_chatlist_item))

    def set_account(self, accid: Optional[int]) -> None:
        self.accid = accid
        if self.selected_chat and accid != self.selected_chat[0]:
            self._select_chat(None)
        self.chatlist_changed(self.client, accid)

    def select_chat(self, chat: Optional[Tuple[int, int]]) -> None:
        self._select_chat(chat)
        self.chatlist_changed(self.client, self.accid)

    def chatlist_changed(self, client: Client, accid: Optional[int]) -> None:
        if not self.accid:
            self.body.clear_cache()
            self.body.clear()
        elif accid == self.accid:
            entries = client.rpc.get_chatlist_entries(accid, ChatlistFlag.NO_SPECIALS, None, None)
            item = self.focus
            self.body.clear_cache()
            self.body[:] = [(accid, chatid) for chatid in entries]
            try:
                index = max(entries.index(item.id), 0) if item else 0
            except ValueError:
                pass
            else:
                if entries:
                    self.set_focus(index)

    def _create_chatlist_item(self, chat: Tuple[int, int]) -> urwid.Widget:
        item = self.client.rpc.get_chatlist_items_by_entries(chat[0], [chat[1]])[str(chat[1])]
        return ChatListItem(chat[0], item, self.selected_chat == chat, self._on_item_clicked)

    def _on_item_clicked(self, item: ChatListItem) -> None:
        self._select_chat((item.accid, item.id))
        self.chatlist_changed(self.client, self.accid)  # so the selected chat widget is updated

    def _select_chat(self, chat: Optional[Tuple[int, int]]) -> None:
        self.selected_chat = chat
        urwid.emit_signal(self, CHAT_SELECTED, self.selected_chat)
