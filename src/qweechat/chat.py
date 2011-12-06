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
# Chat area.
#

import datetime
import qt_compat
QtCore = qt_compat.import_module('QtCore')
QtGui = qt_compat.import_module('QtGui')


class ChatTextEdit(QtGui.QTextEdit):
    """Chat area."""

    def __init__(self, *args):
        apply(QtGui.QTextEdit.__init__, (self,) + args)
        self.readOnly = True
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setFontFamily('monospace')

    def display(self, time, prefix, text, color=None):
        oldcolor = self.textColor()
        if time == 0:
            d = datetime.datetime.now()
        else:
            d = datetime.datetime.fromtimestamp(float(time))
        self.setTextColor(QtGui.QColor('#999999'))
        self.insertPlainText(d.strftime('%H:%M '))
        self.setTextColor(oldcolor)
        if prefix:
            self.insertPlainText(str(prefix).decode('utf-8') + ' ')
        if color:
            self.setTextColor(QtGui.QColor(color))
        self.insertPlainText(str(text).decode('utf-8'))
        if text[-1:] != '\n':
            self.insertPlainText('\n')
        if color:
            self.setTextColor(oldcolor)
        self.scroll_bottom()

    def scroll_bottom(self):
        bar = self.verticalScrollBar()
        bar.setValue(bar.maximum())
