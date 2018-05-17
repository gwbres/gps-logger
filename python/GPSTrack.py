from Waypoint import *

ICON_URL = "http://maps.gstatic.com/mapfiles/ridefinder-images/mm_20_gray.png"

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
		
		elif (ext == 'locus'):
			self.GPSTrackLOCUS(fp)
		
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

	def GPSTrackLOCUS(self, fp):
		"""
		Builds GPS Track by parsing all waypoints
		in .locus log file
		"""
		fd = open(fp,"r")
		for line in fd:
			line = line.strip()

			if (not(line.startswith("$PMTKLOX,1"))):
				# non valid locus log
				continue

			# locus payload parsing
			content = line.split(",")
			checksum = content[-1].split("*")[-1]
			expected = Waypoint.checksum(line)
			if (checksum != expected):
				# checksum is faulty, discard this line
				continue
			
			content = content[3:] # remove header, type & line number
			content[-1] = content[-1].split("*")[0] # remove checksum value
			
			# one line in locus contains 6 waypoints
			# build byte array for this line
			_bytes = []
			for c in content:
				for i in range(0, 4): # 4*2 characters
					_offset = int(i*2) # slice 2 by 2 characthers (hex format)
					_bytes.append(int(c[_offset:_offset+2],16))

			N = int(len(content)/4) # number of records for this line
			for i in range(0,N): 
				try: 
					self.waypoints.append(Waypoint(locus=_bytes))
				except ValueError:
					# missing GPS fix, discard this one 
					pass

				_bytes = _bytes[16:] # shift used bytes

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

	def __str__(self):
		string = "--- GPS Track ---\n"
		for i in range(0, len(self.waypoints)):
			string += str(self.waypoints[i])
		string += "----------------"
		return string

	def append(self, waypoints):
		"""
		Appends waypoint or list of waypoints
		to self
		"""
		self.waypoints.append(waypoints)
	
	def prepend(self, waypoints):
		"""
		Prepends waypoint or list of waypoints
		to self
		"""
		self.waypoints.insert(0, waypoints)

	def insert(self, index, waypoints):
		"""
		Inserts waypoint or list of waypoints
		at given position
		"""
		self.waypoints.insert(index, waypoints)

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

	def drawOnMap(self, map):
		"""
		Draws GPS track on map using qMap
		"""
		
		map.setZoom(14)
		
		[l0,L0] = self.waypoints[0].toDecimalDegrees()
		map.centerAt(l0,L0)
		map.center()
		
		[l,L] = self.waypoints[-1].toDecimalDegrees()
		map.addMarker("Marker", l, L,
			**dict(
				icon=ICON_URL,
				draggable=False,
				title="Waypoint {:d}".format(0)
			)
		)

		"""
		for i in range(0, len(self.waypoints)):
			if ((i%10) == 0):
				[l,L] = self.waypoints[i].toDecimalDegrees() 
				map.runScript(
					"osm_addMarker(key={!r},"
					"latitude= {}, "
					"longitude= {},);".format("test",l,L)
				)
		"""

		map.waitUntilReady()

	def elevationProfile(self):
		"""
		Returns all waypoints altitude
		"""
		elevation = []
		for i in range(0, len(self.waypoints)):
			elevation.append(float(self.waypoints[i].getAltitude()))
		return elevation

	def totalDistance(self):
		"""
		Returns total distance covert in self
		"""
		dist = 0.0
		for i in range(1, len(self.waypoints)):
			dist += self.waypoints[i].distance(self.waypoints[i-1])
		return dist

	def averageSpeed(self, w1=None, w2=None):
		"""
		Returns average speed [m/s] over whole track
		or between specified portion

		TODO: $RMC or other NMEA payload
		provide instant. projected speed value,
		should we use it?
		"""
		speed = 0.0
		
		if w1 is None:
			w1 = 1
		else:
			if (w1 > len(self.waypoints)):
				w1 = len(self.waypoints)-1

		if w2 is None:
			w2 = len(self.waypoints)
		else:
			if (w2 > len(self.waypoints)):
				w2 = len(self.waypoints)
		
		for i in range(w1,w2):
			d = self.waypoints[i].distance(self.waypoints[i-1])/1000
			dt = self.waypoints[i].timeDiff(self.waypoints[i-1]).seconds
			speed += d/dt 

		return speed/len(self.waypoints)

	def instantSpeed(self, minDt=None, minDist=None):
		"""
		Returns instantaneous speed values
		between all waypoints within track.

		If minDt is specified: instant speed is averaged
		between waypoints within specified time interval.

		If minDist is specified: instant speed is averaged
		between waypoints within specified distance range.
		"""
		speed = []
		if ((minDt is None) and (minDist is None)):
			# straight forward
			for i in range(1, len(self.waypoints)):
				d = self.waypoints[i].distance(self.waypoints[i-1])/1000	
				dt = self.waypoints[i].timeDiff(self.waypoints[i-1]).seconds
				speed.append(d/dt)
		return speed
	
	def accumulatedDistance(self):
		"""
		Returns accumulated distance
		along the whole track
		"""
		x = []
		acc = 0.0
		x.append(0.0)
		for i in range(1, len(self.waypoints)):
			acc += self.waypoints[i].distance(self.waypoints[i-1])
			x.append(acc)
		return x
