#include <string.h>
#include <msp430g2553.h>
#include "GPS.h"

extern char tx_buf[128]; 
extern volatile int bytes_to_send;
extern volatile int tx_ptr;

void GPS_start_logging(void){
	tx_ptr = 0;
	strcpy(tx_buf, PMTK_START_LOG);
	bytes_to_send = strlen(tx_buf)+2;
	UC0IE |= UCA0TXIE;
	while (UCA0STAT & UCBUSY);
}

void GPS_stop_logging(void){
	tx_ptr = 0;
	strcpy(tx_buf, PMTK_STOP_LOG);
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

void GPS_stand_by(void){
	tx_ptr &= 0;
	strcpy(tx_buf, PMTK_STAND_BY);
	bytes_to_send = strlen(tx_buf)+2;
	while (UCA0STAT & UCBUSY);
}

void GPS_wake_up(void){
	tx_ptr &= 0;
	strcpy(tx_buf, "Hi\n"); // 1 byte will suffice to wake module up
	bytes_to_send = strlen(tx_buf)+1;
	UC0IE |= UCA0TXIE;
	while (UCA0STAT & UCBUSY);
	__delay_cycles(16383); // give module some time
}
