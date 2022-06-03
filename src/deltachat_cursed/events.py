from logging import Logger
from typing import Callable

import urwid
from deltachat import Chat, Message, account_hookimpl
from deltachat.events import FFIEvent

from .account import Account
from .notifications import notify_msgs
from .util import BatchThrottle, Throttle, get_contact_name, is_multiuser


class EventCenter:
    signals = ["chatlist_changed", "chat_changed", "conversation_changed"]

    def __init__(self, account: Account, logger: Logger, notifications: bool) -> None:
        self.account = account
        self.logger = logger
        self.notifications_enabled = notifications
        urwid.register_signal(self.__class__, self.signals)
        self.chatlist_changed: Callable = Throttle(self._chatlist_changed, interval=1)
        self.conversation_changed: Callable = Throttle(
            self._conversation_changed, interval=1
        )
        self.notify_msgs: Callable = BatchThrottle(self._notify_msgs, interval=2)

        self.account.add_account_plugin(self)

    def _notify_msgs(self, *args) -> None:
        self.logger.debug("Notifying %s new messages", len(args))
        notify_msgs(*args)

    def _chatlist_changed(self, event) -> None:
        self.logger.debug("Chatlist changed, event=%s", event)
        chats = [chat for chat in self.account.get_chats() if chat.id >= 10]
        urwid.emit_signal(self, "chatlist_changed", chats)

    def _conversation_changed(self, event) -> None:
        self.logger.debug("Conversation changed, event=%s", event)
        urwid.emit_signal(self, "conversation_changed")

    def chat_changed(self, chat: Chat) -> None:
        self.logger.debug("Chat changed, chat=%s", chat)
        urwid.emit_signal(self, "chat_changed", chat)

    @account_hookimpl
    def ac_incoming_message(self, message: Message) -> None:
        if not self.notifications_enabled or message.is_system_message():
            return

        chat = message.chat
        notify = not chat.is_muted()
        if not notify and is_multiuser(chat):
            self_contact = self.account.get_self_contact()
            quote = message.quote
            if quote and quote.get_sender_contact() == self_contact:
                notify = True
            else:
                notify = f"@{get_contact_name(self_contact)}" in message.text
        if notify:
            self.notify_msgs(message)

    @account_hookimpl
    def ac_process_ffi_event(self, ffi_event: FFIEvent) -> None:
        if ffi_event.name == "DC_EVENT_CHAT_MODIFIED":
            self.chat_changed(self.account.get_chat_by_id(ffi_event.data1))
            self.chatlist_changed(ffi_event)
        if ffi_event.name == "DC_EVENT_CONTACTS_CHANGED":
            self.chatlist_changed(ffi_event)
        if ffi_event.name == "DC_EVENT_INCOMING_MSG":
            self.conversation_changed(ffi_event)
            self.chatlist_changed(ffi_event)
        if ffi_event.name == "DC_EVENT_MSGS_CHANGED":
            self.conversation_changed(ffi_event)
            self.chatlist_changed(ffi_event)
        if ffi_event.name == "DC_EVENT_MSGS_NOTICED":
            self.chatlist_changed(ffi_event)
        if ffi_event.name == "DC_EVENT_MSG_DELIVERED":
            self.conversation_changed(ffi_event)
        if ffi_event.name == "DC_EVENT_MSG_FAILED":
            self.conversation_changed(ffi_event)
        if ffi_event.name == "DC_EVENT_MSG_READ":
            self.conversation_changed(ffi_event)
