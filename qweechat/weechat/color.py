# -*- coding: utf-8 -*-
#
# color.py - remove/replace colors in WeeChat strings
#
# Copyright (C) 2011-2021 Sébastien Helleu <flashcode@flashtux.org>
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

import re
import logging

RE_COLOR_ATTRS = r'[*!/_|]*'
RE_COLOR_STD = r'(?:%s\d{2})' % RE_COLOR_ATTRS
RE_COLOR_EXT = r'(?:@%s\d{5})' % RE_COLOR_ATTRS
RE_COLOR_ANY = r'(?:%s|%s)' % (RE_COLOR_STD, RE_COLOR_EXT)
# \x19: color code, \x1A: set attribute, \x1B: remove attribute, \x1C: reset
RE_COLOR = re.compile(
    r'(\x19(?:\d{2}|F%s|B\d{2}|B@\d{5}|E|\\*%s(,%s)?|@\d{5}|b.|\x1C))|\x1A.|'
    r'\x1B.|\x1C'
    % (RE_COLOR_ANY, RE_COLOR_ANY, RE_COLOR_ANY))

TERMINAL_COLORS = \
    '000000cd000000cd00cdcd000000cdcd00cd00cdcde5e5e5' \
    '4d4d4dff000000ff00ffff000000ffff00ff00ffffffffff' \
    '00000000002a0000550000800000aa0000d4002a00002a2a' \
    '002a55002a80002aaa002ad400550000552a005555005580' \
    '0055aa0055d400800000802a0080550080800080aa0080d4' \
    '00aa0000aa2a00aa5500aa8000aaaa00aad400d40000d42a' \
    '00d45500d48000d4aa00d4d42a00002a002a2a00552a0080' \
    '2a00aa2a00d42a2a002a2a2a2a2a552a2a802a2aaa2a2ad4' \
    '2a55002a552a2a55552a55802a55aa2a55d42a80002a802a' \
    '2a80552a80802a80aa2a80d42aaa002aaa2a2aaa552aaa80' \
    '2aaaaa2aaad42ad4002ad42a2ad4552ad4802ad4aa2ad4d4' \
    '55000055002a5500555500805500aa5500d4552a00552a2a' \
    '552a55552a80552aaa552ad455550055552a555555555580' \
    '5555aa5555d455800055802a5580555580805580aa5580d4' \
    '55aa0055aa2a55aa5555aa8055aaaa55aad455d40055d42a' \
    '55d45555d48055d4aa55d4d480000080002a800055800080' \
    '8000aa8000d4802a00802a2a802a55802a80802aaa802ad4' \
    '80550080552a8055558055808055aa8055d480800080802a' \
    '8080558080808080aa8080d480aa0080aa2a80aa5580aa80' \
    '80aaaa80aad480d40080d42a80d45580d48080d4aa80d4d4' \
    'aa0000aa002aaa0055aa0080aa00aaaa00d4aa2a00aa2a2a' \
    'aa2a55aa2a80aa2aaaaa2ad4aa5500aa552aaa5555aa5580' \
    'aa55aaaa55d4aa8000aa802aaa8055aa8080aa80aaaa80d4' \
    'aaaa00aaaa2aaaaa55aaaa80aaaaaaaaaad4aad400aad42a' \
    'aad455aad480aad4aaaad4d4d40000d4002ad40055d40080' \
    'd400aad400d4d42a00d42a2ad42a55d42a80d42aaad42ad4' \
    'd45500d4552ad45555d45580d455aad455d4d48000d4802a' \
    'd48055d48080d480aad480d4d4aa00d4aa2ad4aa55d4aa80' \
    'd4aaaad4aad4d4d400d4d42ad4d455d4d480d4d4aad4d4d4' \
    '0808081212121c1c1c2626263030303a3a3a4444444e4e4e' \
    '5858586262626c6c6c7676768080808a8a8a9494949e9e9e' \
    'a8a8a8b2b2b2bcbcbcc6c6c6d0d0d0dadadae4e4e4eeeeee'

# WeeChat basic colors (color name, index in terminal colors)
WEECHAT_BASIC_COLORS = (
    ('default', 0), ('black', 0), ('darkgray', 8), ('red', 1),
    ('lightred', 9), ('green', 2), ('lightgreen', 10), ('brown', 3),
    ('yellow', 11), ('blue', 4), ('lightblue', 12), ('magenta', 5),
    ('lightmagenta', 13), ('cyan', 6), ('lightcyan', 14), ('gray', 7),
    ('white', 0))


log = logging.getLogger(__name__)


class Color():
    def __init__(self, color_options, debug=False):
        self.color_options = color_options
        self.debug = debug

    def _rgb_color(self, index):
        color = TERMINAL_COLORS[index*6:(index*6)+6]
        r = int(color[0:2], 16) * 0.85
        g = int(color[2:4], 16) * 0.85
        b = int(color[4:6], 16) * 0.85
        return '%02x%02x%02x' % (r, g, b)

    def _convert_weechat_color(self, color):
        try:
            index = int(color)
            return '\x01(Fr%s)' % self.color_options[index]
        except:  # noqa: E722
            log.debug('Error decoding WeeChat color "%s"' % color)
            return ''

    def _convert_terminal_color(self, fg_bg, attrs, color):
        try:
            index = int(color)
            return '\x01(%s%s#%s)' % (fg_bg, attrs, self._rgb_color(index))
        except:  # noqa: E722
            log.debug('Error decoding terminal color "%s"' % color)
            return ''

    def _convert_color_attr(self, fg_bg, color):
        extended = False
        if color[0].startswith('@'):
            extended = True
            color = color[1:]
        attrs = ''
        # keep_attrs = False
        while color.startswith(('*', '!', '/', '_', '|')):
            # TODO: manage the "keep attributes" flag
            # if color[0] == '|':
            #    keep_attrs = True
            attrs += color[0]
            color = color[1:]
        if extended:
            return self._convert_terminal_color(fg_bg, attrs, color)
        try:
            index = int(color)
            return self._convert_terminal_color(fg_bg, attrs,
                                                WEECHAT_BASIC_COLORS[index][1])
        except:  # noqa: E722
            log.debug('Error decoding color "%s"' % color)
            return ''

    def _attrcode_to_char(self, code):
        codes = {
            '\x01': '*',
            '\x02': '!',
            '\x03': '/',
            '\x04': '_',
        }
        return codes.get(code, '')

    def _convert_color(self, match):
        color = match.group(0)
        if color[0] == '\x19':
            if color[1] == 'b':
                # bar code, ignored
                return ''
            elif color[1] == '\x1C':
                # reset
                return '\x01(Fr)\x01(Br)'
            elif color[1] in ('F', 'B'):
                # foreground or background
                return self._convert_color_attr(color[1], color[2:])
            elif color[1] == '*':
                # foreground with optional background
                items = color[2:].split(',')
                s = self._convert_color_attr('F', items[0])
                if len(items) > 1:
                    s += self._convert_color_attr('B', items[1])
                return s
            elif color[1] == '@':
                # direct ncurses pair number, ignored
                return ''
            elif color[1] == 'E':
                # text emphasis, ignored
                return ''
            if color[1:].isdigit():
                return self._convert_weechat_color(int(color[1:]))
            # color code
            pass
        elif color[0] == '\x1A':
            # set attribute
            return '\x01(+%s)' % self._attrcode_to_char(color[1])
        elif color[0] == '\x1B':
            # remove attribute
            return '\x01(-%s)' % self._attrcode_to_char(color[1])
        elif color[0] == '\x1C':
            # reset
            return '\x01(Fr)\x01(Br)'
        # should never be executed!
        return match.group(0)

    def _convert_color_debug(self, match):
        group = match.group(0)
        for code in (0x01, 0x02, 0x03, 0x04, 0x19, 0x1A, 0x1B):
            group = group.replace(chr(code), '<x%02X>' % code)
        return group

    def convert(self, text):
        if not text:
            return ''
        if self.debug:
            return RE_COLOR.sub(self._convert_color_debug, text)
        else:
            return RE_COLOR.sub(self._convert_color, text)


def remove(text):
    """Remove colors in a WeeChat string."""
    if not text:
        return ''
    return re.sub(RE_COLOR, '', text)
