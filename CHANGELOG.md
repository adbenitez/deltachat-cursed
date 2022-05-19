# Changelog

## [Unreleased]

### Added

- added `delta` command as a shorter alias for `curseddelta` command.

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


[Unreleased]: https://github.com/adbenitez/deltachat-cursed/compare/v0.3.1...HEAD
[0.3.1]: https://github.com/adbenitez/deltachat-cursed/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/adbenitez/deltachat-cursed/compare/v0.2.0...v0.3.0
