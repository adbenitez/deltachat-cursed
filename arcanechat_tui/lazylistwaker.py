"""A ListWalker that creates the widgets dynamically as needed."""

from functools import lru_cache
from typing import Any, Callable, Iterable, NoReturn

import urwid


class LazyListWalker(urwid.SimpleListWalker):
    """A ListWalker that creates the widgets dynamically as needed."""

    def __init__(
        self,
        contents: Iterable,
        widget_factory: Callable[[Any], urwid.Widget],
        cache_size=1000,
        wrap_around: bool = False,
    ) -> None:
        self.cache_size = cache_size
        self._widget_factory = widget_factory
        self.widget_factory = lru_cache(maxsize=cache_size)(widget_factory)
        super().__init__(contents, wrap_around)

    def clear_cache(self) -> None:
        self.widget_factory = lru_cache(maxsize=self.cache_size)(self._widget_factory)

    def __getitem__(self, position: int) -> urwid.Widget:
        """return widget at position or raise an IndexError or KeyError"""
        return self.widget_factory(super().__getitem__(position))

    def set_modified_callback(self, callback: Callable[[], Any]) -> NoReturn:
        """Ignore this, just copied from SimpleListWalker to avoid pylint warning"""
        raise NotImplementedError('Use connect_signal(list_walker, "modified", ...) instead.')
