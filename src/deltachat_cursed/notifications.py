import os
import sys
from collections import OrderedDict
from typing import Dict, List

from deltachat import Message
from notifypy import Notify

from .util import APP_NAME, get_sender_name, get_summarytext, is_multiuser, shorten_text

__all__ = ["notify", "notify_msg", "notify_msgs"]


def _fake_notify(*args, **kwargs) -> None:
    pass


def _notify(
    account: str,
    title: str,
    body: str,
    image: str = None,
) -> None:
    notification = Notify()
    notification.title = title
    notification.message = body
    if image and os.path.exists(image):
        notification.icon = image
    notification.application_name = f"{APP_NAME} ({account})"
    notification.send(block=False)


def notify_msg(msg: Message) -> None:
    body = get_summarytext(msg, 2000)
    if is_multiuser(msg.chat):
        body = f"{shorten_text(get_sender_name(msg), 40)}: {body}"
    notify(
        account=shorten_text(msg.account.get_self_contact().addr, 30),
        title=msg.chat.get_name(),
        body=body,
        image=msg.chat.get_profile_image(),
    )


def notify_msgs(*args) -> None:
    chats: Dict[int, List[Message]] = OrderedDict()
    for msg in args:
        chats.setdefault(msg.chat.id, []).append(msg)

    for msgs in chats.values():
        if len(msgs) == 1:
            notify_msg(msgs[0])
            continue

        chat = msgs[0].chat
        multiuser = is_multiuser(chat)
        lines: List[str] = []
        for msg in msgs:
            text = get_summarytext(msg, 60)
            if multiuser:
                text = f"{shorten_text(get_sender_name(msg), 20)}: {text}"
            lines.append(text)

        notify(
            account=shorten_text(chat.account.get_self_contact().addr, 20),
            title=chat.get_name(),
            body="\n".join(lines),
            image=chat.get_profile_image(),
        )


if sys.platform != "linux" or "DISPLAY" in os.environ:
    notify = _notify
else:
    notify = _fake_notify
