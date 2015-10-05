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

import collections
import itertools
import qtcompat
import sigrok.core as sr
import util

try:
    from itertools import izip
except ImportError:
    izip = zip

QtCore = qtcompat.QtCore
QtGui = qtcompat.QtGui

class Trace(object):
    '''Class to hold the measured samples.'''

    def __init__(self):
        self.samples = []
        self.new = False

    def append(self, sample):
        self.samples.append(sample)
        self.new = True

class MeasurementDataModel(QtGui.QStandardItemModel):
    '''Model to hold the measured values.'''

    '''Role used to identify and find the item.'''
    idRole = QtCore.Qt.UserRole + 1

    '''Role used to store the device vendor and model.'''
    descRole = QtCore.Qt.UserRole + 2

    '''Role used to store a dictionary with the traces'''
    tracesRole = QtCore.Qt.UserRole + 3

    '''Role used to store the color to draw the graph of the channel.'''
    colorRole = QtCore.Qt.UserRole + 4

    def __init__(self, parent):
        super(self.__class__, self).__init__(parent)

        # Use the description text to sort the items for now, because the
        # idRole holds tuples, and using them to sort doesn't work.
        self.setSortRole(MeasurementDataModel.descRole)

        # Used in 'format_value()' to check against.
        self.inf = float('inf')

        # A generator for the colors of the channels.
        self._colorgen = self._make_colorgen()

    def _make_colorgen(self):
        cols = [
            QtGui.QColor(0x8F, 0x52, 0x02), # brown
            QtGui.QColor(0x73, 0xD2, 0x16), # green
            QtGui.QColor(0xCC, 0x00, 0x00), # red
            QtGui.QColor(0x34, 0x65, 0xA4), # blue
            QtGui.QColor(0xF5, 0x79, 0x00), # orange
            QtGui.QColor(0xED, 0xD4, 0x00), # yellow
            QtGui.QColor(0x75, 0x50, 0x7B)  # violet
        ]

        def myrepeat(g, n):
            '''Repeats every element from 'g' 'n' times'.'''
            for e in g:
                for f in itertools.repeat(e, n):
                    yield f

        colorcycle = itertools.cycle(cols)
        darkness = myrepeat(itertools.count(100, 10), len(cols))

        for c, d in izip(colorcycle, darkness):
            yield QtGui.QColor(c).darker(d)

    def format_mqflags(self, mqflags):
        if sr.QuantityFlag.AC in mqflags:
            return 'AC'
        elif sr.QuantityFlag.DC in mqflags:
            return 'DC'
        else:
            return ''

    def format_value(self, mag):
        if mag == self.inf:
            return u'\u221E'
        return '{:f}'.format(mag)

    def getItem(self, device, channel):
        '''Return the item for the device + channel combination from the
        model, or create a new item if no existing one matches.'''

        # Unique identifier for the device + channel.
        # TODO: Isn't there something better?
        uid = (
            device.vendor,
            device.model,
            device.serial_number(),
            device.connection_id(),
            channel.index
        )

        # Find the correct item in the model.
        for row in range(self.rowCount()):
            item = self.item(row)
            rid = item.data(MeasurementDataModel.idRole)
            rid = tuple(rid) # PySide returns a list.
            if uid == rid:
                return item

        # Nothing found, create a new item.
        desc = '{} {}, {}'.format(
                device.vendor, device.model, channel.name)

        item = QtGui.QStandardItem()
        item.setData(uid, MeasurementDataModel.idRole)
        item.setData(desc, MeasurementDataModel.descRole)
        item.setData(collections.defaultdict(Trace), MeasurementDataModel.tracesRole)
        item.setData(next(self._colorgen), MeasurementDataModel.colorRole)
        self.appendRow(item)
        self.sort(0)
        return item

    @QtCore.Slot(float, sr.classes.Device, sr.classes.Channel, tuple)
    def update(self, timestamp, device, channel, data):
        '''Update the data for the device (+channel) with the most recent
        measurement from the given payload.'''

        item = self.getItem(device, channel)

        value, unit, mqflags = data
        value_str = self.format_value(value)
        unit_str = util.format_unit(unit)
        mqflags_str = self.format_mqflags(mqflags)

        # The display role is a tuple containing the value and the unit/flags.
        disp = (value_str, ' '.join([unit_str, mqflags_str]))
        item.setData(disp, QtCore.Qt.DisplayRole)

        # The samples role is a dictionary that contains the old samples for each unit.
        # Should be trimmed periodically, otherwise it grows larger and larger.
        sample = (timestamp, value)
        traces = item.data(MeasurementDataModel.tracesRole)
        traces[unit].append(sample)

class MultimeterDelegate(QtGui.QStyledItemDelegate):
    '''Delegate to show the data items from a MeasurementDataModel.'''

    def __init__(self, parent, font):
        '''Initialize the delegate.

        :param font: Font used for the text.
        '''

        super(self.__class__, self).__init__(parent)

        self._nfont = font

        fi = QtGui.QFontInfo(self._nfont)
        self._nfontheight = fi.pixelSize()

        fm = QtGui.QFontMetrics(self._nfont)
        r = fm.boundingRect('-XX.XXXXXX X XX')

        w = 1.4 * r.width() + 2 * self._nfontheight
        h = 2.6 * self._nfontheight
        self._size = QtCore.QSize(w, h)

    def sizeHint(self, option=None, index=None):
        return self._size

    def _color_rect(self, outer):
        '''Returns the dimensions of the clickable rectangle.'''
        x1 = (outer.height() - self._nfontheight) / 2
        r = QtCore.QRect(x1, x1, self._nfontheight, self._nfontheight)
        r.translate(outer.topLeft())
        return r

    def paint(self, painter, options, index):
        value, unit = index.data(QtCore.Qt.DisplayRole)
        desc = index.data(MeasurementDataModel.descRole)
        color = index.data(MeasurementDataModel.colorRole)

        painter.setFont(self._nfont)

        # Draw the clickable rectangle.
        painter.fillRect(self._color_rect(options.rect), color)

        # Draw the text
        h = options.rect.height()
        p = options.rect.topLeft()
        p += QtCore.QPoint(h, (h + self._nfontheight) / 2 - 2)
        painter.drawText(p, desc + ': ' + value + ' ' + unit)

    def editorEvent(self, event, model, options, index):
        if type(event) is QtGui.QMouseEvent:
            if event.type() == QtCore.QEvent.MouseButtonPress:
                rect = self._color_rect(options.rect)
                if rect.contains(event.x(), event.y()):
                    c = index.data(MeasurementDataModel.colorRole)
                    c = QtGui.QColorDialog.getColor(c, None,
                        'Choose new color for channel')

                    item = model.itemFromIndex(index)
                    item.setData(c, MeasurementDataModel.colorRole)

                    return True

        return False
