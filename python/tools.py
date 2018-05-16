#! /usr/bin/env python3

import sys
import time
import math
import serial
import datetime

from PMTK import *
from GPSTrack import *
from Waypoint import *

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
	string += "--locus-to-kml\n\tConverts .locus data to .kml file\n"
	string += "--locus-to-gpx\n\tConverts .locus data to .gpx file\n"

	string += "\nGPS Viewer:\n"
	string += "--view-coordinates\n\tDraws waypoints found in .nmea, .kml, .gpx data file onto map\n"
	string += "--elevation-profile\n\tDisplay elevation profile\n"

	print(string)

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
		elif flag == "--locus-to-kml":
			commands.append("locus-to-kml")
		elif flag == "--locus-to-gpx":
			commands.append("locus-to-gpx")

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
			GPSTrack(fp).toKML(fp.split('.')[0]+'.kml')
		
		elif (command == "nmea-to-gpx"):
			if (len(files) == 0):
				fp = input("Set input file path..\n")
			else:
				fp = files[0]
				files = files[1:]
			GPSTrack(fp).toGPX(fp.split('.')[0]+'.gpx')

		elif (command == "locus-to-kml"):
			if (len(files) == 0):
				fp = input("Set input file path..\n")
			else:
				fp = files[0]
				files = files[1:]
			GPSTrack(fp).toKML(fp.split('.')[0]+'.kml')

		elif (command == "locus-to-gpx"):
			if (len(files) == 0):
				fp = input("Set input file path..\n")
			else:
				fp = files[0]
				files = files[1:]
			GPSTrack(fp).toGPX(fp.split('.')[0]+'.gpx')

		elif (command == "viewer"):
			if (len(files) == 0):
				fp = input("Set input file path..\n")
			else:
				fp = files[0]
				files = files[1:]
			GPSTrack(fp).drawOnMap(elevationProfile=view_profile)
		
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
