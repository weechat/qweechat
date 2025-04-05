# WeeChat Qt remote GUI

[![Build Status](https://github.com/weechat/qweechat/workflows/CI/badge.svg)](https://github.com/weechat/qweechat/actions?query=workflow%3A%22CI%22)

QWeeChat is a Qt remote GUI for WeeChat written in Python.

Homepage: https://weechat.org/

## Features

- Multi-platform (GNU/Linux, *BSD, Mac OS X, QNX, Windows & others).
- Free software, released under GPLv3.

![QWeeChat](https://weechat.org/media/images/screenshots/relay/medium/qweechat_shadow.png)

## Install

### Dependencies

QWeeChat requires:

- Python ≥ 3.7
- [PySide6](https://pypi.org/project/PySide6/)
- [WeeChat](https://weechat.org) ≥ 0.3.7, on local or remote machine, with relay plugin enabled and listening on a port with protocol "weechat"

### Install via source distribution

```
$ pip install .
```

## WeeChat setup

You have to add a relay port in WeeChat, for example on port 1234:

```
/set relay.network.password "mypass"
/relay add weechat 1234
```

## Connect to WeeChat

In QWeeChat, click on connect and enter fields:

- `hostname`: the IP address or hostname of your machine with WeeChat running
- `port`: the relay port (defined in WeeChat)
- `password`: the relay password (defined in WeeChat)
- `totp`: the Time-Based One-Time Password (optional, to set if required by WeeChat)

Options can be changed in file `~/.config/qweechat/qweechat.conf`.

## Copyright

Copyright © 2011-2025 [Sébastien Helleu](https://github.com/flashcode)

This file is part of QWeeChat, a Qt remote GUI for WeeChat.

QWeeChat is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
(at your option) any later version.

QWeeChat is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with QWeeChat.  If not, see <https://www.gnu.org/licenses/>.
