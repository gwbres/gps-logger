#include <string.h>
#include <msp430g2553.h>
#include "GPS.h"

extern char tx_buf[128]; 
extern volatile int bytes_to_send;
extern volatile int tx_ptr;

void GPS_set_baud(int baud){
	tx_ptr = 0; // rst

	switch (baud) {
		case 57600:
			strcpy(tx_buf, PMTK_SET_BAUD_57600);
			break;

		default:
		case 9600:
			strcpy(tx_buf, PMTK_SET_BAUD_9600);
			break;
	}

	bytes_to_send = strlen(tx_buf)+2;
	UC0IE |= UCA0TXIE;
	while (UCA0STAT & UCBUSY);
}

void GPS_start_logging(void){
	tx_ptr = 0;
	strcpy(tx_buf, PMTK_STARTLOG);
	bytes_to_send = strlen(tx_buf)+2;
	UC0IE |= UCA0TXIE;
	while (UCA0STAT & UCBUSY);
}

void GPS_stop_logging(void){
	tx_ptr = 0;
	strcpy(tx_buf, PMTK_STOPLOG);
	bytes_to_send = strlen(tx_buf)+2;
	UC0IE |= UCA0TXIE;
	while (UCA0STAT & UCBUSY);
}

void GPS_erase_flash(void){
	tx_ptr = 0;
	strcpy(tx_buf, PMTK_ERASE_FLASH);
	bytes_to_send = strlen(tx_buf)+2;
	UC0IE |= UCA0TXIE;
	while (UCA0STAT & UCBUSY);
}

void GPS_set_fixblink_rate(int rate){
	tx_ptr = 0;

	switch (rate) {
		case PMTK_FIX_RATE_100mhz:
			strcpy(tx_buf, PMTK_API_SET_FIX_CTL_100_MILLIHZ);
			break;

		case PMTK_FIX_RATE_200mhz:
			strcpy(tx_buf, PMTK_API_SET_FIX_CTL_200_MILLIHZ);
			break;

		case PMTK_FIX_RATE_5hz:
			strcpy(tx_buf, PMTK_API_SET_FIX_CTL_5HZ);
			break;

		default:
		case PMTK_FIX_RATE_1hz:
			strcpy(tx_buf, PMTK_API_SET_FIX_CTL_1HZ);
			break;
	}
	
	strcpy(tx_buf, PMTK_STANDBY);
	bytes_to_send = strlen(tx_buf)+2;
	UC0IE |= UCA0TXIE;
	while (UCA0STAT & UCBUSY);
}

void GPS_stand_by(void){
	tx_ptr = 0;
	strcpy(tx_buf, PMTK_STANDBY);
	bytes_to_send = strlen(tx_buf)+2;
	UC0IE |= UCA0TXIE;
	while (UCA0STAT & UCBUSY);
}

void GPS_NMEA_output(int output){
	tx_ptr = 0;

	switch (output) {
		case PMTK_NMEA_OFF:
			strcpy(tx_buf, PMTK_SET_NMEA_OUTPUT_OFF);
			break;

		case PMTK_NMEA_ONLY_RMC_GGA:
			strcpy(tx_buf, PMTK_SET_NMEA_OUTPUT_RMC_GGA);
			break;

		default:
		case PMTK_NMEA_ALL_DATA:
			strcpy(tx_buf, PMTK_SET_NMEA_OUTPUT_ALL_DATA);
			break;
	}
	
	bytes_to_send = strlen(tx_buf)+2;
	UC0IE |= UCA0TXIE;
	while (UCA0STAT & UCBUSY);
}

void GPS_antenna_mode(int mode){
	tx_ptr = 0;
	
	switch (mode) {
		case PMTK_USE_ANTENNA:
			strcpy(tx_buf, PGCMD_USE_ANTENNA);
			break;

		default:
		case PMTK_NO_ANTENNA:
			strcpy(tx_buf, PGCMD_NO_ANTENNA);
			break;
	}
	
	bytes_to_send = strlen(tx_buf)+2;
	UC0IE |= UCA0TXIE;
	while (UCA0STAT & UCBUSY);
}

void GPS_enable_WAAS(void){
	tx_ptr = 0;
	strcpy(tx_buf, PMTK_ENABLE_WAAS);
	bytes_to_send = strlen(tx_buf)+2;
	UC0IE |= UCA0TXIE;
	while (UCA0STAT & UCBUSY);
}

void GPS_enable_SBAS(void){
	tx_ptr = 0;
	strcpy(tx_buf, PMTK_ENABLE_SBAS);
	bytes_to_send = strlen(tx_buf)+2;
	UC0IE |= UCA0TXIE;
	while (UCA0STAT & UCBUSY);
}
