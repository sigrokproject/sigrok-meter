##
## This file is part of the sigrok-meter project.
##
## Copyright (C) 2014 Jens Steinhauser <jens.steinhauser@gmail.com>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
##

def load_modules(force_pyside):
    if force_pyside:
        import PySide.QtCore as _QtCore
        import PySide.QtGui as _QtGui
    else:
        try:
            # Use version 2 API in all cases, because that's what PySide uses.
            import sip
            sip.setapi('QVariant', 2)
            sip.setapi('QDate', 2)
            sip.setapi('QDateTime', 2)
            sip.setapi('QString', 2)
            sip.setapi('QTextStream', 2)
            sip.setapi('QTime', 2)
            sip.setapi('QUrl', 2)
            sip.setapi('QVariant', 2)

            import PyQt4.QtCore as _QtCore
            import PyQt4.QtGui as _QtGui

            # Add PySide compatible names.
            _QtCore.Signal = _QtCore.pyqtSignal
            _QtCore.Slot = _QtCore.pyqtSlot
        except:
            sys.stderr.write('Import of PyQt4 failed, using PySide,\n')
            import PySide.QtCore as _QtCore
            import PySide.QtGui as _QtGui

    global QtCore
    global QtGui
    QtCore = _QtCore
    QtGui = _QtGui
