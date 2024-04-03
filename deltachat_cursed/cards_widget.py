"""Card layout widget, a stack of widgets only one is visible at a time"""

from collections import OrderedDict
from typing import Dict

import urwid

EMPTY = urwid.Widget()


class CardsWidget(urwid.WidgetPlaceholder):
    """Card layout widget, a stack of widgets only one is visible at a time"""

    def __init__(self) -> None:
        super().__init__(EMPTY)
        self.cards: Dict[str, urwid.Widget] = OrderedDict()

    def add(self, name: str, widget: urwid.Widget) -> None:
        self.cards[name] = widget

    def remove(self, name: str) -> urwid.Widget:
        widget = self.cards.pop(name)
        if widget is self.original_widget:  # noqa
            self.original_widget = EMPTY
        return widget

    def show(self, name: str) -> None:
        self.original_widget = self.cards[name]
