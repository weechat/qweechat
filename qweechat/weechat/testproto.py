# -*- coding: utf-8 -*-
#
# testproto.py - command-line program for testing WeeChat/relay protocol
#
# Copyright (C) 2013-2021 Sébastien Helleu <flashcode@flashtux.org>
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
Command-line program for testing WeeChat/relay protocol.
"""

import argparse
import os
import select
import shlex
import socket
import struct
import sys
import time
import traceback

import protocol  # WeeChat/relay protocol
# from .. version import qweechat_version
qweechat_version = '1.1'

NAME = 'qweechat-testproto'


class TestProto(object):
    """Test of WeeChat/relay protocol."""

    def __init__(self, args):
        self.args = args
        self.sock = None
        self.has_quit = False
        self.address = '{self.args.hostname}/{self.args.port} ' \
            '(IPv{0})'.format(6 if self.args.ipv6 else 4, self=self)

    def connect(self):
        """
        Connect to WeeChat/relay.
        Return True if OK, False if error.
        """
        inet = socket.AF_INET6 if self.args.ipv6 else socket.AF_INET
        try:
            self.sock = socket.socket(inet, socket.SOCK_STREAM)
            self.sock.connect((self.args.hostname, self.args.port))
        except:  # noqa: E722
            if self.sock:
                self.sock.close()
            print('Failed to connect to', self.address)
            return False
        print('Connected to', self.address)
        return True

    def send(self, messages):
        """
        Send a text message to WeeChat/relay.
        Return True if OK, False if error.
        """
        try:
            for msg in messages.split(b'\n'):
                if msg == b'quit':
                    self.has_quit = True
                self.sock.sendall(msg + b'\n')
                sys.stdout.write(
                    (b'\x1b[33m<-- ' + msg + b'\x1b[0m\n').decode())
        except:  # noqa: E722
            traceback.print_exc()
            print('Failed to send message')
            return False
        return True

    def decode(self, message):
        """
        Decode a binary message received from WeeChat/relay.
        Return True if OK, False if error.
        """
        try:
            proto = protocol.Protocol()
            msgd = proto.decode(message,
                                separator=b'\n' if self.args.debug > 0
                                else ', ')
            print('')
            if self.args.debug >= 2 and msgd.uncompressed:
                # display raw message
                print('\x1b[32m--> message uncompressed ({0} bytes):\n'
                      '{1}\x1b[0m'
                      ''.format(msgd.size_uncompressed,
                                protocol.hex_and_ascii(msgd.uncompressed, 20)))
            # display decoded message
            print('\x1b[32m--> {0}\x1b[0m'.format(msgd))
        except:  # noqa: E722
            traceback.print_exc()
            print('Error while decoding message from WeeChat')
            return False
        return True

    def send_stdin(self):
        """
        Send commands from standard input if some data is available.
        Return True if OK (it's OK if stdin has no commands),
        False if error.
        """
        inr = select.select([sys.stdin], [], [], 0)[0]
        if inr:
            data = os.read(sys.stdin.fileno(), 4096)
            if data:
                if not self.send(data.strip()):
                    # self.sock.close()
                    return False
            # open stdin to read user commands
            sys.stdin = open('/dev/tty')
        return True

    def mainloop(self):
        """
        Main loop: read keyboard, send commands, read socket,
        decode/display binary messages received from WeeChat/relay.
        Return 0 if OK, 4 if send error, 5 if decode error.
        """
        if self.has_quit:
            return 0
        message = b''
        recvbuf = b''
        prompt = b'\x1b[36mrelay> \x1b[0m'
        sys.stdout.write(prompt.decode())
        sys.stdout.flush()
        try:
            while not self.has_quit:
                inr = select.select([sys.stdin, self.sock], [], [], 1)[0]
                for _file in inr:
                    if _file == sys.stdin:
                        buf = os.read(_file.fileno(), 4096)
                        if buf:
                            message += buf
                            if b'\n' in message:
                                messages = message.split(b'\n')
                                msgsent = b'\n'.join(messages[:-1])
                                if msgsent and not self.send(msgsent):
                                    return 4
                                message = messages[-1]
                                sys.stdout.write((prompt + message).decode())
                                # sys.stdout.write(prompt + message)
                                sys.stdout.flush()
                    else:
                        buf = _file.recv(4096)
                        if buf:
                            recvbuf += buf
                            while len(recvbuf) >= 4:
                                remainder = None
                                length = struct.unpack('>i', recvbuf[0:4])[0]
                                if len(recvbuf) < length:
                                    # partial message, just wait for the
                                    # end of message
                                    break
                                # more than one message?
                                if length < len(recvbuf):
                                    # save beginning of another message
                                    remainder = recvbuf[length:]
                                    recvbuf = recvbuf[0:length]
                                if not self.decode(recvbuf):
                                    return 5
                                if remainder:
                                    recvbuf = remainder
                                else:
                                    recvbuf = b''
                            sys.stdout.write((prompt + message).decode())
                            sys.stdout.flush()
        except:  # noqa: E722
            traceback.print_exc()
            self.send(b'quit')
        return 0

    def __del__(self):
        print('Closing connection with', self.address)
        time.sleep(0.5)
        self.sock.close()


def main():
    """Main function."""
    # parse command line arguments
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        fromfile_prefix_chars='@',
        description='Command-line program for testing WeeChat/relay protocol.',
        epilog='''
Environment variable "QWEECHAT_PROTO_OPTIONS" can be set with default options.
Argument "@file.txt" can be used to read default options in a file.

Some commands can be piped to the script, for example:
  echo "init password=xxxx" | {name} localhost 5000
  {name} localhost 5000 < commands.txt

The script returns:
  0: OK
  2: wrong arguments (command line)
  3: connection error
  4: send error (message sent to WeeChat)
  5: decode error (message received from WeeChat)
'''.format(name=NAME))
    parser.add_argument('-6', '--ipv6', action='store_true',
                        help='connect using IPv6')
    parser.add_argument('-d', '--debug', action='count', default=0,
                        help='debug mode: long objects view '
                        '(-dd: display raw messages)')
    parser.add_argument('-v', '--version', action='version',
                        version=qweechat_version)
    parser.add_argument('hostname',
                        help='hostname (or IP address) of machine running '
                        'WeeChat/relay')
    parser.add_argument('port', type=int,
                        help='port of machine running WeeChat/relay')
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    _args = parser.parse_args(
        shlex.split(os.getenv('QWEECHAT_PROTO_OPTIONS') or '') + sys.argv[1:])

    test = TestProto(_args)

    # connect to WeeChat/relay
    if not test.connect():
        sys.exit(3)

    # send commands from standard input if some data is available
    if not test.send_stdin():
        sys.exit(4)

    # main loop (wait commands, display messages received)
    returncode = test.mainloop()
    del test
    sys.exit(returncode)


if __name__ == "__main__":
    main()
