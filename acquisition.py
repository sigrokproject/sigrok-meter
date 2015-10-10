##
## This file is part of the sigrok-meter project.
##
## Copyright (C) 2013 Uwe Hermann <uwe@hermann-uwe.de>
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
import re
import sigrok.core as sr
import time

QtCore = qtcompat.QtCore

class Acquisition(QtCore.QObject):
    '''Class that handles the sigrok session and the reception of data.'''

    '''Signal emitted when new data arrived.'''
    measured = QtCore.Signal(float, sr.classes.Device, sr.classes.Channel, tuple)

    '''Signal emitted when the session has stopped.'''
    stopped = QtCore.Signal()

    def __init__(self, context):
        super(self.__class__, self).__init__()

        self.context = context
        self.session = self.context.create_session()
        self.session.add_datafeed_callback(self._datafeed_callback)
        self.session.set_stopped_callback(self._stopped_callback)

    def _parse_configstring(self, cs):
        '''Dissect a config string and return the options as a dictionary.'''

        def parse_option(k, v):
            '''Parse the value for a single option.'''
            try:
                ck = sr.ConfigKey.get_by_identifier(k)
            except:
                raise ValueError('No option named "{}".'.format(k))

            try:
                val = ck.parse_string(v)
            except:
                raise ValueError(
                    'Invalid value "{}" for option "{}".'.format(v, k))

            return (k, val)

        if not re.match('(([^:=]+=[^:=]+)(:[^:=]+=[^:=]+)*)?$', cs):
            raise ValueError(
                '"{}" is not a valid configuration string.'.format(cs))

        if not cs:
            return {}

        opts = cs.split(':')
        opts = [tuple(kv.split('=')) for kv in opts]
        opts = [parse_option(k, v) for (k, v) in opts]
        return dict(opts)

    def _parse_driverstring(self, ds):
        '''Dissect the driver string and return a tuple consisting of
        the driver name and the options (as a dictionary).'''

        m = re.match('(?P<name>[^:]+)(?P<opts>(:[^:=]+=[^:=]+)*)$', ds)
        if not m:
            raise ValueError('"{}" is not a valid driver string.'.format(ds))

        opts = m.group('opts')[1:]
        return (m.group('name'), self._parse_configstring(opts))

    def add_device(self, driverstring, configstring):
        '''Add a device to the session.'''

        # Process driver string.
        (name, opts) = self._parse_driverstring(driverstring)
        if not name in self.context.drivers:
            raise RuntimeError('No driver named "{}".'.format(name))

        driver = self.context.drivers[name]
        devs = driver.scan(**opts)
        if not devs:
            raise RuntimeError('No devices found.')

        device = devs[0]

        # Process configuration string.
        cfgs = self._parse_configstring(configstring)
        for k, v in cfgs.items():
            device.config_set(sr.ConfigKey.get_by_identifier(k), v)

        self.session.add_device(device)
        device.open()

    def is_running(self):
        '''Return whether the session is running.'''
        return self.session.is_running()

    @QtCore.Slot()
    def start(self):
        '''Start the session.'''
        self.session.start()

    @QtCore.Slot()
    def stop(self):
        '''Stop the session.'''
        if self.is_running():
            self.session.stop()

    def _datafeed_callback(self, device, packet):
        now = time.time()

        if packet.type != sr.PacketType.ANALOG:
            return

        if not len(packet.payload.channels):
            return

        # TODO: find a device with multiple channels in one packet
        channel = packet.payload.channels[0]

        # The most recent value.
        value = packet.payload.data[0][-1]

        self.measured.emit(now, device, channel,
                (value, packet.payload.unit, packet.payload.mq_flags))

    def _stopped_callback(self, **kwargs):
        self.stopped.emit()
