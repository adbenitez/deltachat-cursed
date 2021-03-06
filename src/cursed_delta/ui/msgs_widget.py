# -*- coding: utf-8 -*-
from datetime import timezone

from ..event import ChatListMonitor
import urwid


class MessagesWidget(urwid.ListBox, ChatListMonitor):
    '''Widget used to print the message list'''

    def __init__(self, date_format, keymap, theme, account):
        self.DATE_FORMAT = date_format
        self.theme = theme
        self.keymap = keymap
        self.model = account
        self.updating = False
        self.model.add_chatlist_monitor(self)

    def chatlist_changed(self, current_chat_index, chats):
        self.update(current_chat_index, chats)
        if current_chat_index is not None:
            chats[current_chat_index].mark_noticed()

    def chat_selected(self, index, chats):
        self.update(index, chats)

    def update(self, current_chat_index, chats):
        if self.updating:
            return
        self.updating = True

        if current_chat_index is None:
            msgs = []
        else:
            msgs = chats[current_chat_index].get_messages()

        self.msg_list = urwid.SimpleFocusListWalker(
            [urwid.Text(('top', ''), align='left')])
        super().__init__(self.msg_list)

        self.pos = 0

        prev_date = None
        for msg in msgs:
            self.print_msg(msg, prev_date)
            local_date = msg.time_sent.replace(
                tzinfo=timezone.utc).astimezone()
            prev_date = local_date.strftime(
                '│ {} │'.format(self.DATE_FORMAT))

        self.pos += 1
        self.msg_list.insert(self.pos, urwid.Text(('bottom', '')))

        self.updating = False

    def print_msg(self, msg, prev_date):
        local_date = msg.time_sent.replace(
            tzinfo=timezone.utc).astimezone()
        sender = msg.get_sender_contact()
        name = sender.display_name
        color = self.get_name_color(sender.id)

        cur_date = local_date.strftime(
            '│ {} │'.format(self.DATE_FORMAT))

        if cur_date != prev_date:
            fill = '─'*(len(cur_date) - 2)
            date_text = '┌' + fill + '┐\n' + cur_date + '\n└' + fill + '┘'

            date_to_display = urwid.Text(('date', date_text), align='center')
            self.focus_position = self.pos
            self.pos += 1
            self.msg_list.insert(self.pos, date_to_display)

        hour = local_date.strftime(' %H:%M ')

        size_name = len(name)
        if size_name > 9:
            name = name[0:9] + '...'
            size_name = len(name)

        status = 'encrypted' if msg.is_encrypted() else 'unencrypted'
        message_meta = urwid.Text(
            [('hour', hour),
             (urwid.AttrSpec(*color), name),
             (status, " > ")])

        if not msg.is_text():
            if msg.text:
                text = '[File] – ' + msg.text
            else:
                text = '[File]'
        else:
            text = msg.text

        if msg.is_out_mdn_received():
            text = text + '  ✓✓'
        elif msg.is_out_delivered():
            text = text + '  ✓'
        elif msg.is_out_failed():
            text = text + '  ✖'
        else:
            text = text

        if msg.is_out_pending() or msg.is_out_failed():
            message_text = urwid.Text(('pending', text))
        else:
            me = self.model.account.get_self_contact()
            display_name = self.model.account.get_config('displayname')
            mention = display_name and '@'+display_name in text
            lines = []
            for line in text.splitlines(keepends=True):
                if line.startswith('>'):
                    quoting = True
                    quote = ''
                    while quoting:
                        if line.startswith('>'):
                            quote += '│'
                            line = line[1:]
                        elif line.startswith(' >'):
                            quote += ' │'
                            line = line[2:]
                        else:
                            quoting = False
                    line = ('quote', quote+line)
                elif sender == me:
                    line = ('self_msg', line)
                elif mention:
                    line = ('mention', line)
                lines.append(line)
            message_text = urwid.Text(lines or '')

        message_to_display = urwid.Columns(
            [(size_name + 10, message_meta), message_text])

        self.pos += 1
        self.msg_list.insert(self.pos, message_to_display)
        self.focus_position = self.pos

    def get_name_color(self, id):
        if id == self.model.account.get_self_contact().id:
            return self.theme['self_color']

        users_color = self.theme['users_color']
        color = id % len(users_color)
        return users_color[color]

    def keypress(self, size, key):
        key = super().keypress(size, key)
        if key == self.keymap['down']:
            self.keypress(size, 'down')
        elif key == self.keymap['up']:
            self.keypress(size, 'up')
        else:
            return key

    def mouse_event(self, size, event, button, col, row, focus):
        if button == 4:
            self.keypress(size, 'up')
            self.keypress(size, 'up')
        if button == 5:
            self.keypress(size, 'down')
            self.keypress(size, 'down')
