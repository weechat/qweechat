#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# connection.py - connection window
#
# Copyright (C) 2011-2014 Sébastien Helleu <flashcode@flashtux.org>
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

import qt_compat
QtGui = qt_compat.import_module('QtGui')


class ConnectionDialog(QtGui.QDialog):
    """Connection window."""

    def __init__(self, values, *args):
        QtGui.QDialog.__init__(*(self,) + args)
        self.values = values
        self.setModal(True)

        grid = QtGui.QGridLayout()
        grid.setSpacing(10)

        self.fields = {}
        for y, field in enumerate(('server', 'port', 'password', 'lines')):
            grid.addWidget(QtGui.QLabel(field.capitalize()), y, 0)
            lineEdit = QtGui.QLineEdit()
            lineEdit.setFixedWidth(200)
            if field == 'password':
                lineEdit.setEchoMode(QtGui.QLineEdit.Password)
            if field == 'lines':
                validator = QtGui.QIntValidator(0, 2147483647, self)
                lineEdit.setValidator(validator)
                lineEdit.setFixedWidth(80)
            lineEdit.insert(self.values[field])
            grid.addWidget(lineEdit, y, 1)
            self.fields[field] = lineEdit
            if field == 'port':
                ssl = QtGui.QCheckBox('SSL')
                ssl.setChecked(self.values['ssl'] == 'on')
                grid.addWidget(ssl, y, 2)
                self.fields['ssl'] = ssl

        self.dialog_buttons = QtGui.QDialogButtonBox()
        self.dialog_buttons.setStandardButtons(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        self.dialog_buttons.rejected.connect(self.close)

        grid.addWidget(self.dialog_buttons, 4, 0, 1, 2)
        self.setLayout(grid)
        self.show()
