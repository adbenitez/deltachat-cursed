from tempfile import NamedTemporaryFile
from typing import List

from deltachat import Account as _Account
from deltachat import Message
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

    def create_message(
        self,
        text: str = None,
        html: str = None,
        viewtype: str = None,
        filename: str = None,
        bytefile=None,
        sender: str = None,
        quote: Message = None,
    ) -> Message:
        if bytefile:
            assert filename is not None, "bytefile given but filename not provided"
            blobdir = self.get_blobdir()
            parts = filename.split(".", maxsplit=1)
            if len(parts) == 2:
                prefix, suffix = parts
                prefix += "-"
                suffix = "." + suffix
            else:
                prefix = filename + "-"
                suffix = None
            with NamedTemporaryFile(
                dir=blobdir, prefix=prefix, suffix=suffix, delete=False
            ) as fp:
                filename = fp.name
            assert filename
            with open(filename, "wb") as f:
                with bytefile:
                    f.write(bytefile.read())

        if not viewtype:
            if filename:
                viewtype = "file"
            else:
                viewtype = "text"
        msg = Message.new_empty(self, viewtype)

        if quote is not None:
            msg.quote = quote
        if text:
            msg.set_text(text)
        if html:
            msg.set_html(html)
        if filename:
            msg.set_file(filename)
        if sender:
            msg.set_override_sender_name(sender)

        return msg
