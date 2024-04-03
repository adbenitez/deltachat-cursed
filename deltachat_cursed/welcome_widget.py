"""Welcome screen widget displayed when no chat is selected"""

import urwid


class WelcomeWidget(urwid.Filler):
    """Welcome screen widget displayed when no chat is selected"""

    def __init__(self) -> None:
        super().__init__(urwid.Text("(No chat selected)", align="center"))
