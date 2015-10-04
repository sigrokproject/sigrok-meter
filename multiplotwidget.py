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

# black foreground on white background
pyqtgraph.setConfigOption('background', 'w')
pyqtgraph.setConfigOption('foreground', 'k')

class MultiPlotItem(pyqtgraph.GraphicsWidget):

    class Plot:
        def __init__(self, view, xaxis, yaxis):
            self.view = view
            self.xaxis = xaxis
            self.yaxis = yaxis

    def __init__(self, parent=None):
        pyqtgraph.GraphicsWidget.__init__(self, parent)

        self.layout = QtGui.QGraphicsGridLayout()
        self.layout.setContentsMargins(10, 10, 10, 1)
        self.layout.setHorizontalSpacing(0)
        self.layout.setVerticalSpacing(0)
        self.setLayout(self.layout)

        self._plots = []

        for i in range(2):
            self.layout.setColumnPreferredWidth(i, 0)
            self.layout.setColumnMinimumWidth(i, 0)
            self.layout.setColumnSpacing(i, 0)

        self.layout.setColumnStretchFactor(0, 0)
        self.layout.setColumnStretchFactor(1, 100)

    def addPlot(self):
        row = self.layout.rowCount()

        view = pyqtgraph.ViewBox(parent=self)
        if self._plots:
            view.setXLink(self._plots[-1].view)
        self.layout.addItem(view, row, 1)

        yaxis = pyqtgraph.AxisItem(parent=self, orientation='left')
        yaxis.linkToView(view)
        yaxis.setGrid(255)
        self.layout.addItem(yaxis, row, 0, QtCore.Qt.AlignRight)

        xaxis = pyqtgraph.AxisItem(parent=self, orientation='bottom')
        xaxis.linkToView(view)
        xaxis.setGrid(255)
        self.layout.addItem(xaxis, row + 1, 1)

        for i in range(row, row + 2):
            self.layout.setRowPreferredHeight(i, 0)
            self.layout.setRowMinimumHeight(i, 0)
            self.layout.setRowSpacing(i, 0)

        self.layout.setRowStretchFactor(row,     100)
        self.layout.setRowStretchFactor(row + 1,   0)

        p = MultiPlotItem.Plot(view, xaxis, yaxis)
        self._plots.append(p)
        return p

class MultiPlotWidget(pyqtgraph.GraphicsView):
    '''Widget that aligns multiple plots on top of each other.

    (The built in classes fail at doing this correctly when the axis grow,
    just try zooming in the "GraphicsLayout" or the "Linked View" examples.)'''

    def __init__(self, parent=None):
        pyqtgraph.GraphicsView.__init__(self, parent)

        self.multiPlotItem = MultiPlotItem()
        self.setCentralItem(self.multiPlotItem)

        for m in [
            'addPlot'
        ]:
            setattr(self, m, getattr(self.multiPlotItem, m))
