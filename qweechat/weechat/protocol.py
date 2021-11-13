# -*- coding: utf-8 -*-
#
# protocol.py - decode binary messages received from WeeChat/relay
#
# Copyright (C) 2011-2021 Sébastien Helleu <flashcode@flashtux.org>
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
# For info about protocol and format of messages, please read document
# "WeeChat Relay Protocol", available at:  https://weechat.org/doc/
#
# History:
#
# 2011-11-23, Sébastien Helleu <flashcode@flashtux.org>:
#     start dev
#

import collections
import struct
import zlib


class WeechatDict(collections.OrderedDict):
    def __str__(self):
        return '{%s}' % ', '.join(
            ['%s: %s' % (repr(key), repr(self[key])) for key in self])


class WeechatObject:
    def __init__(self, objtype, value, separator='\n'):
        self.objtype = objtype
        self.value = value
        self.separator = separator
        self.indent = '  ' if separator == '\n' else ''
        self.separator1 = '\n%s' % self.indent if separator == '\n' else ''

    def _str_value(self, v):
        if type(v) is str and v is not None:
            return '\'%s\'' % v
        return str(v)

    def _str_value_hdata(self):
        lines = ['%skeys: %s%s%spath: %s' % (self.separator1,
                                             str(self.value['keys']),
                                             self.separator,
                                             self.indent,
                                             str(self.value['path']))]
        for i, item in enumerate(self.value['items']):
            lines.append('  item %d:%s%s' % (
                (i + 1), self.separator,
                self.separator.join(
                    ['%s%s: %s' % (self.indent * 2, key,
                                   self._str_value(value))
                     for key, value in item.items()])))
        return '\n'.join(lines)

    def _str_value_infolist(self):
        lines = ['%sname: %s' % (self.separator1, self.value['name'])]
        for i, item in enumerate(self.value['items']):
            lines.append('  item %d:%s%s' % (
                (i + 1), self.separator,
                self.separator.join(
                    ['%s%s: %s' % (self.indent * 2, key,
                                   self._str_value(value))
                     for key, value in item.items()])))
        return '\n'.join(lines)

    def _str_value_other(self):
        return self._str_value(self.value)

    def __str__(self):
        self._obj_cb = {
            'hda': self._str_value_hdata,
            'inl': self._str_value_infolist,
        }
        return '%s: %s' % (self.objtype,
                           self._obj_cb.get(self.objtype,
                                            self._str_value_other)())


class WeechatObjects(list):
    def __init__(self, separator='\n'):
        self.separator = separator

    def __str__(self):
        return self.separator.join([str(obj) for obj in self])


class WeechatMessage:
    def __init__(self, size, size_uncompressed, compression, uncompressed,
                 msgid, objects):
        self.size = size
        self.size_uncompressed = size_uncompressed
        self.compression = compression
        self.uncompressed = uncompressed
        self.msgid = msgid
        self.objects = objects

    def __str__(self):
        if self.compression != 0:
            return 'size: %d/%d (%d%%), id=\'%s\', objects:\n%s' % (
                self.size, self.size_uncompressed,
                100 - ((self.size * 100) // self.size_uncompressed),
                self.msgid, self.objects)
        else:
            return 'size: %d, id=\'%s\', objects:\n%s' % (self.size,
                                                          self.msgid,
                                                          self.objects)


class Protocol:
    """Decode binary message received from WeeChat/relay."""

    def __init__(self):
        self._obj_cb = {
            'chr': self._obj_char,
            'int': self._obj_int,
            'lon': self._obj_long,
            'str': self._obj_str,
            'buf': self._obj_buffer,
            'ptr': self._obj_ptr,
            'tim': self._obj_time,
            'htb': self._obj_hashtable,
            'hda': self._obj_hdata,
            'inf': self._obj_info,
            'inl': self._obj_infolist,
            'arr': self._obj_array,
        }

    def _obj_type(self):
        """Read type in data (3 chars)."""
        if len(self.data) < 3:
            self.data = ''
            return ''
        objtype = self.data[0:3].decode()
        self.data = self.data[3:]
        return objtype

    def _obj_len_data(self, length_size):
        """Read length (1 or 4 bytes), then value with this length."""
        if len(self.data) < length_size:
            self.data = ''
            return None
        if length_size == 1:
            length = struct.unpack('B', self.data[0:1])[0]
            self.data = self.data[1:]
        else:
            length = self._obj_int()
        if length < 0:
            return None
        if length > 0:
            value = self.data[0:length]
            self.data = self.data[length:]
        else:
            value = ''
        return value

    def _obj_char(self):
        """Read a char in data."""
        if len(self.data) < 1:
            return 0
        value = struct.unpack('b', self.data[0:1])[0]
        self.data = self.data[1:]
        return value

    def _obj_int(self):
        """Read an integer in data (4 bytes)."""
        if len(self.data) < 4:
            self.data = ''
            return 0
        value = struct.unpack('>i', self.data[0:4])[0]
        self.data = self.data[4:]
        return value

    def _obj_long(self):
        """Read a long integer in data (length on 1 byte + value as string)."""
        value = self._obj_len_data(1)
        if value is None:
            return None
        return int(value)

    def _obj_str(self):
        """Read a string in data (length on 4 bytes + content)."""
        value = self._obj_len_data(4)
        if value in ("", None):
            return ""
        return value.decode()

    def _obj_buffer(self):
        """Read a buffer in data (length on 4 bytes + data)."""
        return self._obj_len_data(4)

    def _obj_ptr(self):
        """Read a pointer in data (length on 1 byte + value as string)."""
        value = self._obj_len_data(1)
        if value is None:
            return None
        return '0x%s' % value

    def _obj_time(self):
        """Read a time in data (length on 1 byte + value as string)."""
        value = self._obj_len_data(1)
        if value is None:
            return None
        return int(value)

    def _obj_hashtable(self):
        """
        Read a hashtable in data
        (type for keys + type for values + count + items).
        """
        type_keys = self._obj_type()
        type_values = self._obj_type()
        count = self._obj_int()
        hashtable = WeechatDict()
        for _ in range(count):
            key = self._obj_cb[type_keys]()
            value = self._obj_cb[type_values]()
            hashtable[key] = value
        return hashtable

    def _obj_hdata(self):
        """Read a hdata in data."""
        path = self._obj_str()
        keys = self._obj_str()
        count = self._obj_int()
        list_path = path.split('/') if path else []
        list_keys = keys.split(',') if keys else []
        keys_types = []
        dict_keys = WeechatDict()
        for key in list_keys:
            items = key.split(':')
            keys_types.append(items)
            dict_keys[items[0]] = items[1]
        items = []
        for _ in range(count):
            item = WeechatDict()
            item['__path'] = []
            pointers = []
            for _ in enumerate(list_path):
                pointers.append(self._obj_ptr())
            for key, objtype in keys_types:
                item[key] = self._obj_cb[objtype]()
            item['__path'] = pointers
            items.append(item)
        return {
            'path': list_path,
            'keys': dict_keys,
            'count': count,
            'items': items,
        }

    def _obj_info(self):
        """Read an info in data."""
        name = self._obj_str()
        value = self._obj_str()
        return (name, value)

    def _obj_infolist(self):
        """Read an infolist in data."""
        name = self._obj_str()
        count_items = self._obj_int()
        items = []
        for _ in range(count_items):
            count_vars = self._obj_int()
            variables = WeechatDict()
            for _ in range(count_vars):
                var_name = self._obj_str()
                var_type = self._obj_type()
                var_value = self._obj_cb[var_type]()
                variables[var_name] = var_value
            items.append(variables)
        return {
            'name': name,
            'items': items
        }

    def _obj_array(self):
        """Read an array of values in data."""
        type_values = self._obj_type()
        count_values = self._obj_int()
        values = []
        for _ in range(count_values):
            values.append(self._obj_cb[type_values]())
        return values

    def decode(self, data, separator='\n'):
        """Decode binary data and return list of objects."""
        self.data = data
        size = len(self.data)
        size_uncompressed = size
        uncompressed = None
        # uncompress data (if it is compressed)
        compression = struct.unpack('b', self.data[4:5])[0]
        if compression:
            uncompressed = zlib.decompress(self.data[5:])
            size_uncompressed = len(uncompressed) + 5
            uncompressed = b'%s%s%s' % (struct.pack('>i', size_uncompressed),
                                        struct.pack('b', 0), uncompressed)
            self.data = uncompressed
        else:
            uncompressed = self.data[:]
        # skip length and compression flag
        self.data = self.data[5:]
        # read id
        msgid = self._obj_str()
        if msgid is None:
            msgid = ''
        # read objects
        objects = WeechatObjects(separator=separator)
        while len(self.data) > 0:
            objtype = self._obj_type()
            value = self._obj_cb[objtype]()
            objects.append(WeechatObject(objtype, value, separator=separator))
        return WeechatMessage(size, size_uncompressed, compression,
                              uncompressed, msgid, objects)


def hex_and_ascii(data, bytes_per_line=10):
    """Convert a QByteArray to hex + ascii output."""
    num_lines = ((len(data) - 1) // bytes_per_line) + 1
    if num_lines == 0:
        return ''
    lines = []
    for i in range(num_lines):
        str_hex = []
        str_ascii = []
        for j in range(bytes_per_line):
            # We can't easily iterate over individual bytes, so we are going to
            # do it this way.
            index = (i*bytes_per_line) + j
            char = data[index:index+1]
            if not char:
                char = b'x'
            byte = struct.unpack('B', char)[0]
            str_hex.append(b'%02X' % int(byte))
            if byte >= 32 and byte <= 127:
                str_ascii.append(char)
            else:
                str_ascii.append(b'.')
        fmt = b'%%-%ds %%s' % ((bytes_per_line * 3) - 1)
        lines.append(fmt % (b' '.join(str_hex),
                            b''.join(str_ascii)))
    return b'\n'.join(lines)
