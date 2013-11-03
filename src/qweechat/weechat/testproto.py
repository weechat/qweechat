#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# testproto.py - command-line program for testing protocol WeeChat/relay
#
# Copyright (C) 2013 Sebastien Helleu <flashcode@flashtux.org>
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

from __future__ import print_function

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


class TestProto:

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
        except:
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
            for msg in messages.split('\n'):
                if msg == 'quit':
                    self.has_quit = True
                self.sock.sendall(msg + '\n')
                print('\x1b[33m<-- ' + msg + '\x1b[0m')
        except:
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
                                separator='\n' if self.args.verbose > 0
                                else ', ')
            print('')
            if self.args.verbose >= 2 and msgd.uncompressed:
                # display raw message
                print('\x1b[32m--> message uncompressed ({0} bytes):\n'
                      '{1}\x1b[0m'
                      ''.format(msgd.size_uncompressed,
                                protocol.hex_and_ascii(msgd.uncompressed, 20)))
            # display decoded message
            print('\x1b[32m--> {0}\x1b[0m'.format(msgd))
        except:
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
        inr, outr, exceptr = select.select([sys.stdin], [], [], 0)
        if inr:
            data = os.read(sys.stdin.fileno(), 4096)
            if data:
                if not test.send(data.strip()):
                    #self.sock.close()
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
        message = ''
        recvbuf = ''
        prompt = '\x1b[36mrelay> \x1b[0m'
        sys.stdout.write(prompt)
        sys.stdout.flush()
        try:
            while not self.has_quit:
                inr, outr, exceptr = select.select([sys.stdin, self.sock],
                                                   [], [], 1)
                for fd in inr:
                    if fd == sys.stdin:
                        buf = os.read(fd.fileno(), 4096)
                        if buf:
                            message += buf
                            if '\n' in message:
                                messages = message.split('\n')
                                msgsent = '\n'.join(messages[:-1])
                                if msgsent and not self.send(msgsent):
                                    return 4
                                message = messages[-1]
                                sys.stdout.write(prompt + message)
                                sys.stdout.flush()
                    else:
                        buf = fd.recv(4096)
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
                                    recvbuf = ''
                            sys.stdout.write(prompt + message)
                            sys.stdout.flush()
        except:
            traceback.print_exc()
            self.send('quit')
        return 0

    def __del__(self):
        print('Closing connection with', self.address)
        time.sleep(0.5)
        self.sock.close()


if __name__ == "__main__":
    # parse command line arguments
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        fromfile_prefix_chars='@',
        description='Command-line program for testing protocol WeeChat/relay.',
        epilog='''
Environment variable "TESTPROTO_OPTIONS" can be set with default options.
Argument "@file.txt" can be used to read default options in a file.

Some commands can be piped to the script, for example:
  echo "init password=xxxx" | python {0} localhost 5000
  python {0} localhost 5000 < commands.txt

The script returns:
  0: OK
  2: wrong arguments (command line)
  3: connection error
  4: send error (message sent to WeeChat)
  5: decode error (message received from WeeChat)
'''.format(sys.argv[0]))
    parser.add_argument('-6', '--ipv6', action='store_true',
                        help='connect using IPv6')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='verbose mode: long objects view '
                        '(-vv: display raw messages)')
    parser.add_argument('hostname',
                        help='hostname (or IP address) of machine running '
                        'WeeChat/relay')
    parser.add_argument('port', type=int,
                        help='port of machine running WeeChat/relay')
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    args = parser.parse_args(
        shlex.split(os.getenv('TESTPROTO_OPTIONS') or '') + sys.argv[1:])

    test = TestProto(args)

    # connect to WeeChat/relay
    if not test.connect():
        sys.exit(3)

    # send commands from standard input if some data is available
    if not test.send_stdin():
        sys.exit(4)

    # main loop (wait commands, display messages received)
    rc = test.mainloop()
    del test
    sys.exit(rc)
