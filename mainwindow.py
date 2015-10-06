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
import multiplotwidget
import os.path
import qtcompat
import samplingthread
import textwrap
import time
import util

QtCore = qtcompat.QtCore
QtGui = qtcompat.QtGui
pyqtgraph = qtcompat.pyqtgraph

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

    # Number of seconds that the plots display.
    BACKLOG = 30

    # Update interval of the plots in milliseconds.
    UPDATEINTERVAL = 100

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

        self.plotwidget = multiplotwidget.MultiPlotWidget(self)
        self.plotwidget.plotHidden.connect(self._on_plotHidden)

        # Maps from 'unit' to the corresponding plot.
        self._plots = {}
        # Maps from '(plot, device)' to the corresponding curve.
        self._curves = {}

        self.splitter = QtGui.QSplitter(QtCore.Qt.Horizontal);
        self.splitter.addWidget(self.listView)
        self.splitter.addWidget(self.plotwidget)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)

        self.setCentralWidget(self.splitter)
        self.centralWidget().setContentsMargins(0, 0, 0, 0)
        self.resize(800, 500)

        self.startTimer(MainWindow.UPDATEINTERVAL)

    def _getPlot(self, unit):
        '''Looks up or creates a new plot for 'unit'.'''

        if unit in self._plots:
            return self._plots[unit]

        # create a new plot for the unit
        plot = self.plotwidget.addPlot()
        plot.yaxis.setLabel(util.quantity_from_unit(unit), units=util.format_unit(unit))
        plot.view.setXRange(-MainWindow.BACKLOG, 0, update=False)
        plot.view.setYRange(-1, 1)
        plot.view.enableAutoRange(axis=pyqtgraph.ViewBox.YAxis)
        # lock to the range calculated by the view using additional padding,
        # looks nicer this way
        r = plot.view.viewRange()
        plot.view.setLimits(xMin=r[0][0], xMax=r[0][1])

        self._plots[unit] = plot
        return plot

    def _getCurve(self, plot, deviceID):
        '''Looks up or creates a new curve for '(plot, deviceID)'.'''

        key = (id(plot), deviceID)
        if key in self._curves:
            return self._curves[key]

        # create a new curve
        curve = pyqtgraph.PlotDataItem(
            antialias=True,
            symbolPen=pyqtgraph.mkPen(QtGui.QColor(QtCore.Qt.black)),
            symbolBrush=pyqtgraph.mkBrush(QtGui.QColor(QtCore.Qt.black)),
            symbolSize=1
        )
        plot.view.addItem(curve)

        self._curves[key] = curve
        return curve

    def timerEvent(self, event):
        '''Periodically updates all graphs.'''

        self._updatePlots()

    def _updatePlots(self):
        '''Updates all plots.'''

        # loop over all devices and channels
        for row in range(self.model.rowCount()):
            idx = self.model.index(row, 0)
            deviceID = self.model.data(idx,
                            datamodel.MeasurementDataModel.idRole)
            deviceID = tuple(deviceID) # PySide returns a list.
            traces = self.model.data(idx,
                            datamodel.MeasurementDataModel.tracesRole)

            for unit, trace in traces.items():
                now = time.time()

                # remove old samples
                l = now - MainWindow.BACKLOG
                while trace.samples and trace.samples[0][0] < l:
                    trace.samples.pop(0)

                plot = self._getPlot(unit)
                if not plot.visible:
                    if trace.new:
                        self.plotwidget.showPlot(plot)

                if plot.visible:
                    xdata = [s[0] - now for s in trace.samples]
                    ydata = [s[1]       for s in trace.samples]

                    color = self.model.data(idx,
                                datamodel.MeasurementDataModel.colorRole)

                    curve = self._getCurve(plot, deviceID)
                    curve.setPen(pyqtgraph.mkPen(color=color))
                    curve.setData(xdata, ydata)

    @QtCore.Slot(multiplotwidget.Plot)
    def _on_plotHidden(self, plot):
        plotunit = [u for u, p in self._plots.items() if p == plot][0]

        # Mark all traces of all devices/channels with the same unit as the
        # plot as "old" ('trace.new = False'). As soon as a new sample arrives
        # on one trace, the plot will be shown again
        for row in range(self.model.rowCount()):
            idx = self.model.index(row, 0)
            traces = self.model.data(idx, datamodel.MeasurementDataModel.tracesRole)

            for traceunit, trace in traces.items():
                if traceunit == plotunit:
                    trace.new = False

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
