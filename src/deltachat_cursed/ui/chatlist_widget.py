from typing import Optional, Union

import urwid
from deltachat import Chat, const
from emoji import demojize

from ..event import ChatListMonitor
from .scli import LazyEvalListWalker, ListBoxPlus


class ListItem(urwid.Button):
    def __init__(self, caption: Union[tuple, str], callback, arg=None) -> None:
        super().__init__("")
        urwid.connect_signal(self, "click", callback, arg)
        self._w = urwid.AttrMap(
            urwid.SelectableIcon(caption, 1), None, focus_map="status_bar"
        )


class ChatListWidget(ListBoxPlus, ChatListMonitor):
    def __init__(self, keymap: dict, account, display_emoji: bool) -> None:  # noqa
        self.keymap = keymap
        self.model = account
        self.updating = False
        self.display_emoji = display_emoji
        self.current_chat_id = None
        super().__init__(
            LazyEvalListWalker(urwid.MonitoredList(), self.get_chat_widget, 0)
        )
        self.model.add_chatlist_monitor(self)

    def chatlist_changed(self, current_chat_index: Optional[int], chats: list) -> None:
        self.update(current_chat_index, chats)

    def chat_selected(self, index, chats):
        self.update(index, chats)

    def update(self, current_chat_index: Optional[int], chats: list) -> None:
        if self.updating:
            return
        self.updating = True

        if current_chat_index is None:
            self.current_chat_id = None
        else:
            self.current_chat_id = chats[current_chat_index].id
        self.contents = chats

        self.updating = False

    def get_chat_widget(self, chat: Chat, position: int) -> urwid.Widget:
        chat_type = "@" if chat.get_type() == const.DC_CHAT_TYPE_SINGLE else "#"
        name = chat.get_name()
        label = f"{chat_type} {name if self.display_emoji else demojize(name)}"
        new_messages = chat.count_fresh_messages()
        if new_messages > 0:
            label += f" ({new_messages})"

        if chat.id == self.current_chat_id:
            button = ListItem(("cur_chat", label), self.chat_change, position)
        else:
            if new_messages > 0:
                label = ("unread_chat", label)  # type: ignore
            button = ListItem(label, self.chat_change, position)
        return button

    def chat_change(self, button, index: int) -> None:
        self.model.select_chat(index)

    def keypress(self, size, key: str) -> Optional[str]:
        key = super().keypress(size, key)
        if key == self.keymap["down"]:
            self.keypress(size, "down")
        elif key == self.keymap["up"]:
            self.keypress(size, "up")
        else:
            return key
        return None
