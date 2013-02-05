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

#
# Usage:  python testproto.py [-h] [-v] [-6] <hostname> <port>
#
# With initial commands: echo "init password=xxxx" | python testproto.py localhost 5000
#                        python testproto.py localhost 5000 < commands.txt
#
# Return code:
#   0: OK
#   1: missing/invalid arguments (hostname or port)
#   2: connection to WeeChat/relay failed
#   3: I/O error with WeeChat/relay
#

import os, sys, socket, select, struct, time
import protocol  # WeeChat/relay protocol

options = { 'h': False, 'v': False, '6': False }
hostname = None
port = None

def usage():
    """Display usage."""
    print('\nSyntax: python %s [-h] [-v] [-6] <hostname> <port>\n' % sys.argv[0])
    print('  -h              display this help')
    print('  -v              verbose mode (display raw messages received)')
    print('  -6              connect using IPv6')
    print('  hostname, port  hostname (or IP address) and port of machine running WeeChat relay')
    print('')
    print('Some commands can be piped to the script, for example:')
    print('  echo "init password=xxxx" | python %s localhost 5000' % sys.argv[0])
    print('  python %s localhost 5000 < commands.txt' % sys.argv[0])
    print('')

def connect(address, ipv6):
    """Connect to WeeChat/relay."""
    inet = socket.AF_INET6 if ipv6 else socket.AF_INET
    sock = None
    try:
        sock = socket.socket(inet, socket.SOCK_STREAM)
        sock.connect(address)
    except:
        if sock:
            sock.close()
        print('Failed to connect to %s/%d using %s' % (address[0], address[1],
                                                       'IPv4' if inet == socket.AF_INET else 'IPv6'))
        return (None, None)
    print('Connected to %s/%d (%s)' % (hostname, port,
                                       'IPv4' if inet == socket.AF_INET else 'IPv6'))
    return (sock, inet)

def send(sock, messages):
    """Send a text message to WeeChat/relay."""
    has_quit = False
    try:
        for msg in messages.split('\n'):
            if msg == 'quit':
                has_quit = True
            sock.sendall(msg + '\n')
            print('\x1b[33m<-- %s\x1b[0m' % msg)
    except:
        print('Failed to send message')
        return (False, has_quit)
    return (True, has_quit)

def decode(message):
    """Decode a binary message received from WeeChat/relay."""
    global options
    try:
        proto = protocol.Protocol()
        message = proto.decode(message)
        print('')
        if options['v'] and message.uncompressed:
            # display raw message
            print('\x1b[32m--> message uncompressed (%d bytes):\n%s\x1b[0m'
                  % (message.size_uncompressed,
                     protocol.hex_and_ascii(message.uncompressed, 20)))
        # display decoded message
        print('\x1b[32m--> %s\x1b[0m' % message)
    except:
        print('Error while decoding message from WeeChat')
        return False
    return True

def mainloop(sock):
    """Main loop: read keyboard, send commands, read socket and decode and display received binary messages."""
    message = ''
    recvbuf = ''
    prompt = '\x1b[36mrelay> \x1b[0m'
    sys.stdout.write(prompt)
    sys.stdout.flush()
    try:
        while True:
            inr, outr, exceptr = select.select([sys.stdin, sock], [], [], 1)
            for fd in inr:
                if fd == sys.stdin:
                    buf = os.read(fd.fileno(), 4096)
                    if buf:
                        message += buf
                        if '\n' in message:
                            messages = message.split('\n')
                            msgsent = '\n'.join(messages[:-1])
                            if msgsent:
                                (send_ok, has_quit) = send(sock, msgsent)
                                if not send_ok:
                                    return 3
                                if has_quit:
                                    return 0
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
                                # partial message, just wait for end of message
                                break
                            # more than one message?
                            if length < len(recvbuf):
                                # save beginning of another message
                                remainder = recvbuf[length:]
                                recvbuf = recvbuf[0:length]
                            if not decode(recvbuf):
                                return 3
                            if remainder:
                                recvbuf = remainder
                            else:
                                recvbuf = ''
                        sys.stdout.write(prompt + message)
                        sys.stdout.flush()
    except:
        send(sock, 'quit')

# display help if arguments are missing
if len(sys.argv) < 3:
    usage()
    sys.exit(1)

# read command line arguments
try:
    for arg in sys.argv[1:]:
        if arg[0] == '-':
            options[arg[1:]] = True
        elif hostname:
            port = int(arg)
        else:
            hostname = arg
except:
    print('Invalid arguments')
    sys.exit(1)

if options['h']:
    usage()
    sys.exit(0)

# connect to WeeChat/relay
(sock, inet) = connect((hostname, port), options['6'])
if not sock:
    sys.exit(2)

# send commands from standard input if some data is available
has_quit = False
inr, outr, exceptr = select.select([sys.stdin], [], [], 0)
if inr:
    data = os.read(sys.stdin.fileno(), 4096)
    if data:
        (send_ok, has_quit) = send(sock, data.strip())
        if not send_ok:
            sock.close()
            sys.exit(3)
    # open stdin to read user commands
    sys.stdin = open('/dev/tty')

# main loop (wait commands, display messages received)
if not has_quit:
    mainloop(sock)
time.sleep(0.5)
sock.close()
