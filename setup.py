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

import os
from distutils.core import setup

def listfiles(dir):
    return ['%s/%s' % (dir, f) for f in os.listdir(dir)]

setup(name='qweechat',
      version='0.0.1-dev',
      description='Qt remote GUI for WeeChat',
      long_description='Qt remote GUI for WeeChat',
      author='Sébastien Helleu',
      author_email='flashcode@flashtux.org',
      url='http://www.weechat.org/',
      license='GPL3',
      classifiers = ['Development Status :: 2 - Pre-Alpha',
                     'Environment :: X11 Applications :: Qt',
                     'Intended Audience :: End Users/Desktop',
                     'License :: OSI Approved :: GNU General Public License (GPL)',
                     'Natural Language :: English',
                     'Operating System :: OS Independent',
                     'Programming Language :: Python',
                     'Topic :: Communications :: Chat',
                     ],
      platforms='OS Independent',
      packages=['qweechat',
                'qweechat.weechat',
                ],
      package_dir={'qweechat': 'src/qweechat',
                   'qweechat.weechat': 'src/qweechat/weechat',
                   },
      data_files=[('data/icons', listfiles('data/icons'))]
      )
