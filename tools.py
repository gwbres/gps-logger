#! /usr/bin/env python3

import sys
import time
import math
import serial
import datetime
import matplotlib.pyplot as plt

import geoplotlib
from geoplotlib.utils import read_csv

# PMTK module
PMTK_SET_NMEA_UPDATE_100_MILLIHERTZ = "$PMTK220,10000*2F\r\n"
PMTK_SET_NMEA_UPDATE_200_MILLIHERTZ = "$PMTK220,5000*1B\r\n"
PMTK_SET_NMEA_UPDATE_1HZ = "$PMTK220,1000*1F\r\n"
PMTK_SET_NMEA_UPDATE_2HZ = "$PMTK220,500*2B\r\n"
PMTK_SET_NMEA_UPDATE_5HZ = "$PMTK220,200*2C\r\n"
PMTK_SET_NMEA_UPDATE_10HZ = "$PMTK220,100*2F\r\n"

PMTK_API_Q_FIX_CTRL = "$PMTK400*36\r\n"
PMTK_API_SET_FIX_CTL_100_MILLIHERTZ = "$PMTK300,10000,0,0,0,0*2C\r\n" 
PMTK_API_SET_FIX_CTL_200_MILLIHERTZ = "$PMTK300,5000,0,0,0,0*18\r\n" 
PMTK_API_SET_FIX_CTL_1HZ = "$PMTK300,1000,0,0,0,0*1C\r\n"
PMTK_API_SET_FIX_CTL_5HZ = "$PMTK300,200,0,0,0,0*2F\r\n"

PMTK_SET_BAUD_57600 = "$PMTK251,57600*2C\r\n"
PMTK_SET_BAUD_9600 = "$PMTK251,9600*17\r\n"

PMTK_SET_NMEA_OUTPUT_RMC_ONLY = "$PMTK314,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*29\r\n"
PMTK_SET_NMEA_OUTPUT_RMC_GGA = "$PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*28\r\n"
PMTK_SET_NMEA_OUTPUT_ALL_DATA = "$PMTK314,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0*28\r\n"
PMTK_SET_NMEA_OUTPUT_OFF = "$PMTK314,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*28\r\n"

PMTK_START_LOG = "$PMTK185,0*22\r\n"
PMTK_STOP_LOG = "$PMTK185,1*23\r\n"
PMTK_QUERY_STATUS = "$PMTK183*38\r\n"
PMTK_DUMP_FLASH = "$PMTK622,1*29\r\n"
PMTK_ERASE_FLASH = "$PMTK184,1*22\r\n"

PMTK_LOCUS_1_SECONDS = "$PMTK187,1,1*3C\r\n"
PMTK_LOCUS_5_SECONDS = "$PMTK187,1,5*38\r\n"
PMTK_LOCUS_15_SECONDS = "$PMTK187,1,15*09\r\n"

PMTK_ENABLE_SBAS = "$PMTK313,1*2E\r\n"
PMTK_ENABLE_WAAS = "$PMTK301,2*2E\r\n"

PMTK_STANDBY = "$PMTK161,0*28\r\n"
PMTK_STANDBY_SUCCESS = "$PMTK001,161,3*36\r\n"
PMTK_AWAKE = "$PMTK010,002*2D\r\n"
PMTK_Q_RELEASE = "$PMTK605*31\r\n"

PGCMD_ANTENNA = "$PGCMD,33,1*6C\r\n"
PGCMD_NOANTENNA = "$PGCMD,33,0*6D\r\n"

def write_cmd(tty, cmd):
	tty.write(bytes(cmd+"\n",encoding="utf-8"))
	time.sleep(1)
	return tty.readline().decode("utf-8")

def print_help():
	string = " █▀▀█ ▒█▀▀█ ▒█▀▀▀█ 　 ▀▀█▀▀ ▒█▀▀▀█ ▒█▀▀▀█ ▒█░░░ ▒█▀▀▀█\n▒█░▄▄ ▒█▄▄█ ░▀▀▀▄▄ 　 ░▒█░░ ▒█░░▒█ ▒█░░▒█ ▒█░░░ ░▀▀▀▄▄\n▒█▄▄█ ▒█░░░ ▒█▄▄▄█ 　 ░▒█░░ ▒█▄▄▄█ ▒█▄▄▄█ ▒█▄▄█ ▒█▄▄▄█\n"

	string += "\nPMTK module:\n"
	string += "--port\n\tSet serial port to be used\n\tex: --port=/dev/ttyUSB0\n"
	string += "--status\n\tQuery status\n"
	string += "--start-logging\n\tGPS module starts recording frame\n"
	string += "--stop-logging\n\tModule stops recording frames\n"
	string += "--erase-flash\n\tErases frames stored into internal memory\n"
	string += "--dump\n\tDump flash data\n"
	
	string += "\nPMTK module [advanced]\n"
	string += "--baud\n\tSet GPS serial rate [9600,57600] b/s\n"
	string += "--query-fix-rate\n\tCheck current fix rate\n"
	string += "--set-locus-rate\n\tSet internal logging rate [1s,5s,15s]\n"
	string += "--nmea-rate\n\tSet GPS frames update rate [10Hz,5Hz,2Hz,1Hz,200mHz,100mHz]\n"
	string += "--nmea-output\n\tSet nmea frames type to be produced [RMC,RMCGGA,ALL,OFF]\n"

	string += "\nData toolbox:\n"
	string += "--nmea-to-kml\n\tConverts .nmea file to .kml file (google earth, ..)\n"
	string += "--nmea-to-gpx\n\tConverts .nmea file to .gpx file (Garmin, etc..)\n"
	string += "--locus-to-kml\n\tConvers .locus data to .kml file\n"
	string += "--locus-to-gpx\n\tConvers .locus data to .gpx file\n"
	string += "--view-coordinates\n\tDraws waypoints found in .nmea, .kml, .gpx data file onto map\n"

	print(string)

# Converts parsed coordinates 
# lat: ddmm.ssss
# lon: dddmm.ssss
# to D° M' S" 
def coord_to_DMS(coord, islong=False):
	if (islong):
		D = int(coord.split(".")[0][0:3])
		M = int(coord.split(".")[0][3:5])
		S = float("0."+coord.split(".")[1])*60
	else:
		D = int(coord.split(".")[0][0:2])
		M = int(coord.split(".")[0][2:4])
		S = float("0."+coord.split(".")[1])*60
	return [D, M, S]

# converts GPS coordinates to decimal degrees
# coord: ddmm.ssss
def coord_to_decimal_degrees(coord, islong=False):
	[D, M, S] = coord_to_DMS(coord, islong=islong)
	return D+M/60+S/3600

def knots_to_kmph(knots):
	mph = knots*1.15078
	return mph*1.60934

# Harversine: computes distance
# between two waypoints
def Haversine(wp1, wp2):
	deltaLat = math.radians(wp2[0])-math.radians(wp1[0])
	deltaLon = math.radians(wp2[1])-math.radians(wp1[1])
	lat1rad = math.radians(wp1[0])
	lat2rad = math.radians(wp2[0])
	a = math.sqrt((math.sin(deltaLat/2))**2+math.cos(lat1rad)*math.cos(lat2rad)*(math.sin(deltaLon/2))**2)
	return 2*6371000*math.asin(a)

# GPGGA:
# class descriptor for GPGGA NMEA frames
class GPGGA:
	def __init__(self, csv):
		self.utc = "000000.00"
		self.lat = None
		self.long = None
		self.alt = "0" 
		self.hdop = None

		content = csv.split(",")[1:-1] # remove header and checksum
		self.utc = content[0]
		if ((content[1]) is not None): # missing if not FIXed
			self.lat = [content[1],content[2]]
			self.long = [content[3],content[4]]

		# content[5]: '1' is GPS coordinates
		# content[6]: number of sallites used
	
		# HDOP Horizontal dilution of Precision
		if ((content[7] is not None)): # could be missing
			self.hdop = content[7]
		
		if (content[8] != ""): # might be missing
			self.alt = content[8] # content[9]='M' for meters

	def get_utc(self):
		return self.utc
	
	def get_long(self):
		return self.long

	def get_lat(self):
		return self.lat
	
	def get_alt(self):
		return self.alt
	
	def get_hdop(self):
		return self.hdop
	
	def _type(self):
		return "GPGGA"

# GPRMC 
# class descriptor for RMC frames
class GPRMC:
	def __init__(self, csv):
		self.utc = "000000.00"
		self.alt = None
		self.lat = "0" 
		self.long = None
		
		content = csv.split(",")[1:-1] # remove header & checksum
		self.utc = content[0]
		if (content[1] == 'A'): # 'A':valid (proceed), 'V' non valid
			self.lat = [content[2],content[3]]
			self.long = [content[4],content[5]]
			self.speed = knots_to_kmph(float(content[6]))
			# content[7] route sur le fond
			self.date = content[7]

	def _type(self):
		return "GPRMC"

	def get_utc(self):
		return self.utc

	def get_lat(self):
		return self.lat

	def get_alt(self):
		return "0"

	def get_long(self):
		return self.long

	def get_speed(self):
		return self.speed

	def get_date(self):
		return self.date

# parses all waypoints (lat,lon,alt)
# contained in .nmea file
# results [[lat0,lon0,a0],[lat1,lon1,a1],..,[lat(n),lon(n),a(n)]]
# were lat(i),lon(i) are expressed in decimal degrees
def nmea_parse_waypoints(fp):
	waypoints = []
	fd=open(fp,"r")
	for line in fd:
		line = line.strip()
		
		if (line.startswith("$GPGGA")):
			GPS = GPGGA(line)
		elif (line.startswith("$GPRMC")):
			GPS = GPRMC(line)
		else:
			continue
		
		latdeg = coord_to_decimal_degrees(GPS.get_lat()[0])
		if (GPS.get_lat()[1] == "S"):
			latdeg *= (-1)
		
		londeg = coord_to_decimal_degrees(GPS.get_long()[0], islong=True)
		if (GPS.get_long()[1] == "W"):
			londeg *= (-1)

		utc = GPS.get_utc()
		h = utc[0:2]
		m = utc[2:4]
		s = utc[4:]
		text = "{:d}:{:d}:{:f}".format(int(h),int(m),float(s)) # brought up by geoplotlib.labels()

		waypoint = [latdeg,londeg,GPS.get_alt(),text]
		waypoints.append(waypoint)

	fd.close()
	return waypoints

# converts string of bytes into byte array
def pack4Bytes(string):
	Bytes = []
	for i in range(0, int(len(string)/2)):
		Bytes.append(int(string[int(i*2):int(i*2)+2],16))
	return Bytes

def parseInt(Bytes):
	n = ((0xFF & Bytes[1]) << 8) | (0xFF & Bytes[0])
	return n

def parseLong(Bytes):
	n = ((0xFF & Bytes[3]) << 24) | ((0xFF & Bytes[2]) << 16) | ((0xFF & Bytes[1]) << 8) | (0xFF & Bytes[0]) 
	return n

def parseFloat(Bytes):
	longValue = parseLong(Bytes)
	exponent = ((longValue >> 23) & 0xff) # float
	exponent -= 127.0
	exponent = pow(2,exponent)
	mantissa = (longValue & 0x7fffff)
	mantissa = 1.0 + (mantissa/8388607.0)
	floatValue = mantissa * exponent
	if ((longValue & 0x80000000) == 0x80000000):
		floatValue = -floatValue
	return floatValue 

# parses all waypoints contained in locus flash memory/data file
def locus_parse_waypoints(fp):
	waypoints = []
	fd = open(fp, "r")
	for line in fd:
		# only keep valid data
		if not(line.startswith('$PMTKLOX,1')):
			continue

		#TODO verify checkum
		# checksum(line.split('*'))

		data = line.split(',')[3:] # rm cmd/type/line number
		
		timestamp = parseLong(pack4Bytes(data[8]))
		if (timestamp > 4290000000):
			continue

		print(len(data))

		date = datetime.datetime.fromtimestamp(timestamp)
		string = "Date: {:s}\n".format(str(date))
		
		lat = parseFloat(pack4Bytes(data[18]))
		string += "Lat: {:f}\n".format(lat)
		
		lon = parseFloat(pack4Bytes(data[20]))
		string += "Lon: {:f}\n".format(lon)
		
		alt = parseFloat(pack4Bytes(data[22]))
		string += "Alt: {:f}\n".format(alt)

		print(string)
		"""
		{
			"datetime": "2013-10-10T04:52:25", 
			"fix": 2, 
			"height": 56, 
			"latitude": 40.1347017448785, 
			"longitude": -75.2062849052292
		}, 

		"""
		return 0

	fd.close()

# puts data into given file in csv format
# line0: titles[0],titles[1],..,titles[n-1],
# line1: data[0][0],data[0][1],..,data[0][n-1],
#  .
#  .
# line[l-1]: data[l-1][0],...,data[l-1][n-1]
def to_csv(fp, titles, data):
	fd=open(fp,"w")
	line = ""
	for title in titles:
		line += "{:s},".format(title)
	line += "\n"
	fd.write(line)

	for j in range(0, len(data)):	
		line = ""
		for i in range(0, len(data[j])):
			line += "{:s},".format(str(data[j][i]) )
		line += "\n"
		fd.write(line)
	fd.close()

# Converts waypoints to .kml file
def waypoints_to_kml(waypoints, kml):
	kmlfd = open(kml, "w")

	# initialize kml file
	kmlfd.write('<?xml version="1.0" encoding="UTF-8"?>\n')
	kmlfd.write('<kml xmlns="http://earth.google.com/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2">\n')
	kmlfd.write('<Folder>\n')

	# track infos
	kmlfd.write('\t<name>Imported from {:s}</name>\n'.format(nmea))
	kmlfd.write('\t<Placemark>\n')
	kmlfd.write('\t\t<name>Track</name>\n')

	# track style
	kmlfd.write('\t\t<Style>\n')
	kmlfd.write('\t\t\t<LineStyle>\n')
	kmlfd.write('\t\t\t\t<color>00cc00cc</color>\n')
	kmlfd.write('\t\t\t\t<width>4</width>\n')
	kmlfd.write('\t\t\t</LineStyle>\n')
	kmlfd.write('\t\t</Style>\n')

	# track
	kmlfd.write('\t\t<LineString>\n')
	kmlfd.write('\t\t\t<altitudeMode>relativeToGround</altitudeMode>\n')
	kmlfd.write('\t\t\t<coordinates>\n')

	for waypoint in waypoints:
		lat = waypoint[0]
		lon = waypoint[1]
		kmlfd.write('\t\t\t\t{:f},{:f},{:f}\n'.format(lon, lat, 0.0))

	kmlfd.write('\t\t\t</coordinates>\n')
	kmlfd.write('\t\t</LineString>\n')
	
	# finalize kml file 
	kmlfd.write('\t</Placemark>\n')
	kmlfd.write('\t</Folder>\n')
	kmlfd.write('</kml>\n')
	kmlfd.close()
	print("NMEA file {:s} content converted to KML in {:s}".format(nmea,kml))

def kml_parse_waypoints(fp):
	waypoints = []
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
				alt = float(parsed[2])
				waypoints.append([lat,lon,alt])

	fd.close()
	return waypoints

# converts waypoints to .gpx file
def waypoints_to_gpx(waypoints, gpx):
	gpxfd = open(gpx,"w")
	gpxfd.write('<?xml version="1.0" encoding="UTF-8"?>\n')
	gpxfd.write('<gpx version="1.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n')
	gpxfd.write(' xmlns="http://www.topografix.com/GPX/1/0"\n')
	gpxfd.write(' xsi:schemaLocation="http://www.topografix.com/GPX/1/0 http://www.topografix.com/GPX/1/0/gpx.xsd">\n')

	gpxfd.write('\t<name>{:s}</name>\n'.format('Test'))
	gpxfd.write('\t<desc>{:s}</desc>\n'.format("Test"))
	gpxfd.write('\t<trk>\n')
	gpxfd.write('\t\t<name>Track</name>\n')
	gpxfd.write('\t\t<number>1</number>\n')
	gpxfd.write('\t\t<trkseg>\n')

	for waypoint in waypoints:
		lat = waypoint[0]
		lon = waypoint[1]
		gpxfd.write('\t\t\t<trkpt lat="{:f}" lon="{:f}">\n'.format(lat,lon))
		gpxfd.write('\t\t\t\t<ele>{:s}</ele>\n'.format("0"))
		
		"""
		#TODO handle timestamps
		utc = GPS.get_utc()
		h = utc.split(".")[0][0:1]
		m = utc.split(".")[0][2:3]
		s = utc.split(".")[0][4:5]
			
		gpxfd.write('\t\t\t\t<time>20{:s}-{:s}-16T{:s}:{:s}:{:s}Z</time>\n'
			.format(year,month,day,h,m,s)
		)
		"""
		gpxfd.write('\t\t\t</trkpt>\n')
			
	gpxfd.write('\t\t</trkseg>\n')
	gpxfd.write('\t</trk>\n')
	gpxfd.write('</gpx>')
	gpxfd.close()
	print("NMEA file {:s} content converted to GPX in {:s}".format(nmea,gpx))

# opens serial port
def open_serial(tty, baudrate):
	ser = serial.Serial(tty)
	ser.baudrate = baudrate
	ser.flushInput()
	ser.flushOutput()
	# setup
	ser.bytesize = serial.EIGHTBITS
	ser.parity = serial.PARITY_NONE
	ser.stopbits = serial.STOPBITS_ONE
	ser.timeout = 0
	ser.xonxoff = 0
	ser.rtscts = False
	ser.dsrdtr = False
	ser.writeTimeout = 2
	return ser

# draws coordinates contained in given file
# elevation profile can be optionnaly added
def view_coordinates(fp, elevation_profile=None):
	ext = fp.split(".")[-1]
	if (ext == "nmea"):
		waypoints = nmea_parse_waypoints(fp)
	elif (ext == "kml"):
		waypoints = kml_parse_waypoints(fp)
	elif (ext == "gpx"):
		waypoints = gpx_parse_waypoints(fp)
	else:
		print("File format {:s} is not supported".format(ext))
		return -1

	# use temporary .csv file 
	# to make it compliant with geoplot lib.
	to_csv("/tmp/tmp.csv", ["lat","lon","alt","label"], waypoints)
	data = read_csv("/tmp/tmp.csv")
	geoplotlib.dot(data, point_size=4)
	geoplotlib.labels(data, "label", color=[0,0,255,255], font_size=10, anchor_x='center')
	
	if (elevation_profile):
		fig = plt.figure(0)
		plt.subplot(111)
		plt.xlabel("Overall distance [m]")
		plt.ylabel("Elevation [m]")
		plt.grid(which='both', axis='both')
		ax = fig.add_subplot(111)
		dist = []
		i = 0
		elevation = []
		for waypoint in waypoints:
			elevation.append(waypoint[2])
			if (len(dist) == 0):
				accDist = 0
			else:
				accDist += Haversine(waypoint, waypoints[i-1])
			dist.append(accDist)
			i += 1

		ax.plot(dist, elevation)
		ax.fill_between(dist, elevation, 0)
		plt.show()
	
	geoplotlib.show()

def main(argv):
	argv = argv[1:]

	if (len(argv) == 0):
		print_help()
		return -1

	commands = []
	view_profile = None
	files = []
	port = None

	for flag in argv:
		if (flag.split("=")[0] == "--port"):
			port = flag.split("=")[-1]
		
		# GPS logger
		elif flag == "--status":
			commands.append("status")
		elif flag == "--start-logging":
			commands.append("start")
		elif flag == "--stop-logging":
			commands.append("stop")
		elif flag == "--locus-rate":
			commands.append("locus-rate")
		
		# internal flash
		elif flag == "--dump":
			commands.append("dump")
		elif flag == "--erase-flash":
			commands.append("erase")

		# GPS serial bus 
		elif flag == "--nmea-rate":
			commands.append("nmea-rate")
		elif flag == "--nmea-output":
			commands.append("nmea-output")
		elif flag == "--baud":
			commands.append("baud")

		# GPS Fix
		elif flag == "--led-fix-rate":
			commands.append("led-rate")

		# GPS data tools
		elif flag == "--nmea-to-kml":
			commands.append("nmea-to-kml")
		elif flag == "--nmea-to-gpx":
			commands.append("nmea-to-gpx")

		# Input file paths
		elif (flag.split("=")[0] == "--file"):
			files.append(flag.split("=")[-1])
		
		# coordinates viewer
		elif flag == "--view-coordinates":
			commands.append("viewer")
		elif flag == "--elevation-profile":
			view_profile = True

	for command in commands:
		if (command == "status"):
			ser = open_serial(port,9600)
			answer = write_cmd(ser, PMTK_QUERY_STATUS)

			print(answer)
			string = "Status:\n"
			string += "SN {:s}\n".format(answer.split(",")[1])
			
			logType = int(answer.split(",")[2])
			string += "Log type: "
			if (logType == 0):
				string += "locus overlap\n"
			else:
				string += "locus fullstop\n"

			try:
				logMode = int(answer.split(',')[3])
			except ValueError:
				logMode = int(answer.split(',')[3],16)

			string += "locus mode:"
			if (logMode & 0x1):
				string += " AlwaysLocate"
			if (logMode & 0x2):
				string += " FixOnly"
			if (logMode & 0x4):
				string += " Normal"
			if (logMode & 0x8):
				string += " Interval"
			if (logMode & 0x10):
				string += " Distance"
			if (logMode & 0x20):
				string += " Speed"
			string += "\n"

			string += 'locus content: {:d}\n'.format(int(answer.split(',')[4]))
			string += 'locus interval: {:d} [s]\n'.format(int(answer.split(',')[5]))
			string += 'locus distance: {:d} [m]\n'.format(int(answer.split(',')[6]))
			string += 'locus speed: {:d} [m/s]\n'.format(int(answer.split(',')[7]))
			string += 'locus logging: {:d}\n'.format(not(bool(answer.split(',')[8])))
			string += "Data records: {:s}\n".format(answer.split(',')[9])
			string += "{:s}% flash used:\n".format(answer.split(",")[10].split("*")[0])
			print(string)
			ser.close()
		
		elif (command == "start"):
			ser = open_serial(port,9600)
			answer = write_cmd(ser, PMTK_START_LOG).strip()
			if (answer == "$PMTK001,185,3*3C"):
				print("Logger has been started")
			else:
				print("Error: {:s}".format(answer))
			ser.close()
		
		elif (command == "stop"):
			ser = open_serial(port,9600)
			print(write_cmd(ser, PMTK_STOP_LOG))
			ser.close()

		elif (command == "dump"):
			ser = open_serial(port,9600)
			write_cmd(ser, PMTK_SET_NMEA_OUTPUT_OFF)
			write_cmd(ser, PMTK_DUMP_FLASH)
			ser.close()
			
			"""
			# dump locus content to temporary file
			fd = open("/tmp/.locus","w")
			for i in range(0, n):
				fd.write(ser.readline().decode("utf-8"))
			fd.close()
	
			# convert to waypoints
			[timestamps, fix, lat, lon, alt] = locus_parse_waypoints("/tmp/.locus")
			today = datetime.date.today()
			fp = "{:s}-{:s}-{:s}".format(today.year,today.month,today.day)
			waypoints_to_kml(fp+".kml")
			waypoints_to_gpx(fp+".gpx")

			ser.close()
			"""

		elif (command == "erase"):
			c = input("Erasing.. are you sure? [Y/N]")
			if (c == "Y"):
				ser = open_serial(port,9600)
				answer = write_cmd(ser, PMTK_ERASE_FLASH).strip()
				if (answer == "$PMTK001,184,3*3D"):
					print("Flash has been erased")
				else:
					print("error")
				ser.close()

		elif (command == "nmea-rate"):
			r = input("Set GPS frames rate [100mHz, 200mHz, 1Hz, 2Hz, 5Hz, 10Hz]")

			if r == "100mHz":
				cmd = PMTK_SET_NMEA_UPDATE_100_MILLIHERTZ
			elif r == "200mHz":
				cmd = PMTK_SET_NMEA_UPDATE_200_MILLIHERTZ
			elif r == "1Hz":
				cmd = PMTK_SET_NMEA_UPDATE_1HZ
			elif r == "2Hz":
				cmd = PMTK_SET_NMEA_UPDATE_2HZ
			elif r == "5Hz":
				cmd = PMTK_SET_NMEA_UPDATE_5HZ
			elif r == "10Hz":
				cmd = PMTK_SET_NMEA_UPDATE_10HZ
			else:
				cmd = PMTK_SET_NMEA_UPDATE_1HZ
				print("Rate {:s} is not supported")
				print("Switching back to 1 Hz default rate")
			
			ser = open_serial(port,9600)
			answer = write_cmd(ser,cmd).strip()
			if (answer == "$PMTK001,220,3*30"):
				print("Success")
			else:
				print("Error: {:s}".format(answer))
			ser.close()

		elif (command == "led-rate"):
			ser = open_serial(port,9600)
			answer = write_cmd(ser,PMTK_API_Q_FIX_CTRL).strip()
			print(answer)
	
		elif (command == "locus-rate"):
			rate = input("Set logging rate..[1s,5s,15s]") 
			if (not(rate in ["1s","5s","15s"])):
				print("Rate {:s} is not supported, aborting".format(rate))
			else:
				if rate == "1s":
					cmd = PMTK_LOCUS_1_SECONDS 
				elif rate == "5s":
					cmd = PMTK_LOCUS_5_SECONDS 
				elif rate == "15s":
					cmd = PMTK_LOCUS_15_SECONDS 
				ser = open_serial(port, 9600)
				answer = write_cmd(ser, cmd).strip()
				print(answer)
				ser.close()

		elif (command == "nmea-output"):
			output = input("Set nmea output frames [RMC,RMC-GGA,ALL,OFF]..")
			if not(output in ["RMC","RMC-GGA","ALL","OFF"]):
				print("NMEA mode {:s} is not valid".format(output))
			else:
				if output == "RMC":
					cmd = PMTK_SET_NMEA_OUTPUT_RMC_ONLY
				elif output == "RMC-GGA":
					cmd = PMTK_SET_NMEA_OUTPUT_RMC_GGA
				elif output == "OFF":
					cmd = PMTK_SET_NMEA_OUTPUT_OFF
				else:
					cmd = PMTK_SET_NMEA_OUTPUT_ALL_DATA

				ser = open_serial(port,9600)
				answer = write_cmd(ser,cmd).strip()
				if (answer == "$PMTK001,314,3*36"):
					print("Success")
				else:
					print("Error: {:s}".format(answer))
				ser.close()

		elif (command == "nmea-to-kml"):
			if (len(files) == 0):
				fp = input("Set input file path..\n")
			else:
				fp = files[0]
				files = files[1:]
				
			waypoints_to_kml(nmea_parse_waypoints(fp), fp.split(".")[0]+".kml")
		
		elif (command == "nmea-to-gpx"):
			if (len(files) == 0):
				fp = input("Set input file path..\n")
			else:
				fp = files[0]
				files = files[1:]
			waypoints_to_gpx(nmea_parse_waypoints(fp), fp.split(".")[0]+".gpx")

		elif (command == "viewer"):
			if (len(files) == 0):
				fp = input("Set input file path..\n")
			else:
				fp = files[0]
				files = files[1:]
			view_coordinates(fp, elevation_profile=view_profile)
		
		elif command == "--help":
			print_help()
			return 0

		elif command == "--h":
			print_help()
			return 0

		elif command == "help":
			print_help()
			return 0

		else:
			print("Command {:s} is not supported".format(command))

main(sys.argv)
