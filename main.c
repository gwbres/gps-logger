/*
	Guillaume W. Bres, 2018  <guillaume.bressaix@gmail.com>

	Permission is hereby granted, free of charge, to any person obtaining a copy
	of this software and associated documentation files (the "Software"), to deal
	in the Software without restriction, including without limitation the rights
	to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
	copies of the Software, and to permit persons to whom the Software is
	furnished to do so, subject to the following conditions:
	The above copyright notice and this permission notice shall be included in
	all copies or substantial portions of the Software.
 
	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
	OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
	THE SOFTWARE.
*/

#include "GPS.h"
#include <string.h>
#include <msp430g2553.h>

#define LED				BIT0 // P1
#define RXD				BIT1 // P1 UART: Rx
#define TXD				BIT2 // P1 UART: Tx
#define START_BTN		BIT0 // P2
#define STOP_BTN		BIT1 // P2
#define ERASE_BTN		BIT2 // P2
volatile 

#define BUFSIZE	128
volatile int tx_ptr;
volatile int bytes_to_send;
char tx_buf[BUFSIZE];

#ifdef LOW_POWER
	volatile int wdcnt;
	#define WDT_NO_ACT	256
#endif

void init_gpio(void);
void init_uart(void);
void init_timers(void);
void init_platform(void);
void welcome(void);
void pmtk_module_tests(void);
	
int main(int argc, char **argv){
	init_platform();
	while(1);
	return 0;
}

void init_platform(void){
	uint16_t _mask = 0;

	if (CALBC1_1MHZ == 0xff || CALDCO_1MHZ == 0xff){while(1);}
	BCSCTL1 = CALBC1_1MHZ;
	DCOCTL = CALDCO_1MHZ;

#ifndef LOW_POWER
	WDTCTL = WDTPW + WDTHOLD;
#else
	WDTCTL = WDT_MDLY_32;
#endif

	init_gpio();
	init_timers();
	init_uart();
	_mask |= GIE;
	_mask |= P1IE;
#ifdef LOW_POWER
	wdcnt = 0;
	_mask |= LPM3_bits;
#endif
	_BIS_SR(_mask); 

	welcome();
	pmtk_module_tests();
}

void init_timers(void){
	TACTL |= MC_0; // stop
	TACTL = TASSEL_2 + ID_2 + TAIE; // SMCLK
	TA0R = 0;
	CCR0 = 10000;
	CCTL0 |= CCIE; // CCR0 IE
	TACTL |= MC_2; // continuous op. mode
}

void init_gpio(void){
	P1DIR |= LED;
	P1DIR |= RXD+TXD;
	P1SEL |= RXD+TXD; // USCI requires 
	P1SEL2 |= RXD+TXD; // special opmode
	P1OUT &= 0x00;

	P2OUT &= 0x00; 
	P2IE |= START_BTN+STOP_BTN+ERASE_BTN; // enable required ISR
	// clear related flags
	P2IFG &= ~START_BTN; 
	P2IFG &= ~STOP_BTN;
	P2IFG &= ~ERASE_BTN;
}

void init_uart(void){
	UCA0CTL1 |= UCSSEL_2; // SMCLK
	UCA0BR0 = 0x08; // 115200b/s @1M
	UCA0BR1 = 0x00; // 115200b/s @1M
	UCA0MCTL = UCBRS2 + UCBRS0; // 5% modulation
	UCA0CTL1 &= ~UCSWRST;
	UC0IE &= ~UCA0TXIE; // disable TX ISR
}

void welcome(void){
	tx_ptr = 0;
	strcpy(tx_buf, "\r\n| GPS logger v1.0 |\r\n");
	bytes_to_send = strlen(tx_buf)+4;
	UC0IE |= UCA0TXIE; // TX IE
	while (UCA0STAT & UCBUSY);
}

void pmtk_module_tests(void){
// baud:
	GPS_set_baud(9600);
	GPS_set_baud(57600);
// flash:
	GPS_start_logging();
	GPS_stop_logging();
	GPS_erase_flash();
// FIX:
	GPS_set_fixblink_rate(PMTK_FIX_RATE_100mhz);
	GPS_set_fixblink_rate(PMTK_FIX_RATE_200mhz);
	GPS_set_fixblink_rate(PMTK_FIX_RATE_1hz);
	GPS_set_fixblink_rate(PMTK_FIX_RATE_5hz);
// NMEA:
	GPS_NMEA_output(PMTK_NMEA_OFF);
	GPS_NMEA_output(PMTK_NMEA_ONLY_RMC_GGA);
	GPS_NMEA_output(PMTK_NMEA_ALL_DATA);
// others:
	GPS_stand_by();
	GPS_antenna_mode(PMTK_NO_ANTENNA);
	GPS_antenna_mode(PMTK_USE_ANTENNA);
	GPS_enable_WAAS();
	GPS_enable_SBAS();
}

#pragma vector = TIMER0_A0_VECTOR
__interrupt void CCR0_ISR(void){
	TA0R = 0;
}

#pragma vector = PORT2_VECTOR
__interrupt void P2_ISR(void){
	P1OUT ^= LED;
#ifdef LOW_POWER
	__bic_SR_register_on_exit(CPUOFF);
	WDTCTL = WDTPW + WDTHOLD;
#endif
	// clear flag
	if (P2IFG & START_BTN) P2IFG &= ~START_BTN;
	if (P2IFG & STOP_BTN) P2IFG &= ~STOP_BTN;
	if (P2IFG & ERASE_BTN) P2IFG &= ~ERASE_BTN;
}

#pragma vector = USCIAB0TX_VECTOR
__interrupt void USCI0TX_ISR(void){
	UCA0TXBUF = tx_buf[tx_ptr++];
	if (tx_ptr == bytes_to_send-1){ // tx done
		UC0IE &= ~UCA0TXIE; // disable TX ISR
	} 
}

#ifdef LOW_POWER
#pragma vector = WDT_VECTOR
__interrupt void watchdog_timer(void){
	if (wdcnt == WDT_NO_ACT-1){
		_BIS_SR(LPM3_bits + GIE); // LPM3 hibernation from now on
		WDTCTL = WDTPW + WDTHOLD; // kill WDT
		wdcnt = 0;
	} else
		wdcnt ++;
}
#endif
