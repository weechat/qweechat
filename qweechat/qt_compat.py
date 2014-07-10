# -*- coding: utf-8 -*-
#
# File downloaded from:
#   https://github.com/epage/PythonUtils/blob/master/util/qt_compat.py
# Author: epage
# License: LGPL 2.1
#

from __future__ import with_statement
from __future__ import division

_TRY_PYSIDE = True
uses_pyside = False

try:
    if not _TRY_PYSIDE:
        raise ImportError()
    import PySide.QtCore as _QtCore
    QtCore = _QtCore
    uses_pyside = True
except ImportError:
    import sip
    sip.setapi('QString', 2)
    sip.setapi('QVariant', 2)
    import PyQt4.QtCore as _QtCore
    QtCore = _QtCore
    uses_pyside = False


def _pyside_import_module(moduleName):
    pyside = __import__('PySide', globals(), locals(), [moduleName], -1)
    return getattr(pyside, moduleName)


def _pyqt4_import_module(moduleName):
    pyside = __import__('PyQt4', globals(), locals(), [moduleName], -1)
    return getattr(pyside, moduleName)


if uses_pyside:
    import_module = _pyside_import_module

    Signal = QtCore.Signal
    Slot = QtCore.Slot
    Property = QtCore.Property
else:
    import_module = _pyqt4_import_module

    Signal = QtCore.pyqtSignal
    Slot = QtCore.pyqtSlot
    Property = QtCore.pyqtProperty


if __name__ == "__main__":
    pass
