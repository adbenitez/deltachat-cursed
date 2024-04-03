"""Event center"""

import urwid
from deltachat2 import Client, CoreEvent, EventType

CHATLIST_CHANGED = "chatlist_changed"
CHAT_CHANGED = "chat_changed"
MESSAGES_CHANGED = "msgs_changed"


class EventCenter:
    """Event center dispatching Delta Chat core events"""

    signals = [CHATLIST_CHANGED, CHAT_CHANGED, MESSAGES_CHANGED]

    def __init__(self) -> None:
        urwid.register_signal(self.__class__, self.signals)

    def process_core_event(self, client: Client, accid: int, event: CoreEvent) -> None:
        if event.kind == EventType.CHAT_MODIFIED:
            urwid.emit_signal(self, CHAT_CHANGED, client, accid, event.chat_id)
            urwid.emit_signal(self, CHATLIST_CHANGED, client, accid)

        elif event.kind == EventType.CONTACTS_CHANGED:
            urwid.emit_signal(self, CHATLIST_CHANGED, client, accid)

        elif event.kind == EventType.INCOMING_MSG:
            urwid.emit_signal(self, MESSAGES_CHANGED, client, accid, event.chat_id, event.msg_id)
            urwid.emit_signal(self, CHATLIST_CHANGED, client, accid)

        elif event.kind == EventType.MSGS_CHANGED:
            urwid.emit_signal(self, MESSAGES_CHANGED, client, accid, event.chat_id, event.msg_id)
            urwid.emit_signal(self, CHATLIST_CHANGED, client, accid)

        elif event.kind == EventType.MSGS_NOTICED:
            urwid.emit_signal(self, CHATLIST_CHANGED, client, accid)

        elif event.kind == EventType.MSG_DELIVERED:
            urwid.emit_signal(self, MESSAGES_CHANGED, client, accid, event.chat_id, event.msg_id)

        elif event.kind == EventType.MSG_FAILED:
            urwid.emit_signal(self, MESSAGES_CHANGED, client, accid, event.chat_id, event.msg_id)

        elif event.kind == EventType.MSG_READ:
            urwid.emit_signal(self, MESSAGES_CHANGED, client, accid, event.chat_id, event.msg_id)
