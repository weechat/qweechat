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
# Buffers.
#

import qt_compat
QtCore = qt_compat.import_module('QtCore')
QtGui = qt_compat.import_module('QtGui')
from chat import ChatTextEdit
from input import InputLineEdit


class GenericListWidget(QtGui.QListWidget):
    """Generic QListWidget with dynamic size."""

    def __init__(self, *args):
        apply(QtGui.QListWidget.__init__, (self,) + args)
        self.setMaximumWidth(100)
        self.setTextElideMode(QtCore.Qt.ElideNone)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        pal = self.palette()
        pal.setColor(QtGui.QPalette.Highlight, QtGui.QColor('#ddddff'))
        pal.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor('black'))
        self.setPalette(pal)

    def addItem(self, *args):
        """Re-implement addItem to set dynamic size after add."""
        apply(QtGui.QListWidget.addItem, (self,) + args)
        self.setMaximumWidth(self.sizeHintForColumn(0) + 4)


class BufferListWidget(GenericListWidget):
    """Widget with list of buffers."""

    def __init__(self, *args):
        apply(GenericListWidget.__init__, (self,) + args)

    def switch_prev_buffer(self):
        if self.currentRow() > 0:
            self.setCurrentRow(self.currentRow() - 1)
        else:
            self.setCurrentRow(self.count() - 1)

    def switch_next_buffer(self):
        if self.currentRow() < self.count() - 1:
            self.setCurrentRow(self.currentRow() + 1)
        else:
            self.setCurrentRow(0)


class BufferWidget(QtGui.QWidget):
    """Widget with (from top to bottom): title, chat + nicklist (optional) + prompt/input."""

    def __init__(self, display_nicklist=False):
        QtGui.QWidget.__init__(self)

        # title
        self.title = QtGui.QLineEdit()

        # splitter with chat + nicklist
        self.chat_nicklist = QtGui.QSplitter()
        self.chat_nicklist.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.chat = ChatTextEdit()
        self.chat_nicklist.addWidget(self.chat)
        self.nicklist = GenericListWidget()
        if not display_nicklist:
            self.nicklist.setVisible(False)
        self.chat_nicklist.addWidget(self.nicklist)

        # prompt + input
        hbox_edit = QtGui.QHBoxLayout()
        hbox_edit.setContentsMargins(0, 0, 0, 0)
        hbox_edit.setSpacing(0)
        self.prompt = QtGui.QLabel('FlashCode')
        self.prompt.setContentsMargins(0, 0, 5, 0)
        hbox_edit.addWidget(self.prompt)
        self.input = InputLineEdit(self.chat)
        hbox_edit.addWidget(self.input)
        prompt_input = QtGui.QWidget()
        prompt_input.setLayout(hbox_edit)
        prompt_input.setContentsMargins(0, 0, 0, 0)

        # vbox with title + chat/nicklist + prompt/input
        vbox = QtGui.QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        vbox.addWidget(self.title)
        vbox.addWidget(self.chat_nicklist)
        vbox.addWidget(prompt_input)

        self.setLayout(vbox)

    def set_title(self, title):
        """Set buffer title."""
        self.title.clear()
        if not title is None:
            self.title.setText(title)


class Buffer(QtCore.QObject):
    """A WeeChat buffer."""

    bufferInput = qt_compat.Signal(str, str)

    def __init__(self, data={}):
        QtCore.QObject.__init__(self)
        self.data = data
        self.widget = BufferWidget(display_nicklist=self.data.get('nicklist', 0))
        if self.data and self.data['title']:
            self.widget.set_title(self.data['title'])
        self.widget.input.textSent.connect(self.input_text_sent)

    def pointer(self):
        """Return pointer on buffer."""
        return self.data.get('__path', [''])[0]

    def input_text_sent(self, text):
        """Called when text has to be sent to buffer."""
        if self.data:
            self.bufferInput.emit(self.data['full_name'], text)

    def add_nick(self, prefix, nick):
        """Add a nick to nicklist."""
        self.widget.nicklist.addItem('%s%s' % (prefix, nick))
