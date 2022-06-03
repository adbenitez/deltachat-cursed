from logging import Logger
from typing import Callable, List, Optional

import urwid
from deltachat import Chat, const
from emoji import demojize

from ..scli import LazyEvalListWalker, ListBoxPlus
from ..util import is_pinned, shorten_text


class ChatListItem(urwid.Button):
    def __init__(self, caption: list, callback: Callable, chat: Chat) -> None:
        super().__init__("")
        urwid.connect_signal(self, "click", callback, chat)
        self._w = urwid.AttrMap(
            urwid.SelectableIcon(caption, 3), None, focus_map="focused_item"
        )


class ChatListWidget(ListBoxPlus):
    signals = ["chat_selected"]

    def __init__(self, keymap: dict, display_emoji: bool, logger: Logger) -> None:
        self.keymap = keymap
        self.display_emoji = display_emoji
        self.selected_chat: Optional[Chat] = None
        self.logger = logger
        super().__init__(
            LazyEvalListWalker(urwid.MonitoredList(), self._get_chat_widget, 0)
        )

    def _item_clicked(self, _button, chat: Chat) -> None:
        self.select_chat(chat)

    def _get_chat(self, position) -> Optional[Chat]:
        if 0 <= position < len(self.contents):
            return self.contents[position]
        return None

    def set_chats(self, chats: List[Chat]) -> None:
        prev_position = self.get_focus()[1]
        self.contents = chats
        if prev_position is not None:
            self.try_set_focus(prev_position)
        if self.selected_chat and self.selected_chat not in self.contents:
            self.select_chat(None)

    def select_chat(self, chat: Chat) -> None:
        self.logger.debug("Chat selected: %s", chat)
        self.selected_chat = chat
        urwid.emit_signal(self, "chat_selected", chat)

    def select_next_chat(self) -> None:
        if self.selected_chat:
            i = self.contents.index(self.selected_chat)
            if i < 0:  # no chat selected, skip
                return
            i -= 1
            if i < 0:
                i = len(self.contents) - 1
            self.try_set_focus(i)
            self.select_chat(self.contents[i])

    def select_previous_chat(self) -> None:
        if self.selected_chat:
            i = self.contents.index(self.selected_chat)
            if i < 0:  # no chat selected, skip
                return
            i += 1
            if i >= len(self.contents):
                i = 0
            self.try_set_focus(i)
            self.select_chat(self.contents[i])

    def keypress(self, size: list, key: str) -> Optional[str]:
        key = super().keypress(size, key)
        if key == self.keymap["down"]:
            self.keypress(size, "down")
        elif key == self.keymap["up"]:
            self.keypress(size, "up")
        else:
            return key
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
        if self.select_chat and chat == self.selected_chat:
            label = ("cur_chat", label)  # type: ignore
        elements.append(label)

        new_messages = chat.count_fresh_messages()
        if new_messages > 0:
            elements.append(" ")
            if chat.is_muted():
                elements.append(f"({new_messages})")
            else:
                elements.append(("unread_chat", f"({new_messages})"))

        widget = ChatListItem(elements, self._item_clicked, chat)

        if is_pinned(chat):
            next_chat = self._get_chat(position + 1)
            if next_chat and not is_pinned(next_chat):
                divider = urwid.AttrMap(urwid.Divider("─"), "pinned_marker")
                widget = urwid.Pile([widget, divider])

        return widget
