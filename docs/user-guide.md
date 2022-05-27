# User Guide

## Installation

Install Cursed Delta with pip:

```
$ pip install -U deltachat-cursed
```

## Usage

After installation the command `delta` should be available, or you can use `python3 -m deltachat-cursed`. You can check if it is installed running the command `delta --help`

The first time you use Cursed Delta you need to configure your account:

```
$ delta init me@example.com YourStrongPassword  # omit password to use OAuth2
```

Then run `delta` command to start the application with your configured account.

If you want to use an already existent account, for example to open an account created with the official Delta Chat client:

```
$ delta --db ~/.config/DeltaChat/accounts/XXXXXXXXX/dc.db
```

## Tips

- Messages will be displayed in red if someone mentions you.
- You will get a notification if someone mentions you in a group.
- The message timestamp will be gray if the message is encrypted, or red if message is not encrypted.
- You will see `→` in your message if it is not sent yet, `✓` if it was send, `✓✓` when the message was read, or `✖` if the message was not delivered to some of the recipients.
- You can send emojis sending typing their string representation, for example: `:thumbs_up:`
- You can have emoji, contact names and commands autocompletion typing `:`, `@` or `/` and pressing <kbd>Tab</kbd>
- You can tweak the app colors editing `~/.curseddelta/theme.json`
- You can tweak the app keymap editing `~/.curseddelta/keymap.json`
- You can tweak the app settings editing `~/.curseddelta/curseddelta.conf`
- Put global theme, keymap, and config files in `/etc/curseddelta/`
- You can have per-folder config files, the application search for this files in the current working directory: `./curseddelta-theme.json`,  `./curseddelta-keymap.json`, `./curseddelta.conf`
- If you like to use the mouse, you can use the mouse to select chats in the chat list, select the draft area or scroll in the message history.

## Configuration File Options

Inside your `curseddelta.conf` file, create a `[global]` section and there you can set:

* `account_path`: the path to the default accouunt database to be open when the program is launched without `--db` option
* `notification`: set to `yes`/`no` to enable/disable notifications (default: yes)
* `date_format`: format of the date marker in chats (default: `%x`)
* `display_emoji`: set to `yes`/`no` to enable/disable emoji rendering (default: no)

## Default Shortcuts

- Press <kbd>Esc</kbd> to leave the draft/editing area.
- Press <kbd>q</kbd> to quit the program.
- Press <kbd>Ctrl</kbd> + <kbd>x</kbd> to toggle the chat list.
- Use <kbd>Meta</kbd> + <kbd>Enter</kbd> to enter new line.
- Use <kbd>Ctrl</kbd> + <kbd>o</kbd> to open attachemnt in the last message in chat.
- You can switch chats with <kbd>Meta</kbd> + <kbd>↑</kbd> and
  <kbd>Meta</kbd> + <kbd>↓</kbd>.
- Vim-like key bindings are also available, use <kbd>h</kbd> <kbd>j</kbd>
  <kbd>k</kbd> <kbd>l</kbd> to navigate between lists, use <kbd>i</kbd>
  to select the draft area and <kbd>Esc</kbd> to leave it.
- For shortcuts in the draft/editing area see: [urwid_readline](https://github.com/rr-/urwid_readline)

## Commands

This are some temporal commands to do things that are not implemented yet using a menu:

- Send `/query user@example.com` to start a private chat with `user@example.com`
- Send `/add user@example.com` to add `user@example.com` to the group where the command is sent
- Send `/kick user@example.com` to remove `user@example.com` from the group where the command is sent
- Send `/part` in a group to leave it
- Send `/delete` to delete the chat
- Send `/names` in a group to get the member list in the buffer, use
  <kbd>Ctrl</kbd> + <kbd>l</kbd> to clear
- Use `/join GroupName` to create a group named `GroupName`
- Send `/id` in a chat to get the chat's ID
- Use `/send /path/to/file.txt` to send a file attachment
- Send `/nick` YourNick to set your display name
- Send `/pin` / `/unpin` to pin/unpin chat
- To send a message starting with `/` use `//`
