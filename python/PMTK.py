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
