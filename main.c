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

#include <msp430g2553.h>

#define LED1 	BIT0
#define LED2	BIT6

void init_gpio(void);
void init_platform(void);

int main(int argc, char **argv){
	init_platform();
	while(1);
	return 0;
}

void init_platform(void){
	if (CALBC1_1MHZ == 0xff || CALDCO_1MHZ == 0xff){while(1);}
	WDTCTL = WDTPW + WDTHOLD;
	BCSCTL1 = CALBC1_1MHZ;
	DCOCTL = CALDCO_1MHZ;

	TACTL |= MC_0; // stop
	TACTL = TASSEL_2 + ID_2 + TAIE;
	CCR0 = 10000;
	TACTL |= MC_2; // continuous
	CCTL0 |= CCIE;
	_BIS_SR(GIE);
	init_gpio();
}

void init_gpio(void){
	P1DIR = 0xff;
	P1OUT = 0x00;
}

#pragma vector = TIMER0_A0_VECTOR // CCR0 routine
__interrupt void TimerA(void){
	P1OUT = ~P1OUT;
}
