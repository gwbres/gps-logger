#! /usr/bin/env python3

import sys
import serial
from datetime import date

# PMTK module
PMTK_SET_NMEA_UPDATE_100_MILLIHERTZ = "$PMTK220,10000*2F" 
PMTK_SET_NMEA_UPDATE_200_MILLIHERTZ = "$PMTK220,5000*1B" 
PMTK_SET_NMEA_UPDATE_1HZ = "$PMTK220,1000*1F"
PMTK_SET_NMEA_UPDATE_2HZ = "$PMTK220,500*2B"
PMTK_SET_NMEA_UPDATE_5HZ = "$PMTK220,200*2C"
PMTK_SET_NMEA_UPDATE_10HZ = "$PMTK220,100*2F"

PMTK_API_SET_FIX_CTL_100_MILLIHERTZ = "$PMTK300,10000,0,0,0,0*2C" 
PMTK_API_SET_FIX_CTL_200_MILLIHERTZ = "$PMTK300,5000,0,0,0,0*18" 
PMTK_API_SET_FIX_CTL_1HZ = "$PMTK300,1000,0,0,0,0*1C"
PMTK_API_SET_FIX_CTL_5HZ = "$PMTK300,200,0,0,0,0*2F"

PMTK_SET_BAUD_57600 = "$PMTK251,57600*2C"
PMTK_SET_BAUD_9600 = "$PMTK251,9600*17"

PMTK_SET_NMEA_OUTPUT_RMCONLY = "$PMTK314,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*29"
PMTK_SET_NMEA_OUTPUT_RMCGGA = "$PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*28"
PMTK_SET_NMEA_OUTPUT_ALLDATA = "$PMTK314,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0*28"
PMTK_SET_NMEA_OUTPUT_OFF = "$PMTK314,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*28"

PMTK_STARTLOG = "$PMTK185,0*22"
PMTK_STOPLOG = "$PMTK185,1*23"
PMTK_STARTSTOPACK = "$PMTK001,185,3*3C"
PMTK_QUERY_STATUS = "$PMTK183*38"
PMTK_ERASE_FLASH = "$PMTK184,1*22"

PMTK_ENABLE_SBAS = "$PMTK313,1*2E"
PMTK_ENABLE_WAAS = "$PMTK301,2*2E"

PMTK_STANDBY = "$PMTK161,0*28"
PMTK_STANDBY_SUCCESS = "$PMTK001,161,3*36"
PMTK_AWAKE = "$PMTK010,002*2D"

PMTK_Q_RELEASE = "$PMTK605*31"

PGCMD_ANTENNA = "$PGCMD,33,1*6C" 
PGCMD_NOANTENNA = "$PGCMD,33,0*6D" 

def write_cmd(tty, cmd):
	tty.write(cmd+"\n")
	sleep(0.1)
	return tty.readline()

def print_help():
	string = " █▀▀█ ▒█▀▀█ ▒█▀▀▀█ 　 ▀▀█▀▀ ▒█▀▀▀█ ▒█▀▀▀█ ▒█░░░ ▒█▀▀▀█\n▒█░▄▄ ▒█▄▄█ ░▀▀▀▄▄ 　 ░▒█░░ ▒█░░▒█ ▒█░░▒█ ▒█░░░ ░▀▀▀▄▄\n▒█▄▄█ ▒█░░░ ▒█▄▄▄█ 　 ░▒█░░ ▒█▄▄▄█ ▒█▄▄▄█ ▒█▄▄█ ▒█▄▄▄█\n"

	string += "\nPMTK module:\n"
	string += "--start-logging\n\tGPS module starts recording frame\n"
	string += "--stop-logging\n\tModule stops recording frames\n"
	string += "--erase-flash\n\tErases frames stored into internal memory\n"
	
	string += "\nPMTK module [advanced]\n"
	string += "--baud\n\tSet GPS serial rate [9600,57600] b/s\n"
	string += "--fix-rate\n\tSet LED fix blink rate\n"
	string += "--nmea-rate\n\tSet GPS frames update rate [10Hz,5Hz,2Hz,1Hz,200mHz,100mHz]\n"

	string += "\nNMEA data:\n"
	string += "--nmea-to-kml\n\tConverts .nmea file to .kml file (google earth, ..)\n"
	string += "--nmea-to-gpx\n\tConverts .nmea file to .gpx file (Garmin, etc..)\n"

	print(string)

# Converts parsed coordinates to degrees/min/secs
def coord_to_deg_min(coord):
	#2503.6319 i.e ddmm.mmmm: 25°03.6319' = 25°03'37,914"
	deg = coord.split(".")[0][0:1]
	min = coord.split(".")[0][2:3]
	secs = coord.split(".")[1]
	return [deg,min,secs]

def knots_to_kmph(knots):
	mph = knots*1.15078
	return mph*1.60934

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

# Converts .nmea file into .kml file
def nmea_to_kml(nmea, kml):
	nmeafd = open(nmea, "r")
	kmlfd = open(kml, "w")

	# initialize kml file
	kmlfd.write('<?xml version="1.0" encoding="UTF-8"?>\n')
	kmlfd.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
	kmlfd.write(' <Document>\n')

	# set one style for polygons drawing
	# declare a style to group waypoints
	kmlfd.write('\t<Style id="greenPolyLine">\n')
	kmlfd.write('\t\t<LineStyle>\n')
	kmlfd.write('\t\t\t<color>7fff00ff</color>\n')
	kmlfd.write('\t\t\t<width>4</width>\n')
	kmlfd.write('\t\t</LineStyle>\n')
	kmlfd.write('\t</Style>\n')

	for line in nmeafd:
		GPS = None
		line = line.strip() # cleanup
		if not(line):
			continue

		if (line.startswith("$GPGGA")):
			GPS = GPGGA(line)
		elif (line.startswith("$GPRMC")):
			GPS = GPRMC(line)
		else:
			continue

		if (GPS is not None):
			if (GPS.get_lat() == None):
				continue

			kmlfd.write('\t<Placemark>\n')
			kmlfd.write("\t  <altitudeMode>relativeToGround</altitudeMode>\n")

			kmlfd.write('\t  <TimeStamp>\n')
			if (GPS._type() == "GPRMC"):
				d = GPS.get_date()
				day = d[0:1]
				month = d[2:3]
				year = d[4:5]
			else:
				d = date.today()
				year = str(d.year)
				month = str(d.month)
				day = str(d.day)

			utc = GPS.get_utc()
			h = utc.split(".")[0][0:1]
			m = utc.split(".")[0][2:3]
			s = utc.split(".")[0][4:5]

			kmlfd.write('\t  <when>20{:s}-{:s}-{:s}T{:s}:{:s}:{:s}Z</when>\n'.format(
				year,month,day,h,m,s	
			))
			kmlfd.write('\t  </TimeStamp>\n')

			kmlfd.write('\t  <styleUrl>#greenPolyLine</styleUrl>\n')

			kmlfd.write('\t  <Point>\n')
			kmlfd.write('\t\t<coordinates>{:s},{:s},{:s}</coordinates>\n'.format(
				GPS.get_lat()[0],GPS.get_long()[0],GPS.get_alt()
			))
			kmlfd.write('\t  </Point>\n')
			kmlfd.write('\t</Placemark>\n')

	# finalize kml file 
	kmlfd.write(' </Document>\n')
	kmlfd.write('</kml>\n')

	nmeafd.close()
	kmlfd.close()
	print("NMEA file {:s} content converted to KML in {:s}".format(nmea,kml))

def nmea_to_gpx(nmea, gpx):
	nmeafd = open(nmea,"r")
	gpxfd = open(gpx,"w")

	gpxfd.write('<?xml version="1.0" encoding="UTF-8" standalone="no" ?>\n')
	gpxfd.write('<gpx xmlns="http://www.topografix.com/GPX/1/1" creator="byHand" version="1.1"\n')
	gpxfd.write('  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n') 
	gpxfd.write('  xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">\n')

	for line in nmeafd:
		GPS = None
		line = line.strip() # cleanup
		if not(line):
			continue
		
		if (line.startswith("$GPGGA")):
			GPS = GPGGA(line)
		elif (line.startswith("$GPRMC")):
			GPS = GPRMC(line) 
		else:
			continue

		if (GPS is not None):
			gpxfd.write('<wpt lat="{:s}" lon="{:s}">\n'.format(GPS.get_lat()[0],GPS.get_long()[0]))
			gpxfd.write('\t<ele>{:s}</ele>\n'.format(GPS.get_alt()))
			if (GPS._type() == "GPRMC"):
				date = GPS.get_date()
				day = date[0:1]
				month = date[2:3]
				year = date[4:5]

				utc = GPS.get_utc()
				h = utc.split(".")[0][0:1]
				m = utc.split(".")[0][2:3]
				s = utc.split(".")[0][4:5]

				gpxfd.write('\t<time>20{:s}-{:s}-16T{:s}:{:s}:{:s}Z</time>\n'
					.format(year,month,day,h,m,s)
				)
			
			gpxfd.write('</wpt>\n')

	gpxfd.write('</gpx>')
	nmeafd.close()
	gpxfd.close()
	print("NMEA file {:s} content converted to GPX in {:s}".format(nmea,gpx))
	
# opens serial port
def open_serial(tty):
	ser = serial.Serial(tty)
	ser.open()
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

def main(argv):
	argv = argv[1:]

	if (len(argv) == 0):
		print_help()
		return -1

	for flag in argv:
		print(flag)
		
		if flag == "--start-logging":
			print(write_cmd(open_serial(argv[0]), PMKT_START_LOGGER))
		
		elif flag == "--stop-logging":
			ser = open_serial()
			print(write_cmd(open_serial(argv[0]), PMKT_STOP_LOGGER))

		elif flag == "--erase-flash":
			c = input("Are you sure? [Y/N]")
			if (c == "Y"):
				ser = open_serial()
				print(write_cmd(open_serial(argv[0]), PMKT_FLASH))

		elif flag == "--baud":
			b = input("Select baud [9600;57600]")
			#print(write_cmd(open_serial(argv[0],*),b)

		elif flag == "--rate":
			r = input("Set GPS frames rate [100mHz, 200mHz, 1Hz, 2Hz, 5Hz, 10Hz]")
			r.lower()

			if r == "100mhz":
				cmd = PMTK_SET_NMEA_UPDATE_100_MILLIHERTZ
			elif r == "200mhz":
				cmd = PMTK_SET_NMEA_UPDATE_200_MILLIHERTZ
			elif r == "1hz":
				cmd = PMTK_SET_NMEA_UPDATE_1HZ
			elif r == "2hz":
				cmd = PMTK_SET_NMEA_UPDATE_2HZ
			elif r == "5hz":
				cmd = PMTK_SET_NMEA_UPDATE_5HZ
			elif r == "10hz":
				cmd = PMTK_SET_NMEA_UPDATE_10HZ
			else:
				cmd = PMTK_SET_NMEA_UPDATE_1HZ
				print("Rate {:s} is not supported")
				print("Switching back to 1 Hz default rate")
			print(write_cmd(open_serial(argv[0]), cmd))

		elif flag == "--nmea-to-kml":
			fp = input("Set input file path..\n")
			nmea_to_kml(fp, fp.split(".")[0]+".kml")

		elif flag == "--nmea-to-gpx":
			fp = input("Set input file path..\n")
			nmea_to_gpx(fp, fp.split(".")[0]+".gpx")
		
		elif flag == "--help":
			print_help()
			return 0

		elif flag == "--h":
			print_help()
			return 0

		elif flag == "help":
			print_help()
			return 0

main(sys.argv)
