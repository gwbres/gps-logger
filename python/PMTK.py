import time
import serial

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
PMTK_STATUS_QUERY = "$PMTK183*38\r\n"
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

class PMTK:

	def __init__(self, dev):
		self.serial = self.openSerial(dev, 9600)

	def status(self):
		"""
		Returns GPS module status
		"""
		status = self.sendCommand(PMTK_STATUS_QUERY)
		string = "Status:\n"
		string += "SN {:s}\n".format(status.split(",")[1])
			
		logType = int(status.split(",")[2])
		string += "Log type: "
		if (logType == 0):
			string += "locus overlap\n"
		else:
			string += "locus fullstop\n"

		try:
			logMode = int(status.split(',')[3])
		except ValueError:
			logMode = int(status.split(',')[3],16)

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

		string += 'locus content: {:d}\n'.format(int(status.split(',')[4]))
		string += 'locus interval: {:d} [s]\n'.format(int(status.split(',')[5]))
		string += 'locus distance: {:d} [m]\n'.format(int(status.split(',')[6]))
		string += 'locus speed: {:d} [m/s]\n'.format(int(status.split(',')[7]))
		string += 'locus logging: {:d}\n'.format(not(bool(status.split(',')[8])))
		string += "Data records: {:s}\n".format(status.split(',')[9])
		string += "{:s}% flash used:\n".format(status.split(",")[10].split("*")[0])
		return string

	def startLogger(self):
		"""
		Starts built in locus logger
		"""
		answer = self.sendCommand(PMTK_START_LOG)
		if (answer == "$PMTK001,185,3*3C"):
			print("Locus logger has been started")
		else:
			print("Error: {:s}".format(answer))
			
	def stopLogger(self):
		print("answer: {:s}".format(self.serial.sendCommand(PMTK_STOP_LOG)))
	
	def dumpFlash(self, fp):
		"""
		Dumps internal flash content
		into desired file
		"""
		print("Turning NMEA off..\n")
		self.sendCommand(PMTK_SET_NMEA_OUTPUT_OFF)
		print("Dumping flash content..\n")
		self.sendCommand(PMTK_DUMP_FLASH)

		fd = open(fp, "w")
		while (True):
			try:
				locus = self.serial.readline().decode("utf-8")
				print(locus)
				fd.write(locus+"\n")
			except SerialTimeout:
				break
		fd.close()

	def eraseFlash(self):
		"""
		Erases internal flash content
		"""
		c = input("About to erase flash content.. are you sure? [Y/N]")
		if (c == "Y"):
			answer = self.sendCommand(PMTK_ERASE_FLASH).strip()
			if (answer == "$PMTK001,184,3*3D"):
				print("Flash has been erased")
			else:
				print("Error")
		else:
			print("Aborting")
	
	def setLocusRate(self, rate):
		if (not(rate in ["1s","5s","15s"])):
			print("Rate {:s} is not supported".format(rate))
			print("Aborting..")
		else:
			if rate == "1s":
				cmd = PMTK_LOCUS_1_SECONDS 
			elif rate == "5s":
				cmd = PMTK_LOCUS_5_SECONDS 
			elif rate == "15s":
				cmd = PMTK_LOCUS_15_SECONDS 
			print(self.sendCommand(cmd).strip())
	
	def setNMEAMode(self, output):
		"""
		Sets type of NMEA frames
		to be output by GPS module
		"""
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

			answer = self.sendCommand(cmd)
			if (answer == "$PMTK001,314,3*36"):
				print("NMEA mode set to {:s}".format(output))
			else:
				print("Error: {:s}".format(answer))

	def setNMEARate(self, rate):
		if (rate == "100mHz"):
			cmd = PMTK_SET_NMEA_UPDATE_100_MILLIHERTZ
		elif (rate == "200mHz"):
			cmd = PMTK_SET_NMEA_UPDATE_200_MILLIHERTZ
		elif (rate == "1Hz"):
			cmd = PMTK_SET_NMEA_UPDATE_1HZ
		elif (rate == "2Hz"):
			cmd = PMTK_SET_NMEA_UPDATE_2HZ
		elif (rate == "5Hz"):
			cmd = PMTK_SET_NMEA_UPDATE_5HZ
		elif (rate == "10Hz"):
			cmd = PMTK_SET_NMEA_UPDATE_10HZ
		else:
			cmd = PMTK_SET_NMEA_UPDATE_1HZ
			print("Rate {:s} is not supported".format(rate))
			print("Switching back to 1 Hz default rate")
			
		answer = self.sendCommand(cmd).strip()
		if (answer == "$PMTK001,220,3*30"):
			print("Success")
		else:
			print("Error: {:s}".format(answer))

	def getFixBlinkRate(self, rate):
		"""
		Returns current LED fix blinking rate
		"""
		print(self.sendCommand(PMTK_API_Q_FIX_CTRL).strip())
	
	def sendCommand(self, cmd):
		"""
		Sends command over serial port
		and returns answer
		"""
		self.serial.write(bytes(cmd+"\n",encoding="utf-8"))
		time.sleep(1)
		return self.serial.readline().decode("utf-8").strip()

	def openSerial(self, tty, baudrate):
		"""
		Opens a serial port
		for 8N1 UART communication
		at specified baud rate
		"""
		ser = serial.Serial(tty)
		ser.baudrate = baudrate
		ser.flushInput()
		ser.flushOutput()
		# 8N1
		ser.bytesize = serial.EIGHTBITS
		ser.parity = serial.PARITY_NONE
		ser.stopbits = serial.STOPBITS_ONE
		ser.timeout = 0
		ser.xonxoff = 0
		ser.rtscts = False
		ser.dsrdtr = False
		ser.writeTimeout = 2
		ser.readTimeout = 2
		return ser
