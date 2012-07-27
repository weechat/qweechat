#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011-2012 Sebastien Helleu <flashcode@flashtux.org>
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
# QWeeChat - WeeChat remote GUI using Qt toolkit.
# (this script requires WeeChat 0.3.7 or newer, running on local or remote host)
#
# History:
#
# 2011-05-27, Sebastien Helleu <flashcode@flashtux.org>:
#     start dev
#

import sys, struct
import qt_compat
QtCore = qt_compat.import_module('QtCore')
QtGui = qt_compat.import_module('QtGui')
import config
import weechat.protocol as protocol
from network import Network
from connection import ConnectionDialog
from buffer import BufferListWidget, Buffer
from debug import DebugDialog
from about import AboutDialog

NAME = 'QWeeChat'
VERSION = '0.0.1-dev'
AUTHOR = 'Sébastien Helleu'
AUTHOR_MAIL= 'flashcode@flashtux.org'
WEECHAT_SITE = 'http://www.weechat.org/'

# number of lines in buffer for debug window
DEBUG_NUM_LINES = 50


class MainWindow(QtGui.QMainWindow):
    """Main window."""

    def __init__(self, *args):
        QtGui.QMainWindow.__init__(*(self,) + args)

        self.config = config.read()

        self.resize(1000, 600)
        self.setWindowTitle(NAME)

        self.debug_dialog = None
        self.debug_lines = []

        # network
        self.network = Network()
        self.network.statusChanged.connect(self.network_status_changed)
        self.network.messageFromWeechat.connect(self.network_message_from_weechat)

        # list of buffers
        self.list_buffers = BufferListWidget()
        self.list_buffers.currentRowChanged.connect(self.buffer_switch)

        # default buffer
        self.buffers = [Buffer()]
        self.stacked_buffers = QtGui.QStackedWidget()
        self.stacked_buffers.addWidget(self.buffers[0].widget)

        # splitter with buffers + chat/input
        splitter = QtGui.QSplitter()
        splitter.addWidget(self.list_buffers)
        splitter.addWidget(self.stacked_buffers)

        self.setCentralWidget(splitter)

        if self.config.getboolean('look', 'statusbar'):
            self.statusBar().visible = True

        # actions for menu and toolbar
        actions_def = {'connect'    : ['network-connect.png', 'Connect to WeeChat', 'Ctrl+O', self.open_connection_dialog],
                       'disconnect' : ['network-disconnect.png', 'Disconnect from WeeChat', 'Ctrl+D', self.network.disconnect_weechat],
                       'debug'      : ['edit-find.png', 'Debug console window', 'Ctrl+B', self.open_debug_dialog],
                       'preferences': ['preferences-other.png', 'Preferences', 'Ctrl+P', self.open_preferences_dialog],
                       'about'      : ['help-about.png', 'About', 'Ctrl+H', self.open_about_dialog],
                       'quit'       : ['application-exit.png', 'Quit application', 'Ctrl+Q', self.close],
                       }
        self.actions = {}
        for name, action in list(actions_def.items()):
            self.actions[name] = QtGui.QAction(QtGui.QIcon('data/icons/%s' % action[0]), name.capitalize(), self)
            self.actions[name].setStatusTip(action[1])
            self.actions[name].setShortcut(action[2])
            self.actions[name].triggered.connect(action[3])

        # menu
        self.menu = self.menuBar()
        menu_file = self.menu.addMenu('&File')
        menu_file.addActions([self.actions['connect'], self.actions['disconnect'],
                              self.actions['preferences'], self.actions['quit']])
        menu_window = self.menu.addMenu('&Window')
        menu_window.addAction(self.actions['debug'])
        menu_help = self.menu.addMenu('&Help')
        menu_help.addAction(self.actions['about'])
        self.network_status = QtGui.QLabel()
        self.network_status.setFixedHeight(20)
        self.network_status.setFixedWidth(200)
        self.network_status.setContentsMargins(0, 0, 10, 0)
        self.network_status.setAlignment(QtCore.Qt.AlignRight)
        if hasattr(self.menu, 'setCornerWidget'):
            self.menu.setCornerWidget(self.network_status, QtCore.Qt.TopRightCorner)
        self.network_status_set(self.network.status_disconnected, None)

        # toolbar
        toolbar = self.addToolBar('toolBar')
        toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        toolbar.addActions([self.actions['connect'], self.actions['disconnect'],
                            self.actions['debug'], self.actions['preferences'],
                            self.actions['about'], self.actions['quit']])

        self.buffers[0].widget.input.setFocus()

        # open debug dialog
        if self.config.getboolean('look', 'debug'):
            self.open_debug_dialog()

        # auto-connect to relay
        if self.config.getboolean('relay', 'autoconnect'):
            self.network.connect_weechat(self.config.get('relay', 'server'),
                                         self.config.get('relay', 'port'),
                                         self.config.get('relay', 'ssl') == 'on',
                                         self.config.get('relay', 'password'))

        self.show()

    def buffer_switch(self, index):
        if index >= 0:
            self.stacked_buffers.setCurrentIndex(index)
            self.stacked_buffers.widget(index).input.setFocus()

    def buffer_input(self, full_name, text):
        if self.network.is_connected():
            message = 'input %s %s\n' % (full_name, text)
            self.network.send_to_weechat(message)
            self.debug_display(0, '<==', message, forcecolor='#AA0000')

    def open_preferences_dialog(self):
        pass # TODO

    def debug_display(self, *args, **kwargs):
        self.debug_lines.append((args, kwargs))
        self.debug_lines = self.debug_lines[-DEBUG_NUM_LINES:]
        if self.debug_dialog:
            self.debug_dialog.chat.display(*args, **kwargs)

    def open_debug_dialog(self):
        if not self.debug_dialog:
            self.debug_dialog = DebugDialog(self)
            self.debug_dialog.input.textSent.connect(self.debug_input_text_sent)
            self.debug_dialog.finished.connect(self.debug_dialog_closed)
            self.debug_dialog.display_lines(self.debug_lines)
            self.debug_dialog.chat.scroll_bottom()

    def debug_input_text_sent(self, text):
        if self.network.is_connected():
            text = str(text)
            pos = text.find(')')
            if text.startswith('(') and pos >= 0:
                text = '(debug_%s)%s' % (text[1:pos], text[pos+1:])
            else:
                text = '(debug) %s' % text
            self.debug_display(0, '<==', text, forcecolor='#AA0000')
            self.network.send_to_weechat(text + '\n')

    def debug_dialog_closed(self, result):
        self.debug_dialog = None

    def open_about_dialog(self):
        messages = ['<b>%s</b> %s' % (NAME, VERSION),
                    '&copy; 2011-2012 %s &lt;<a href="mailto:%s">%s</a>&gt;' % (AUTHOR, AUTHOR_MAIL, AUTHOR_MAIL),
                    '',
                    'WeeChat site: <a href="%s">%s</a>' % (WEECHAT_SITE, WEECHAT_SITE),
                    '']
        self.about_dialog = AboutDialog(NAME, messages, self)

    def open_connection_dialog(self):
        values = {}
        for option in ('server', 'port', 'ssl', 'password'):
            values[option] = self.config.get('relay', option)
        self.connection_dialog = ConnectionDialog(values, self)
        self.connection_dialog.dialog_buttons.accepted.connect(self.connect_weechat)

    def connect_weechat(self):
        self.network.connect_weechat(self.connection_dialog.fields['server'].text(),
                                     self.connection_dialog.fields['port'].text(),
                                     self.connection_dialog.fields['ssl'].isChecked(),
                                     self.connection_dialog.fields['password'].text())
        self.connection_dialog.close()

    def network_status_changed(self, status, extra):
        if self.config.getboolean('look', 'statusbar'):
            self.statusBar().showMessage(status)
        self.debug_display(0, '', status, forcecolor='#0000AA')
        self.network_status_set(status, extra)

    def network_status_set(self, status, extra):
        pal = self.network_status.palette()
        if status == self.network.status_connected:
            pal.setColor(self.network_status.foregroundRole(), QtGui.QColor('green'))
        else:
            pal.setColor(self.network_status.foregroundRole(), QtGui.QColor('#aa0000'))
        ssl = ' (SSL)' if status != self.network.status_disconnected and self.network.is_ssl() else ''
        self.network_status.setPalette(pal)
        icon = self.network.status_icon(status)
        if icon:
            self.network_status.setText('<img src="data/icons/%s"> %s' % (icon, status.capitalize() + ssl))
        else:
            self.network_status.setText(status.capitalize())
        if status == self.network.status_disconnected:
            self.actions['connect'].setEnabled(True)
            self.actions['disconnect'].setEnabled(False)
        else:
            self.actions['connect'].setEnabled(False)
            self.actions['disconnect'].setEnabled(True)

    def network_message_from_weechat(self, message):
        self.debug_display(0, '==>',
                           'message (%d bytes):\n%s'
                           % (len(message), protocol.hex_and_ascii(message, 20)),
                           forcecolor='#008800')
        try:
            proto = protocol.Protocol()
            message = proto.decode(str(message))
            if message.uncompressed:
                self.debug_display(0, '==>',
                                   'message uncompressed (%d bytes):\n%s'
                                   % (message.size_uncompressed,
                                      protocol.hex_and_ascii(message.uncompressed, 20)),
                                   forcecolor='#008800')
            self.debug_display(0, '', 'Message: %s' % message)
            self.parse_message(message)
        except:
            print("Error while decoding message from WeeChat")
            self.network.disconnect_weechat()

    def parse_message(self, message):
        if message.msgid.startswith('debug'):
            self.debug_display(0, '', '(debug message, ignored)')
            return
        if message.msgid == 'listbuffers':
            for obj in message.objects:
                if obj.objtype == 'hda' and obj.value['path'][-1] == 'buffer':
                    self.list_buffers.clear()
                    while self.stacked_buffers.count() > 0:
                        buf = self.stacked_buffers.widget(0)
                        self.stacked_buffers.removeWidget(buf)
                    self.buffers = []
                    for item in obj.value['items']:
                        buf = self.create_buffer(item)
                        self.insert_buffer(len(self.buffers), buf)
                    self.list_buffers.setCurrentRow(0)
                    self.buffers[0].widget.input.setFocus()
        elif message.msgid in ('listlines', '_buffer_line_added'):
            for obj in message.objects:
                if obj.objtype == 'hda' and obj.value['path'][-1] == 'line_data':
                    for item in obj.value['items']:
                        if message.msgid == 'listlines':
                            ptrbuf = item['__path'][0]
                        else:
                            ptrbuf = item['buffer']
                        index = [i for i, b in enumerate(self.buffers) if b.pointer() == ptrbuf]
                        if index:
                            self.buffers[index[0]].widget.chat.display(item['date'],
                                                                       item['prefix'],
                                                                       item['message'])
        elif message.msgid in ('_nicklist', 'nicklist'):
            buffer_nicklist = {}
            for obj in message.objects:
                if obj.objtype == 'hda' and obj.value['path'][-1] == 'nicklist_item':
                    for item in obj.value['items']:
                        index = [i for i, b in enumerate(self.buffers) if b.pointer() == item['__path'][0]]
                        if index:
                            if not item['__path'][0] in buffer_nicklist:
                                self.buffers[index[0]].remove_all_nicks()
                            buffer_nicklist[item['__path'][0]] = True
                            if not item['group'] and item['visible']:
                                self.buffers[index[0]].add_nick(item['prefix'], item['name'])
        elif message.msgid == '_buffer_opened':
            for obj in message.objects:
                if obj.objtype == 'hda' and obj.value['path'][-1] == 'buffer':
                    for item in obj.value['items']:
                        buf = self.create_buffer(item)
                        index = self.find_buffer_index_for_insert(item['next_buffer'])
                        self.insert_buffer(index, buf)
        elif message.msgid.startswith('_buffer_'):
            for obj in message.objects:
                if obj.objtype == 'hda' and obj.value['path'][-1] == 'buffer':
                    for item in obj.value['items']:
                        index = [i for i, b in enumerate(self.buffers) if b.pointer() == item['__path'][0]]
                        if index:
                            index = index[0]
                            if message.msgid == '_buffer_type_changed':
                                self.buffers[index].data['type'] = item['type']
                            elif message.msgid in ('_buffer_moved', '_buffer_merged', '_buffer_unmerged'):
                                buf = self.buffers[index]
                                buf.data['number'] = item['number']
                                self.remove_buffer(index)
                                index2 = self.find_buffer_index_for_insert(item['next_buffer'])
                                self.insert_buffer(index2, buf)
                            elif message.msgid == '_buffer_renamed':
                                self.buffers[index].data['full_name'] = item['full_name']
                                self.buffers[index].data['short_name'] = item['short_name']
                            elif message.msgid == '_buffer_title_changed':
                                self.buffers[index].data['title'] = item['title']
                                self.buffers[index].update_title()
                            elif message.msgid.startswith('_buffer_localvar_'):
                                self.buffers[index].data['local_variables'] = item['local_variables']
                                self.buffers[index].update_prompt()
                            elif message.msgid == '_buffer_closing':
                                self.remove_buffer(index)
        elif message.msgid == '_upgrade':
            self.network.desync_weechat()
        elif message.msgid == '_upgrade_ended':
            self.network.sync_weechat()

    def create_buffer(self, item):
        buf = Buffer(item)
        buf.bufferInput.connect(self.buffer_input)
        buf.widget.input.bufferSwitchPrev.connect(self.list_buffers.switch_prev_buffer)
        buf.widget.input.bufferSwitchNext.connect(self.list_buffers.switch_next_buffer)
        return buf

    def insert_buffer(self, index, buf):
        self.buffers.insert(index, buf)
        self.list_buffers.insertItem(index, '%d. %s' % (buf.data['number'], buf.data['full_name']))
        self.stacked_buffers.insertWidget(index, buf.widget)

    def remove_buffer(self, index):
        if self.list_buffers.currentRow == index and index > 0:
            self.list_buffers.setCurrentRow(index - 1)
        self.list_buffers.takeItem(index)
        self.stacked_buffers.removeWidget(self.stacked_buffers.widget(index))
        self.buffers.pop(index)

    def find_buffer_index_for_insert(self, next_buffer):
        index = -1
        if next_buffer == '0x0':
            index = len(self.buffers)
        else:
            index = [i for i, b in enumerate(self.buffers) if b.pointer() == next_buffer]
            if index:
                index = index[0]
        if index < 0:
            print('Warning: unable to find position for buffer, using end of list by default')
            index = len(self.buffers)
        return index

    def closeEvent(self, event):
        self.network.disconnect_weechat()
        if self.debug_dialog:
            self.debug_dialog.close()
        config.write(self.config)
        QtGui.QMainWindow.closeEvent(self, event)


app = QtGui.QApplication(sys.argv)
app.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))
app.setWindowIcon(QtGui.QIcon('data/icons/weechat_icon_32.png'))
main = MainWindow()
sys.exit(app.exec_())
