/*
	Copyright (c) 2018 - Guillaume W. Bres  <guillaume.bressaix@gmail.com>

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

#include <string.h>
#include <msp430g2553.h>

#define LED_UART		BIT0
#define RXD				BIT1 // UART: Rx
#define TXD				BIT2 // UART: Tx
#define START_BTN		BIT3
#define STOP_BTN		BIT4
#define ERASE_BTN		BIT5

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
	welcome();

	_mask |= GIE;
	_mask |= P1IE;
#ifdef LOW_POWER
	wdcnt = 0;
	_mask |= LPM3_bits;
#endif
	_BIS_SR(_mask); 
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
	P2DIR = 0xff;
	P2OUT &= 0x00; 

	P1DIR |= LED_UART;
	P1DIR |= RXD+TXD;
	P1SEL |= RXD+TXD; // USCI requires 
	P1SEL2 |= RXD+TXD; // special opmode
	P1REN |= START_BTN; // internal pull up
	P1OUT &= 0x00;

	P1IE |= START_BTN; // enable ISR
	P1IES |= START_BTN; // falling edge
	P1IFG &= ~START_BTN; // clear flag
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
	int _head = 0;
	tx_ptr = 0;

	strcpy(tx_buf+_head, "\r\n\r\n------------------\r\n");
	_head += strlen("\r\n\r\n------------------\r\n");

	strcpy(tx_buf+_head, "| GPS logger v1.0 |\r\n");
	_head += strlen("| GPS logger v1.0 |\r\n");
	
	strcpy(tx_buf+_head, "------------------\r\n");
	_head += strlen("------------------\r\n");

	bytes_to_send = strlen(tx_buf);
	UC0IE |= UCA0TXIE; // TX IE
	while (UCA0STAT & UCBUSY);
}

#pragma vector = TIMER0_A0_VECTOR
__interrupt void CCR0_ISR(void){
	TA0R = 0;
}

#pragma vector = PORT1_VECTOR
__interrupt void P1_ISR(void){
#ifdef LOW_POWER
//	_BIS_CR(LPM3_bits);
	WDTCTL = WDTPW + WDTHOLD;
#endif
	tx_ptr = 0;
	strcpy(tx_buf, "P1.3 IRQ\n");
	bytes_to_send = strlen(tx_buf);
	UC0IE |= UCA0TXIE; // TX IE
	while (UCA0STAT & UCBUSY);
	
	P1IFG &= ~START_BTN; // clear IFG
}

#pragma vector = USCIAB0TX_VECTOR
__interrupt void USCI0TX_ISR(void){
	P1OUT |= LED_UART;
	UCA0TXBUF = tx_buf[tx_ptr++];
	
	if (tx_ptr == bytes_to_send-1){ // tx done
		UC0IE &= ~UCA0TXIE; // disable TX ISR
		P1OUT &= ~LED_UART;
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
