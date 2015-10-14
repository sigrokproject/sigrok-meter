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

import acquisition
import datamodel
import datetime
import icons
import multiplotwidget
import os.path
import qtcompat
import settings
import sigrok.core as sr
import sys
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

    # Update interval of the plots in milliseconds.
    UPDATEINTERVAL = 100

    def __init__(self, context, drivers):
        super(self.__class__, self).__init__()

        # Used to coordinate the stopping of the acquisition and
        # the closing of the window.
        self._closing = False

        self.context = context
        self.drivers = drivers

        self.logModel = QtGui.QStringListModel(self)
        self.context.set_log_callback(self._log_callback)

        self.delegate = datamodel.MultimeterDelegate(self, self.font())
        self.model = datamodel.MeasurementDataModel(self)

        # Maps from 'unit' to the corresponding plot.
        self._plots = {}
        # Maps from '(plot, device)' to the corresponding curve.
        self._curves = {}

        self._setup_ui()

        self._plot_update_timer = QtCore.QTimer()
        self._plot_update_timer.setInterval(MainWindow.UPDATEINTERVAL)
        self._plot_update_timer.timeout.connect(self._updatePlots)

        settings.graph.backlog.changed.connect(self.on_setting_graph_backlog_changed)

        QtCore.QTimer.singleShot(0, self._start_acquisition)

    def _start_acquisition(self):
        self.acquisition = acquisition.Acquisition(self.context)
        self.acquisition.measured.connect(self.model.update)
        self.acquisition.stopped.connect(self._stopped)

        try:
            for (ds, cs) in self.drivers:
                self.acquisition.add_device(ds, cs)
        except Exception as e:
            QtGui.QMessageBox.critical(self, 'Error', str(e))
            self.close()
            return

        self.start_stop_acquisition()

    def _log_callback(self, level, message):
        if level.id > settings.logging.level.value().id:
            return

        t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        message = '[{}] sr: {}'.format(t, message)

        sys.stderr.write(message + '\n')

        scrollBar = self.logView.verticalScrollBar()
        bottom = scrollBar.value() == scrollBar.maximum()

        rows = self.logModel.rowCount()
        maxrows = settings.logging.lines.value()
        while rows > maxrows:
            self.logModel.removeRows(0, 1)
            rows -= 1

        if self.logModel.insertRow(rows):
            index = self.logModel.index(rows)
            self.logModel.setData(index, message, QtCore.Qt.DisplayRole)

            if bottom:
                self.logView.scrollToBottom()

    def _setup_ui(self):
        self.setWindowTitle('sigrok-meter')
        # Resizing the listView below will increase this again.
        self.resize(350, 10)

        self.setWindowIcon(QtGui.QIcon(':/logo.png'))

        self._setup_graphPage()
        self._setup_addDevicePage()
        self._setup_logPage()
        self._setup_preferencesPage()

        self._pages = [
            self.graphPage,
            self.addDevicePage,
            self.logPage,
            self.preferencesPage
        ]

        self.stackedWidget = QtGui.QStackedWidget(self)
        for page in self._pages:
            self.stackedWidget.addWidget(page)

        self._setup_sidebar()

        self.setCentralWidget(QtGui.QWidget())
        self.centralWidget().setContentsMargins(0, 0, 0, 0)

        layout = QtGui.QHBoxLayout(self.centralWidget())
        layout.addWidget(self.sideBar)
        layout.addWidget(self.stackedWidget)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.resize(settings.mainwindow.size.value())
        if settings.mainwindow.pos.value():
            self.move(settings.mainwindow.pos.value())

    def _setup_sidebar(self):
        self.sideBar = QtGui.QToolBar(self)
        self.sideBar.setOrientation(QtCore.Qt.Vertical)

        actionGraph = self.sideBar.addAction('Instantaneous Values and Graphs')
        actionGraph.setCheckable(True)
        actionGraph.setIcon(icons.graph)
        actionGraph.triggered.connect(self.showGraphPage)

        #actionAdd = self.sideBar.addAction('Add Device')
        #actionAdd.setCheckable(True)
        #actionAdd.setIcon(icons.add)
        #actionAdd.triggered.connect(self.showAddDevicePage)

        actionLog = self.sideBar.addAction('Logs')
        actionLog.setCheckable(True)
        actionLog.setIcon(icons.log)
        actionLog.triggered.connect(self.showLogPage)

        actionPreferences = self.sideBar.addAction('Preferences')
        actionPreferences.setCheckable(True)
        actionPreferences.setIcon(icons.preferences)
        actionPreferences.triggered.connect(self.showPreferencesPage)

        # make the buttons at the top exclusive
        self.actionGroup = QtGui.QActionGroup(self)
        self.actionGroup.addAction(actionGraph)
        #self.actionGroup.addAction(actionAdd)
        self.actionGroup.addAction(actionLog)
        self.actionGroup.addAction(actionPreferences)

        # show graph at startup
        actionGraph.setChecked(True)

        # fill space between buttons on the top and on the bottom
        fill = QtGui.QWidget(self)
        fill.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        self.sideBar.addWidget(fill)

        self.actionStartStop = self.sideBar.addAction('Start Acquisition')
        self.actionStartStop.setIcon(icons.start)
        self.actionStartStop.triggered.connect(self.start_stop_acquisition)

        actionAbout = self.sideBar.addAction('About')
        actionAbout.setIcon(icons.about)
        actionAbout.triggered.connect(self.show_about)

        actionQuit = self.sideBar.addAction('Quit')
        actionQuit.setIcon(icons.exit)
        actionQuit.triggered.connect(self.close)

        s = self.style().pixelMetric(QtGui.QStyle.PM_LargeIconSize)
        self.sideBar.setIconSize(QtCore.QSize(s, s))

        self.sideBar.setStyleSheet('''
            QToolBar {
                background-color: white;
                margin: 0px;
                border: 0px;
                border-right: 1px solid black;
            }

            QToolButton {
                padding: 10px;
                border: 0px;
                border-right: 1px solid black;
            }

            QToolButton:checked,
            QToolButton[checkable="false"]:hover {
                background-color: #c0d0e8;
            }
        ''')

    def _setup_graphPage(self):
        listView = EmptyMessageListView('waiting for data...')
        listView.setFrameShape(QtGui.QFrame.NoFrame)
        listView.viewport().setBackgroundRole(QtGui.QPalette.Window)
        listView.viewport().setAutoFillBackground(True)
        listView.setMinimumWidth(260)
        listView.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        listView.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        listView.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        listView.setItemDelegate(self.delegate)
        listView.setModel(self.model)
        listView.setUniformItemSizes(True)
        listView.setMinimumSize(self.delegate.sizeHint())

        self.plotwidget = multiplotwidget.MultiPlotWidget(self)
        self.plotwidget.plotHidden.connect(self._on_plotHidden)

        self.graphPage = QtGui.QSplitter(QtCore.Qt.Horizontal, self)
        self.graphPage.addWidget(listView)
        self.graphPage.addWidget(self.plotwidget)
        self.graphPage.setStretchFactor(0, 0)
        self.graphPage.setStretchFactor(1, 1)

    def _setup_addDevicePage(self):
        self.addDevicePage = QtGui.QWidget(self)
        layout = QtGui.QVBoxLayout(self.addDevicePage)
        label = QtGui.QLabel('add device page')
        layout.addWidget(label)

    def _setup_logPage(self):
        self.logView = QtGui.QListView(self)
        self.logView.setModel(self.logModel)
        self.logView.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.logView.setSelectionMode(QtGui.QAbstractItemView.NoSelection)

        self.logPage = QtGui.QWidget(self)
        layout = QtGui.QVBoxLayout(self.logPage)
        layout.addWidget(self.logView)

    def _setup_preferencesPage(self):
        self.preferencesPage = QtGui.QWidget(self)
        layout = QtGui.QGridLayout(self.preferencesPage)

        layout.addWidget(QtGui.QLabel('<b>Graph</b>'), 0, 0)
        layout.addWidget(QtGui.QLabel('Recording time (seconds):'), 1, 0)

        spin = QtGui.QSpinBox(self)
        spin.setMinimum(10)
        spin.setMaximum(3600)
        spin.setSingleStep(10)
        spin.setValue(settings.graph.backlog.value())
        spin.valueChanged[int].connect(settings.graph.backlog.setValue)
        layout.addWidget(spin, 1, 1)

        layout.addWidget(QtGui.QLabel('<b>Logging</b>'), 2, 0)
        layout.addWidget(QtGui.QLabel('Log level:'), 3, 0)

        cbox = QtGui.QComboBox()
        descriptions = [
            'no messages at all',
            'error messages',
            'warnings',
            'informational messages',
            'debug messages',
            'very noisy debug messages'
        ]
        for i, desc in enumerate(descriptions):
            level = sr.LogLevel.get(i)
            text = '{} ({})'.format(level.name, desc)
            # The numeric log level corresponds to the index of the text in the
            # combo box. Should this ever change, we could use the 'userData'
            # that can also be stored in the item.
            cbox.addItem(text)

        cbox.setCurrentIndex(settings.logging.level.value().id)
        cbox.currentIndexChanged[int].connect(
            (lambda i: settings.logging.level.setValue(sr.LogLevel.get(i))))
        layout.addWidget(cbox, 3, 1)

        layout.addWidget(QtGui.QLabel('Number of lines to log:'), 4, 0)

        spin = QtGui.QSpinBox(self)
        spin.setMinimum(100)
        spin.setMaximum(10 * 1000 * 1000)
        spin.setSingleStep(100)
        spin.setValue(settings.logging.lines.value())
        spin.valueChanged[int].connect(settings.logging.lines.setValue)
        layout.addWidget(spin, 4, 1)

        layout.setRowStretch(layout.rowCount(), 100)

    def showPage(self, page):
        self.stackedWidget.setCurrentIndex(self._pages.index(page))

    @QtCore.Slot(bool)
    def showGraphPage(self):
        self.showPage(self.graphPage)

    @QtCore.Slot(bool)
    def showAddDevicePage(self):
        self.showPage(self.addDevicePage)

    @QtCore.Slot(bool)
    def showLogPage(self):
        self.showPage(self.logPage)

    @QtCore.Slot(bool)
    def showPreferencesPage(self):
        self.showPage(self.preferencesPage)

    @QtCore.Slot(int)
    def on_setting_graph_backlog_changed(self, bl):
        for unit in self._plots:
            plot = self._plots[unit]

            # Remove the limits first, otherwise the range update would
            # be ignored.
            plot.view.setLimits(xMin=None, xMax=None)

            # Now change the range, and then use the calculated limits
            # (also see the comment in '_getPlot()').
            plot.view.setXRange(-bl, 0, update=True)
            r = plot.view.viewRange()
            plot.view.setLimits(xMin=r[0][0], xMax=r[0][1])

    def _getPlot(self, unit):
        '''Looks up or creates a new plot for 'unit'.'''

        if unit in self._plots:
            return self._plots[unit]

        # create a new plot for the unit
        plot = self.plotwidget.addPlot()
        plot.yaxis.setLabel(util.quantity_from_unit(unit), units=util.format_unit(unit))
        plot.view.setXRange(-settings.graph.backlog.value(), 0, update=False)
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

        key = (plot, deviceID)
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
                l = now - settings.graph.backlog.value()
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

    @QtCore.Slot()
    def _stopped(self):
        if self._closing:
            # The acquisition was stopped by the 'closeEvent()', close the
            # window again now that the acquisition has stopped.
            self.close()

    def closeEvent(self, event):
        if self.acquisition.is_running():
            # Stop the acquisition before closing the window.
            self._closing = True
            self.start_stop_acquisition()
            event.ignore()
        else:
            settings.mainwindow.size.setValue(self.size())
            settings.mainwindow.pos.setValue(self.pos())
            event.accept()

    @QtCore.Slot()
    def start_stop_acquisition(self):
        if self.acquisition.is_running():
            self.acquisition.stop()
            self._plot_update_timer.stop()
            self.actionStartStop.setText('Start Acquisition')
            self.actionStartStop.setIcon(icons.start)
        else:
            # before starting (again), remove all old samples and old curves
            self.model.clear_samples()

            for key in self._curves:
                plot, _ = key
                curve = self._curves[key]
                plot.view.removeItem(curve)
            self._curves = {}

            self.acquisition.start()
            self._plot_update_timer.start()
            self.actionStartStop.setText('Stop Acquisition')
            self.actionStartStop.setIcon(icons.stop)

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
                         http://www.gnu.org/licenses/gpl.html</a><br/>
                <br/>
                Some icons by <a href='https://www.gnome.org'>
                              the GNOME project</a>
            </div>
        '''.format(self.context.package_version, self.context.lib_version))

        QtGui.QMessageBox.about(self, 'About sigrok-meter', text)
