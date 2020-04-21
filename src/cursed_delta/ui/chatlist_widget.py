# -*- coding: utf-8 -*-
from ..event import ChatListMonitor
import urwid


class ListItem(urwid.Button):
    def __init__(self, caption, callback, arg=None):
        super().__init__("")
        urwid.connect_signal(self, 'click', callback, arg)
        self._w = urwid.AttrMap(urwid.SelectableIcon(caption, 1),
                                None, focus_map='status_bar')


class ChatListWidget(urwid.ListBox, ChatListMonitor):
    def __init__(self, keymap, account):
        self.keymap = keymap
        self.model = account
        self.updating = False
        self.model.add_chatlist_monitor(self)

    def chatlist_changed(self, current_chat_index, chats):
        self.update(current_chat_index, chats)

    def chat_selected(self, index, chats):
        self.update(index, chats)

    def update(self, current_chat_index, chats):
        if self.updating:
            return
        self.updating = True

        # refresh chat list
        self.chat_list = urwid.SimpleFocusListWalker(
            [urwid.AttrMap(urwid.Text("Chat list:"), 'status_bar')])
        super().__init__(self.chat_list)

        pos = self.focus_position

        if current_chat_index is None:
            current_id = None
        else:
            current_id = chats[current_chat_index].id

        # build the chat list
        for i, chat in enumerate(chats):
            pos += 1
            self.chat_list.insert(pos, urwid.AttrMap(urwid.Divider('─'), 'hour'))

            pos += 1
            label = '➜ ' + chat.get_name()
            new_messages = chat.count_fresh_messages()
            if chat.is_deaddrop():
                new_messages = len(chat.get_messages())
            if new_messages > 0:
                label += ' ({})'.format(new_messages)

            if chat.id == current_id:
                button = ListItem(
                    ('cur_chat', label), self.chat_change, i)
                self.chat_list.insert(pos, button)
                self.focus_position = pos
            else:
                if new_messages > 0:
                    label = ('unread_chat', label)
                button = ListItem(label, self.chat_change, i)
                self.chat_list.insert(pos, button)

        if chats:
            pos += 1
            self.chat_list.insert(pos, urwid.AttrMap(urwid.Divider('─'), 'hour'))

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

    def chat_change(self, button, index):
        self.model.select_chat(index)

    def keypress(self, size, key):
        key = super().keypress(size, key)
        if key == self.keymap['down']:
            self.keypress(size, 'down')
        elif key == self.keymap['up']:
            self.keypress(size, 'up')
        else:
            return key
