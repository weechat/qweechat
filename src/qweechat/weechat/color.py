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
# Remove or replace colors in WeeChat strings.
#

import re

RE_COLOR_ATTRS = r'[*!/_|]*'
RE_COLOR_STD = r'(?:%s\d{2})' % RE_COLOR_ATTRS
RE_COLOR_EXT = r'(?:@%s\d{5})' % RE_COLOR_ATTRS
RE_COLOR_ANY = r'(?:%s|%s)' % (RE_COLOR_STD, RE_COLOR_EXT)
RE_COLOR = re.compile(r'(\x19(?:\d{2}|F%s|B\d{2}|B@\d{5}|\\*%s(,%s)?|@\d{5}|b.|\x1C))|\x1A.|\x1B.|\x1C'
                      % (RE_COLOR_ANY, RE_COLOR_ANY, RE_COLOR_ANY))

def _replace_color(match):
    return match.group(0)

def remove(text):
    """Remove colors in a WeeChat string."""
    if not text:
        return text
    return re.sub(RE_COLOR, '', text)
    #return RE_COLOR.sub(_replace_color, text)
