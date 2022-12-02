# Changelog

## [v0.8.0]

### Changed

- removed support for per-folder configuration files
- changed default app configuration folder to `~/.config/curseddelta/`, `~/.curseddelta/` is still
  supported for backward compatibility (thanks @formula-spectre and @dotlambda)

### Fixed

- avoid crash if theme/skin definition has invalid values

## [v0.7.2]

### Fixed

- Updated to work with the new version (`2.0.0`) of `emoji` library

### Changed

- Added support for an space-delimited list of addresses as argument for `/kick` and `/add` commands

## [v0.7.1]

### Fixed

- update conversation on incoming messages
- avoid crashes on wrong command usage

## [v0.7.0]

### Added

- `--log` option to control debugging level, logs are saved in a file in the app's folder
- throttle events to avoid too much lag in the UI when several new messages arrive
- throttle notifications, group several notifications per chat
- "focused_item" property to theme to style the focused item in chatlist

### Changed

- removed `--show-ffi` CLI option
- improved failed delivery indicator style
- ignore case in auto-completion of nicks, emojis and commands

### Fixed

- show proper description in status bar for "Saved Messages" and "Device Messages" chats
- don't notify any system message
- avoid crash when using commands without a chat selected
- improve core events handling
- don't reset focus every time the chatlist is refreshed
- avoid crash if the user tries to send a message without selecting a chat
- avoid crash if theme.json or keymaps.json are invalid

## [v0.6.0]

### Added

- support for Delta Chat contact colors
- style pinned chats in chat list
- `/pin` and `/unpin` commands to pin/unpin chats
- `/mute` and `/unmute` commands to mute/unmute chats
- `/topic` command to change chat name
- `/clear` command to delete all messages in current chat
- support for importing/exporting encryption keys
- support for importing/exporting backups (including password-protected backups)
- support for creating and opening encrypted databases

### Changed

- `display_emoji` is enabled by default
- improved chatlist style
- if no password is provided to `init` subcommand a prompt will be shown to enter the password, entering an empty password will then trigger OAuth2, to avoid the prompt an empty password ("") can be passed to the CLI

## [v0.5.0]

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

## [v0.4.1]

### Changed

- moved `--port` option to `init` subcommand

### Fixed

- expand user home (`~`) in paths given to `/send` command
- fixed bug introduced in `v0.4.0` that caused some incoming messages to be not displayed

## [v0.4.0]

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

## [v0.3.1]

- fix `IndexError` in `ui/chatlist_widget.py`

## [v0.3.0]

- Updated code to work with the new `deltachat-1.58.0` API, "Contact Requests" chat was removed.
- improved notifications, added support for notifications in Windows and MacOS platforms.
- bugfix: save draft on exit.
- removed chat list item separators.
- code quality: added type hints, and improved CI to check code quality.
- added `/delete` command to delete chat and other command improvements.
- bugfix: mark chat as noticed when it is open, so the unread counter disappears.

## 0.2.0

- Initial release


[v0.8.0]: https://github.com/adbenitez/deltachat-cursed/compare/v0.7.2...v0.8.0
[v0.7.2]: https://github.com/adbenitez/deltachat-cursed/compare/v0.7.1...v0.7.2
[v0.7.1]: https://github.com/adbenitez/deltachat-cursed/compare/v0.7.0...v0.7.1
[v0.7.0]: https://github.com/adbenitez/deltachat-cursed/compare/v0.6.0...v0.7.0
[v0.6.0]: https://github.com/adbenitez/deltachat-cursed/compare/v0.5.0...v0.6.0
[v0.5.0]: https://github.com/adbenitez/deltachat-cursed/compare/v0.4.1...v0.5.0
[v0.4.1]: https://github.com/adbenitez/deltachat-cursed/compare/v0.4.0...v0.4.1
[v0.4.0]: https://github.com/adbenitez/deltachat-cursed/compare/v0.3.1...v0.4.0
[v0.3.1]: https://github.com/adbenitez/deltachat-cursed/compare/v0.3.0...v0.3.1
[v0.3.0]: https://github.com/adbenitez/deltachat-cursed/compare/v0.2.0...v0.3.0
