#
# preferences.py - preferences dialog box
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

"""Preferences dialog box."""

from PySide6 import QtCore, QtWidgets as QtGui


class PreferencesDialog(QtGui.QDialog):
    """Preferences dialog."""

    def __init__(self, *args):
        QtGui.QDialog.__init__(*(self,) + args)
        self.setModal(True)
        self.setWindowTitle('Preferences')

        close_button = QtGui.QPushButton('Close')
        close_button.pressed.connect(self.close)

        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(close_button)
        hbox.addStretch(1)

        vbox = QtGui.QVBoxLayout()

        label = QtGui.QLabel('Not yet implemented!')
        label.setAlignment(QtCore.Qt.AlignHCenter)
        vbox.addWidget(label)

        label = QtGui.QLabel('')
        label.setAlignment(QtCore.Qt.AlignHCenter)
        vbox.addWidget(label)

        vbox.addLayout(hbox)

        self.setLayout(vbox)
        self.show()
