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

// P1
#define RXD 			BIT1
#define TXD 			BIT2
// P2
#define START_BTN		BIT2
#define STOP_BTN		BIT1
#define ERASE_BTN		BIT0
#define LED 			BIT3

#define BUFSIZE	128
volatile int tx_ptr;
volatile int bytes_to_send;
char tx_buf[BUFSIZE];

volatile char rx_done;

volatile uint8_t _user_action;
volatile uint8_t debouncing;
volatile int debounce_cnt;
#define DEBOUNCE_CNT_MAX	1024

#ifdef LOW_POWER
	volatile int wdcnt;
	#define WDT_NO_ACT	256
#endif

void init_gpio(void);
void init_uart(void);
void init_timers(void);
void init_platform(void);
void wait_for_answer(void);

int main(int argc, char **argv){
	init_platform();

	while(1){
		if (_user_action & 0x01){
			// P2OUT |= GPS_EN;
			GPS_start_logging();
			wait_for_answer();
			_user_action &= 0x00;
			_BIS_SR(GIE|P1IE|LPM0_bits); // hibernate
		} 
		/*else if (_user_action & 0x02){
			GPS_stop_logging();
			wait_for_answer();
			// P2OUT &= ~GPS_EN;
			_user_action &= 0x00;

		} else if (_user_action & 0x04){
			GPS_erase_flash();
			wait_for_answer();
			_user_action &= 0x00;
		}*/
	}
	return 0;
}

void init_platform(void){
	if (CALBC1_1MHZ == 0xff || CALDCO_1MHZ == 0xff){while(1);}
	BCSCTL1 = CALBC1_1MHZ;
	DCOCTL = CALDCO_1MHZ;
	WDTCTL = WDTPW + WDTHOLD;

	init_gpio();
	init_timers();
	init_uart();

	_BIS_SR(GIE|P1IE);
	GPS_NMEA_output(PMTK_NMEA_OFF); // reduces power drawn by module
	_BIS_SR(GIE|P1IE|LPM0_bits); // hibernate
}

void init_timers(void){
	TACTL |= MC_0; // stop
	TACTL = TASSEL_2 + ID_2 + TAIE; // SMCLK
	TA0R = 0;
	// debouncer will run for
	// (CCR0+1)*DEBOUNCE_CNT_MAX/1E6 [s]
	CCR0 = 128-1;
	CCTL0 |= CCIE; // CCR0 IE
	TACTL |= MC_2; // continuous op. mode
}

void init_gpio(void){
	P1DIR |= RXD+TXD;
	P1SEL |= RXD+TXD; // USCI requires 
	P1SEL2 |= RXD+TXD; // special opmode
	P1OUT &= 0x00;

	//P2DIR |= GPS_EN;
	// P2OUT |= GPS_EN;
	P2DIR |= LED;
	P2OUT &= 0x00;
	P2IE |= START_BTN+STOP_BTN+ERASE_BTN; // enable required ISR
	// clear related flags
	P2IFG &= ~START_BTN; 
	P2IFG &= ~STOP_BTN;
	P2IFG &= ~ERASE_BTN;
	// initialize
	_user_action &= 0x00;
	debounce_cnt = 0;
	debouncing &= 0x00;
}

void init_uart(void){
	UCA0CTL1 |= UCSSEL_2; // SMCLK
	UCA0BR0 = 0x08; // 115200b/s @1M
	UCA0BR1 = 0x00; // 115200b/s @1M
	UCA0MCTL = UCBRS2 + UCBRS0; // 5% modulation
	UCA0CTL1 &= ~UCSWRST;
	// disable ISR 
	UC0IE &= ~UCA0TXIE;
	UC0IE &= ~UCA0RXIE;
	rx_done &= 0x00;
}

void wait_for_answer(void){
/* TODO should wait proper answer 
	rx_done &= 0x00;
	UC0IE |= UCA0RXIE;
	while (!rx_done);
*/
	__delay_cycles(0xffff);
}

#pragma vector = TIMER0_A0_VECTOR
__interrupt void CCR0_ISR(void){
	if (debouncing){
		if (debounce_cnt < DEBOUNCE_CNT_MAX-1){
			debounce_cnt++;
			P2OUT ^= LED;
		} else {
			debounce_cnt &= 0;
			debouncing &= 0x00;
		}
	}
	TA0R = 0;
}

#pragma vector = PORT2_VECTOR
__interrupt void P2_ISR(void){
	if (!debouncing){ 
		debounce_cnt &= 0;
		debouncing |= 0x01;
		P2OUT ^= LED;
		__bic_SR_register_on_exit(LPM0_bits);

		if (P2IFG & START_BTN)
			_user_action |= 0x01;
		else if (P2IFG & STOP_BTN)
			_user_action |= (0x01<<1);
		else if (P2IFG & ERASE_BTN)
			_user_action |= (0x01<<2);
	}
	
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

#pragma vector = USCIAB0RX_VECTOR
__interrupt void USCI0RX_ISR(void){
	if (UCA0RXBUF == '\n'){ // PMTK module answered
		rx_done |= 0x01;
		UC0IE &= ~UCA0RXIE; // we're done
	} 
}
