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

"""Chat area."""

import datetime

from PySide6 import QtCore, QtWidgets, QtGui

from qweechat import config
from qweechat.weechat import color


class ChatTextEdit(QtWidgets.QTextEdit):
    """Chat area."""

    def __init__(self, debug, *args):
        QtWidgets.QTextEdit.__init__(*(self,) + args)
        self.debug = debug
        self.readOnly = True
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setFontFamily('monospace')
        self._textcolor = self.textColor()
        self._bgcolor = QtGui.QColor('#FFFFFF')
        self._setcolorcode = {
            'F': (self.setTextColor, self._textcolor),
            'B': (self.setTextBackgroundColor, self._bgcolor)
        }
        self._setfont = {
            '*': self.setFontWeight,
            '_': self.setFontUnderline,
            '/': self.setFontItalic
        }
        self._fontvalues = {
            False: {
                '*': QtGui.QFont.Normal,
                '_': False,
                '/': False
            },
            True: {
                '*': QtGui.QFont.Bold,
                '_': True,
                '/': True
            }
        }
        self._color = color.Color(config.color_options(), self.debug)

    def display(self, time, prefix, text, forcecolor=None):
        if time == 0:
            now = datetime.datetime.now()
        else:
            now = datetime.datetime.fromtimestamp(float(time))
        self.setTextColor(QtGui.QColor('#999999'))
        self.insertPlainText(now.strftime('%H:%M '))
        prefix = self._color.convert(prefix)
        text = self._color.convert(text)
        if forcecolor:
            if prefix:
                prefix = '\x01(F%s)%s' % (forcecolor, prefix)
            text = '\x01(F%s)%s' % (forcecolor, text)
        if prefix:
            self._display_with_colors(prefix + ' ')
        if text:
            self._display_with_colors(text)
            if text[-1:] != '\n':
                self.insertPlainText('\n')
        else:
            self.insertPlainText('\n')
        self.scroll_bottom()

    def _display_with_colors(self, string):
        self.setTextColor(self._textcolor)
        self.setTextBackgroundColor(self._bgcolor)
        self._reset_attributes()
        items = string.split('\x01')
        for i, item in enumerate(items):
            if i > 0 and item.startswith('('):
                pos = item.find(')')
                if pos >= 2:
                    action = item[1]
                    code = item[2:pos]
                    if action == '+':
                        # set attribute
                        self._set_attribute(code[0], True)
                    elif action == '-':
                        # remove attribute
                        self._set_attribute(code[0], False)
                    else:
                        # reset attributes and color
                        if code == 'r':
                            self._reset_attributes()
                            self._setcolorcode[action][0](
                                self._setcolorcode[action][1])
                        else:
                            # set attributes + color
                            while code.startswith(('*', '!', '/', '_', '|',
                                                   'r')):
                                if code[0] == 'r':
                                    self._reset_attributes()
                                elif code[0] in self._setfont:
                                    self._set_attribute(
                                        code[0],
                                        not self._font[code[0]])
                                code = code[1:]
                            if code:
                                self._setcolorcode[action][0](
                                    QtGui.QColor(code))
                    item = item[pos+1:]
            if len(item) > 0:
                self.insertPlainText(item)

    def _reset_attributes(self):
        self._font = {}
        for attr in self._setfont:
            self._set_attribute(attr, False)

    def _set_attribute(self, attr, value):
        self._font[attr] = value
        self._setfont[attr](self._fontvalues[self._font[attr]][attr])

    def scroll_bottom(self):
        scroll = self.verticalScrollBar()
        scroll.setValue(scroll.maximum())
