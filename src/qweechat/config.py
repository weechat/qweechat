#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Sebastien Helleu <flashcode@flashtux.org>
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

#
# Configuration for QWeeChat (~/.qweechat/qweechat.conf)
#

import os, ConfigParser

CONFIG_DIR = '%s/.qweechat' % os.getenv('HOME')
CONFIG_FILENAME = '%s/qweechat.conf' % CONFIG_DIR

CONFIG_DEFAULT_SECTIONS = ('relay', 'look')
CONFIG_DEFAULT_OPTIONS = (('relay.server', ''),
                          ('relay.port', ''),
                          ('relay.password', ''),
                          ('relay.autoconnect', 'off'),
                          ('look.debug', 'off'),
                          ('look.statusbar', 'off'))


def read():
    """Read config file."""
    config = ConfigParser.RawConfigParser()
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
    return config

def write(config):
    """Write config file."""
    if not os.path.exists(CONFIG_DIR):
        os.mkdir(CONFIG_DIR, 0755)
    with open(CONFIG_FILENAME, 'wb') as cfg:
        config.write(cfg)
