# -*- coding: utf-8 -*-
#
# buffer.py - management of WeeChat buffers/nicklist
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
from pkg_resources import resource_filename

from qweechat.chat import ChatTextEdit
from qweechat.input import InputLineEdit
from qweechat.weechat import color

from PySide6 import QtCore, QtGui, QtWidgets


class GenericListWidget(QtWidgets.QListWidget):
    """Generic QListWidget with dynamic size."""

    def __init__(self, *args):
        super().__init__(*args)
        self.setMaximumWidth(100)
        self.setTextElideMode(QtCore.Qt.ElideNone)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        pal = self.palette()
        pal.setColor(QtGui.QPalette.Highlight, QtGui.QColor('#ddddff'))
        pal.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor('black'))
        self.setPalette(pal)

    def auto_resize(self):
        size = self.sizeHintForColumn(0)
        if size > 0:
            size += 4
        self.setMaximumWidth(size)

    def clear(self, *args):
        """Re-implement clear to set dynamic size after clear."""
        QtWidgets.QListWidget.clear(*(self,) + args)
        self.auto_resize()

    def addItem(self, *args):
        """Re-implement addItem to set dynamic size after add."""
        QtWidgets.QListWidget.addItem(*(self,) + args)
        self.auto_resize()

    def insertItem(self, *args):
        """Re-implement insertItem to set dynamic size after insert."""
        QtWidgets.QListWidget.insertItem(*(self,) + args)
        self.auto_resize()


class BufferListWidget(GenericListWidget):
    """Widget with list of buffers."""

    def __init__(self, *args):
        super().__init__(*args)

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


class BufferWidget(QtWidgets.QWidget):
    """
    Widget with (from top to bottom):
    title, chat + nicklist (optional) + prompt/input.
    """

    def __init__(self, display_nicklist=False):
        super().__init__()

        # title
        self.title = QtWidgets.QLineEdit()
        self.title.setFocusPolicy(QtCore.Qt.NoFocus)

        # splitter with chat + nicklist
        self.chat_nicklist = QtWidgets.QSplitter()
        self.chat_nicklist.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                         QtWidgets.QSizePolicy.Expanding)
        self.chat = ChatTextEdit(debug=False)
        self.chat_nicklist.addWidget(self.chat)
        self.nicklist = GenericListWidget()
        if not display_nicklist:
            self.nicklist.setVisible(False)
        self.chat_nicklist.addWidget(self.nicklist)

        # prompt + input
        self.hbox_edit = QtWidgets.QHBoxLayout()
        self.hbox_edit.setContentsMargins(0, 0, 0, 0)
        self.hbox_edit.setSpacing(0)
        self.input = InputLineEdit(self.chat)
        self.hbox_edit.addWidget(self.input)
        prompt_input = QtWidgets.QWidget()
        prompt_input.setLayout(self.hbox_edit)

        # vbox with title + chat/nicklist + prompt/input
        vbox = QtWidgets.QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        vbox.addWidget(self.title)
        vbox.addWidget(self.chat_nicklist)
        vbox.addWidget(prompt_input)

        self.setLayout(vbox)

    def set_title(self, title):
        """Set buffer title."""
        self.title.clear()
        if title is not None:
            self.title.setText(title)

    def set_prompt(self, prompt):
        """Set prompt."""
        if self.hbox_edit.count() > 1:
            self.hbox_edit.takeAt(0)
        if prompt is not None:
            label = QtWidgets.QLabel(prompt)
            label.setContentsMargins(0, 0, 5, 0)
            self.hbox_edit.insertWidget(0, label)


class Buffer(QtCore.QObject):
    """A WeeChat buffer."""

    bufferInput = QtCore.Signal(str, str)

    def __init__(self, data={}):
        QtCore.QObject.__init__(self)
        self.data = data
        self.nicklist = {}
        self.widget = BufferWidget(display_nicklist=self.data.get('nicklist',
                                                                  0))
        self.update_title()
        self.update_prompt()
        self.widget.input.textSent.connect(self.input_text_sent)

    def pointer(self):
        """Return pointer on buffer."""
        return self.data.get('__path', [''])[0]

    def update_title(self):
        """Update title."""
        try:
            self.widget.set_title(
                color.remove(self.data['title']))
        except Exception:  # noqa: E722
            # TODO: Debug print the exception to be fixed.
            # traceback.print_exc()
            self.widget.set_title(None)

    def update_prompt(self):
        """Update prompt."""
        try:
            self.widget.set_prompt(self.data['local_variables']['nick'])
        except Exception:  # noqa: E722
            self.widget.set_prompt(None)

    def input_text_sent(self, text):
        """Called when text has to be sent to buffer."""
        if self.data:
            self.bufferInput.emit(self.data['full_name'], text)

    def nicklist_add_item(self, parent, group, prefix, name, visible):
        """Add a group/nick in nicklist."""
        if group:
            self.nicklist[name] = {
                'visible': visible,
                'nicks': []
            }
        else:
            self.nicklist[parent]['nicks'].append({
                'prefix': prefix,
                'name': name,
                'visible': visible,
            })

    def nicklist_remove_item(self, parent, group, name):
        """Remove a group/nick from nicklist."""
        if group:
            if name in self.nicklist:
                del self.nicklist[name]
        else:
            if parent in self.nicklist:
                self.nicklist[parent]['nicks'] = [
                    nick for nick in self.nicklist[parent]['nicks']
                    if nick['name'] != name
                ]

    def nicklist_update_item(self, parent, group, prefix, name, visible):
        """Update a group/nick in nicklist."""
        if group:
            if name in self.nicklist:
                self.nicklist[name]['visible'] = visible
        else:
            if parent in self.nicklist:
                for nick in self.nicklist[parent]['nicks']:
                    if nick['name'] == name:
                        nick['prefix'] = prefix
                        nick['visible'] = visible
                        break

    def nicklist_refresh(self):
        """Refresh nicklist."""
        self.widget.nicklist.clear()
        for group in sorted(self.nicklist):
            for nick in sorted(self.nicklist[group]['nicks'],
                               key=lambda n: n['name']):
                prefix_color = {
                    '': '',
                    ' ': '',
                    '+': 'yellow',
                }
                color = prefix_color.get(nick['prefix'], 'green')
                if color:
                    icon = QtGui.QIcon(
                        resource_filename(__name__,
                                          'data/icons/bullet_%s_8x8.png' %
                                          color))
                else:
                    pixmap = QtGui.QPixmap(8, 8)
                    pixmap.fill()
                    icon = QtGui.QIcon(pixmap)
                item = QtWidgets.QListWidgetItem(icon, nick['name'])
                self.widget.nicklist.addItem(item)
                self.widget.nicklist.setVisible(True)
