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

"""About dialog box."""

from PySide6 import QtCore, QtWidgets as QtGui

from qweechat.version import qweechat_version


class AboutDialog(QtGui.QDialog):
    """About dialog."""

    def __init__(self, app_name, author, weechat_site, *args):
        QtGui.QDialog.__init__(*(self,) + args)
        self.setModal(True)
        self.setWindowTitle('About')

        close_button = QtGui.QPushButton('Close')
        close_button.pressed.connect(self.close)

        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(close_button)
        hbox.addStretch(1)

        vbox = QtGui.QVBoxLayout()
        messages = [
            f'<b>{app_name}</b> {qweechat_version()}',
            f'© 2011-2022 {author}',
            '',
            f'<a href="{weechat_site}">{weechat_site}</a>',
            '',
        ]
        for msg in messages:
            label = QtGui.QLabel(msg)
            label.setAlignment(QtCore.Qt.AlignHCenter)
            vbox.addWidget(label)
        vbox.addLayout(hbox)

        self.setLayout(vbox)
        self.show()
