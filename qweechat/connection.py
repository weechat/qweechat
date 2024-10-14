# -*- coding: utf-8 -*-
#
# connection.py - connection window
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

"""Connection window."""

from PySide6 import QtGui, QtWidgets


class ConnectionDialog(QtWidgets.QDialog):
    """Connection window."""

    def __init__(self, values, *args):
        super().__init__(*args)
        self.values = values
        self.setModal(True)
        self.setWindowTitle('Connect to WeeChat')

        grid = QtWidgets.QGridLayout()
        grid.setSpacing(10)

        self.fields = {}
        focus = None

        # hostname
        grid.addWidget(QtWidgets.QLabel('<b>Hostname</b>'), 0, 0)
        line_edit = QtWidgets.QLineEdit()
        line_edit.setFixedWidth(200)
        value = self.values.get('hostname', '')
        line_edit.insert(value)
        grid.addWidget(line_edit, 0, 1)
        self.fields['hostname'] = line_edit
        if not focus and not value:
            focus = 'hostname'

        # port / SSL
        grid.addWidget(QtWidgets.QLabel('<b>Port</b>'), 1, 0)
        line_edit = QtWidgets.QLineEdit()
        line_edit.setFixedWidth(200)
        value = self.values.get('port', '')
        line_edit.insert(value)
        grid.addWidget(line_edit, 1, 1)
        self.fields['port'] = line_edit
        if not focus and not value:
            focus = 'port'

        ssl = QtWidgets.QCheckBox('SSL')
        ssl.setChecked(self.values['ssl'] == 'on')
        grid.addWidget(ssl, 1, 2)
        self.fields['ssl'] = ssl

        # password
        grid.addWidget(QtWidgets.QLabel('<b>Password</b>'), 2, 0)
        line_edit = QtWidgets.QLineEdit()
        line_edit.setFixedWidth(200)
        line_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        value = self.values.get('password', '')
        line_edit.insert(value)
        grid.addWidget(line_edit, 2, 1)
        self.fields['password'] = line_edit
        if not focus and not value:
            focus = 'password'

        # TOTP (Time-Based One-Time Password)
        label = QtWidgets.QLabel('TOTP')
        label.setToolTip('Time-Based One-Time Password (6 digits)')
        grid.addWidget(label, 3, 0)
        line_edit = QtWidgets.QLineEdit()
        line_edit.setPlaceholderText('6 digits')
        validator = QtGui.QIntValidator(0, 999999, self)
        line_edit.setValidator(validator)
        line_edit.setFixedWidth(80)
        value = self.values.get('totp', '')
        line_edit.insert(value)
        grid.addWidget(line_edit, 3, 1)
        self.fields['totp'] = line_edit
        if not focus and not value:
            focus = 'totp'

        # lines
        grid.addWidget(QtWidgets.QLabel('Lines'), 4, 0)
        line_edit = QtWidgets.QLineEdit()
        line_edit.setFixedWidth(200)
        validator = QtGui.QIntValidator(0, 2147483647, self)
        line_edit.setValidator(validator)
        line_edit.setFixedWidth(80)
        value = self.values.get('lines', '')
        line_edit.insert(value)
        grid.addWidget(line_edit, 4, 1)
        self.fields['lines'] = line_edit
        if not focus and not value:
            focus = 'lines'

        self.dialog_buttons = QtWidgets.QDialogButtonBox()
        self.dialog_buttons.setStandardButtons(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.dialog_buttons.rejected.connect(self.close)

        grid.addWidget(self.dialog_buttons, 5, 0, 1, 2)
        self.setLayout(grid)
        self.show()

        if focus:
            self.fields[focus].setFocus()
