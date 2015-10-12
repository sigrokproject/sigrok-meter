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
import resources

QtCore = qtcompat.QtCore
QtGui = qtcompat.QtGui

def _load_icon(name):
    icon = QtGui.QIcon()

    nameFilters = ['{}-*'.format(name)]
    it = QtCore.QDirIterator(':/icons/', nameFilters)
    while it.hasNext():
        filename = it.next()
        icon.addFile(filename)

    globals()[name] = icon

def load_icons():
    '''Loads all available icons in all sizes from the resource file.

    A QApplication must have been created before this function can be called.
    '''
    _load_icon('about')
    _load_icon('add')
    _load_icon('exit')
    _load_icon('graph')
    _load_icon('log')
    _load_icon('preferences')
    _load_icon('start')
    _load_icon('stop')
