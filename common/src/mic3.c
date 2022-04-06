#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// #include <libbase/console.h>

#include "menu.h"

#include <generated/csr.h>

#define BUF_SIZE 0x2000
static unsigned short buf[BUF_SIZE];

static void mic3(unsigned delay) 
{

    if (delay > BUF_SIZE) {
        printf("Unsupported delay 0x%x samples\n", delay);
        return;
    }

    mic3_spi_clk_divider_write(4);
    //busy_wait(5);

    mic3_spi_loopback_mode_write(0);
    mic3_spi_cs_mode_write(0);

    printf("START MIC--->DAC\n");

    unsigned int p = 0;

    uint32_t gmax = 0;
    uint32_t gmin = 0xffffffff;
    uint32_t giter = 0;
    const uint32_t max_iter = 10;
    for (uint32_t j=0; j<max_iter; j++) {
        uint32_t max = 0;
        uint32_t min = 0xffffffff;

        printf("iter %u/%u\n", j, max_iter);

        for (int i=0; i<100000; i++) {
            /* Write byte on MOSI */
            //mic3_spi_mosi_write(0xabcd);
            /* Initiate SPI Xfer */
            mic3_spi_control_write(16<<8 | 0x1);
            /* Wait SPI Xfer to be done */
            uint32_t iter=0;
            while(mic3_spi_status_read() == 0) ++iter;
            giter = iter > giter ? iter : giter;
            //busy_wait(1);
            /* Read MISO */
            uint32_t v = (mic3_spi_miso_read() & 0x00000fff);
            max = v > max ? v : max;
            min = v < min ? v : min;
            //printf("%08lx\n", v);

#ifdef CSR_DAC_BASE
            // write old value in DAC
            dac_value_write(buf[p]);
#endif

            // write new value 
            buf[p] = v;

            // update circular buf ptr
            p++;
            if (p >= delay) p = 0;

            // fake a sample period approx. 1/20khz
            busy_wait_us(50);
        }
        printf("%08lx -- %08lx\n", min, max);
        gmax = max > gmax ? max : gmax;
        gmin = min < gmin ? min : gmin;
    }
    printf("GLOBAL: %08lx -- %08lx;    max iter %lu\n", gmin, gmax, giter);
}


static inline void audio_no_delay()      { mic3(0);      }
static inline void audio_15ms_delay()    { mic3(0x00ff); }
static inline void audio_250ms_delay()   { mic3(0x0fff); }
static inline void audio_500ms_delay()   { mic3(0x1fff); }
static inline void audio_1000ms_delay()  { mic3(0x3fff); }


static struct Menu MENU = {
    "Mic3 Test Menu",
    "mic3",
    {
     MENU_ITEM('p', "passthru audio", audio_no_delay),
#ifdef CSR_DAC_BASE
     //MENU_ITEM('d', "audio with small delay", audio_15ms_delay),
     MENU_ITEM('d', "audio with quarter-second delay", audio_250ms_delay),
     MENU_ITEM('D', "audio with half-second delay", audio_500ms_delay),
     //MENU_ITEM('D', "audio with one second delay", audio_1000ms_delay),
#endif
     MENU_END,
      },
};

void do_mic3_menu(void)
{
    menu_run(&MENU);
}

