import os
import sys

from deltachat import Message
from notifypy import Notify

from .util import APP_NAME, get_sender_name, is_multiuser

__all__ = ["notify", "notify_msg"]


def _fake_notify(title: str, body: str, image: str) -> None:
    pass


def _notify(title: str, body: str, image: str = None) -> None:
    notification = Notify()
    notification.title = title
    notification.message = body
    if image and os.path.exists(image):
        notification.icon = image
    notification.application_name = APP_NAME
    notification.send(block=False)


def notify_msg(msg: Message) -> None:
    if is_multiuser(msg.chat):
        title = f"{msg.chat.get_name()}: {get_sender_name(msg)}"
    else:
        title = get_sender_name(msg)
    notify(body=msg.text, title=title, image=msg.chat.get_profile_image())


if sys.platform == "linux" and "DISPLAY" not in os.environ:
    notify = _fake_notify
else:
    notify = _notify
