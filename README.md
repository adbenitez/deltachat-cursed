# Cursed Delta

A ncurses Delta Chat client developed in Python with the urwid library.

<p align="center">
  <img src="screenshots/e1.png" alt="screenshot of Cursed Delta"/>
</p>


## Dependencies

* [deltachat python bindings](https://github.com/deltachat/deltachat-core-rust/tree/master/python)
* [urwid](http://urwid.org)
* libnotify (optional)


## Installation

Install Cursed Delta through pip:

```
$ sudo pip3 install --upgrade https://github.com/adbenitez/deltachat-cursed/archive/master.tar.gz
```

If you want notifications (Debian example):

```
$ sudo apt-get install libnotify-bin
```


## Usage

After installation the command `curseddelta` should be available, or you can use `python3 -m cursed_delta`.
The first time you run `curseddelta` you need to specify an email and password:

```
$ curseddelta --email me@example.com --password H4rdPassw0rd
```

To use an already existent account:

```
$ curseddelta --db /path/to/your/account.db
```


#### Tips

- Messages will be dispalyed in red if someone mentions you.

- You will get a notification if someone mentions you in a group. (needs libnotify)

- The message marker '>' will be gray if the message is encrypted, if it is red that means message is not encrypted.

- Message will be gray until it is sent.

- You will get `✓` when the message is sent, `✓✓` when the message was noticed, or `✖` if message failed to send.

- You can tweak the app colors editing `~/.curseddelta/theme.json`

- You can tweak the app keymap editing `~/.curseddelta/keymap.json`

- If you like to use the mouse, you can use the mouse to select chats in the chat list, select the draft area or scroll in the message history.


#### Default Shortcuts

- Press `esc` to leave the text area.

- Press `q` to quit the Cursed Delta.

- Use `alt+enter` to insert a linebreak.

- Use `ctrl+r` to reply last message in chat.

- Use `ctrl+o` to open attachemnt in the last message in chat.

- You can navigate the chat list with `ctrl+p` and `ctrl+n`.

- Vim-like key bindings are also available, use `hjkl` to navigate
  between lists, use `i` to select the text area and `esc` to leave it.

- You can also use `ctrl+u` to clear the draft area.


### Commands

This are some temporal commands to do things that are not implemented yet using a menu:

- Send `/query user@example.com` to start a chat with `user@example.com`

- Send `/add user@example.com` to add `user@example.com` to the group where the command is sent.

- Send `/kick user@example.com` to remove `user@example.com` from the group where the command is sent.

- Send `/part` in a group to leave it.

- Send `/names` in a group to get the member list in the buffer, use `ctrl+u` to clear.

- Use `/join GroupName` to create a group with named `GroupName`

- Use `/accept n` to accept contact request number `n` (starting from 1)


## Credits

The user interface is based on [ncTelegram](https://github.com/Nanoseb/ncTelegram)


## License

Licensed GPLv3+, see the LICENSE file for details.

Copyright © 2020 Cursed Delta contributors.
