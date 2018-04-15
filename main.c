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

#define LED_UART	BIT0
#define RXD			BIT1 // UART: Rx
#define TXD			BIT2 // UART: Tx
#define LED_ISR	BIT6

#define BUFSIZE	16

volatile int tx_ptr;
volatile uint8_t tx_done;
int bytes_to_send;
char tx_buf[128];

//volatile int rx_ptr;
//int bytes_received;
//char rx_buf[128];

void init_gpio(void);
void init_uart(void);
void init_timers(void);
void init_platform(void);

int main(int argc, char **argv){
	init_platform();

	tx_ptr = 0;
	tx_done = 0x00;
	strcpy(tx_buf, "\r\nHello from MSP430\r\n");
	bytes_to_send = strlen(tx_buf);
	UC0IE |= UCA0TXIE; // TX IE
	while(!tx_done);

	tx_ptr = 0;
	strcpy(tx_buf, "Line2 from MSP430\r\n");
	bytes_to_send = strlen(tx_buf);
	UC0IE |= UCA0TXIE; // TX IE
	while(!tx_done); 

	while(1);
	return 0;
}

void init_platform(void){
	if (CALBC1_1MHZ == 0xff || CALDCO_1MHZ == 0xff){while(1);}
	WDTCTL = WDTPW + WDTHOLD;
	BCSCTL1 = CALBC1_1MHZ;
	DCOCTL = CALDCO_1MHZ;

	init_gpio();
	init_timers();
	init_uart();

	_BIS_SR(GIE); // allow all IE
}

void init_timers(void){
	TACTL |= MC_0; // stop
	TACTL = TASSEL_2 + ID_2 + TAIE; // SMCLK
	CCR0 = 10000;
	CCTL0 |= CCIE; // CCR0 IE
	TACTL |= MC_2; // continuous
}

void init_gpio(void){
// unused ports
	P2DIR = 0xff;
	P2OUT &= 0x00; 

	P1DIR = 0xff;
	P1SEL |= RXD+TXD; // special mode
	P1SEL2 |= RXD+TXD; // special mode

	P1OUT = 0x00;
}

void init_uart(void){
	UCA0CTL1 |= UCSSEL_2; // SMCLK
	UCA0BR0 = 0x08; // 1MHz 115200
	UCA0BR1 = 0x00; // 1MHz 115200
	UCA0MCTL = UCBRS2 + UCBRS0;
	UCA0CTL1 &= ~UCSWRST;
	//UC0IE |= UCA0RXIE; // RX IE
	UC0IE &= ~UCA0TXIE; // disable TX ISR
}

#pragma vector = TIMER0_A0_VECTOR
__interrupt void CCR0_ISR(void){
	P1OUT = ~LED_ISR;
}

#pragma vector = USCIAB0RX_VECTOR
__interrupt void USCI0RX_ISR(void){
	P1OUT |= LED_UART;

	if (UCA0RXBUF == 'a'){
		UC0IE |= UCA0TXIE; // enable TX ISR
		//UCA0TXBUF = string[i++];
	}

	P1OUT &= ~LED_UART;
}

#pragma vector = USCIAB0TX_VECTOR
__interrupt void USCI0TX_ISR(void){
	P1OUT |= LED_UART;
	UCA0TXBUF = tx_buf[tx_ptr];
	if (tx_ptr == bytes_to_send-1){ // tx done
		UC0IE &= ~UCA0TXIE; // disable TX ISR
		P1OUT &= ~LED_UART;
		tx_done |= 0x01;
	} else
		tx_ptr++;
}
