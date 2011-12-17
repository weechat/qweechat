#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Sebastien Helleu <flashcode@flashtux.org>
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
# I/O with WeeChat/relay.
#

import struct
import qt_compat
QtCore = qt_compat.import_module('QtCore')
QtNetwork = qt_compat.import_module('QtNetwork')

_PROTO_INIT_CMDS = ['init password=%(password)s,compression=gzip',
                    '(listbuffers) hdata buffer:gui_buffers(*) number,full_name,short_name,nicklist,title',
                    '(listlines) hdata buffer:gui_buffers(*)/own_lines/first_line(*)/data date,displayed,prefix,message',
                    '(nicklist) nicklist',
                    'sync',
                    '']


class Network(QtCore.QObject):
    """I/O with WeeChat/relay."""

    statusChanged = qt_compat.Signal(str, str)
    messageFromWeechat = qt_compat.Signal(QtCore.QByteArray)

    def __init__(self, *args):
        apply(QtCore.QObject.__init__, (self,) + args)
        self.status_disconnected = 'disconnected'
        self.status_connecting = 'connecting...'
        self.status_connected = 'connected'
        self._server = None
        self._port = None
        self._password = None
        self._buffer = QtCore.QByteArray()
        self._socket = QtNetwork.QTcpSocket()
        self._socket.connected.connect(self._socket_connected)
        self._socket.error.connect(self._socket_error)
        self._socket.readyRead.connect(self._socket_read)
        self._socket.disconnected.connect(self._socket_disconnected)

    def _socket_connected(self):
        """Slot: socket connected."""
        self.statusChanged.emit(self.status_connected, None)
        if self._password:
            self._socket.write('\n'.join(_PROTO_INIT_CMDS) % {'password': str(self._password)})

    def _socket_error(self, error):
        """Slot: socket error."""
        self.statusChanged.emit(self.status_disconnected, 'Failed, error: %s' % self._socket.errorString())

    def _socket_read(self):
        """Slot: data available on socket."""
        avail = self._socket.bytesAvailable()
        bytes = self._socket.read(avail)
        self._buffer.append(bytes)
        while len(self._buffer) >= 4:
            remainder = None
            length = struct.unpack('>i', self._buffer[0:4])[0]
            if len(self._buffer) < length:
                # partial message, just wait for end of message
                break
            # more than one message?
            if length < len(self._buffer):
                # save beginning of another message
                remainder = self._buffer[length:]
                self._buffer = self._buffer[0:length]
            self.messageFromWeechat.emit(self._buffer)
            self._buffer.clear()
            if remainder:
                self._buffer.append(remainder)

    def _socket_disconnected(self):
        """Slot: socket disconnected."""
        self._server = None
        self._port = None
        self._password = None
        self.statusChanged.emit(self.status_disconnected, None)

    def is_connected(self):
        return self._socket.state() == QtNetwork.QAbstractSocket.ConnectedState

    def connect_weechat(self, server, port, password):
        self._server = server
        try:
            self._port = int(port)
        except:
            self._port = 0
        self._password = password
        if self._socket.state() == QtNetwork.QAbstractSocket.ConnectedState:
            return
        if self._socket.state() != QtNetwork.QAbstractSocket.UnconnectedState:
            self._socket.abort()
        self._socket.connectToHost(self._server, self._port)
        self.statusChanged.emit(self.status_connecting, None)

    def disconnect_weechat(self):
        if self._socket.state() != QtNetwork.QAbstractSocket.UnconnectedState:
            if self._socket.state() != QtNetwork.QAbstractSocket.ConnectedState:
                self.statusChanged.emit(self.status_disconnected, None)
            self._socket.abort()

    def send_to_weechat(self, message):
        self._socket.write(str(message))

    def status_icon(self, status):
        icon = {self.status_disconnected: 'dialog-close.png',
                self.status_connecting: 'dialog-close.png',
                self.status_connected: 'dialog-ok-apply.png'}
        return icon.get(status, '')
