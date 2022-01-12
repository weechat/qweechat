# -*- coding: utf-8 -*-
#
# network.py - I/O with WeeChat/relay
#
# Copyright (C) 2011-2022 Sébastien Helleu <flashcode@flashtux.org>
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

"""I/O with WeeChat/relay."""

import hashlib
import secrets
import struct

from PySide6 import QtCore, QtNetwork

from qweechat import config
from qweechat.debug import DebugDialog


# list of supported hash algorithms on our side
# (the hash algorithm will be negotiated with the remote WeeChat)
_HASH_ALGOS_LIST = [
    'plain',
    'sha256',
    'sha512',
    'pbkdf2+sha256',
    'pbkdf2+sha512',
]
_HASH_ALGOS = ':'.join(_HASH_ALGOS_LIST)

# handshake with remote WeeChat (before init)
_PROTO_HANDSHAKE = f'(handshake) handshake password_hash_algo={_HASH_ALGOS}\n'

# initialize with the password (plain text)
_PROTO_INIT_PWD = 'init password=%(password)s%(totp)s\n'  # nosec

# initialize with the hashed password
_PROTO_INIT_HASH = ('init password_hash='
                    '%(algo)s:%(salt)s%(iter)s:%(hash)s%(totp)s\n')

_PROTO_SYNC_CMDS = [
    # get buffers
    '(listbuffers) hdata buffer:gui_buffers(*) number,full_name,short_name,'
    'type,nicklist,title,local_variables',
    # get lines
    '(listlines) hdata buffer:gui_buffers(*)/own_lines/last_line(-%(lines)d)/'
    'data date,displayed,prefix,message',
    # get nicklist for all buffers
    '(nicklist) nicklist',
    # enable synchronization
    'sync',
]

STATUS_DISCONNECTED = 'disconnected'
STATUS_CONNECTING = 'connecting'
STATUS_AUTHENTICATING = 'authenticating'
STATUS_CONNECTED = 'connected'

NETWORK_STATUS = {
    STATUS_DISCONNECTED: {
        'label': 'Disconnected',
        'color': '#aa0000',
        'icon': 'dialog-close.png',
    },
    STATUS_CONNECTING: {
        'label': 'Connecting…',
        'color': '#dd5f00',
        'icon': 'dialog-warning.png',
    },
    STATUS_AUTHENTICATING: {
        'label': 'Authenticating…',
        'color': '#007fff',
        'icon': 'dialog-password.png',
    },
    STATUS_CONNECTED: {
        'label': 'Connected',
        'color': 'green',
        'icon': 'dialog-ok-apply.png',
    },
}


class Network(QtCore.QObject):
    """I/O with WeeChat/relay."""

    statusChanged = QtCore.Signal(str, str)
    messageFromWeechat = QtCore.Signal(QtCore.QByteArray)

    def __init__(self, *args):
        super().__init__(*args)
        self._init_connection()
        self.debug_lines = []
        self.debug_dialog = None
        self._lines = config.CONFIG_DEFAULT_RELAY_LINES
        self._buffer = QtCore.QByteArray()
        self._socket = QtNetwork.QSslSocket()
        self._socket.connected.connect(self._socket_connected)
        self._socket.readyRead.connect(self._socket_read)
        self._socket.disconnected.connect(self._socket_disconnected)

    def _init_connection(self):
        self.status = STATUS_DISCONNECTED
        self._hostname = None
        self._port = None
        self._ssl = None
        self._password = None
        self._totp = None
        self._handshake_received = False
        self._handshake_timer = None
        self._handshake_timer = False
        self._pwd_hash_algo = None
        self._pwd_hash_iter = 0
        self._server_nonce = None

    def set_status(self, status):
        """Set current status."""
        self.status = status
        self.statusChanged.emit(status, None)

    def pbkdf2(self, hash_name, salt):
        """Return hashed password with PBKDF2-HMAC."""
        return hashlib.pbkdf2_hmac(
            hash_name,
            password=self._password.encode('utf-8'),
            salt=salt,
            iterations=self._pwd_hash_iter,
        ).hex()

    def _build_init_command(self):
        """Build the init command to send to WeeChat."""
        totp = f',totp={self._totp}' if self._totp else ''
        if self._pwd_hash_algo == 'plain':
            cmd = _PROTO_INIT_PWD % {
                'password': self._password,
                'totp': totp,
            }
        else:
            client_nonce = secrets.token_bytes(16)
            salt = self._server_nonce + client_nonce
            pwd_hash = None
            iterations = ''
            if self._pwd_hash_algo == 'pbkdf2+sha512':
                pwd_hash = self.pbkdf2('sha512', salt)
                iterations = f':{self._pwd_hash_iter}'
            elif self._pwd_hash_algo == 'pbkdf2+sha256':
                pwd_hash = self.pbkdf2('sha256', salt)
                iterations = f':{self._pwd_hash_iter}'
            elif self._pwd_hash_algo == 'sha512':
                pwd = salt + self._password.encode('utf-8')
                pwd_hash = hashlib.sha512(pwd).hexdigest()
            elif self._pwd_hash_algo == 'sha256':
                pwd = salt + self._password.encode('utf-8')
                pwd_hash = hashlib.sha256(pwd).hexdigest()
            if not pwd_hash:
                return None
            cmd = _PROTO_INIT_HASH % {
                'algo': self._pwd_hash_algo,
                'salt': bytearray(salt).hex(),
                'iter': iterations,
                'hash': pwd_hash,
                'totp': totp,
            }
        return cmd

    def _build_sync_command(self):
        """Build the sync commands to send to WeeChat."""
        cmd = '\n'.join(_PROTO_SYNC_CMDS) + '\n'
        return cmd % {'lines': self._lines}

    def handshake_timer_expired(self):
        if self.status == STATUS_AUTHENTICATING:
            self._pwd_hash_algo = 'plain'
            self.send_to_weechat(self._build_init_command())
            self.sync_weechat()
            self.set_status(STATUS_CONNECTED)

    def _socket_connected(self):
        """Slot: socket connected."""
        self.set_status(STATUS_AUTHENTICATING)
        self.send_to_weechat(_PROTO_HANDSHAKE)
        self._handshake_timer = QtCore.QTimer()
        self._handshake_timer.setSingleShot(True)
        self._handshake_timer.setInterval(2000)
        self._handshake_timer.timeout.connect(self.handshake_timer_expired)
        self._handshake_timer.start()

    def _socket_read(self):
        """Slot: data available on socket."""
        data = self._socket.readAll()
        self._buffer.append(data)
        while len(self._buffer) >= 4:
            remainder = None
            length = struct.unpack('>i', self._buffer[0:4].data())[0]
            if len(self._buffer) < length:
                # partial message, just wait for end of message
                break
            # more than one message?
            if length < len(self._buffer):
                # save beginning of another message
                remainder = self._buffer[length:]
                self._buffer = self._buffer[0:length]
            self.messageFromWeechat.emit(self._buffer)
            if not self.is_connected():
                return
            self._buffer.clear()
            if remainder:
                self._buffer.append(remainder)

    def _socket_disconnected(self):
        """Slot: socket disconnected."""
        if self._handshake_timer:
            self._handshake_timer.stop()
        self._init_connection()
        self.set_status(STATUS_DISCONNECTED)

    def is_connected(self):
        """Return True if the socket is connected, False otherwise."""
        return self._socket.state() == QtNetwork.QAbstractSocket.ConnectedState

    def is_ssl(self):
        """Return True if SSL is used, False otherwise."""
        return self._ssl

    def connect_weechat(self, hostname, port, ssl, password, totp, lines):
        """Connect to WeeChat."""
        self._hostname = hostname
        try:
            self._port = int(port)
        except ValueError:
            self._port = 0
        self._ssl = ssl
        self._password = password
        self._totp = totp
        try:
            self._lines = int(lines)
        except ValueError:
            self._lines = config.CONFIG_DEFAULT_RELAY_LINES
        if self._socket.state() == QtNetwork.QAbstractSocket.ConnectedState:
            return
        if self._socket.state() != QtNetwork.QAbstractSocket.UnconnectedState:
            self._socket.abort()
        if self._ssl:
            self._socket.ignoreSslErrors()
            self._socket.connectToHostEncrypted(self._hostname, self._port)
        else:
            self._socket.connectToHost(self._hostname, self._port)
        self.set_status(STATUS_CONNECTING)

    def disconnect_weechat(self):
        """Disconnect from WeeChat."""
        if self._socket.state() == QtNetwork.QAbstractSocket.UnconnectedState:
            self.set_status(STATUS_DISCONNECTED)
            return
        if self._socket.state() == QtNetwork.QAbstractSocket.ConnectedState:
            self.send_to_weechat('quit\n')
            self._socket.waitForBytesWritten(1000)
        else:
            self.set_status(STATUS_DISCONNECTED)
        self._socket.abort()

    def send_to_weechat(self, message):
        """Send a message to WeeChat."""
        self.debug_print(0, '<==', message, forcecolor='#AA0000')
        self._socket.write(message.encode('utf-8'))

    def init_with_handshake(self, response):
        """Initialize with WeeChat using the handshake response."""
        self._pwd_hash_algo = response['password_hash_algo']
        self._pwd_hash_iter = int(response['password_hash_iterations'])
        self._server_nonce = bytearray.fromhex(response['nonce'])
        if self._pwd_hash_algo:
            cmd = self._build_init_command()
            if cmd:
                self.send_to_weechat(cmd)
                self.sync_weechat()
                self.set_status(STATUS_CONNECTED)
                return
        # failed to initialize: disconnect
        self.disconnect_weechat()

    def desync_weechat(self):
        """Desynchronize from WeeChat."""
        self.send_to_weechat('desync\n')

    def sync_weechat(self):
        """Synchronize with WeeChat."""
        self.send_to_weechat(self._build_sync_command())

    def status_label(self, status):
        """Return the label for a given status."""
        return NETWORK_STATUS.get(status, {}).get('label', '')

    def status_color(self, status):
        """Return the color for a given status."""
        return NETWORK_STATUS.get(status, {}).get('color', 'black')

    def status_icon(self, status):
        """Return the name of icon for a given status."""
        return NETWORK_STATUS.get(status, {}).get('icon', '')

    def get_options(self):
        """Get connection options."""
        return {
            'hostname': self._hostname,
            'port': self._port,
            'ssl': 'on' if self._ssl else 'off',
            'password': self._password,
            'lines': str(self._lines),
        }

    def debug_print(self, *args, **kwargs):
        """Display a debug message."""
        self.debug_lines.append((args, kwargs))
        if self.debug_dialog:
            self.debug_dialog.chat.display(*args, **kwargs)

    def _debug_dialog_closed(self, result):
        """Called when debug dialog is closed."""
        self.debug_dialog = None

    def debug_input_text_sent(self, text):
        """Send debug buffer input to WeeChat."""
        if self.network.is_connected():
            text = str(text)
            pos = text.find(')')
            if text.startswith('(') and pos >= 0:
                text = '(debug_%s)%s' % (text[1:pos], text[pos+1:])
            else:
                text = '(debug) %s' % text
            self.network.debug_print(0, '<==', text, forcecolor='#AA0000')
            self.network.send_to_weechat(text + '\n')

    def open_debug_dialog(self):
        """Open a dialog with debug messages."""
        if not self.debug_dialog:
            self.debug_dialog = DebugDialog()
            self.debug_dialog.input.textSent.connect(
                self.debug_input_text_sent)
            self.debug_dialog.finished.connect(self._debug_dialog_closed)
            self.debug_dialog.display_lines(self.debug_lines)
            self.debug_dialog.chat.scroll_bottom()
