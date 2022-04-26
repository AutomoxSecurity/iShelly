![Logo](/assets/logo.png?raw=true)

iShelly is tool to generate macOS initial access vectors using [Prelude Operator](https://www.prelude.org/) payloads

# Currently supports:

Agents:

- PneumaEX

Modules:

- Installer Package w/ only preinstall script
- Installer Package w/ Launch Daemon for Persistence
- Installer Package w/ Installer Plugin
- Installer Package w/ JavaScript Functionality embedded
- Installer Package w/ JavaScript Functionality in Script
- Disk Image (DMG file)
- Macro VBA
- Macro SYLK with Excel


# Installation

This tool will only run on macOS, since the package builders are native to macOS.

1. Use your favorite virtualenv tool to create a virtualenv.
2. Launch Operator tool on macOS
3. `pip install -r requirements`
4. `python3 iShelly.py`

# Credit

This project is a rewrite of [Mystikal](https://github.com/D00MFist/Mystikal), an initial access payload generator for the Mythic c2 platform written by Leo Pitt.
