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
# Input line (for chat or debug window).
#

import qt_compat
QtCore = qt_compat.import_module('QtCore')
QtGui = qt_compat.import_module('QtGui')


class InputLineEdit(QtGui.QLineEdit):
    """Input line."""

    bufferSwitchPrev = qt_compat.Signal()
    bufferSwitchNext = qt_compat.Signal()
    textSent = qt_compat.Signal(str)

    def __init__(self, scroll_widget):
        QtGui.QLineEdit.__init__(self)
        self.scroll_widget = scroll_widget
        self._history = []
        self._history_index = -1
        self.returnPressed.connect(self._input_return_pressed)

    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        bar = self.scroll_widget.verticalScrollBar()
        if modifiers == QtCore.Qt.ControlModifier and key == QtCore.Qt.Key_PageUp:
            self.bufferSwitchPrev.emit()
        elif modifiers == QtCore.Qt.ControlModifier and key == QtCore.Qt.Key_PageDown:
            self.bufferSwitchNext.emit()
        elif modifiers == QtCore.Qt.AltModifier and key == QtCore.Qt.Key_PageUp:
            bar.setValue(bar.value() - (bar.pageStep() / 10))
        elif modifiers == QtCore.Qt.AltModifier and key == QtCore.Qt.Key_PageDown:
            bar.setValue(bar.value() + (bar.pageStep() / 10))
        elif key == QtCore.Qt.Key_PageUp:
            bar.setValue(bar.value() - bar.pageStep())
        elif key == QtCore.Qt.Key_PageDown:
            bar.setValue(bar.value() + bar.pageStep())
        elif modifiers == QtCore.Qt.AltModifier and key == QtCore.Qt.Key_Home:
            bar.setValue(bar.minimum())
        elif modifiers == QtCore.Qt.AltModifier and key == QtCore.Qt.Key_End:
            bar.setValue(bar.maximum())
        elif key == QtCore.Qt.Key_Up:
            self._history_navigate(-1)
        elif key == QtCore.Qt.Key_Down:
            self._history_navigate(1)
        else:
            QtGui.QLineEdit.keyPressEvent(self, event)

    def _input_return_pressed(self):
        self._history.append(str(self.text()))
        self._history_index = len(self._history)
        self.textSent.emit(self.text())
        self.clear()

    def _history_navigate(self, direction):
        if self._history:
            self._history_index += direction
            if self._history_index < 0:
                self._history_index = 0
                return
            if self._history_index > len(self._history) - 1:
                self._history_index = len(self._history)
                self.clear()
                return
            self.setText(self._history[self._history_index])
