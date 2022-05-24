from typing import List

from deltachat import Account as _Account
from deltachat import Chat, const
from deltachat.capi import ffi, lib


class Account(_Account):
    """Patched Delta Chat Account"""

    def get_fresh_messages_cnt(self) -> int:
        """Return the number of fresh messages"""
        return lib.dc_array_get_cnt(
            ffi.gc(lib.dc_get_fresh_msgs(self._dc_context), lib.dc_array_unref)
        )

    def get_messages(self, chat_id: int) -> List[int]:
        """Return list of messages ids in the chat with the given id."""
        dc_array = ffi.gc(
            lib.dc_get_chat_msgs(self._dc_context, chat_id, 0, 0), lib.dc_array_unref
        )
        return [
            lib.dc_array_get_id(dc_array, i)
            for i in range(0, lib.dc_array_get_cnt(dc_array))
        ]

    @staticmethod
    def is_multiuser(chat: Chat) -> bool:
        return chat.get_type() != const.DC_CHAT_TYPE_SINGLE
