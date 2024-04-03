# Cursed Delta

> a lightweight Delta Chat client for the command line

<p align="center">
  <img src="https://github.com/adbenitez/deltachat-cursed/blob/master/screenshots/e1.png?raw=true" alt="screenshot of Cursed Delta"/>
</p>

[![Latest Release](https://img.shields.io/pypi/v/deltachat-cursed.svg)](https://pypi.org/project/deltachat-cursed)
[![Downloads](https://pepy.tech/badge/deltachat-cursed)](https://pepy.tech/project/deltachat-cursed)
[![License](https://img.shields.io/pypi/l/deltachat-cursed.svg)](https://pypi.org/project/deltachat-cursed)
[![CI](https://github.com/adbenitez/deltachat-cursed/actions/workflows/python-ci.yml/badge.svg)](https://github.com/adbenitez/deltachat-cursed/actions/workflows/python-ci.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Cursed Delta is a ncurses Delta Chat client developed in Python with the urwid library.

#### Features

- [X] Create accounts
- [X] Tweak account configuration (ex. set display name and status)
- [X] Ability to send text messages :)
- [X] Read receipts ✓✓
- [X] Display quoted messages
- [ ] Account switcher
- [ ] Chat operations: delete, pin/unpin, mute/unmute, archive/unarchive, add/remove members, etc.
- [ ] Message operations: reply, delete, open attachment/links, see info, jump to quote
- [ ] Import/export keys and backups
- [ ] Ability to send files
- [ ] Notifications
- [ ] Support for contact verification and group invitations links
- [ ] Block/unblock contacts and see the list of blocked contacts
- [ ] See contact list
- [ ] Search messages and chats
- [ ] Open HTML messages
- [ ] View archived chats

## Installation

Install Cursed Delta with pip:

```
$ pip install -U deltachat-cursed
```

This program depends on the `deltachat-rpc-server` program to be installed in your system,
if you want to try to install it using pip run:

```
$ pip install -U deltachat-cursed[full]
```

After installation the command `delta` should be available.
For more tips and info check [the user guide](./docs/user-guide.md)
