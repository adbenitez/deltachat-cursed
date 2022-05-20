import os
import sys

from notifypy import Notify

from ..util import APP_NAME

__all__ = ["notify", "notify_msg"]
app_icon = os.path.join(os.path.abspath(os.path.dirname(__file__)), "logo.png")


def _fake_notify(title: str, body: str, image: str) -> None:
    pass


def notify_msg(msg) -> None:
    image = msg.chat.get_profile_image()
    if msg.chat.is_group():
        title = f"{msg.chat.get_name()}: {msg.get_sender_contact().display_name}"
    else:
        title = msg.get_sender_contact().display_name
    notify(body=msg.text, title=title, image=image)


def _notify(title: str, body: str, image: str = None) -> None:
    notification = Notify()
    notification.title = title
    notification.message = body
    notification.icon = image if image and os.path.exists(image) else app_icon
    notification.application_name = APP_NAME
    notification.send(block=False)


if sys.platform == "linux" and "DISPLAY" not in os.environ:
    notify = _fake_notify
else:
    notify = _notify
