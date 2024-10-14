# -*- coding: utf-8 -*-
#
# debug.py - debug window
#
# Copyright (C) 2011-2024 Sébastien Helleu <flashcode@flashtux.org>
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

"""Debug window."""

from PySide6 import QtWidgets

from qweechat.chat import ChatTextEdit
from qweechat.input import InputLineEdit


class DebugDialog(QtWidgets.QDialog):
    """Debug dialog."""

    def __init__(self, *args):
        QtWidgets.QDialog.__init__(*(self,) + args)
        self.resize(1024, 768)
        self.setWindowTitle('Debug console')

        self.chat = ChatTextEdit(debug=True)
        self.input = InputLineEdit(self.chat)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.chat)
        vbox.addWidget(self.input)

        self.setLayout(vbox)
        self.show()

    def display_lines(self, lines):
        for line in lines:
            self.chat.display(*line[0], **line[1])
