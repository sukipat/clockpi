# scheduler.py
import time
from concurrent.futures import ThreadPoolExecutor

from waveshare_epd import epd7in5_V2
from PIL import Image,ImageDraw,ImageFont

from draw_screen import draw_time
from draw_screen import draw_quote
from draw_screen import draw_trains
from draw_screen import get_current_time_quote

epd = epd7in5_V2.EPD()
existing_image = None
existing_draw = None

import logging
logging.basicConfig(level=logging.DEBUG)

def full_display_update():
    logging.info("Attempting full refresh")
    try:
        epd.init()
        screen_image = Image.new('1',(epd.width, epd.height),255)
        draw = ImageDraw.Draw(screen_image)

        timestr = time.strftime("%I:%M %p")
        quote = get_current_time_quote()

        draw_time(draw, timestr)
        draw_quote(draw, quote)
        draw_trains(draw)

        existing_draw = draw
        existing_image = screen_image

        epd.display(epd.getbuffer(screen_image))
        logging.info("Closing connection after partial refresh")
        epd.sleep()
    except IOError as e:
        logging.info(e)
        
    except KeyboardInterrupt:    
        logging.info("ctrl + c:")
        epd7in5_V2.epdconfig.module_exit(cleanup=True)
        exit()

def partial_train_refresh():
    logging.info("Attempting partial refresh")
    if not existing_draw or not existing_image:
        full_display_update()
        logging.info("No existing image found")
        return

    try:
        existing_draw.rectangle((0,320,800,480), fill = 255)
        draw_trains(existing_draw)

        epd.display_Partial(epd.getbuffer(existing_image),0,0,epd.width,epd.height)
        logging.info("Closing connection after partial refresh")
        epd.sleep()

    except IOError as e:
        logging.info(e)
        
    except KeyboardInterrupt:    
        logging.info("ctrl + c:")
        epd7in5_V2.epdconfig.module_exit(cleanup=True)
        exit()

def run_scheduler():
    # Adjust max_workers based on how many overlaps you expect
    executor = ThreadPoolExecutor(max_workers=4)

    full_display_update()

    while True:
        now = time.time()

        # Align to next minute boundary
        next_minute = (int(now) // 60 + 1) * 60
        time.sleep(max(0, next_minute - now))

        # Submit full update immediately
        executor.submit(full_display_update())

        # Sleep 30 seconds (scheduler thread only)
        time.sleep(30)

        # Submit partial update
        executor.submit(partial_train_refresh)


if __name__ == "__main__":
    run_scheduler()