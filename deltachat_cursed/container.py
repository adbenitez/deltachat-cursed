"""Widget container that handles key presses in the contained widget."""

from typing import Callable, Optional

import urwid


class Container(urwid.WidgetPlaceholder):
    """Widget container that handles key presses in the contained widget."""

    def __init__(
        self,
        widget: urwid.Widget,
        callback: Callable[[list, str], Optional[str]],
        unhandled_only: bool = True,
    ) -> None:
        """
        :param widget: the contained widget
        :param callback: the callback to call on key presses unhandled by the contained widget
        :param unhandled_only: if set to False call callback first and if it didn't handle
                               the key press then pass it to the contained widget. If set to True
                               only call callback on unhandled key presses
        """
        self._callback = callback
        self._unhandled_only = unhandled_only
        super().__init__(widget)

    def keypress(self, size: list, key: str) -> Optional[str]:
        if self._unhandled_only:
            return super().keypress(size, key) and self._callback(size, key)
        return self._callback(size, key) and super().keypress(size, key)
