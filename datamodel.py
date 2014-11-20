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

import qtcompat
import sigrok.core as sr

QtCore = qtcompat.QtCore
QtGui = qtcompat.QtGui

class MeasurementDataModel(QtGui.QStandardItemModel):
    '''Model to hold the measured values.'''

    '''Role used to identify and find the item.'''
    _idRole = QtCore.Qt.UserRole + 1

    '''Role used to store the device vendor and model.'''
    descRole = QtCore.Qt.UserRole + 2

    def __init__(self, parent):
        super(self.__class__, self).__init__(parent)

        # Use the description text to sort the items for now, because the
        # _idRole holds tuples, and using them to sort doesn't work.
        self.setSortRole(MeasurementDataModel.descRole)

        # Used in 'format_value()' to check against.
        self.inf = float('inf')

    def format_unit(self, u):
        units = {
            sr.Unit.VOLT:                   'V',
            sr.Unit.AMPERE:                 'A',
            sr.Unit.OHM:                   u'\u03A9',
            sr.Unit.FARAD:                  'F',
            sr.Unit.KELVIN:                 'K',
            sr.Unit.CELSIUS:               u'\u00B0C',
            sr.Unit.FAHRENHEIT:            u'\u00B0F',
            sr.Unit.HERTZ:                  'Hz',
            sr.Unit.PERCENTAGE:             '%',
          # sr.Unit.BOOLEAN
            sr.Unit.SECOND:                 's',
            sr.Unit.SIEMENS:                'S',
            sr.Unit.DECIBEL_MW:             'dBu',
            sr.Unit.DECIBEL_VOLT:           'dBV',
          # sr.Unit.UNITLESS
            sr.Unit.DECIBEL_SPL:            'dB',
          # sr.Unit.CONCENTRATION
            sr.Unit.REVOLUTIONS_PER_MINUTE: 'rpm',
            sr.Unit.VOLT_AMPERE:            'VA',
            sr.Unit.WATT:                   'W',
            sr.Unit.WATT_HOUR:              'Wh',
            sr.Unit.METER_SECOND:           'm/s',
            sr.Unit.HECTOPASCAL:            'hPa',
            sr.Unit.HUMIDITY_293K:          '%rF',
            sr.Unit.DEGREE:                u'\u00B0',
            sr.Unit.HENRY:                  'H'
        }

        return units.get(u, '')

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
            rid = item.data(MeasurementDataModel._idRole)
            rid = tuple(rid) # PySide returns a list.
            if uid == rid:
                return item

        # Nothing found, create a new item.
        desc = '{} {}, {}'.format(
                device.vendor, device.model, channel.name)

        item = QtGui.QStandardItem()
        item.setData(uid, MeasurementDataModel._idRole)
        item.setData(desc, MeasurementDataModel.descRole)
        self.appendRow(item)
        self.sort(0)
        return item

    @QtCore.Slot(object, object, object)
    def update(self, device, channel, data):
        '''Update the data for the device (+channel) with the most recent
        measurement from the given payload.'''

        item = self.getItem(device, channel)

        value, unit, mqflags = data
        value_str = self.format_value(value)
        unit_str = self.format_unit(unit)
        mqflags_str = self.format_mqflags(mqflags)

        # The display role is a tuple containing the value and the unit/flags.
        disp = (value_str, ' '.join([unit_str, mqflags_str]))
        item.setData(disp, QtCore.Qt.DisplayRole)

class MultimeterDelegate(QtGui.QStyledItemDelegate):
    '''Delegate to show the data items from a MeasurementDataModel.'''

    def __init__(self, parent, font):
        '''Initialize the delegate.

        :param font: Font used for the description text, the value is drawn
                     with a slightly bigger and bold variant of the font.
        '''

        super(self.__class__, self).__init__(parent)

        self._nfont = font
        self._bfont = QtGui.QFont(self._nfont)

        self._bfont.setBold(True)
        if self._bfont.pixelSize() != -1:
            self._bfont.setPixelSize(self._bfont.pixelSize() * 1.2)
        else:
            self._bfont.setPointSizeF(self._bfont.pointSizeF() * 1.2)

        fi = QtGui.QFontInfo(self._nfont)
        self._nfontheight = fi.pixelSize()

        fm = QtGui.QFontMetrics(self._bfont)
        r = fm.boundingRect('-XX.XXXXXX X XX')
        self._size = QtCore.QSize(r.width() * 1.4, r.height() * 2.2)

        # Values used to calculate the positions of the strings in the
        # 'paint()' function.
        self._space_width = fm.boundingRect('_').width()
        self._value_width = fm.boundingRect('-XX.XXXXXX').width()

    def sizeHint(self, option=None, index=None):
        return self._size

    def paint(self, painter, options, index):
        value, unit = index.data(QtCore.Qt.DisplayRole)
        desc = index.data(MeasurementDataModel.descRole)

        painter.setFont(self._nfont)
        p = options.rect.topLeft()
        p += QtCore.QPoint(self._nfontheight, 2 * self._nfontheight)
        painter.drawText(p, desc + ': ' + value + ' ' + unit)
