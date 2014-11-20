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

import datamodel
import os.path
import qtcompat
import samplingthread
import textwrap

QtCore = qtcompat.QtCore
QtGui = qtcompat.QtGui

class EmptyMessageListView(QtGui.QListView):
    '''List view that shows a message if the model im empty.'''

    def __init__(self, message, parent=None):
        super(self.__class__, self).__init__(parent)

        self._message = message

    def paintEvent(self, event):
        m = self.model()
        if m and m.rowCount():
            super(self.__class__, self).paintEvent(event)
            return

        painter = QtGui.QPainter(self.viewport())
        painter.drawText(self.rect(), QtCore.Qt.AlignCenter, self._message)

class MainWindow(QtGui.QMainWindow):
    '''The main window of the application.'''

    def __init__(self, context, drivers):
        super(self.__class__, self).__init__()

        self.context = context

        self.delegate = datamodel.MultimeterDelegate(self, self.font())
        self.model = datamodel.MeasurementDataModel(self)
        self.model.rowsInserted.connect(self.modelRowsInserted)

        self.setup_ui()

        self.thread = samplingthread.SamplingThread(self.context, drivers)
        self.thread.measured.connect(self.model.update)
        self.thread.error.connect(self.error)
        self.thread.start()

    def setup_ui(self):
        self.setWindowTitle('sigrok-meter')
        # Resizing the listView below will increase this again.
        self.resize(350, 10)

        p = os.path.abspath(os.path.dirname(__file__))
        p = os.path.join(p, 'sigrok-logo-notext.png')
        self.setWindowIcon(QtGui.QIcon(p))

        actionQuit = QtGui.QAction(self)
        actionQuit.setText('&Quit')
        actionQuit.setIcon(QtGui.QIcon.fromTheme('application-exit'))
        actionQuit.setShortcut('Ctrl+Q')
        actionQuit.triggered.connect(self.close)

        actionAbout = QtGui.QAction(self)
        actionAbout.setText('&About')
        actionAbout.setIcon(QtGui.QIcon.fromTheme('help-about'))
        actionAbout.triggered.connect(self.show_about)

        menubar = self.menuBar()
        menuFile = menubar.addMenu('&File')
        menuFile.addAction(actionQuit)
        menuHelp = menubar.addMenu('&Help')
        menuHelp.addAction(actionAbout)

        self.listView = EmptyMessageListView('waiting for data...')
        self.listView.setFrameShape(QtGui.QFrame.NoFrame)
        self.listView.viewport().setBackgroundRole(QtGui.QPalette.Window)
        self.listView.viewport().setAutoFillBackground(True)
        self.listView.setMinimumWidth(260)
        self.listView.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.listView.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.listView.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.listView.setItemDelegate(self.delegate)
        self.listView.setModel(self.model)
        self.listView.setUniformItemSizes(True)
        self.listView.setMinimumSize(self.delegate.sizeHint())

        self.setCentralWidget(self.listView)
        self.centralWidget().setContentsMargins(0, 0, 0, 0)

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()

    @QtCore.Slot()
    def show_about(self):
        text = textwrap.dedent('''\
            <div align="center">
                <b>sigrok-meter 0.1.0</b><br/><br/>
                Using libsigrok {} (lib version {}).<br/><br/>
                <a href='http://www.sigrok.org'>
                         http://www.sigrok.org</a><br/>
                <br/>
                License: GNU GPL, version 3 or later<br/>
                <br/>
                This program comes with ABSOLUTELY NO WARRANTY;<br/>
                for details visit
                <a href='http://www.gnu.org/licenses/gpl.html'>
                         http://www.gnu.org/licenses/gpl.html</a>
            </div>
        '''.format(self.context.package_version, self.context.lib_version))

        QtGui.QMessageBox.about(self, 'About sigrok-meter', text)

    @QtCore.Slot(str)
    def error(self, msg):
        '''Error handler for the sampling thread.'''
        QtGui.QMessageBox.critical(self, 'Error', msg)
        self.close()

    @QtCore.Slot(object, int, int)
    def modelRowsInserted(self, parent, start, end):
        '''Resize the list view to the size of the content.'''
        rows = self.model.rowCount()
        dh = self.delegate.sizeHint().height()
        self.listView.setMinimumHeight(dh * rows)
