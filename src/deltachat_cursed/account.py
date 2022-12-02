from tempfile import NamedTemporaryFile
from threading import Event
from typing import List, Optional

from deltachat import Account as _Account
from deltachat import Message, const, hookspec
from deltachat.capi import ffi, lib
from deltachat.cutil import as_dc_charpointer
from deltachat.events import EventThread
from deltachat.tracker import ImexTracker


class Account(_Account):
    """Patched Delta Chat Account"""

    def __init__(  # noqa
        self, db_path: str, logging: bool = True, closed: bool = False
    ) -> None:
        # initialize per-account plugin system
        self._pm = hookspec.PerAccount._make_plugin_manager()
        self._logging = logging

        self.add_account_plugin(self)

        self.db_path = db_path
        path = db_path.encode("utf8") if hasattr(db_path, "encode") else db_path

        self._dc_context = ffi.gc(
            lib.dc_context_new_closed(path)
            if closed
            else lib.dc_context_new(ffi.NULL, path, ffi.NULL),
            lib.dc_context_unref,
        )
        if self._dc_context == ffi.NULL:
            raise ValueError(f"Could not dc_context_new: {db_path}")

        self._shutdown_event = Event()
        self._event_thread = EventThread(self)
        self._configkeys = self.get_config("sys.config_keys").split()
        hook = hookspec.Global._get_plugin_manager().hook
        hook.dc_account_init(account=self)

    def open(self, passphrase: str = "") -> bool:
        return bool(
            lib.dc_context_open(self._dc_context, as_dc_charpointer(passphrase))
        )

    def export_all(self, path: str, passphrase: Optional[str] = None) -> str:
        export_files = self._export(path, const.DC_IMEX_EXPORT_BACKUP, passphrase)
        if len(export_files) != 1:
            raise RuntimeError("found more than one new file")
        return export_files[0]

    def import_all(self, path: str, passphrase: Optional[str] = None) -> None:
        assert not self.is_configured(), "cannot import into configured account"
        self._import(path, const.DC_IMEX_IMPORT_BACKUP, passphrase)

    def _import(
        self, path: str, imex_cmd: int, passphrase: Optional[str] = None
    ) -> None:
        with self.temp_plugin(ImexTracker()) as imex_tracker:
            self.imex(path, imex_cmd, passphrase)
            imex_tracker.wait_finish()

    def _export(
        self, path: str, imex_cmd: int, passphrase: Optional[str] = None
    ) -> list:
        with self.temp_plugin(ImexTracker()) as imex_tracker:
            self.imex(path, imex_cmd, passphrase)
            return imex_tracker.wait_finish()

    def imex(self, path, imex_cmd, passphrase=None):
        if not passphrase:
            passphrase = ffi.NULL
        else:
            passphrase = as_dc_charpointer(passphrase)
        lib.dc_imex(self._dc_context, imex_cmd, as_dc_charpointer(path), passphrase)

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

    def delete_messages(self, messages: List[int]) -> None:
        lib.dc_delete_msgs(self._dc_context, messages, len(messages))

    def create_message(
        self,
        text: Optional[str] = None,
        html: Optional[str] = None,
        viewtype: Optional[str] = None,
        filename: Optional[str] = None,
        bytefile=None,
        sender: Optional[str] = None,
        quote: Optional[Message] = None,
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
