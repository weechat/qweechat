# -*- coding: utf-8 -*-
#
# preferences.py - preferences dialog box
#
# Copyright (C) 2016 Ricky Brent <ricky@rickybrent.com>
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

        # Follow same order as defaults:
        section_panes = {}
        for section in self.config.sections():
            item = QtGui.QTreeWidgetItem(section)
            item.setText(0, section)
            section_panes[section] = PreferencesPaneWidget(section)
            self.list_panes.addTopLevelItem(item)
            self.stacked_panes.addWidget(section_panes[section])

        for setting, default in config.CONFIG_DEFAULT_OPTIONS:
            section, key = setting.split(".")
            section_panes[section].addItem(key, self.config.get(section, key))
        for key, value in self.config.items("color"):
            section_panes["color"].addItem(key, value)

        self.list_panes.currentItemChanged.connect(self._pane_switch)
        self.list_panes.setCurrentItem(self.list_panes.topLevelItem(0))

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
                elif isinstance(field, QtGui.QCheckBox):
                    text = "on" if field.isChecked() else "off"
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
        self.setMaximumWidth(90)
        self.setTextElideMode(QtCore.Qt.ElideNone)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setFocusPolicy(QtCore.Qt.NoFocus)


class PreferencesColorEdit(QtGui.QPushButton):
    """Simple color square that changes based on the color selected."""
    def __init__(self, *args):
        QtGui.QPushButton.__init__(*(self,) + args)
        self.color = "#000000"
        self.clicked.connect(self._color_picker)
        # Some of the configured colors use a astrisk prefix.
        # Toggle this on right click.
        self.star = False
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._color_star)

    def insert(self, color):
        """Insert the desired color for the widget."""
        if color[:1] == "*":
            self.star = True
            color = color[1:]
        self.setText("*" if self.star else "")
        self.color = color
        self.setStyleSheet("background-color: " + color)

    def text(self):
        """Returns the hex value of the color."""
        return ("*" if self.star else "") + self.color

    def _color_picker(self):
        color = QtGui.QColorDialog.getColor()
        self.insert(color.name())

    def _color_star(self):
        self.star = not self.star
        self.insert(self.text())


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
        self.checkboxes = ("ssl", "autoconnect", "statusbar", "topic",
                           "menubar", "toolbar", "nicklist", "debug")
        self.comboboxes = {"style": QtGui.QStyleFactory.keys(),
                           "buffer_list": ["left", "right"]}

    def addItem(self, key, value):
        """Add a key-value pair."""
        line = len(self.fields)
        name = key.capitalize().replace("_", " ")
        start = 0
        if self.section_name == "color":
            start = 2 * (line % 2)
            line = line // 2
        self.grid.addWidget(QtGui.QLabel(name), line, start + 0)
        if self.section_name == "color":
            edit = PreferencesColorEdit()
            edit.setFixedWidth(edit.sizeHint().height())
            edit.insert(value)
        elif key in self.comboboxes.keys():
            edit = QtGui.QComboBox()
            edit.addItems(self.comboboxes[key])
            edit.setCurrentIndex(edit.findText(value))
            edit.setFixedWidth(200)
        elif key in self.checkboxes:
            edit = QtGui.QCheckBox()
            edit.setChecked(value == "on")
        else:
            edit = QtGui.QLineEdit()
            edit.setFixedWidth(200)
            edit.insert(value)
        if key == 'password':
            edit.setEchoMode(QtGui.QLineEdit.Password)
        self.grid.addWidget(edit, line, start + 1)
        self.fields[key] = edit
