import time
import math
import datetime

class Waypoint:
	"""
	A Waypoint is a GPS coordinate
	made of latitude & longitude coordinates,
	optionnal UTC timestamp and altitude.
	"""
	
	def __init__(self, nmea=None, locus=None, latDeg=None, lonDeg=None, date=None, alt=None):
		"""
		Creates a Waypoint object
		from either: an nmea frame (CSV)
		or from lat/lon in decimal degrees.
		alt [m]: optional
		date: optional

		Object contains latitude & longitude coordinates,
		a date built from given UTC timestamp or complete date.
		"""

		self.lat = ["ddmm.ssss","N"]
		self.lon = ["dddmm.ssss","E"]
		self.alt = "0" 
		self.speed = None
		
		if (nmea is not None):
			content = nmea.split(",")
			checksum = content[-1].split("*")[-1]
			expecting = Waypoint.checksum(nmea)
			if (checksum != expecting):
				raise ValueError("Checksum is faulty for line {:s}".format(nmea))

			if (content[0] == "$GPGGA"):
				# GGA frame
				utc = content[1] # hhmmss.ss
				# day is missing, use today for day
				today = datetime.date.today()
				string = "{:d}/{:d}/{:d} ".format(today.day,today.month,today.year)
				# use utc for time of day
				string += "{:s}:{:s}:{:s}".format(utc[0:2],utc[2:4],utc[4:6])
				format = "%d/%m/%y %H:%M:%S"
				self.date = datetime.datetime.strptime(string,format)
				
				self.lat = [content[2],content[3]]
				self.lon = [content[4],content[5]]
				self.alt = content[9]

			elif (content[0] == "$GPRMC"):
				# RMC frame
				if (content[2] == 'A'): # 'A':valid (GPS fix), 'V' non valid
					# combine given UTC & date to build date value
					utc = content[1] # hhmmss.ss
					day = content[9] # ddmmyy
					string = "{:s}/{:s}/{:s} ".format(day[0:2],day[2:4],day[4:6])
					string += "{:s}:{:s}:{:s}".format(utc[0:2],utc[2:4],utc[4:6])
					format = "%d/%m/%y %H:%M:%S"
					self.date = datetime.datetime.strptime(string, format)

					self.lat = [content[3],content[4]]
					self.lon = [content[5],content[6]]
					self.speed = self.knotsToKmph(float(content[7]))
				else:
					raise ValueError("'V' non valid $GPRMC frame")

			else:
				raise NameError("Only $GGA & $RMC nmea frames are supported at the moment")

		elif (locus is not None):
			b0 = locus[0:4]

			b1 = locus[4]
			if (not((b1 > 0) and (b1 < 5))):
				raise ValueError("Locus/GPS Fix error")

			b2 = locus[5:9]
			b3 = locus[9:13]
			b4 = locus[13:16]

			self.date = datetime.datetime.fromtimestamp(self.parseInt32(b0))
			
			latDeg = self.parseFloat32(b2)
			DMS = self.decimalDegreesToDMS(latDeg)
			if (latDeg < 0):
				EM = "S"
			else:
				EM = "N"
			self.lat = [self.DMStoDDMMSSSS(DMS),EM]

			lonDeg = self.parseFloat32(b3)
			DMS = self.decimalDegreesToDMS(lonDeg)
			if (lonDeg < 0):
				EM = "W"
			else:
				EM = "E"
			self.lon = [self.DMStoDDMMSSSS(DMS, isLongitude=True),EM]

			self.alt = str(self.parseInt16(b4)) 

		else:
			DMS = self.decimalDegreesToDMS(latDeg)
			if (latDeg < 0):
				EM = "S"
			else:
				EM = "N"
			self.lat = [self.DMStoDDMMSSSS(DMS), EM]

			DMS = self.decimalDegreesToDMS(lonDeg)
			if (lonDeg < 0):
				EM = "W"
			else:
				EM = "E"
			self.lon = [self.DMStoDDMMSSSS(DMS, isLongitude=True),EM]

			if (alt is not None):
				self.alt = alt
			
			if (date is None): # use now()
				self.date = datetime.date.today()
			else:
				self.date = date

	def decimalDegreesToDMS(self, deg):
		""" Converts decimal degrees to D°M'S" """
		D = int(float(deg))
		M = int((abs(float(deg))*60)%60)
		S = (abs(float(deg))*3600)%60
		return [D,M,S]

	def DMStoDDMMSSSS(self, DMS, isLongitude=False):
		""" Converts D°M'S" to 'ddmm.ssss' string """

		nD = 2
		if (isLongitude):
			nD += 1

		dd = "{:d}".format(DMS[0]).zfill(nD)
		mm = "{:d}".format(DMS[1]).zfill(2)
		
		fractionnal = (DMS[2]/60)%1
		stringFract = "{:4f}".format(fractionnal)
		ssss = stringFract[2:]

		return dd+mm+"."+ssss

	def __str__(self):
		lat = self.getLatitude()
		lon = self.getLongitude()
		string = "{:s}|".format(str(self.date))
		string += "{:s}{:s}|".format(lat[0],lat[1])
		string += "{:s}{:s}".format(lon[0],lon[1])
		return string

	def __eq__(self, wp):
		"""
		Returns true if GPS coordinates are
		stricly identical
		"""
		[l0,L0] = self.toDecimalDegrees()
		[l, L] = wp.toDecimalDegrees()
		if (l0 == l):
			if (L == L0):
				return True
		return False

	def getLatitude(self):
		return self.lat
	
	def getLongitude(self):
		return self.lon

	def getAltitude(self):
		return self.alt

	def getDate(self):
		return self.date

	def toDMS(self):
		"""
		Converts self to D° M' S"
		lat: ddmm.ssss
		lon: dddmm.ssss
		to D° M' S" 
		returns [DMSlat,DMSlon]
		"""
		coord = self.getLatitude()[0] # ddmm.ssss
		Dl = int(coord.split(".")[0][0:2])
		Ml = int(coord.split(".")[0][2:4])
		Sl = float("0."+coord.split(".")[1])*60

		coord = self.getLongitude()[0] # dddmm.ssss
		DL = int(coord.split(".")[0][0:3])
		ML = int(coord.split(".")[0][3:5])
		SL = float("0."+coord.split(".")[1])*60
		return [[Dl, Ml, Sl], [DL, ML, SL]]

	def toDecimalDegrees(self):
		"""
		Converts self to decimal degrees
		returns [Lat(deg),Lon(deg)] 
		"""
		DMS = self.toDMS()
		
		lat = DMS[0][0]+DMS[0][1]/60+DMS[0][2]/3600
		if (self.getLatitude()[1] == "S"):
			lat *= (-1)
		
		lon = DMS[1][0]+DMS[1][1]/60+DMS[1][2]/3600
		if (self.getLongitude()[1] == "W"):
			lon *= (-1)

		return [lat,lon]

	def knotsToKmph(self, knots):
		""" Converts knots to km/h """
		mph = knots*1.15078
		return mph*1.60934

	def distance(self, wp):
		"""
		Returns distance between self & another waypoint
		using Harversine formula
		"""
		lat1 = float(self.getLatitude()[0])
		lon1 = float(self.getLongitude()[0])
		lat2 = float(wp.getLatitude()[0])
		lon2 = float(wp.getLongitude()[0])
		deltaLat = math.radians(lat2)-math.radians(lat1)
		deltaLon = math.radians(lon2)-math.radians(lon2)
		lat1rad = math.radians(lat1)
		lat2rad = math.radians(lat2)
		a = math.sqrt((math.sin(deltaLat/2))**2+math.cos(lat1rad)*math.cos(lat2rad)*(math.sin(deltaLon/2))**2)
		return 2*6371000*math.asin(a)

	def timeDiff(self, wp):
		"""
		Returns time difference (timedelta object)
		between two waypoints
		"""
		return self.getDate()-wp.getDate()

	@classmethod
	def checksum(cls, line):
		""" 
		Evaluates checksum for given nmea/locus line.
		Returns zero padded hex string.
		"""
		check = 0
		content = line[1:].split("*")[0] # drop leading '$'
		for c in content: # drop leading '$'
			check ^= ord(c)
		return hex(check)[2:].upper().zfill(2) # zero padding / keep last 2 bits

	def toByteArray(self, string):
		"""
		Converts a string into a byte array
		"""
		Bytes = []
		n = 0
		while (n < len(string)):
			b = string[n:n+2]
			Bytes.append(int(b,16)) # conversion
			n += 2
		return Bytes

	def parseInt32(self, Bytes):
		"""
		Converts array of 4 bytes into
		32 bit integer value
		"""
		return ((0xFF & Bytes[3]) << 24) | ((0xFF & Bytes[2]) << 16) | ((0xFF & Bytes[1]) << 8) | (0xFF & Bytes[0])    

	def parseInt16(self, Bytes):
		return (((0xFF & Bytes[1]) << 8) | (0xFF & Bytes[0]))
	
	def parseFloat32(self, Bytes):
		"""
		Convers array of 4 bytes into
		32 bit float single precision number
		"""
		int32 = self.parseInt32(Bytes)
		exponent = ((int32 >> 23)&0xff)
		exponent -= 127.0
		exponent = pow(2,exponent)
		mantissa = (int32 & 0x7fffff)
		mantissa = 1.0 + (mantissa/8388607.0)
		floatValue = mantissa * exponent
		if ((int32 & 0x80000000) == 0x80000000):
			floatValue = -floatValue
		return floatValue
