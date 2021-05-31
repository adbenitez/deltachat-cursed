# -*- coding: utf-8 -*-
import urwid


class ChatListContainer(urwid.WidgetPlaceholder):
    def __init__(self, root, chatlist_widget):
        self.root = root
        self.keymap = root.keymap
        super().__init__(chatlist_widget)

    def keypress(self, size, key):
        if key == self.keymap["right"]:
            self.root.main_columns.focus_position = 2
            self.root.right_side.focus_position = 1
        if key == self.keymap["toggle_chatlist"]:
            self.root.main_columns.focus_position = 2
            self.root.right_side.focus_position = 1
            return super().keypress(size, key)
        else:
            return super().keypress(size, key)


class MessagesContainer(urwid.WidgetPlaceholder):
    def __init__(self, root, msgs_widget):
        self.root = root
        self.keymap = root.keymap
        super().__init__(msgs_widget)

    def keypress(self, size, key):
        if key == self.keymap["left"]:
            self.root.main_columns.focus_position = 0
        else:
            return super().keypress(size, key)


class MessageSendContainer(urwid.WidgetPlaceholder):
    def __init__(self, root, msg_send_widget):
        self.root = root
        self.keymap = root.keymap
        self.msg_send_widget = msg_send_widget
        super().__init__(msg_send_widget)

    def keypress(self, size, key):
        key = super().keypress(size, key)
        # send message
        if key == self.keymap["send_msg"]:
            edit = self.msg_send_widget.widgetEdit
            text = edit.get_edit_text().strip()
            if not text:
                return
            if text.startswith("//"):
                text = text[1:]
            elif text.startswith("/"):
                edit.set_edit_text(self.process_command(text))
                self.resize_zone(size)
                return
            current_chat = self.root.account.current_chat
            current_chat.send_text(text)
            edit.set_edit_text("")
            self.resize_zone(size)
        # give the focus to the chat list
        elif key == self.keymap["left"]:
            self.root.main_columns.focus_position = 0
        # give the focus to the message list
        elif key == "up" or key == "page up" or key == "esc":
            self.root.right_side.focus_position = 0
        elif key == self.keymap["reply"]:
            current_chat = self.root.account.current_chat
            if not current_chat:
                return
            msgs = current_chat.get_messages()
            if not msgs:
                return
            edit = self.msg_send_widget.widgetEdit
            sender = msgs[-1].get_sender_contact().display_name
            text = msgs[-1].text.strip()
            if not msgs[-1].is_text():
                text = "[File]\n" + text
            reply = "\n> @{}:\n".format(sender)
            for line in text.splitlines(keepends=True):
                reply += "> " + line
            edit.set_edit_text(reply + "\n\n")
            self.root.main_columns.focus_position = 2
            self.root.right_side.focus_position = 1
            self.resize_zone(size)
        else:
            self.resize_zone(size)
            return key

    def resize_zone(self, size):
        text_caption = self.msg_send_widget.text_caption
        text = self.msg_send_widget.widgetEdit.get_edit_text()
        rows_needed = 1
        for line in text.split("\n"):
            rows_needed += int((len(line) + len(text_caption)) / size[0]) + 1
        if rows_needed > 10:
            rows_needed = 10
        contents = self.root.right_side.contents
        if rows_needed != size[1]:
            contents[1] = (contents[1][0], ("given", rows_needed))

    def process_command(self, cmd):
        model = self.root.account
        acc = model.account
        args = cmd.split(maxsplit=1)
        if args[0] == "/query":
            acc.create_chat(args[1].strip())
        if args[0] == "/add":
            for addr in args[1].split(","):
                model.current_chat.add_contact(addr.strip())
        if args[0] == "/kick":
            for addr in args[1].split(","):
                model.current_chat.remove_contact(addr.strip())
        if args[0] == "/part":
            model.current_chat.remove_contact(acc.get_self_contact())
        if args[0] == "/names":
            return "\n".join(c.addr for c in model.current_chat.get_contacts())
        if args[0] == "/join":
            model.current_chat = acc.create_group_chat(args[1].strip())
            msg = model.current_chat.get_draft()
            if msg:
                return msg.text
        if args[0] == "/accept":
            i = int(args[1].strip()) - 1
            msg = acc.get_deaddrop_chat().get_messages()[i]
            acc._create_chat_by_message_id(msg.id)

        return ""
