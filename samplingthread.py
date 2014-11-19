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
import sigrok.core as sr

QtCore = qtcompat.QtCore
QtGui = qtcompat.QtGui

class SamplingThread(QtCore.QObject):
    '''A class that handles the reception of sigrok packets in the background.'''

    class Worker(QtCore.QObject):
        '''Helper class that does the actual work in another thread.'''

        '''Signal emitted when new data arrived.'''
        measured = QtCore.Signal(object, object, object)

        '''Signal emmited in case of an error.'''
        error = QtCore.Signal(str)

        def __init__(self, context, drivers):
            super(self.__class__, self).__init__()

            self.context = context
            self.drivers = drivers

            self.sampling = False

        @QtCore.Slot()
        def start_sampling(self):
            devices = []
            for name, options in self.drivers:
                try:
                    dr = self.context.drivers[name]
                    devices.append(dr.scan(**options)[0])
                except:
                    self.error.emit(
                        'Unable to get device for driver "{}".'.format(name))
                    return

            self.session = self.context.create_session()
            for dev in devices:
                self.session.add_device(dev)
                dev.open()
            self.session.add_datafeed_callback(self.callback)
            self.session.start()
            self.sampling = True
            self.session.run()

            # If sampling is 'True' here, it means that 'stop_sampling()' was
            # not called, therefore 'session.run()' ended too early, indicating
            # an error.
            if self.sampling:
                self.error.emit('An error occured during the acquisition.')

        def stop_sampling(self):
            if self.sampling:
                self.sampling = False
                self.session.stop()

        def callback(self, device, packet):
            if not sr:
                # In rare cases it can happen that the callback fires while
                # the interpreter is shutting down. Then the sigrok module
                # is already set to 'None'.
                return

            if packet.type != sr.PacketType.ANALOG:
                return

            if not len(packet.payload.channels):
                return

            # TODO: find a device with multiple channels in one packet
            channel = packet.payload.channels[0]

            # the most recent value
            value = packet.payload.data[0][-1]

            self.measured.emit(device, channel,
                    (value, packet.payload.unit, packet.payload.mq_flags))

    # signal used to start the worker across threads
    _start_signal = QtCore.Signal()

    def __init__(self, context, drivers):
        super(self.__class__, self).__init__()

        self.worker = self.Worker(context, drivers)
        self.thread = QtCore.QThread()
        self.worker.moveToThread(self.thread)

        self._start_signal.connect(self.worker.start_sampling)

        # expose the signals of the worker
        self.measured = self.worker.measured
        self.error = self.worker.error

        self.thread.start()

    def start(self):
        '''Starts sampling'''
        self._start_signal.emit()

    def stop(self):
        '''Stops sampling and the background thread.'''
        self.worker.stop_sampling()
        self.thread.quit()
        self.thread.wait()
