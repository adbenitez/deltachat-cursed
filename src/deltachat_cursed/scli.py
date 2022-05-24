"""stuff adapted from https://github.com/isamert/scli/"""

from typing import Callable, Iterable

import urwid


def noop(*_args, **_kwargs):
    pass


class LazyEvalListWalker(urwid.ListWalker):
    """A ListWalker that creates widgets only as they come into view.

    This ListWalker subclass saves resources by deferring widgets creation until they are actually visible. For large `contents` list, most of the items might not be viewed in a typical usage.

    "If you need to display a large number of widgets you should implement your own list walker that manages creating widgets as they are requested and destroying them later to avoid excessive memory use."
    https://urwid.readthedocs.io/en/latest/manual/widgets.html#list-walkers
    """

    def __init__(self, contents, eval_func: Callable, init_focus_pos=0):
        if not getattr(contents, "__getitem__", None):
            raise urwid.ListWalkerError(
                f"ListWalker expecting list like object, got: {contents}"
            )
        self._init_focus_pos = init_focus_pos
        self._eval_func = eval_func
        self.contents = contents
        super().__init__()  # Not really needed, just here to make pylint happy.

    @property
    def contents(self):
        return self._contents

    @contents.setter
    def contents(self, contents_new) -> None:
        self._remove_contents_modified_callback()
        self._contents = contents_new
        self._set_contents_modified_callback(self._modified)

        if self._init_focus_pos < 0:
            self.focus = max(0, len(self.contents) + self._init_focus_pos)
        else:
            self.focus = self._init_focus_pos

        self._modified()

    def _set_contents_modified_callback(self, callback: Callable) -> None:
        try:
            self.contents.set_modified_callback(callback)
        except AttributeError:
            # Changes to object will not be automatically updated
            pass

    def _remove_contents_modified_callback(self) -> None:
        try:
            self.contents.set_modified_callback(noop)
        except AttributeError:
            pass

    def _modified(self) -> None:
        if self.focus >= len(self.contents):
            # Making sure that if after some items are removed from `contents` it becomes shorter then the current `focus` position, we don't crash.
            self.focus = max(0, len(self.contents) - 1)
        super()._modified()

    def __getitem__(self, position: int) -> urwid.Widget:
        item = self.contents[position]
        widget = self._eval_func(item, position)
        return widget

    def next_position(self, position: int) -> int:
        if position >= len(self.contents) - 1:
            raise IndexError
        return position + 1

    @staticmethod
    def prev_position(position: int) -> int:
        if position <= 0:
            raise IndexError
        return position - 1

    def set_focus(self, position: int) -> None:
        if position < 0 or position >= len(self.contents):
            # NOTE: there is crash in this method that I can not reliably recproduce:
            # Happens when I start a search through message widgets w `/` and mash the keyboard. Seems to only happen if I push many keys fast enough..
            # This might well be an urwid bug
            raise IndexError
        self.focus = position
        self._modified()

    def positions(self, reverse=False) -> Iterable:
        ret = range(len(self.contents))
        if reverse:
            return reversed(ret)
        return ret


def listbox_set_body(listbox: urwid.ListBox, body_new) -> None:
    # Can't just do `listbox.body = body_new`:
    # https://github.com/urwid/urwid/issues/428
    # pylint: disable=protected-access
    if body_new is listbox.body:
        return
    urwid.disconnect_signal(listbox.body, "modified", listbox._invalidate)
    listbox.body = body_new
    urwid.connect_signal(listbox.body, "modified", listbox._invalidate)


class ListBoxPlus(urwid.ListBox):

    """ListBox plus a few useful features.

    - Filter visible contents to the items passing test by a given function.
    - Updates to new `contents` are displayed automatically. Fixes an urwid bug (see listbox_set_body function).
    """

    def __init__(self, body=None) -> None:
        if body is None:
            body = []
        super().__init__(body)
        self._contents_pre_filter = self.contents

    def _get_contents(self):
        try:
            return self.body.contents
        except AttributeError:
            return self.body

    def _set_contents(self, contents_new) -> None:
        # This method does not change the self._contents_pre_filter, unlike self._set_contents_pre_filter()
        try:
            self.body.contents = contents_new
        except AttributeError:
            listbox_set_body(self, contents_new)

    def _set_contents_pre_filter(self, contents_new) -> None:
        if type(contents_new) is list:  # pylint: disable=unidiomatic-typecheck
            # If contents_new is a `list` (not one of the `ListWalker`s), make the new body the same type as the original (e.g. SimpleListWalker)
            # Shouldn't use `if isinstance(contents_new, list)` test: a ListWalker returns `True` for it too.
            contents_new = type(self.contents)(contents_new)
        self._set_contents(contents_new)
        self._contents_pre_filter = self.contents

    contents = property(_get_contents, _set_contents_pre_filter)
    # Would be nice to override the base class's `body` property, so that this class can be easily replaced by any other `ListWalker`s.
    # However, overriding a property which is used in superclass's __init__ seems problematic. Need a way to delay the assignment of property. Maybe something like this is necessary:
    # https://code.activestate.com/recipes/408713-late-binding-properties-allowing-subclasses-to-ove/

    def try_set_focus(self, index: int, valign=None) -> None:
        index_orig_arg = index
        if index < 0:
            index = len(self.contents) + index
        try:
            self.focus_position = index
        except IndexError:
            return
        if index_orig_arg == -1 and valign is None:
            valign = "bottom"
        if valign is not None:
            self.set_focus_valign(valign)

    def filter_contents(self, test_function: Callable, scope=None) -> None:
        """Remove widgets not passing `test_function`.

        Retain only the items in `self.contents` that return `True` when passed as arguments to `test_function`. Pre-filtered `contents` is stored before filtering and can be restored by running `filter_contents` again with `test_function=None`.
        The `scope` argument specifies the itarable to apply the filter to. By default, the scope is all the pre-filtered items. Passing `scope=self.contents' can be useful to further filter an already filtered contents.
        """

        # Note that if `contents` is modified directly elsewhere in the code while a filter is on, this modification applies only to the filtered contents. So, for instance the code for adding a new MessageWidget to ChatView shouldn't do `self.contents.append()`, but rather `current_chat.append()` (after doing `_set_contents_pre_filter(current_chat)`). That way the new msg will show up after the filter is removed.
        # Alternatively, can do `self._contents_pre_filter.append()`. That should work fine either with filter on or off.

        if scope is None:
            scope = self._contents_pre_filter
        if test_function is None:
            self._set_contents(scope)
        else:
            contents_type = type(self.contents)
            matching_widgets = contents_type([w for w in scope if test_function(w)])
            self._set_contents(matching_widgets)

    @property
    def is_filter_on(self) -> bool:
        return self.contents is not self._contents_pre_filter

    def move_item(self, w, pos, pos_in_prefilter=None) -> None:
        def try_move(seq, w, pos):
            try:
                ind = seq.index(w)
            except ValueError:
                # Widget might be absent from `body` e.g. while doing a search on contacts, or if the contact is 'new' (i.e. not in Contacts yet)
                return
            if ind == pos:
                return
            seq.insert(pos, seq.pop(ind))

        try_move(self.contents, w, pos)

        if self.is_filter_on:
            if pos_in_prefilter is None:
                pos_in_prefilter = pos
            try_move(self._contents_pre_filter, w, pos_in_prefilter)
