import os
import sys

from .. import APP_NAME

__all__ = ["notify", "notify_msg"]
app_logo = os.path.join(os.path.abspath(os.path.dirname(__file__)), "logo.png")


def _fake_notify(*args, **kwargs) -> None:
    pass


def _notify_send(title: str, body: str, image: str = None) -> None:
    if not image:
        image = app_logo
    subprocess.run(["notify-send", "-a", APP_NAME, "-i", image, title, body])


def _notify(title: str, body: str, image: str = None) -> None:
    if not image:
        image = app_logo
    kwargs = dict(title=title)
    if image and sys.platform == "linux":
        kwargs["image"] = image
        kwargs["app_name"] = APP_NAME
    notification(body, **kwargs)


def notify_msg(msg) -> None:
    image = msg.chat.get_profile_image() or app_logo
    if msg.chat.is_group():
        title = "{}: {}".format(
            msg.chat.get_name(), msg.get_sender_contact().display_name
        )
    else:
        title = msg.get_sender_contact().display_name
    notify(body=msg.text, title=title, image=image)


try:
    from notify import notification

    notify = _notify
except:
    try:
        import subprocess

        subprocess.check_output(["notify-send", "--help"])
        notify = _notify_send
    except:
        notify = _fake_notify
if sys.platform == "linux" and "DISPLAY" not in os.environ:
    notify = _fake_notify
