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
import sigrok.core as sr

QtCore = qtcompat.QtCore
QtGui = qtcompat.QtGui

class Setting(QtCore.QObject):
    '''Wrapper class around the raw 'QSettings' class that emits signals
    when the value of the setting changes.'''

    '''Signal emitted when the setting has changed.'''
    changed = QtCore.Signal(object)

    def __init__(self, key, default=None, s=None, d=None):
        '''Initializes the Settings object.

        :param key: The key of the used 'QSettings' object.
        :param default: Value returned if the setting doesn't already exist.
        :param s: Function used to serialize the value into a string.
        :param d: Function used to convert a string into a value.
        '''

        super(self.__class__, self).__init__()

        self._key = key
        self._default = default
        self._serialize = s if s else (lambda x: x)
        self._deserialize = d if d else (lambda x: x)
        self._value = None

    def value(self):
        s = QtCore.QSettings()
        v = s.value(self._key, self._default)
        self._value = self._deserialize(v)
        return self._value

    @QtCore.Slot(object)
    def setValue(self, value):
        if value != self._value:
            s = QtCore.QSettings()
            s.setValue(self._key, self._serialize(value))
            s.sync()
            self._value = value
            self.changed.emit(self._value)

class _SettingsGroup(object):
    '''Dummy class to group multiple 'Setting' objects together.'''
    pass

_default_loglevel = 'WARN'

def _d_loglevel(s):
    '''Converts a string into a sr.LogLevel.'''
    d = {
        'NONE': sr.LogLevel.NONE,
        'ERR':  sr.LogLevel.ERR,
        'WARN': sr.LogLevel.WARN,
        'INFO': sr.LogLevel.INFO,
        'DBG':  sr.LogLevel.DBG,
        'SPEW': sr.LogLevel.SPEW
    }

    if not (s in d):
        s = _default_loglevel

    return d[s]

def _s_loglevel(l):
    '''Converts a sr.LogLevel into a string.'''
    return l.name

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
    graph.backlog = Setting('graph/backlog', 30, d=int)
    globals()['graph'] = graph

    logging = _SettingsGroup()
    logging.level = Setting('logging/level', _default_loglevel,
        s=_s_loglevel, d=_d_loglevel)
    logging.lines = Setting('logging/lines', 1000, d=int)
    globals()['logging'] = logging
