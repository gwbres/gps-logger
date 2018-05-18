#ifndef __GPS_H__
#define __GPS_H__

#include <stdint.h>

#define PMTK_SET_BAUD_57600 "$PMTK251,57600*2C\r\n"
#define PMTK_SET_BAUD_9600 "$PMTK251,9600*17\r\n"

#define PMTK_NMEA_RMC_ONLY			0
#define PMTK_NMEA_ONLY_RMC_GGA 	1
#define PMTK_NMEA_ALL_DATA			2
#define PMTK_NMEA_OFF				3

#define PMTK_SET_NMEA_OUTPUT_RMC_ONLY "$PMTK314,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*29\r\n"
#define PMTK_SET_NMEA_OUTPUT_RMC_GGA "$PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*28\r\n"
#define PMTK_SET_NMEA_OUTPUT_ALL_DATA "$PMTK314,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0*28\r\n"
#define PMTK_SET_NMEA_OUTPUT_OFF "$PMTK314,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*28\r\n"

#define PMTK_FIX_RATE_100mhz   0
#define PMTK_FIX_RATE_200mhz   1
#define PMTK_FIX_RATE_1hz      2
#define PMTK_FIX_RATE_2hz      3
#define PMTK_FIX_RATE_5hz      4
#define PMTK_FIX_RATE_10hz     5

#define PMTK_API_SET_FIX_CTL_100_MILLIHZ  "$PMTK300,10000,0,0,0,0*2C\r\n" 
#define PMTK_API_SET_FIX_CTL_200_MILLIHZ  "$PMTK300,5000,0,0,0,0*18\r\n" 
#define PMTK_API_SET_FIX_CTL_1HZ  "$PMTK300,1000,0,0,0,0*1C\r\n"
#define PMTK_API_SET_FIX_CTL_5HZ  "$PMTK300,200,0,0,0,0*2F\r\n"

#define PMTK_START_LOG  "$PMTK185,0*22\r\n"
#define PMTK_STOP_LOG "$PMTK185,1*23\r\n"
#define PMTK_ERASE_FLASH "$PMTK184,1*22\r\n"

#define PMTK_STAND_BY "$PMTK161,0*28\r\n"

// Sets PMTK module's baud rate
// baud: [9600;57600]
void GPS_set_baud(int baud);

// PMTK module starts recording NMEA frames
void GPS_start_logging(void);

// pauses PMTK frames storage 
void GPS_stop_logging(void);

// flushes PMTK module internal flash memory
void GPS_erase_flash(void);

// sets PMTK module FIX LED blink rate to adjust power consumption
// rate: [PMTK_FIX_RATE_100mhz;_200mhz;_5hz;_1hz;_2hz;_10hz]
void GPS_set_fixblink_rate(int rate);

// parses & returns current flash usage
// from requested status
int GPS_flash_usage(char *status);

// controls PMTK module NMEA framing
// output: PMTK_NMEA_OFF: no frames to be output
// output: PMTK_NMEA_RMC_ONLY: only RMC frames
// output: PMTK_NMEA_ONLY_RMC_GGA: disable any other NMEA frames
// output: PMTK_NMEA_ALL_DATA: allow all NMEA frames
void GPS_NMEA_output(int output);

void GPS_stand_by(void);
void GPS_wake_up(void);

#endif
