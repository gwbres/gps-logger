from Waypoint import *

import geoplotlib
from geoplotlib.utils import read_csv

import matplotlib.pyplot as plt

class GPSTrack:
	"""
	GPS track is a list of GPS waypoints
	"""
	
	def __init__(self, fp):
		"""
		Builds GPS Track by parsing all waypoints
		in either NMEA or KML file
		"""
		self.waypoints = []

		ext = fp.split('.')[-1]
		if (ext == 'nmea'):
			self.GPSTrackNMEA(fp)
		
		elif (ext == 'kml'):
			self.GPSTrackKML(fp)
		
		else:
			raise ValueError("GPS Track cannot be built from a '.{:s}' log file".format(ext))

	def GPSTrackNMEA(self, fp):
		"""
		Builds GPS Track by parsing all waypoints
		in .nmea log file
		"""
		fd = open(fp,"r")
		for line in fd:
			line = line.strip()
			try:
				self.waypoints.append(Waypoint(nmea=line))
			except NameError: # not $GGA or $RMC frame
				pass

		fd.close()

	def GPSTrackKML(self, fp):
		"""
		Builds GPS Track by parsing all waypoints
		in .kml log file
		"""
		fd = open(fp,"r")
		coordinates_found = False
		for line in fd:
			line = line.strip()
		
			if (not(coordinates_found)):
				if ("<coordinates>" in line):
					coordinates_found = True
		
			else:
				if ("</coordinates>" in line):
					break
				else:
					parsed = line.split(",")
					lat = float(parsed[1])
					lon = float(parsed[0])
					alt = parsed[2]
					self.waypoints.append(Waypoint(latDeg=lat,lonDeg=lon,alt=alt))

		fd.close()

	def __len__(self):
		""" GPS Track lenght returns number of waypoints """
		return len(self.waypoints)

	def __iter__(self):
		""" Iterator over GPS track """
		return iter(self.waypoints)

	def __reversed__(self):
		""" Iterates backwards over GPS track """
		return reversed(self.waypoints)

	def __setitem__(self, index, wp):
		""" Sets waypoint at given index in track """
		self.waypoints[index] = wp

	def __getitem__(self, index):
		""" Returns waypoint in GPS track at given index """
		return self.waypoints[index]
	
	def __delitem__(self, index):
		""" Removes given waypoint in track """
		del self.waypoints[index]

	def toKML(self, fp):
		"""
		Writes GPS track in a KML file
		"""
		fd = open(fp, "w")

		# initialize kml file
		fd.write('<?xml version="1.0" encoding="UTF-8"?>\n')
		fd.write('<kml xmlns="http://earth.google.com/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2">\n')
		fd.write('<Folder>\n')

		# track infos
		fd.write('\t<name>Imported from {:s}</name>\n'.format(fp))
		fd.write('\t<Placemark>\n')
		fd.write('\t\t<name>Track</name>\n')

		# track style
		fd.write('\t\t<Style>\n')
		fd.write('\t\t\t<LineStyle>\n')
		fd.write('\t\t\t\t<color>00cc00cc</color>\n')
		fd.write('\t\t\t\t<width>4</width>\n')
		fd.write('\t\t\t</LineStyle>\n')
		fd.write('\t\t</Style>\n')

		# track
		fd.write('\t\t<LineString>\n')
		fd.write('\t\t\t<altitudeMode>relativeToGround</altitudeMode>\n')
		fd.write('\t\t\t<coordinates>\n')

		for i in range(0, len(self.waypoints)):
			[lat, lon] = self.waypoints[i].toDecimalDegrees()
			fd.write('\t\t\t\t{:f},{:f},{:s}\n'.format(lon,lat,self.waypoints[i].getAltitude()))

		fd.write('\t\t\t</coordinates>\n')
		fd.write('\t\t</LineString>\n')
		
		# finalize kml file 
		fd.write('\t</Placemark>\n')
		fd.write('\t</Folder>\n')
		fd.write('</kml>\n')
		fd.close()
		print("GPS track written into {:s}".format(fp))

	def toGPX(self, fp):
		"""
		Writes GPS track in a GPX file
		"""
		fd = open(fp,"w")
		fd.write('<?xml version="1.0" encoding="UTF-8"?>\n')
		fd.write('<gpx version="1.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n')
		fd.write(' xmlns="http://www.topografix.com/GPX/1/0"\n')
		fd.write(' xsi:schemaLocation="http://www.topografix.com/GPX/1/0 http://www.topografix.com/GPX/1/0/gpx.xsd">\n')

		fd.write('\t<name>{:s}</name>\n'.format(fp))
		fd.write('\t<desc>Imported from {:s}</desc>\n'.format(fp))
		fd.write('\t<trk>\n')
		fd.write('\t\t<name>GPS Track</name>\n')
		fd.write('\t\t<number>1</number>\n')
		fd.write('\t\t<trkseg>\n')
	
		for i in range(0, len(self.waypoints)):
			[lat, lon] = self.waypoints[i].toDecimalDegrees()
			fd.write('\t\t\t<trkpt lat="{:f}" lon="{:f}">\n'.format(lat,lon))
			fd.write('\t\t\t\t<ele>{:s}</ele>\n'.format(self.waypoints[i].getAltitude()))
			fd.write('\t\t\t</trkpt>\n')
			
		fd.write('\t\t</trkseg>\n')
		fd.write('\t</trk>\n')
		fd.write('</gpx>')
		fd.close()
		print("GPS Track written into {:s}".format(fp))

	def toCSV(self, fp):
		"""
		Writes GPS Track in CSV format,
		line0: titles[0], titles[1], .., titles[n-1]
		line[1]: data[0][0], ..., data[0][n-1]
		line[l-1]: data[l-1][0], ..., data[l-1][n-1]
		"""
		fd = open(fp,"w")
		line = ""
		fd.write("lat,lon,alt\n") # add 'label' here to view extra info
	
		for i in range(0, len(self.waypoints)):
			[lat, lon] = self.waypoints[i].toDecimalDegrees()
			line = "{:f},{:f},{:s}\n".format(lat,lon,self.waypoints[i].getAltitude())
			fd.write(line)
		fd.close()

	def drawOnMap(self, elevationProfile=None):
		"""
		Draws GPS track on map using
		geoplotlib.
		Elevation profile can optionnaly be viewed using
		matplotlib.
		"""
		
		# use temporary .csv file 
		# to make it compliant with geoplot lib.
		self.toCSV("/tmp/tmp.csv")
		data = read_csv("/tmp/tmp.csv")
		geoplotlib.dot(data, point_size=4)
		# retrieve labels here
		#geoplotlib.labels(data, "label", color=[0,0,255,255], font_size=10, anchor_x='center')
		geoplotlib.show()
		
		if (elevationProfile):
			fig = plt.figure(0)
			plt.subplot(111)
			plt.xlabel("Overall distance [m]")
			plt.ylabel("Elevation [m]")
			plt.grid(which='both', axis='both')
			ax = fig.add_subplot(111)

			acc = 0
			dist = [0]
			elevation = [float(self.waypoints[0].getAltitude())]
			for i in range(1, len(self.waypoints)):
				acc += self.waypoints[i].distance(self.waypoints[i-1])
				elevation.append(float(self.waypoints[i].getAltitude()))
				dist.append(acc)
			ax.plot(dist, elevation)
			ax.fill_between(dist, elevation, 0)
			plt.show()
