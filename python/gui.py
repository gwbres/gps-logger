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
from PyQt5.QtWidgets import QListWidget, QPushButton

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
		action = QAction("Open/Append", fileMenu)
		action.setShortcut("CTRL+O")
		action.triggered.connect(self.open)
		fileMenu.addAction(action)
		
		action = QAction("Close/Remove", fileMenu)
		action.setShortcut("CTRL+C")
		action.triggered.connect(self.close)
		fileMenu.addAction(action)

		action = QAction("Exit", fileMenu)
		action.setShortcut("ALT+F4")
		action.triggered.connect(self.exit)
		fileMenu.addAction(action)
		
		# map
		mapWidget = QWidget()
		self.map = QOSM(mapWidget)

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

		"""
		map.mapMoved.connect(onMapMoved)
    	map.markerMoved.connect(onMarkerMoved)
	   map.mapClicked.connect(onMapLClick)
	   map.mapDoubleClicked.connect(onMapDClick)
	   map.mapRightClicked.connect(onMapRClick)
	   map.markerClicked.connect(onMarkerLClick)
	   map.markerDoubleClicked.connect(onMarkerDClick)
	   map.markerRightClicked.connect(onMarkerRClick)
   	h.addWidget(map)
    	map.setSizePolicy(
   	     QSizePolicy.MinimumExpanding,
        	QSizePolicy.MinimumExpanding)
		)
		"""
		
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
		docks.addDock(d4,"bottom",d1)

		d5 = Dock("Accumated. Distance", size=(1,1))
		d5.addWidget(p3)
		docks.addDock(d5,"above",d4)
		
		d2 = Dock("Elevation profile", size=(1,1))
		d2.addWidget(p2)
		docks.addDock(d2)

		self.setCentralWidget(docks)
		self.resize(WIN_WIDTH,WIN_HEIGHT)
		self.show()

	def buildTrackHandler(self):
		widget = QWidget()
		qvboxlayout = QVBoxLayout()
		self.qlist = QListWidget()
		self.qlist.currentItemChanged.connect(self.listItemChanged)
		qvboxlayout.addWidget(self.qlist)

		_qhboxlayout = QHBoxLayout()
		RM = QPushButton("remove")
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
		
		self.clear() # clear previous plots

		# visualize track on map
		self.track.drawOnMap(self.map)

		# track handler
		for i in range(0, len(self.track)):
			self.qlist.addItem(str(self.track[i]))

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

	def clear(self):
		"""
		Clears all plot
		"""
		for plt in self.plots:
			plt.clear()

	def removeClicked(self, clicked):
		"""
		Called when 'remove' was clicked
		in the track handler
		"""
		if (clicked):
			item = self.qlist.currentItem()

	def listItemChanged(self, current, previous):
		text = current.text()
		# use date to retrieve waypoint
		day = text.split(' ')[1]
		time = text.split(' ')[2]
		string = day+' '+time
		format = '%Y-%m-%d %H:%M:%S'
		date = datetime.datetime.strptime(string,format)
		index = self.track.searchByDate(date)
		print(index)

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
