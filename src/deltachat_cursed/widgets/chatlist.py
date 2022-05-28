from typing import Callable, List, Optional

import urwid
from deltachat import Chat, const
from emoji import demojize

from ..event import ChatListMonitor
from ..scli import LazyEvalListWalker, ListBoxPlus
from ..util import is_pinned, shorten_text


class ListItem(urwid.Button):
    def __init__(self, caption: list, callback: Callable, arg=None) -> None:
        super().__init__("")
        urwid.connect_signal(self, "click", callback, arg)
        self._w = urwid.AttrMap(
            urwid.SelectableIcon(caption, 3), None, focus_map="status_bar"
        )


class ChatListWidget(ListBoxPlus, ChatListMonitor):
    def __init__(
        self,
        keymap: dict,
        select_chat_callback: Callable,
        display_emoji: bool,
    ) -> None:  # noqa
        self.keymap = keymap
        self._select_chat = select_chat_callback
        self.updating = False
        self.display_emoji = display_emoji
        self.current_chat_id = None
        self.chats: List[Chat] = []
        super().__init__(
            LazyEvalListWalker(urwid.MonitoredList(), self._get_chat_widget, 0)
        )

    def chatlist_changed(
        self, current_chat_index: Optional[int], chats: List[Chat]
    ) -> None:
        self._update(current_chat_index, chats)

    def chat_selected(self, index: Optional[int], chats: List[Chat]) -> None:
        self._update(index, chats)

    def keypress(self, size: list, key: str) -> Optional[str]:
        key = super().keypress(size, key)
        if key == self.keymap["down"]:
            self.keypress(size, "down")
        elif key == self.keymap["up"]:
            self.keypress(size, "up")
        else:
            return key
        return None

    def _update(self, current_chat_index: Optional[int], chats: List[Chat]) -> None:
        if self.updating:
            return
        self.updating = True

        if current_chat_index is None:
            self.current_chat_id = None
        else:
            self.current_chat_id = chats[current_chat_index].id
        self.chats = chats
        self.contents = chats
        if current_chat_index is not None:
            self.try_set_focus(current_chat_index)

        self.updating = False

    def _get_chat(self, position) -> Optional[Chat]:
        if 0 <= position < len(self.chats):
            return self.chats[position]
        return None

    def _get_chat_widget(self, chat: Chat, position: int) -> urwid.Widget:
        elements: list = []

        chat_color = urwid.AttrSpec(
            "#fff",
            f"#{chat.get_color():06X}",
        )
        elements.append(
            (
                chat_color,
                " @ " if chat.get_type() == const.DC_CHAT_TYPE_SINGLE else " # ",
            )
        )

        elements.append(" ")

        name = shorten_text(chat.get_name(), 40)
        label = f"{name if self.display_emoji else demojize(name)}"
        if chat.id == self.current_chat_id:
            label = ("cur_chat", label)  # type: ignore
        elements.append(label)

        new_messages = chat.count_fresh_messages()
        if new_messages > 0:
            elements.append(" ")
            if chat.is_muted():
                elements.append(f"({new_messages})")
            else:
                elements.append(("unread_chat", f"({new_messages})"))

        widget = ListItem(elements, self._chat_change, position)

        if is_pinned(chat):
            next_chat = self._get_chat(position + 1)
            if next_chat and not is_pinned(next_chat):
                divider = urwid.AttrMap(urwid.Divider("─"), "pinned_marker")
                widget = urwid.Pile([widget, divider])

        return widget

    def _chat_change(self, _button, index: int) -> None:
        self._select_chat(index)
