from typing import List, Optional

import urwid
import urwid_readline
from deltachat import Chat, Message
from emoji import demojize
from emoji.unicode_codes import EMOJI_UNICODE_ENGLISH

from ..event import ChatListMonitor
from ..util import COMMANDS, get_subtitle


class ComposerWidget(urwid.Filler, ChatListMonitor):
    def __init__(self, keymap: dict, display_emoji: bool) -> None:
        self.display_emoji = display_emoji
        self.text_caption = " >> "
        self.status_bar = urwid.Text(("status_bar", " "), align="left")
        self.attr = urwid.AttrMap(self.status_bar, "status_bar")

        self.widgetEdit = urwid_readline.ReadlineEdit(
            self.text_caption, "", multiline=True
        )
        del self.widgetEdit.keymap["enter"]
        self.widgetEdit.keymap[
            keymap["insert_new_line"]
        ] = self.widgetEdit.insert_new_line
        self.widgetEdit.enable_autocomplete(self._complete)

        self.pile = urwid.Pile([self.attr, self.widgetEdit])
        super().__init__(self.pile)

        self.keymap = keymap
        self.current_chat: Optional[Chat] = None
        self.typing = False

    def _complete(self, text: str, state: int) -> Optional[str]:
        items = []
        if text.startswith("@"):
            if self.current_chat:
                me = self.current_chat.account.get_self_contact()
                items.extend(
                    [f"@{c.name}" for c in self.current_chat.get_contacts() if c != me]
                )
        elif text.startswith(":"):
            items.extend(EMOJI_UNICODE_ENGLISH.keys())
        elif text.startswith("/") or not text:
            items.extend(COMMANDS.keys())

        if text:
            matches = []
            fuzzy_matches = []
            for item in items:
                if not item:
                    continue
                if item.startswith(text):
                    matches.append(item)
                elif text[1:] in item[1:]:
                    fuzzy_matches.append(item)
            items = matches + fuzzy_matches
        try:
            return items[state]
        except (IndexError, TypeError):
            return None

    def _update_status_bar(
        self, current_chat_index: Optional[int], chats: List[Chat]
    ) -> None:
        if current_chat_index is None:
            text = ""
        else:
            chat = chats[current_chat_index]
            verified = ""
            if chat.is_protected():
                verified = "✓ "
            name = chat.get_name() if self.display_emoji else demojize(chat.get_name())
            text = f" {verified}[ {name} ] -- {get_subtitle(chat)}"

        self.status_bar.set_text(text)

    def chatlist_changed(
        self, current_chat_index: Optional[int], chats: List[Chat]
    ) -> None:
        if self.current_chat is None:
            self.chat_selected(current_chat_index, chats)
        else:
            self._update_status_bar(current_chat_index, chats)

    def chat_selected(self, index: Optional[int], chats: List[Chat]) -> None:
        if index is not None and self.current_chat == chats[index]:
            return
        self.typing = False
        if self.current_chat:
            self.save_draft(self.current_chat)
        if index is None:
            self.current_chat = None
            return
        self.current_chat = chats[index]
        msg = self.current_chat.get_draft()
        self.widgetEdit.set_edit_text(msg.text if msg else "")
        self.widgetEdit.set_edit_pos(len(self.widgetEdit.get_edit_text()))
        self._update_status_bar(index, chats)

    def save_draft(self, chat: Chat) -> None:
        text = self.widgetEdit.get_edit_text()
        msg = Message.new_empty(chat.account, "text")
        msg.set_text(text)
        chat.set_draft(msg)

    def keypress(self, size: list, key: str) -> Optional[str]:
        key = super().keypress(size, key)
        # save draft on exit
        if key == self.keymap["quit"]:
            if not self.current_chat:
                return None
            text = self.widgetEdit.get_edit_text()
            prev_draft = self.current_chat.get_draft()
            if not prev_draft or prev_draft.text != text:
                msg = Message.new_empty(self.current_chat.account, "text")
                msg.set_text(text)
                self.current_chat.set_draft(msg)
        # save draft on first type
        elif not key and not self.typing and self.current_chat:
            text = self.widgetEdit.get_edit_text()
            draft = self.current_chat.get_draft()
            if not draft or draft.text != text:
                self.typing = True
                msg = Message.new_empty(self.current_chat.account, "text")
                msg.set_text(text)
                self.current_chat.set_draft(msg)

        return key
