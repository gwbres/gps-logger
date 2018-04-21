#! /usr/bin/env python3

import sys
import serial

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

def enable_SBAS(tty):
	write_cmd(tty, PMTK_ENABLE_SBAS)

def enable_WAAS(tty):
	write_cmd(tty, PMTK_ENABLE_WAAS)

def allow_external_antenna(tty, allowed):
	if (allowed):
		cmd = PGCMD_ANTENNA
	else:
		cmd = PGCMD_NOANTENNA
	write_cmd(tty, cmd)

def print_help():
	string = " █▀▀█ ▒█▀▀█ ▒█▀▀▀█ 　 ▀▀█▀▀ ▒█▀▀▀█ ▒█▀▀▀█ ▒█░░░ ▒█▀▀▀█\n▒█░▄▄ ▒█▄▄█ ░▀▀▀▄▄ 　 ░▒█░░ ▒█░░▒█ ▒█░░▒█ ▒█░░░ ░▀▀▀▄▄\n▒█▄▄█ ▒█░░░ ▒█▄▄▄█ 　 ░▒█░░ ▒█▄▄▄█ ▒█▄▄▄█ ▒█▄▄█ ▒█▄▄▄█\n\n"
	string += "--start-logging\n\tGPS module starts recording frame\n\n"
	string += "--stop-logging\n\tModule stops recording frames\n\n"
	string += "--erase-flash\n\tErases frames stored into internal memory\n\n"
	string += "--dump\n\tDumps all frames stored in internal memory into a file\n\n"
	string += "\n\t>>> advanced\n"
	string += "--fix-rate\n\tSet GPS locking rate\n\n"
	string += "--rate\n\tSet GPS frames update rate [10Hz,5Hz,2Hz,1Hz,200mHz,100mHz]\n"
	string += "--baud\n\tSet GPS serial rate [9600,57600] b/s\n"
	print(string)

# Dumps all nmea frames into a .nmea file
def dump_flash(tty, nmea):
	print(write_cmd(PMKT_STOP_LOGGER))

	fd = open(nmea)
	while (tty.readline()):
		fd.write(line+"\n")
	fd.close()

# Converts .nmea file into .kml file
# to use in most graphical GPS coordinates displayers
# uses GPGGA frames only
def convert_to_kml(nmea, kml):
	extn = nmea.split(".")[-1]
	fnmea = open(nmea, "r")
	fkml = open(kml, "w")

	for line in fnmea:
		line = line.strip() # cleanup
		if not(line):
			continue

		# keep only GPGGA frames
		if not(line.startswith("$GPGGA")):
			continue

		NMEA = GPGGA(line)

		kml_content = "<when>T%(time_string)sZ</when>" % result
		kml_content = "<gx:coord>%(longitude)s %(latitude)s %(altitude)s</gx:coord>\n" % result
		kml.write(kml_content)

	fnmea.close()
	fkml.close()
	print("NMEA file {:s} content converted into KML in {:s}\n".format(nmea,kml))

def main(argv):
	argv = argv[1:]

	if (len(argv) == 0):
		print_help()
		return -1

	ser = serial.Serial(argv[0])
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

	for flag in argv[1:]:
		
		if flag == "--start-logging":
			print(write_cmd(PMKT_START_LOGGER))
		
		elif flag == "--stop-logging":
			print(write_cmd(PMKT_STOP_LOGGER))

		elif flag == "--erase-flash":
			c = input("Are you sure? [Y/N]")
			if (c == "Y"):
				print(write_cmd(PMKT_FLASH))

		elif flag == "--dump":
			dump_flash(ser)

		elif flag == "--baud":
			b = input("Select baud [9600;57600]")

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
			print(ser.write_cmd(cmd))
		
		elif flag == "--help":
			print_help()
		elif flag == "--h":
			print_help()
		elif flag == "help":
			print_help()

	ser.close()

main(sys.argv)
