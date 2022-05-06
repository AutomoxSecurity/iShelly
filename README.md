![Logo](/assets/logo.png?raw=true)

iShelly is tool to generate macOS initial access vectors using [Prelude Operator](https://www.prelude.org/) payloads.

It automates the following:
- Compilation of Prelude Operator agents
- Staging of payloads
- Generation of initial access vectors on macOS. This includes various installer and disk image techniques (for a complete list, see the list of currently supported modules)

![iShellyDemo](/assets/iShelly.gif)

# Currently supports:

Agents:

- PneumaEX
- Pneuma (supported on free Prelude Operator license!)

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
3. `pip3 install -r requirements`
4. `python3 iShelly.py`

# Release Notes

## 1.1
- Added a temporary patch to fix https://github.com/preludeorg/pneuma/pull/115
- Added support for Pneuma. This means you can use iShelly on the free version of Prelude Operator
- Added support for agent names, which are passed on the command line. This makes it easy to identify agents in Operator that are tied to a specific initial access technique. It also makes it easy for the blue team to hunt for a specific technique: use the cmdline.

# Credit

This project is a rewrite of [Mystikal](https://github.com/D00MFist/Mystikal), an initial access payload generator for the Mythic c2 platform written by Leo Pitt.
