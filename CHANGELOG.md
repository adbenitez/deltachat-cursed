# Changelog

## [Unreleased]

### Added

- new boolean setting `display_emoji` in `curseddelta.conf` file, to enable/disable display of emoji in chat names, contact names, and messages.
- support for sending emoji typing its name between `:`, example `:thumbs_up:`
- emoji autocompletion when `Tab` is pressed after a `:` character
- contact names autocompletion when `Tab` is pressed after a `@` character
- command autocompletion when `Tab` is pressed
- support for messages with quotes
- "failed" theme attribute, to style failed message badge
- support for messages with impersonation/override names
- notify reply-mentions in muted groups
- support for marking messages as read while they are read
- `/nick` command to set/show nick / display name
- `--version` argument to print program version

### Changed

- renamed `[general]` configuration section to `[global]`
- improved chat information in status bar, detect properly mailing lists
- show notifications for all unmuted chats instead
- removed `ctrl + r` shortcut until a proper way to reply a message is added
- removed "hour" and "pending" theme attributes
- removed `>` status indicator, encryption status is now displayed in the message timestamp
- show message delivery status beside the user's name
- message layout tweaked
- truncate long names and addresses in the status bar, and long chat names in the chat list
- improved notifications, better notification summaries, show account address to differentiate between notifications of several running instances of Cursed Delta
- don't highlight muted chats with unread messages
- show own display name instead of "Me" for self messages
- day marker style

### Fixed

- avoid `RuntimeError` on `AccountPlugin.chatlist_changed()`
- search for `curseddelta.conf` inside `/etc/curseddelta/` as documented
- cursor is shown properly at the end of the input field when a draft exists
- improved app speed loading chats and messages
- show chat name in notifications for mailing lists
- don't notify mentions in muted direct/private chats
- draft saving

## [0.4.1]

### Changed

- moved `--port` option to `init` subcommand

### Fixed

- expand user home (`~`) in paths given to `/send` command
- fixed bug introduced in `v0.4.0` that caused some incoming messages to be not displayed

## [0.4.0]

### Added

- `delta` command as a shorter alias for `curseddelta` command
- `send` subcommand to send a message from CLI
- `list` subcommand to print chat list and see chat IDs that can be used with `send` subcommand
- `/id` command in the input field to get chat ID of the chat where the command is sent
- `/send` command to send file in current chat passing the path to a file

### Changed

- improved error messages when trying to use an account that is not configured
- replaced `--set-conf` and `--get-conf` options with a `config` subcommand
- replaced `--email` and `--password` options with an `init` subcommand
- pressing `enter` now sends message and `meta enter` now inserts new line
- show file path URI instead of `[File]` token in messages with file attachments, this allows to open files with clicks in some Terminals
- replaced `➜` from chat list items with `@` (for direct chats) or `#` (for groups) indicators

### Fixed

- end UI gracefully when `ctrl + C` is pressed
- clear draft if command doesn't print any text
- don't print "unknown command" for `/add`, `/kick` and `/part` commands
- capture errors in commands and display message in the draft area
- avoid crash if user tries to send message in a chat where it is not possible to send messages (ex. user is not member, or it is the "Device Messages" chat)
- hide "Archived Chats" (special chat) from the chat list

## [0.3.1]

- fix `IndexError` in `ui/chatlist_widget.py`

## [0.3.0]

- Updated code to work with the new `deltachat-1.58.0` API, "Contact Requests" chat was removed.
- improved notifications, added support for notifications in Windows and MacOS platforms.
- bugfix: save draft on exit.
- removed chat list item separators.
- code quality: added type hints, and improved CI to check code quality.
- added `/delete` command to delete chat and other command improvements.
- bugfix: mark chat as noticed when it is open, so the unread counter disappears.

## 0.2.0

- Initial release


[Unreleased]: https://github.com/adbenitez/deltachat-cursed/compare/v0.4.1...HEAD
[0.4.1]: https://github.com/adbenitez/deltachat-cursed/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/adbenitez/deltachat-cursed/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/adbenitez/deltachat-cursed/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/adbenitez/deltachat-cursed/compare/v0.2.0...v0.3.0
