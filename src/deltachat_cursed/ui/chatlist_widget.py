from typing import Optional, Union

import urwid
from deltachat import const

from ..event import ChatListMonitor


class ListItem(urwid.Button):
    def __init__(self, caption: Union[tuple, str], callback, arg=None) -> None:
        super().__init__("")
        urwid.connect_signal(self, "click", callback, arg)
        self._w = urwid.AttrMap(
            urwid.SelectableIcon(caption, 1), None, focus_map="status_bar"
        )


class ChatListWidget(urwid.ListBox, ChatListMonitor):
    def __init__(self, keymap: dict, account) -> None:  # noqa
        self.keymap = keymap
        self.model = account
        self.updating = False
        self.model.add_chatlist_monitor(self)

    def chatlist_changed(self, current_chat_index: Optional[int], chats: list) -> None:
        self.update(current_chat_index, chats)

    def chat_selected(self, index, chats):
        self.update(index, chats)

    def update(self, current_chat_index: Optional[int], chats: list) -> None:
        if self.updating:
            return
        self.updating = True

        # refresh chat list
        self.chat_list = urwid.SimpleFocusListWalker(  # noqa
            [urwid.AttrMap(urwid.Text("Chat list:"), "status_bar")]
        )
        super().__init__(self.chat_list)

        pos = self.focus_position  # noqa

        if current_chat_index is None:
            current_id = None
        else:
            current_id = chats[current_chat_index].id

        # build the chat list
        for i, chat in enumerate(chats):
            if chat.id < 10:
                continue
            pos += 1
            chat_type = "@" if chat.get_type() == const.DC_CHAT_TYPE_SINGLE else "#"
            label = f"{chat_type} {chat.get_name()}"
            new_messages = chat.count_fresh_messages()
            if new_messages > 0:
                label += f" ({new_messages})"

            if chat.id == current_id:
                button = ListItem(("cur_chat", label), self.chat_change, i)
                self.chat_list.insert(pos, button)
                self.focus_position = pos
            else:
                if new_messages > 0:
                    label = ("unread_chat", label)  # type: ignore
                button = ListItem(label, self.chat_change, i)
                self.chat_list.insert(pos, button)

        # pos += 1
        # self.chat_list.insert(
        #     pos, urwid.AttrMap(urwid.Divider('─'), 'separator'))
        # pos += 1
        # self.chat_list.insert(pos, urwid.Text('✚  New group'))
        # pos += 1
        # self.chat_list.insert(pos, urwid.Text('✚  New contact'))
        # pos += 1
        # self.chat_list.insert(pos, urwid.Text('☺  Contacts'))
        # pos += 1
        # self.chat_list.insert(pos, urwid.AttrMap(urwid.Divider('─'), 'separator'))
        self.updating = False

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
