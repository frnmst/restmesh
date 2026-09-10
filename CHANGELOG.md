<!--
SPDX-FileCopyrightText: 2026-2026 Franco Masotti (See /README.md)

SPDX-License-Identifier: GPL-3.0-or-later
-->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--TOC-->

- [Changelog](#changelog)
  - [\[Unreleased\]](#unreleased)
  - [\[0.6.0\] - 2026-09-10](#060---2026-09-10)
  - [\[0.5.0\] - 2026-09-04](#050---2026-09-04)
  - [\[0.4.0\] - 2026-08-31](#040---2026-08-31)
  - [\[0.3.0\] - 2026-08-15](#030---2026-08-15)
  - [\[0.2.0\] - 2026-08-04](#020---2026-08-04)
  - [\[0.1.0\] - 2026-07-30](#010---2026-07-30)

<!--TOC-->

## [Unreleased]

## [0.6.0] - 2026-09-10

### Changed

- `AppriseNotificationType` variable (`type`) now also accepts empty string
  (`""`).

### Added

- Basic BBS-style commands are now available:
  - `!api`
  - `!help`
  - `!motd`
  - `!ping`

  The meaning of each is explained in the readme.

### Fixed

- Safe install script is now available: old verification methods are
  deprecated.

## [0.5.0] - 2026-09-04

### Changed

- **Breaking:** Set `want_ack` to `True` and `want_response` to `False`. These
  two variable settings improve reliability for Meshtastic message delivery at
  the firmware level. The values were stopped in earlier versions.
- **Breaking:** Automatic API documentation is moved to a separate ./API.md
  file.

### Added

- New `onResponse` callback that shows basic logging on the server side if a
  message received a NAK or if `want_response` = `True`.

## [0.4.0] - 2026-08-31

### Added

- Text messages can now be cleaned using regex substitution right before the
  message is sent.

### Fixed

- Modem variable is now passed correctly to the meshtastic Python submodule.

## [0.3.0] - 2026-08-15

### Added

- `--version` option is now available in the CLI.

### Changed

- **Breaking:** All variables and arguments exposed via the API are
  snake\_case.

## [0.2.0] - 2026-08-04

### Changed

- **Breaking:** Change project official home from Codeberg to GitHub: Codeberg
  is suffering from infrastructure reliability issues.
- Meshtastic operations now happen in a new separate Python module.

### Fixed

- Python annotations are now more descriptive.

## [0.1.0] - 2026-07-30

### Added

- First release.
