# -*- coding: utf-8 -*-
#
# qweechat.py - WeeChat remote GUI using Qt toolkit
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

"""
QWeeChat is a WeeChat remote GUI using Qt toolkit.

It requires requires WeeChat 0.3.7 or newer, running on local or remote host.
"""

#
# History:
#
# 2011-05-27, Sébastien Helleu <flashcode@flashtux.org>:
#     start dev
#

import sys
import traceback
from pkg_resources import resource_filename
import qt_compat
QTCORE = qt_compat.import_module('QtCore')
QTGUI = qt_compat.import_module('QtGui')
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
AUTHOR_MAIL = 'flashcode@flashtux.org'
WEECHAT_SITE = 'http://weechat.org/'

# number of lines in buffer for debug window
DEBUG_NUM_LINES = 50


class MainWindow(QTGUI.QMainWindow):
    """Main window."""

    def __init__(self, *args):
        QTGUI.QMainWindow.__init__(*(self,) + args)

        self.config = config.read()

        self.resize(1000, 600)
        self.setWindowTitle(NAME)

        self.debug_dialog = None
        self.debug_lines = []

        self.about_dialog = None
        self.connection_dialog = None

        # network
        self.network = Network()
        self.network.statusChanged.connect(self._network_status_changed)
        self.network.messageFromWeechat.connect(self._network_weechat_msg)

        # list of buffers
        self.list_buffers = BufferListWidget()
        self.list_buffers.currentRowChanged.connect(self._buffer_switch)

        # default buffer
        self.buffers = [Buffer()]
        self.stacked_buffers = QTGUI.QStackedWidget()
        self.stacked_buffers.addWidget(self.buffers[0].widget)

        # splitter with buffers + chat/input
        splitter = QTGUI.QSplitter()
        splitter.addWidget(self.list_buffers)
        splitter.addWidget(self.stacked_buffers)

        self.setCentralWidget(splitter)

        if self.config.getboolean('look', 'statusbar'):
            self.statusBar().visible = True

        # actions for menu and toolbar
        actions_def = {
            'connect': [
                'network-connect.png', 'Connect to WeeChat',
                'Ctrl+O', self.open_connection_dialog],
            'disconnect': [
                'network-disconnect.png', 'Disconnect from WeeChat',
                'Ctrl+D', self.network.disconnect_weechat],
            'debug': [
                'edit-find.png', 'Debug console window',
                'Ctrl+B', self.open_debug_dialog],
            'preferences': [
                'preferences-other.png', 'Preferences',
                'Ctrl+P', self.open_preferences_dialog],
            'about': [
                'help-about.png', 'About',
                'Ctrl+H', self.open_about_dialog],
            'save connection': [
                'document-save.png', 'Save connection configuration',
                'Ctrl+S', self.save_connection],
            'quit': [
                'application-exit.png', 'Quit application',
                'Ctrl+Q', self.close],
        }
        self.actions = {}
        for name, action in list(actions_def.items()):
            self.actions[name] = QTGUI.QAction(
                QTGUI.QIcon(
                    resource_filename(__name__, 'data/icons/%s' % action[0])),
                name.capitalize(), self)
            self.actions[name].setStatusTip(action[1])
            self.actions[name].setShortcut(action[2])
            self.actions[name].triggered.connect(action[3])

        # menu
        self.menu = self.menuBar()
        menu_file = self.menu.addMenu('&File')
        menu_file.addActions([self.actions['connect'],
                              self.actions['disconnect'],
                              self.actions['preferences'],
                              self.actions['save connection'],
                              self.actions['quit']])
        menu_window = self.menu.addMenu('&Window')
        menu_window.addAction(self.actions['debug'])
        menu_help = self.menu.addMenu('&Help')
        menu_help.addAction(self.actions['about'])
        self.network_status = QTGUI.QLabel()
        self.network_status.setFixedHeight(20)
        self.network_status.setFixedWidth(200)
        self.network_status.setContentsMargins(0, 0, 10, 0)
        self.network_status.setAlignment(QTCORE.Qt.AlignRight)
        if hasattr(self.menu, 'setCornerWidget'):
            self.menu.setCornerWidget(self.network_status,
                                      QTCORE.Qt.TopRightCorner)
        self.network_status_set(self.network.status_disconnected)

        # toolbar
        toolbar = self.addToolBar('toolBar')
        toolbar.setToolButtonStyle(QTCORE.Qt.ToolButtonTextUnderIcon)
        toolbar.addActions([self.actions['connect'],
                            self.actions['disconnect'],
                            self.actions['debug'],
                            self.actions['preferences'],
                            self.actions['about'],
                            self.actions['quit']])

        self.buffers[0].widget.input.setFocus()

        # open debug dialog
        if self.config.getboolean('look', 'debug'):
            self.open_debug_dialog()

        # auto-connect to relay
        if self.config.getboolean('relay', 'autoconnect'):
            self.network.connect_weechat(self.config.get('relay', 'server'),
                                         self.config.get('relay', 'port'),
                                         self.config.getboolean('relay',
                                                                'ssl'),
                                         self.config.get('relay', 'password'),
                                         self.config.get('relay', 'lines'))

        self.show()

    def _buffer_switch(self, index):
        """Switch to a buffer."""
        if index >= 0:
            self.stacked_buffers.setCurrentIndex(index)
            self.stacked_buffers.widget(index).input.setFocus()

    def buffer_input(self, full_name, text):
        """Send buffer input to WeeChat."""
        if self.network.is_connected():
            message = 'input %s %s\n' % (full_name, text)
            self.network.send_to_weechat(message)
            self.debug_display(0, '<==', message, forcecolor='#AA0000')

    def open_preferences_dialog(self):
        """Open a dialog with preferences."""
        pass  # TODO

    def save_connection(self):
        """Save connection configuration."""
        if self.network:
            options = self.network.get_options()
            for option in options.keys():
                self.config.set('relay', option, options[option])

    def debug_display(self, *args, **kwargs):
        """Display a debug message."""
        self.debug_lines.append((args, kwargs))
        self.debug_lines = self.debug_lines[-DEBUG_NUM_LINES:]
        if self.debug_dialog:
            self.debug_dialog.chat.display(*args, **kwargs)

    def open_debug_dialog(self):
        """Open a dialog with debug messages."""
        if not self.debug_dialog:
            self.debug_dialog = DebugDialog(self)
            self.debug_dialog.input.textSent.connect(
                self.debug_input_text_sent)
            self.debug_dialog.finished.connect(self._debug_dialog_closed)
            self.debug_dialog.display_lines(self.debug_lines)
            self.debug_dialog.chat.scroll_bottom()

    def debug_input_text_sent(self, text):
        """Send debug buffer input to WeeChat."""
        if self.network.is_connected():
            text = str(text)
            pos = text.find(')')
            if text.startswith('(') and pos >= 0:
                text = '(debug_%s)%s' % (text[1:pos], text[pos+1:])
            else:
                text = '(debug) %s' % text
            self.debug_display(0, '<==', text, forcecolor='#AA0000')
            self.network.send_to_weechat(text + '\n')

    def _debug_dialog_closed(self, result):
        """Called when debug dialog is closed."""
        self.debug_dialog = None

    def open_about_dialog(self):
        """Open a dialog with info about QWeeChat."""
        messages = ['<b>%s</b> %s' % (NAME, VERSION),
                    '&copy; 2011-2014 %s &lt;<a href="mailto:%s">%s</a>&gt;'
                    % (AUTHOR, AUTHOR_MAIL, AUTHOR_MAIL),
                    '',
                    'Running with %s' % ('PySide' if qt_compat.uses_pyside
                                         else 'PyQt4'),
                    '',
                    'WeeChat site: <a href="%s">%s</a>'
                    % (WEECHAT_SITE, WEECHAT_SITE),
                    '']
        self.about_dialog = AboutDialog(NAME, messages, self)

    def open_connection_dialog(self):
        """Open a dialog with connection settings."""
        values = {}
        for option in ('server', 'port', 'ssl', 'password', 'lines'):
            values[option] = self.config.get('relay', option)
        self.connection_dialog = ConnectionDialog(values, self)
        self.connection_dialog.dialog_buttons.accepted.connect(
            self.connect_weechat)

    def connect_weechat(self):
        """Connect to WeeChat."""
        self.network.connect_weechat(
            self.connection_dialog.fields['server'].text(),
            self.connection_dialog.fields['port'].text(),
            self.connection_dialog.fields['ssl'].isChecked(),
            self.connection_dialog.fields['password'].text(),
            int(self.connection_dialog.fields['lines'].text()))
        self.connection_dialog.close()

    def _network_status_changed(self, status, extra):
        """Called when the network status has changed."""
        if self.config.getboolean('look', 'statusbar'):
            self.statusBar().showMessage(status)
        self.debug_display(0, '', status, forcecolor='#0000AA')
        self.network_status_set(status)

    def network_status_set(self, status):
        """Set the network status."""
        pal = self.network_status.palette()
        if status == self.network.status_connected:
            pal.setColor(self.network_status.foregroundRole(),
                         QTGUI.QColor('green'))
        else:
            pal.setColor(self.network_status.foregroundRole(),
                         QTGUI.QColor('#aa0000'))
        ssl = ' (SSL)' if status != self.network.status_disconnected \
              and self.network.is_ssl() else ''
        self.network_status.setPalette(pal)
        icon = self.network.status_icon(status)
        if icon:
            self.network_status.setText(
                '<img src="%s"> %s' %
                (resource_filename(__name__, 'data/icons/%s' % icon),
                 status.capitalize() + ssl))
        else:
            self.network_status.setText(status.capitalize())
        if status == self.network.status_disconnected:
            self.actions['connect'].setEnabled(True)
            self.actions['disconnect'].setEnabled(False)
        else:
            self.actions['connect'].setEnabled(False)
            self.actions['disconnect'].setEnabled(True)

    def _network_weechat_msg(self, message):
        """Called when a message is received from WeeChat."""
        self.debug_display(0, '==>',
                           'message (%d bytes):\n%s'
                           % (len(message),
                              protocol.hex_and_ascii(message, 20)),
                           forcecolor='#008800')
        try:
            proto = protocol.Protocol()
            message = proto.decode(str(message))
            if message.uncompressed:
                self.debug_display(
                    0, '==>',
                    'message uncompressed (%d bytes):\n%s'
                    % (message.size_uncompressed,
                       protocol.hex_and_ascii(message.uncompressed, 20)),
                    forcecolor='#008800')
            self.debug_display(0, '', 'Message: %s' % message)
            self.parse_message(message)
        except:
            print('Error while decoding message from WeeChat:\n%s'
                  % traceback.format_exc())
            self.network.disconnect_weechat()

    def _parse_listbuffers(self, message):
        """Parse a WeeChat with list of buffers."""
        for obj in message.objects:
            if obj.objtype != 'hda' or obj.value['path'][-1] != 'buffer':
                continue
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

    def _parse_line(self, message):
        """Parse a WeeChat message with a buffer line."""
        for obj in message.objects:
            lines = []
            if obj.objtype != 'hda' or obj.value['path'][-1] != 'line_data':
                continue
            for item in obj.value['items']:
                if message.msgid == 'listlines':
                    ptrbuf = item['__path'][0]
                else:
                    ptrbuf = item['buffer']
                index = [i for i, b in enumerate(self.buffers)
                         if b.pointer() == ptrbuf]
                if index:
                    lines.append((item['date'], item['prefix'],
                                  item['message']))
            if message.msgid == 'listlines':
                lines.reverse()
            for line in lines:
                self.buffers[index[0]].widget.chat.display(*line)

    def _parse_nicklist(self, message):
        """Parse a WeeChat message with a buffer nicklist."""
        buffer_refresh = {}
        for obj in message.objects:
            if obj.objtype != 'hda' or \
               obj.value['path'][-1] != 'nicklist_item':
                continue
            group = '__root'
            for item in obj.value['items']:
                index = [i for i, b in enumerate(self.buffers)
                         if b.pointer() == item['__path'][0]]
                if index:
                    if not index[0] in buffer_refresh:
                        self.buffers[index[0]].nicklist = {}
                    buffer_refresh[index[0]] = True
                    if item['group']:
                        group = item['name']
                    self.buffers[index[0]].nicklist_add_item(
                        group, item['group'], item['prefix'], item['name'],
                        item['visible'])
        for index in buffer_refresh:
            self.buffers[index].nicklist_refresh()

    def _parse_nicklist_diff(self, message):
        """Parse a WeeChat message with a buffer nicklist diff."""
        buffer_refresh = {}
        for obj in message.objects:
            if obj.objtype != 'hda' or \
               obj.value['path'][-1] != 'nicklist_item':
                continue
            group = '__root'
            for item in obj.value['items']:
                index = [i for i, b in enumerate(self.buffers)
                         if b.pointer() == item['__path'][0]]
                if not index:
                    continue
                buffer_refresh[index[0]] = True
                if item['_diff'] == ord('^'):
                    group = item['name']
                elif item['_diff'] == ord('+'):
                    self.buffers[index[0]].nicklist_add_item(
                        group, item['group'], item['prefix'], item['name'],
                        item['visible'])
                elif item['_diff'] == ord('-'):
                    self.buffers[index[0]].nicklist_remove_item(
                        group, item['group'], item['name'])
                elif item['_diff'] == ord('*'):
                    self.buffers[index[0]].nicklist_update_item(
                        group, item['group'], item['prefix'], item['name'],
                        item['visible'])
        for index in buffer_refresh:
            self.buffers[index].nicklist_refresh()

    def _parse_buffer_opened(self, message):
        """Parse a WeeChat message with a new buffer (opened)."""
        for obj in message.objects:
            if obj.objtype != 'hda' or obj.value['path'][-1] != 'buffer':
                continue
            for item in obj.value['items']:
                buf = self.create_buffer(item)
                index = self.find_buffer_index_for_insert(item['next_buffer'])
                self.insert_buffer(index, buf)

    def _parse_buffer(self, message):
        """Parse a WeeChat message with a buffer event
        (anything except a new buffer).
        """
        for obj in message.objects:
            if obj.objtype != 'hda' or obj.value['path'][-1] != 'buffer':
                continue
            for item in obj.value['items']:
                index = [i for i, b in enumerate(self.buffers)
                         if b.pointer() == item['__path'][0]]
                if not index:
                    continue
                index = index[0]
                if message.msgid == '_buffer_type_changed':
                    self.buffers[index].data['type'] = item['type']
                elif message.msgid in ('_buffer_moved', '_buffer_merged',
                                       '_buffer_unmerged'):
                    buf = self.buffers[index]
                    buf.data['number'] = item['number']
                    self.remove_buffer(index)
                    index2 = self.find_buffer_index_for_insert(
                        item['next_buffer'])
                    self.insert_buffer(index2, buf)
                elif message.msgid == '_buffer_renamed':
                    self.buffers[index].data['full_name'] = item['full_name']
                    self.buffers[index].data['short_name'] = item['short_name']
                elif message.msgid == '_buffer_title_changed':
                    self.buffers[index].data['title'] = item['title']
                    self.buffers[index].update_title()
                elif message.msgid.startswith('_buffer_localvar_'):
                    self.buffers[index].data['local_variables'] = \
                        item['local_variables']
                    self.buffers[index].update_prompt()
                elif message.msgid == '_buffer_closing':
                    self.remove_buffer(index)

    def parse_message(self, message):
        """Parse a WeeChat message."""
        if message.msgid.startswith('debug'):
            self.debug_display(0, '', '(debug message, ignored)')
        elif message.msgid == 'listbuffers':
            self._parse_listbuffers(message)
        elif message.msgid in ('listlines', '_buffer_line_added'):
            self._parse_line(message)
        elif message.msgid in ('_nicklist', 'nicklist'):
            self._parse_nicklist(message)
        elif message.msgid == '_nicklist_diff':
            self._parse_nicklist_diff(message)
        elif message.msgid == '_buffer_opened':
            self._parse_buffer_opened(message)
        elif message.msgid.startswith('_buffer_'):
            self._parse_buffer(message)
        elif message.msgid == '_upgrade':
            self.network.desync_weechat()
        elif message.msgid == '_upgrade_ended':
            self.network.sync_weechat()

    def create_buffer(self, item):
        """Create a new buffer."""
        buf = Buffer(item)
        buf.bufferInput.connect(self.buffer_input)
        buf.widget.input.bufferSwitchPrev.connect(
            self.list_buffers.switch_prev_buffer)
        buf.widget.input.bufferSwitchNext.connect(
            self.list_buffers.switch_next_buffer)
        return buf

    def insert_buffer(self, index, buf):
        """Insert a buffer in list."""
        self.buffers.insert(index, buf)
        self.list_buffers.insertItem(index, '%d. %s'
                                     % (buf.data['number'],
                                        buf.data['full_name'].decode('utf-8')))
        self.stacked_buffers.insertWidget(index, buf.widget)

    def remove_buffer(self, index):
        """Remove a buffer."""
        if self.list_buffers.currentRow == index and index > 0:
            self.list_buffers.setCurrentRow(index - 1)
        self.list_buffers.takeItem(index)
        self.stacked_buffers.removeWidget(self.stacked_buffers.widget(index))
        self.buffers.pop(index)

    def find_buffer_index_for_insert(self, next_buffer):
        """Find position to insert a buffer in list."""
        index = -1
        if next_buffer == '0x0':
            index = len(self.buffers)
        else:
            index = [i for i, b in enumerate(self.buffers)
                     if b.pointer() == next_buffer]
            if index:
                index = index[0]
        if index < 0:
            print('Warning: unable to find position for buffer, using end of '
                  'list by default')
            index = len(self.buffers)
        return index

    def closeEvent(self, event):
        """Called when QWeeChat window is closed."""
        self.network.disconnect_weechat()
        if self.debug_dialog:
            self.debug_dialog.close()
        config.write(self.config)
        QTGUI.QMainWindow.closeEvent(self, event)


app = QTGUI.QApplication(sys.argv)
app.setStyle(QTGUI.QStyleFactory.create('Cleanlooks'))
app.setWindowIcon(QTGUI.QIcon(
    resource_filename(__name__, 'data/icons/weechat_icon_32.png')))
main = MainWindow()
sys.exit(app.exec_())
