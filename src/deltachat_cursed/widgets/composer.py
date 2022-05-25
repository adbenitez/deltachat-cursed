from threading import RLock, Thread
from time import sleep
from typing import List, Optional

import urwid
import urwid_readline
from deltachat import Chat, Message
from emoji import demojize
from emoji.unicode_codes import EMOJI_UNICODE_ENGLISH

from ..event import ChatListMonitor
from ..util import COMMANDS, get_subtitle, shorten_text


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

        self.current_chat: Optional[Chat] = None
        self._draft_lock = RLock()
        self._worker = Thread(target=self._autosave_draft, daemon=True)
        self._worker.start()

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
            name = shorten_text(name, 40)
            text = f" {verified}[ {name} ] -- {shorten_text(get_subtitle(chat), 40)}"

        self.status_bar.set_text(text)

    def _autosave_draft(self) -> None:
        while True:
            self.save_draft()
            sleep(15)

    def save_draft(self) -> None:
        with self._draft_lock:
            chat = self.current_chat
            if not chat:
                return
            text = self.widgetEdit.get_edit_text().strip()
            if text:
                draft = Message.new_empty(chat.account, "text")
                draft.set_text(text)
            else:
                draft = None
            chat.set_draft(draft)

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

        with self._draft_lock:
            # save draft of previous chat before switching
            if self.current_chat:
                self.save_draft()
            if index is None:
                self.current_chat = None
                text = ""
            else:
                self.current_chat = chats[index]
                msg = chats[index].get_draft()
                text = msg.text if msg else ""
            self.widgetEdit.set_edit_text(text)
            self.widgetEdit.set_edit_pos(len(text))
        self._update_status_bar(index, chats)
