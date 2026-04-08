# Changelog

## v0.2.0 - 2026-04-08

- Added a full pytest-based test suite covering app handlers, overlay behavior, dot views, dot controller logic, key utilities, JSON utilities, and touch management.
- Fixed multiple runtime and state-management issues in dot handling, overlay refresh behavior, touch updates, and key string formatting.
- Fixed app startup with modern `pynput` by making keyboard listener callbacks compatible with `Listener` construction.
- Updated supported Python versions and dependency constraints to modern package releases, including Python 3.10+.
