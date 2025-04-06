#
# config.py - configuration for QWeeChat
#
# SPDX-FileCopyrightText: 2011-2025 Sébastien Helleu <flashcode@flashtux.org>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of QWeeChat, a Qt remote GUI for WeeChat.
#
# QWeeChat is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# QWeeChat is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with QWeeChat.  If not, see <http://www.gnu.org/licenses/>.
#

"""Configuration for QWeeChat."""

import configparser
import os

from pathlib import Path

CONFIG_DIR = '%s/.config/qweechat' % os.getenv('HOME')
CONFIG_FILENAME = '%s/qweechat.conf' % CONFIG_DIR

CONFIG_DEFAULT_RELAY_LINES = 50

CONFIG_DEFAULT_SECTIONS = ('relay', 'look', 'color')
CONFIG_DEFAULT_OPTIONS = (('relay.hostname', ''),
                          ('relay.port', ''),
                          ('relay.ssl', 'off'),
                          ('relay.password', ''),
                          ('relay.autoconnect', 'off'),
                          ('relay.lines', str(CONFIG_DEFAULT_RELAY_LINES)),
                          ('look.debug', 'off'),
                          ('look.statusbar', 'off'))

# Default colors for WeeChat color options (option name, #rgb value)
CONFIG_DEFAULT_COLOR_OPTIONS = (
    ('separator', '#000066'),  # 0
    ('chat', '#000000'),  # 1
    ('chat_time', '#999999'),  # 2
    ('chat_time_delimiters', '#000000'),  # 3
    ('chat_prefix_error', '#FF6633'),  # 4
    ('chat_prefix_network', '#990099'),  # 5
    ('chat_prefix_action', '#000000'),  # 6
    ('chat_prefix_join', '#00CC00'),  # 7
    ('chat_prefix_quit', '#CC0000'),  # 8
    ('chat_prefix_more', '#CC00FF'),  # 9
    ('chat_prefix_suffix', '#330099'),  # 10
    ('chat_buffer', '#000000'),  # 11
    ('chat_server', '#000000'),  # 12
    ('chat_channel', '#000000'),  # 13
    ('chat_nick', '#000000'),  # 14
    ('chat_nick_self', '*#000000'),  # 15
    ('chat_nick_other', '#000000'),  # 16
    ('', '#000000'),  # 17 (nick1 -- obsolete)
    ('', '#000000'),  # 18 (nick2 -- obsolete)
    ('', '#000000'),  # 19 (nick3 -- obsolete)
    ('', '#000000'),  # 20 (nick4 -- obsolete)
    ('', '#000000'),  # 21 (nick5 -- obsolete)
    ('', '#000000'),  # 22 (nick6 -- obsolete)
    ('', '#000000'),  # 23 (nick7 -- obsolete)
    ('', '#000000'),  # 24 (nick8 -- obsolete)
    ('', '#000000'),  # 25 (nick9 -- obsolete)
    ('', '#000000'),  # 26 (nick10 -- obsolete)
    ('chat_host', '#666666'),  # 27
    ('chat_delimiters', '#9999FF'),  # 28
    ('chat_highlight', '#3399CC'),  # 29
    ('chat_read_marker', '#000000'),  # 30
    ('chat_text_found', '#000000'),  # 31
    ('chat_value', '#000000'),  # 32
    ('chat_prefix_buffer', '#000000'),  # 33
    ('chat_tags', '#000000'),  # 34
    ('chat_inactive_window', '#000000'),  # 35
    ('chat_inactive_buffer', '#000000'),  # 36
    ('chat_prefix_buffer_inactive_buffer', '#000000'),  # 37
    ('chat_nick_offline', '#000000'),  # 38
    ('chat_nick_offline_highlight', '#000000'),  # 39
    ('chat_nick_prefix', '#000000'),  # 40
    ('chat_nick_suffix', '#000000'),  # 41
    ('emphasis', '#000000'),  # 42
    ('chat_day_change', '#000000'),  # 43
)
config_color_options = []


def read():
    """Read config file."""
    global config_color_options
    config = configparser.RawConfigParser()
    if os.path.isfile(CONFIG_FILENAME):
        config.read(CONFIG_FILENAME)

    # add missing sections/options
    for section in CONFIG_DEFAULT_SECTIONS:
        if not config.has_section(section):
            config.add_section(section)
    for option in reversed(CONFIG_DEFAULT_OPTIONS):
        section, name = option[0].split('.', 1)
        if not config.has_option(section, name):
            config.set(section, name, option[1])
    section = 'color'
    for option in reversed(CONFIG_DEFAULT_COLOR_OPTIONS):
        if option[0] and not config.has_option(section, option[0]):
            config.set(section, option[0], option[1])

    # build list of color options
    config_color_options = []
    for option in CONFIG_DEFAULT_COLOR_OPTIONS:
        if option[0]:
            config_color_options.append(config.get('color', option[0]))
        else:
            config_color_options.append('#000000')

    return config


def write(config):
    """Write config file."""
    Path(CONFIG_DIR).mkdir(mode=0o0700, parents=True, exist_ok=True)
    with open(CONFIG_FILENAME, 'w') as cfg:
        config.write(cfg)


def color_options():
    """Return color options."""
    return config_color_options
