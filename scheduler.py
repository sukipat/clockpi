#!/usr/bin/env python3
# scheduler.py
from concurrent.futures import thread
import time
import asyncio
import signal
import threading
import requests

from waveshare_epd import epd7in5_V2
from PIL import Image,ImageDraw,ImageFont

from draw_screen import draw_time
from draw_screen import draw_quote
from draw_screen import draw_trains
from draw_screen import draw_startup_status

from literature_clock import get_current_time_quote

epd = epd7in5_V2.EPD()
existing_image = None
existing_draw = None

shutdown_event = asyncio.Event()
epd_lock = threading.Lock()

import logging
logging.basicConfig(level=logging.DEBUG)

def full_display_update():
    global existing_draw, existing_image

    logging.info("Attempting full refresh")

    with epd_lock:
        try:
            epd.init_fast()
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
            logging.info("Closing connection after full refresh")
            epd.sleep()
        except IOError as e:
            logging.info(e)
            
        except KeyboardInterrupt:    
            logging.info("ctrl + c:")
            epd7in5_V2.epdconfig.module_exit(cleanup=True)
            exit()

def partial_screen_refresh():
    global existing_draw, existing_image

    logging.info("Attempting partial screen refresh")

    with epd_lock:
        if not existing_draw or not existing_image:
            logging.info("No existing image found")
            full_display_update()
            return

        try:
            epd.init_part()

            existing_draw.rectangle((0,0,epd.width,epd.height), fill = 255)
            
            timestr = time.strftime("%I:%M %p")
            quote = get_current_time_quote()

            draw_time(existing_draw, timestr)
            draw_quote(existing_draw, quote)
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

def partial_train_refresh():
    global existing_draw, existing_image

    logging.info("Attempting partial refresh")

    with epd_lock:
        if not existing_draw or not existing_image:
            logging.info("No existing image found")
            full_display_update()
            return

        try:
            epd.init_part()

            existing_draw.rectangle((0,375,epd.width,epd.height), fill = 255)
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

def install_signal_handlers():
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown_event.set)

async def scheduler():
    tasks = set()
    counter = -1

    try:
        while not shutdown_event.is_set():
            now = time.time()
            next_minute = (int(now) // 60 + 1) * 60

            # Sleep until next minute boundary or shutdown
            try:
                await asyncio.wait_for(
                    shutdown_event.wait(),
                    timeout=max(0, next_minute - now),
                )
                break
            except asyncio.TimeoutError:
                pass

            # Schedule full update
            if counter == 3 or counter == -1:
                task = asyncio.create_task(asyncio.to_thread(full_display_update))
                counter = 1
            else:
                task = asyncio.create_task(asyncio.to_thread(partial_screen_refresh))
                counter += 1
            tasks.add(task)
            task.add_done_callback(tasks.discard)

            # Wait 30 seconds or shutdown
            try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=30)
                break
            except asyncio.TimeoutError:
                pass

            # Schedule partial update
            task = asyncio.create_task(asyncio.to_thread(partial_train_refresh))
            tasks.add(task)
            task.add_done_callback(tasks.discard)

    finally:
        print("Shutdown requested — waiting for running tasks to finish...")
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        epd.init_fast()
        epd.Clear()
        epd7in5_V2.epdconfig.module_exit(cleanup=True)
        print("Scheduler stopped cleanly.")


def prepare():
    wifi_connected = False
    cycle_count = 0
    
    try:
        epd.init()
        screen_image = Image.new('1',(epd.width, epd.height),255)
        draw = ImageDraw.Draw(screen_image)

        draw_startup_status(draw,wifi_connected)

        epd.display(epd.getbuffer(screen_image))
        epd.sleep()

        while(cycle_count < 8):
            try:
                response = requests.get("https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace", timeout=12)
            except requests.exceptions.Timeout:
                cycle_count += 1
            except requests.exceptions.ConnectionError:
                cycle_count += 1
                time.sleep(12)
            else:
                wifi_connected = True

                epd.init_part()
                draw.rectangle((0,0,epd.width,epd.height),fill = 255)
                draw_startup_status(draw,wifi_connected)

                epd.display_Partial(epd.getbuffer(screen_image),0,0,epd.width,epd.height)
                epd.sleep()
                time.sleep(2)
                break
    except IOError as e:
        logging.info(e)
    except KeyboardInterrupt:    
        logging.info("ctrl + c:")
        epd7in5_V2.epdconfig.module_exit(cleanup=True)
        exit()


async def main():
    install_signal_handlers()
    await scheduler()

if __name__ == "__main__":
#    prepare()
    asyncio.run(main())