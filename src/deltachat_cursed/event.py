from typing import List, Optional, Set

from deltachat import Chat, Contact, Message, account_hookimpl
from deltachat.events import FFIEvent

from .account import Account


class ChatListMonitor:
    def chatlist_changed(
        self, current_chat_index: Optional[int], chats: List[Chat]
    ) -> None:
        pass

    def chat_selected(self, index: Optional[int], chats: List[Chat]) -> None:
        pass


class AccountPlugin:
    def __init__(self, account: Account) -> None:
        self.account = account
        self.chatlist_monitors: Set[ChatListMonitor] = set()
        for chat in self._get_chats():
            self.current_chat = chat
            break
        else:
            self.current_chat = None

    def _get_chats(self) -> List[Chat]:
        return [chat for chat in self.account.get_chats() if chat.id >= 10]

    def add_chatlist_monitor(self, monitor: ChatListMonitor) -> None:
        self.chatlist_monitors.add(monitor)
        chats = self._get_chats()
        monitor.chatlist_changed(self.get_current_index(chats), chats)

    def remove_monitor(self, monitor: ChatListMonitor) -> None:
        self.chatlist_monitors.discard(monitor)

    def chatlist_changed(self) -> None:
        chats = self._get_chats()
        if self.current_chat not in chats:
            if chats:
                self.current_chat = chats[0]
                index: Optional[int] = 0
            else:
                self.current_chat = None
                index = None
        else:
            index = chats.index(self.current_chat)

        for m in list(self.chatlist_monitors):
            m.chatlist_changed(index, chats)

    def select_chat(self, index: Optional[int]) -> None:
        chats = self._get_chats()
        for m in self.chatlist_monitors:
            m.chat_selected(index, chats)
        self.current_chat = None if index is None else chats[index]

    def select_chat_by_id(self, chat_id: int) -> None:
        chats = self._get_chats()
        chat = self.account.get_chat_by_id(chat_id)
        index = chats.index(chat)
        for m in self.chatlist_monitors:
            m.chat_selected(index, chats)
        self.current_chat = chat

    def select_next_chat(self) -> None:
        chats = self._get_chats()
        if self.current_chat is None:
            if chats:
                self.select_chat(len(chats) - 1)
        else:
            i = chats.index(self.current_chat)
            i -= 1
            if i < 0:
                i = len(chats) - 1
            self.select_chat(i)

    def select_previous_chat(self) -> None:
        chats = self._get_chats()
        if self.current_chat is None:
            if chats:
                self.select_chat(0)
        else:
            i = chats.index(self.current_chat)
            i += 1
            if i >= len(chats):
                i = 0
            self.select_chat(i)

    def get_current_index(self, chats: List[Chat]) -> Optional[int]:
        if self.current_chat is None:
            return None
        return chats.index(self.current_chat)

    @account_hookimpl
    def ac_incoming_message(self, message: Message) -> None:
        self.chatlist_changed()

    @account_hookimpl
    def ac_message_delivered(self, message: Message) -> None:
        self.chatlist_changed()

    @account_hookimpl
    def ac_member_added(self, chat: Chat, contact: Contact) -> None:
        self.chatlist_changed()

    @account_hookimpl
    def ac_member_removed(self, chat: Chat, contact: Contact) -> None:
        self.chatlist_changed()

    @account_hookimpl
    def ac_process_ffi_event(self, ffi_event: FFIEvent) -> None:
        if ffi_event.name == "DC_EVENT_MSGS_CHANGED":
            self.chatlist_changed()
        # if ffi_event.name == 'DC_EVENT_CONTACTS_CHANGED':
        #     self.chatlist_changed()
