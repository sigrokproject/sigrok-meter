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
pyqtgraph = qtcompat.pyqtgraph

# Black foreground on white background.
pyqtgraph.setConfigOption('background', 'w')
pyqtgraph.setConfigOption('foreground', 'k')

class Plot(object):
    '''Helper class to keep all graphics items of a plot together.'''

    def __init__(self, view, xaxis, yaxis):
        self.view = view
        self.xaxis = xaxis
        self.yaxis = yaxis
        self.visible = False

class MultiPlotItem(pyqtgraph.GraphicsWidget):

    # Emitted when a plot is shown.
    plotShown = QtCore.Signal()

    # Emitted when a plot is hidden by the user via the context menu.
    plotHidden = QtCore.Signal(Plot)

    def __init__(self, parent=None):
        pyqtgraph.GraphicsWidget.__init__(self, parent)

        self.setLayout(QtGui.QGraphicsGridLayout())
        self.layout().setContentsMargins(10, 10, 10, 1)
        self.layout().setHorizontalSpacing(0)
        self.layout().setVerticalSpacing(0)

        for i in range(2):
            self.layout().setColumnPreferredWidth(i, 0)
            self.layout().setColumnMinimumWidth(i, 0)
            self.layout().setColumnSpacing(i, 0)

        self.layout().setColumnStretchFactor(0, 0)
        self.layout().setColumnStretchFactor(1, 100)

        # List of 'Plot' objects that are shown.
        self._plots = []

        self._hideActions = {}

    def addPlot(self):
        '''Adds and returns a new plot.'''

        row = self.layout().rowCount()

        view = pyqtgraph.ViewBox(parent=self)

        # If this is not the first plot, link to the axis of the previous one.
        if self._plots:
            view.setXLink(self._plots[-1].view)

        yaxis = pyqtgraph.AxisItem(parent=self, orientation='left')
        yaxis.linkToView(view)
        yaxis.setGrid(255)

        xaxis = pyqtgraph.AxisItem(parent=self, orientation='bottom')
        xaxis.linkToView(view)
        xaxis.setGrid(255)

        plot = Plot(view, xaxis, yaxis)
        self._plots.append(plot)

        self.showPlot(plot)

        # Create a separate action object for each plots context menu, so that
        # we can later find out which plot should be hidden by looking at
        # 'self._hideActions'.
        hideAction = QtGui.QAction('Hide', self)
        hideAction.triggered.connect(self._onHideActionTriggered)
        self._hideActions[id(hideAction)] = plot
        view.menu.insertAction(view.menu.actions()[0], hideAction)

        return plot

    def _rowNumber(self, plot):
        '''Returns the number of the first row a plot occupies.'''

        # Every plot takes up two rows.
        return 2 * self._plots.index(plot)

    @QtCore.Slot()
    def _onHideActionTriggered(self, checked=False):
        # The plot that we want to hide.
        plot = self._hideActions[id(self.sender())]
        self.hidePlot(plot)

    def hidePlot(self, plot):
        '''Hides 'plot'.'''

        # Only hiding wouldn't give up the space occupied by the items,
        # we have to remove them from the layout.
        self.layout().removeItem(plot.view)
        self.layout().removeItem(plot.xaxis)
        self.layout().removeItem(plot.yaxis)

        plot.view.hide()
        plot.xaxis.hide()
        plot.yaxis.hide()

        row = self._rowNumber(plot)
        self.layout().setRowStretchFactor(row,     0)
        self.layout().setRowStretchFactor(row + 1, 0)

        plot.visible = False
        self.plotHidden.emit(plot)

    def showPlot(self, plot):
        '''Adds the items of the plot to the scene's layout and makes
        them visible.'''

        if plot.visible:
            return

        row = self._rowNumber(plot)
        self.layout().addItem(plot.yaxis, row,     0, QtCore.Qt.AlignRight)
        self.layout().addItem(plot.view,  row,     1)
        self.layout().addItem(plot.xaxis, row + 1, 1)

        plot.view.show()
        plot.xaxis.show()
        plot.yaxis.show()

        for i in range(row, row + 2):
            self.layout().setRowPreferredHeight(i, 0)
            self.layout().setRowMinimumHeight(i, 0)
            self.layout().setRowSpacing(i, 0)

        self.layout().setRowStretchFactor(row,     100)
        self.layout().setRowStretchFactor(row + 1,   0)

        plot.visible = True
        self.plotShown.emit()

class MultiPlotWidget(pyqtgraph.GraphicsView):
    '''Widget that aligns multiple plots on top of each other.

    (The built in classes fail at doing this correctly when the axis grow,
    just try zooming in the "GraphicsLayout" or the "Linked View" examples.)'''

    def __init__(self, parent=None):
        pyqtgraph.GraphicsView.__init__(self, parent)

        self.multiPlotItem = MultiPlotItem()
        self.setCentralItem(self.multiPlotItem)

        for m in [
            'addPlot',
            'hidePlot',
            'showPlot'
        ]:
            setattr(self, m, getattr(self.multiPlotItem, m))

        self.multiPlotItem.plotShown.connect(self._on_plotShown)

        # Expose the signal of the plot item.
        self.plotHidden = self.multiPlotItem.plotHidden

    def _on_plotShown(self):
        # This call is needed if only one plot exists and it was hidden,
        # without it the layout would start acting weird and not make the
        # MultiPlotItem fill the view widget after showing the plot again.
        self.resizeEvent(None)
