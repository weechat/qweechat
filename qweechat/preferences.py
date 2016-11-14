# -*- coding: utf-8 -*-
#
# preferences.py - preferences dialog box
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
import config

QtCore = qt_compat.import_module('QtCore')
QtGui = qt_compat.import_module('QtGui')


class PreferencesDialog(QtGui.QDialog):
    """Preferences dialog."""

    def __init__(self, name, parent, *args):
        QtGui.QDialog.__init__(*(self,) + args)
        self.setModal(True)
        self.setWindowTitle(name)
        self.parent = parent
        self.config = parent.config
        self.stacked_panes = QtGui.QStackedWidget()
        self.list_panes = PreferencesTreeWidget("Settings")

        splitter = QtGui.QSplitter()
        splitter.addWidget(self.list_panes)
        splitter.addWidget(self.stacked_panes)

        for section_name in self.config.sections():
            item = QtGui.QTreeWidgetItem(section_name)
            item.setText(0, section_name)
            pane = PreferencesPaneWidget(section_name)
            self.list_panes.addTopLevelItem(item)
            self.stacked_panes.addWidget(pane)
            for name, value in self.config.items(section_name):
                pane.addItem(name, value)
        self.list_panes.currentItemChanged.connect(self._pane_switch)

        hbox = QtGui.QHBoxLayout()
        self.dialog_buttons = QtGui.QDialogButtonBox()
        self.dialog_buttons.setStandardButtons(
            QtGui.QDialogButtonBox.Save | QtGui.QDialogButtonBox.Cancel)
        self.dialog_buttons.rejected.connect(self.close)
        self.dialog_buttons.accepted.connect(self._save_and_close)

        hbox.addStretch(1)
        hbox.addWidget(self.dialog_buttons)
        hbox.addStretch(1)

        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(splitter)
        vbox.addLayout(hbox)

        self.setLayout(vbox)
        self.show()

    def _pane_switch(self, item):
        """Switch the visible preference pane."""
        index = self.list_panes.indexOfTopLevelItem(item)
        if index >= 0:
            self.stacked_panes.setCurrentIndex(index)

    def _save_and_close(self):
        for widget in (self.stacked_panes.widget(i)
                       for i in range(self.stacked_panes.count())):
            for key, field in widget.fields.items():
                if isinstance(field, QtGui.QComboBox):
                    text = field.itemText(field.currentIndex())
                else:
                    text = field.text()
                self.config.set(widget.section_name, key, str(text))
        config.write(self.config)
        self.parent.apply_preferences()
        self.close()


class PreferencesTreeWidget(QtGui.QTreeWidget):
    """Widget with tree list of preferences."""

    def __init__(self, header_label, *args):
        QtGui.QTreeWidget.__init__(*(self,) + args)
        self.setHeaderLabel(header_label)
        self.setRootIsDecorated(False)

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


class PreferencesPaneWidget(QtGui.QWidget):
    """
    Widget with (from top to bottom):
    title, chat + nicklist (optional) + prompt/input.
    """

    def __init__(self, section_name):
        QtGui.QWidget.__init__(self)
        self.grid = QtGui.QGridLayout()
        self.grid.setAlignment(QtCore.Qt.AlignTop)
        self.section_name = section_name
        self.fields = {}
        self.setLayout(self.grid)
        self.grid.setColumnStretch(2, 1)
        self.grid.setSpacing(10)

    def addItem(self, key, value):
        """Add a key-value pair."""
        line = len(self.fields)
        start = 0
        if self.section_name == "color":
            start = 2 * (line % 2)
            line = line // 2
        self.grid.addWidget(QtGui.QLabel(key.capitalize()), line, start + 0)
        edit = QtGui.QLineEdit()
        edit.setFixedWidth(200)
        edit.insert(value)
        if key == 'password':
            edit.setEchoMode(QtGui.QLineEdit.Password)
        if key == 'style':
            edit = QtGui.QComboBox()
            edit.addItems(QtGui.QStyleFactory.keys())
            edit.setCurrentIndex(edit.findText(QtGui.qApp.style().objectName(),
                                               QtCore.Qt.MatchFixedString))
        self.grid.addWidget(edit, line, start + 1)
        self.fields[key] = edit
