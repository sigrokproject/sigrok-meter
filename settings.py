##
## This file is part of the sigrok-meter project.
##
## Copyright (C) 2015 Jens Steinhauser <jens.steinhauser@gmail.com>
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

import qtcompat

QtCore = qtcompat.QtCore
QtGui = qtcompat.QtGui

class Setting(QtCore.QObject):
    '''Wrapper class around the raw 'QSettings' class that emits signals
    when the value of the setting changes.'''

    '''Signal emitted when the setting has changed.'''
    changed = QtCore.Signal(object)

    def __init__(self, key, default=None, conv=None):
        '''Initializes the Settings object.

        :param key: The key of the used 'QSettings' object.
        :param default: Value returned if the setting doesn't already exist.
        :param conv: Function used to convert the setting to the correct type.
        '''

        super(self.__class__, self).__init__()

        self._key = key
        self._default = default
        self._conv = conv
        self._value = None

    def value(self):
        s = QtCore.QSettings()
        v = s.value(self._key, self._default)
        self._value = self._conv(v) if self._conv else v
        return self._value

    @QtCore.Slot(object)
    def setValue(self, value):
        if value != self._value:
            s = QtCore.QSettings()
            s.setValue(self._key, value)
            s.sync()
            self._value = value
            self.changed.emit(self._value)

class _SettingsGroup(object):
    '''Dummy class to group multiple 'Setting' objects together.'''
    pass

def init():
    '''Creates the 'Settings' objects for all known settings and places them
    into the module's namespace.

    A QApplication must have been created before this function can be called.
    '''

    app = QtGui.QApplication.instance()
    app.setApplicationName('sigrok-meter')
    app.setOrganizationName('sigrok')
    app.setOrganizationDomain('sigrok.org')

    mainwindow = _SettingsGroup()
    mainwindow.size = Setting('mainwindow/size', QtCore.QSize(900, 550))
    mainwindow.pos  = Setting('mainwindow/pos')
    globals()['mainwindow'] = mainwindow

    graph = _SettingsGroup()
    graph.backlog = Setting('graph/backlog', 30, conv=int)
    globals()['graph'] = graph
