"""Cards layout widget, a stack of widgets, only one is visible at a time"""

from typing import Dict

import urwid

EMPTY = urwid.Widget()


class CardsWidget(urwid.WidgetPlaceholder):
    """Cards layout widget, a stack of widgets, only one of them is visible at a time"""

    original_widget: urwid.Widget

    def __init__(self) -> None:
        super().__init__(EMPTY)
        self.cards: Dict[str, urwid.Widget] = {}

    def add(self, name: str, widget: urwid.Widget) -> None:
        """Add a new widget to the stack.

        The name must be an unique string ID to identify the item.
        """
        self.cards[name] = widget

    def remove(self, name: str) -> urwid.Widget:
        """Remove an item from the stack corresponding to the given name."""
        widget = self.cards.pop(name)
        if widget is self.original_widget:
            self.original_widget = EMPTY
        return widget

    def show(self, name: str) -> None:
        """Show the widget corresponding to the given name."""
        self.original_widget = self.cards[name]
