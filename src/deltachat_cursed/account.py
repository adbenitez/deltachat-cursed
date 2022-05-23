from deltachat import Account as _Account
from deltachat.capi import ffi, lib


class Account(_Account):
    """Patched Delta Chat Account"""

    def get_fresh_messages_cnt(self) -> int:
        """Return the number of fresh messages"""
        return lib.dc_array_get_cnt(
            ffi.gc(lib.dc_get_fresh_msgs(self._dc_context), lib.dc_array_unref)
        )
