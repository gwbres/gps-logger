#! /usr/bin/env python3

import sys

# Dimensions
WIN_WIDTH = 800 # px
WIN_HEIGHT = 500 # px

# Qt5
from PyQt5.QtCore import Qt
from PyQt5.QtWebKit import * 
from PyQt5.QtNetwork import *
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QMenu, QAction
from PyQt5.QtWidgets import QFileDialog, QDialog
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QAbstractItemView
from PyQt5.QtWidgets import QPushButton

# pyqtgraph
import pyqtgraph as pg
from pyqtgraph.dockarea import *
import pyqtgraph.console

# maths
import numpy as np

# API
from PMTK import *
from GPSTrack import *
from Waypoint import *

# map viewer
sys.path.insert(0, "qMap")
import qOSM
qOSM.use("PyQt5")
from qOSM.common import QOSM
        
class MainWindow (QMainWindow):
	
	def __init__(self, parent=None):
		super(MainWindow, self).__init__()

		# menu bar
		bar = self.menuBar()
		# file
		fileMenu = bar.addMenu("File")
		action = QAction("Open", fileMenu)
		action.setShortcut("CTRL+O")
		action.triggered.connect(self.open)
		fileMenu.addAction(action)
		
		action = QAction("Clear", fileMenu)
		action.setShortcut("CTRL+C")
		action.triggered.connect(self.clear)
		fileMenu.addAction(action)

		action = QAction("Exit", fileMenu)
		action.setShortcut("ALT+F4")
		action.triggered.connect(self.exit)
		fileMenu.addAction(action)
		
		# map
		mapWidget = QWidget()
		self.map = QOSM(mapWidget)
		self.map.markerClicked.connect(self.onMarkerClicks)
		self.highlights = None
    	
		"""
		self.map.setSizePolicy(
   	     QSizePolicy.MinimumExpanding,
        	QSizePolicy.MinimumExpanding
		)
		"""
		
		# plots
		self.plots = []

		p2 = pg.PlotWidget(title="Elevation profile")
		p2.enableAutoRange()
		p2Item = p2.getPlotItem()
		p2Item.setLabel('left', 'Elevation', units='m')
		p2Item.setLabel('bottom', 'Distance', units='m')
		#p2Item.addLegend()
		p2.showGrid(x=True,y=True)
		self.plots.append(p2)

		# console
		self.console = pg.console.ConsoleWidget()

		# speed plot 
		p1 = pg.PlotWidget(title="Instant. speed")
		p1.enableAutoRange()
		p1Item = p1.getPlotItem()
		p1Item.setLabel('left', 'Speed', units='m/s')
		p1Item.setLabel('bottom', 'GPS Waypoint')
		p1.showGrid(x=True,y=True)
		self.plots.append(p1)

		# accumulated distance
		p3 = pg.PlotWidget(title="Accumulated distance")
		p3.enableAutoRange()
		p3Item = p3.getPlotItem()
		p3Item.setLabel('left', 'Accumulated Distance', units='m')
		p3Item.setLabel('bottom', 'GPS Waypoint')
		p3.showGrid(x=True,y=True)
		self.plots.append(p3)

		docks = DockArea()
		
		d1 = Dock("Console", size=(1,1))
		d1.addWidget(self.console)
		docks.addDock(d1)

		d12 = Dock("Track", size=(1,1))
		d12.addWidget(self.buildTrackHandler())
		docks.addDock(d12, "above", d1)
		
		d0 = Dock("Map", size=(1,2))
		d0.hideTitleBar()
		d0.addWidget(mapWidget)
		docks.addDock(d0,"left",d1)
		
		d4 = Dock("Instant. speed", size=(1,1))
		d4.addWidget(p1)

		d5 = Dock("Accumated. Distance", size=(1,1))
		d5.addWidget(p3)
		
		d2 = Dock("Elevation profile", size=(1,1))
		d2.addWidget(p2)
		docks.addDock(d4)
		docks.addDock(d5,"above",d4)
		docks.addDock(d2,"above",d5)

		self.setCentralWidget(docks)
		self.resize(WIN_WIDTH,WIN_HEIGHT)
		self.show()

	def buildTrackHandler(self):
		widget = QWidget()
		qvboxlayout = QVBoxLayout()
		self.qtree = QTreeWidget()

		header = QTreeWidgetItem(["date","latitude","longitude"])
		self.qtree.setHeaderItem(header)
		self.qtree.setSelectionMode(
			QAbstractItemView.SingleSelection|QAbstractItemView.MultiSelection
		)

		self.qtree.currentItemChanged.connect(self.listItemChanged)
		qvboxlayout.addWidget(self.qtree)

		_qhboxlayout = QHBoxLayout()
		RM = QPushButton("Remove")
		RM.clicked.connect(self.removeClicked)
		_qhboxlayout.addWidget(RM)
		qvboxlayout.addLayout(_qhboxlayout)

		widget.setLayout(qvboxlayout)
		widget.show()
		return widget

	def open(self):
		"""
		Called when 'open' from toolbar was clicked
		TODO: allow multiple files selection
		"""
		self.qdialog = QFileDialog(self)
		self.qdialog.setDirectory("data")
		self.qdialog.finished.connect(self.openDialogConfirmed)
		self.qdialog.show()
	
	def openDialogConfirmed(self, confirmed):
		"""
		Called when file dialog has been confirmed
		TODO:
			+ handle list of files
		"""
		if not(confirmed):
			return 0

		files = self.qdialog.selectedFiles()
		self.track = GPSTrack(files[0])
		for fp in files[1:]:
			self.track.append(GPSTrack(fp).getWaypoints())
		
		self.clearPlots() # clear previous plots

		# visualize track on map
		self.track.drawOnMap(self.map)

		# track handler
		for i in range(0, len(self.track)):
			item = QTreeWidgetItem(self.qtree, str(self.track[i]).split('|'))
			self.qtree.addTopLevelItem(item)

		# instant speed
		self.plots[1].plot(self.track.instantSpeed())

		# accumulated distance
		self.plots[2].plot(self.track.accumulatedDistance())
		
		# elevation profile
		self.plots[0].plot(self.track.accumulatedDistance(), self.track.elevationProfile())
		# draw line @ sea level
		c1 = self.plots[0].getPlotItem().curves[0]
		self.plots[0].plot([0,c1.getData()[0][-1]],[0,0]) # draw line @ sea level
		# fill between sea level & curve
		c2 = self.plots[0].getPlotItem().curves[1]
		brush = (100,100,255)
		self.elevFill = pg.FillBetweenItem(c1,c2,brush)
		self.plots[0].addItem(self.elevFill)

	def clearPlots(self):
		"""
		Clears all plot
		"""
		for plt in self.plots:
			plt.clear()

	def clearMap(self):
		"""
		Removes all waypoints from GPS track
		Removes focused markers
		"""
		for i in range(0, len(self.track)):
			self.map.deleteMarker(str(i))

	def clear(self, clicked):
		"""
		Clears entire interface, including:
			+ Plots
			+ Map visualization
			+ GPS Track interface
		"""
		self.clearPlots()
		self.clearMap()
		#self.qtree = QListWidget() # empty
		self.qtree.clear()

	def removeClicked(self, clicked):
		"""
		Called when 'remove' was clicked
		in the track handler
		"""
		item = self.qtree.currentItem()
		text = item.text(0)
		format = '%Y-%m-%d %H:%M:%S'
		date = datetime.datetime.strptime(text,format)
		index = self.track.searchByDate(date)
		self.map.deleteMarker(str(index))
		self.qtree.removeItemWidget(item)

	def listItemChanged(self, current, previous):
		if (len(self.qtree.selectedItems()) == 0):
			return -1

		items = []
		if (len(self.qtree.selectedItems()) == 1):
			items.append(self.qtree.selectedItems()[0])
			items.append(self.qtree.itemBelow(self.qtree.selectedItems()[0]))
		else:
			items = [self.qtree.selectedItems()[0]] # currently highlighted
			items.append(self.qtree.selectedItems()[-1])

		indexes = []
		for item in items:
			# use date to retrieve waypoint
			date = datetime.datetime.strptime(
				item.text(0), # date
				'%Y-%m-%d %H:%M:%S'
			)

			indexes.append(self.track.searchByDate(date))

		self.track.highlightOnMap(self.map, indexes[0], indexes[1])
		
		# indicate current selection on elevation profile
		elevationProfile = self.plots[0].getPlotItem()
		curves = elevationProfile.curves
		if (len(curves) > 2):
			curves[-1].clear() # rm previous point
			del curves[-1]

		[xp,yp] = curves[0].getData()
		self.plots[0].plot([xp[indexes[-1]]],[yp[indexes[-1]]],symbol='o')
		
	def onMarkerClicks(self, key, lat, lon):
		index = self.track.search(Waypoint(latDeg=lat,lonDeg=lon))
		self.map.deleteMarker('current')
		self.map.addMarker('current', lat, lon,
			**dict(
				icon="http://maps.gstatic.com/mapfiles/ridefinder-images/mm_20_blue.png",
				draggable=False,
				title="previous"
			)
		)

		item = QTreeWidgetItem(self.qtree, str(self.track[index]).split('|'))
		self.qtree.setCurrentItem(item)
		
	def close(self):
		print("tut")
	
	def exit(self):
		print("tut")

app = QApplication([])
win = MainWindow()
pg.setConfigOptions(antialias=True)

if __name__ == '__main__':
	QApplication.instance().exec_()
	app = QApplication(sys.argv)
	app.setStyle("plastique")
	sys.exit(app.exec_())
