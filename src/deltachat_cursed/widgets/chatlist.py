from typing import Callable, List, Optional, Union

import urwid
from deltachat import Chat, const
from emoji import demojize

from ..event import ChatListMonitor
from ..scli import LazyEvalListWalker, ListBoxPlus
from ..util import shorten_text


class ListItem(urwid.Button):
    def __init__(
        self, caption: Union[tuple, str], callback: Callable, arg=None
    ) -> None:
        super().__init__("")
        urwid.connect_signal(self, "click", callback, arg)
        self._w = urwid.AttrMap(
            urwid.SelectableIcon(caption, 1), None, focus_map="status_bar"
        )


class ChatListWidget(ListBoxPlus, ChatListMonitor):
    def __init__(
        self, keymap: dict, select_chat_callback: Callable, display_emoji: bool
    ) -> None:  # noqa
        self.keymap = keymap
        self._select_chat = select_chat_callback
        self.updating = False
        self.display_emoji = display_emoji
        self.current_chat_id = None
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
        self.contents = chats
        if current_chat_index is not None:
            self.try_set_focus(current_chat_index)

        self.updating = False

    def _get_chat_widget(self, chat: Chat, position: int) -> urwid.Widget:
        chat_type = "@" if chat.get_type() == const.DC_CHAT_TYPE_SINGLE else "#"
        name = shorten_text(chat.get_name(), 40)
        label = f"{chat_type} {name if self.display_emoji else demojize(name)}"
        new_messages = chat.count_fresh_messages()
        if new_messages > 0:
            label += f" ({new_messages})"

        if chat.id == self.current_chat_id:
            button = ListItem(("cur_chat", label), self._chat_change, position)
        else:
            if new_messages > 0 and not chat.is_muted():
                label = ("unread_chat", label)  # type: ignore
            button = ListItem(label, self._chat_change, position)
        return button

    def _chat_change(self, _button, index: int) -> None:
        self._select_chat(index)
