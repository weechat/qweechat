# -*- coding: utf-8 -*-
#
# about.py - about dialog box
#
# Copyright (C) 2011-2018 Sébastien Helleu <flashcode@flashtux.org>
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

QtCore = qt_compat.import_module('QtCore')
QtGui = qt_compat.import_module('QtGui')


class AboutDialog(QtGui.QDialog):
    """About dialog."""

    def __init__(self, name, messages, *args):
        QtGui.QDialog.__init__(*(self,) + args)
        self.setModal(True)
        self.setWindowTitle(name)

        close_button = QtGui.QPushButton('Close')
        close_button.pressed.connect(self.close)

        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(close_button)
        hbox.addStretch(1)

        vbox = QtGui.QVBoxLayout()
        for msg in messages:
            label = QtGui.QLabel(msg.decode('utf-8'))
            label.setAlignment(QtCore.Qt.AlignHCenter)
            vbox.addWidget(label)
        vbox.addLayout(hbox)

        self.setLayout(vbox)
        self.show()
