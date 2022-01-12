# -*- coding: utf-8 -*-
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

from setuptools import setup
from qweechat.version import qweechat_version

DESCRIPTION = 'Qt remote GUI for WeeChat'

setup(
    name='qweechat',
    version=qweechat_version(),
    description=DESCRIPTION,
    long_description=DESCRIPTION,
    author='Sébastien Helleu',
    author_email='flashcode@flashtux.org',
    url='https://weechat.org/',
    license='GPL3',
    keywords='weechat qt gui',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 '
        'or later (GPLv3+)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Communications :: Chat',
    ],
    packages=['qweechat', 'qweechat.weechat'],
    include_package_data=True,
    package_data={'qweechat': ['data/icons/*.png']},
    entry_points={
        'gui_scripts': [
            'qweechat = qweechat.qweechat:main',
        ],
        'console_scripts': [
            'qweechat-testproto = qweechat.weechat.testproto:main',
        ]
    },
    install_requires=[
        'PySide6',
    ],
)
