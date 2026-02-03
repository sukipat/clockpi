from typing import Any

import logging

from waveshare_epd import epd7in5_V2
import time
from PIL import Image,ImageDraw,ImageFont

from train_status import get_arriving_trains
from literature_clock import get_current_time_quote

logging.basicConfig(level=logging.DEBUG)

font35 = ImageFont.truetype("resources/Helvetica Roman.ttf", 35)
font18 = ImageFont.truetype("resources/Helvetica Roman.ttf", 18)

try:
    logging.info("epd7in5_V2 Demo")
    epd = epd7in5_V2.EPD()
    
    logging.info("4Gray display--------------------------------")
    epd.init_4Gray()
    
    Limage = Image.new('L', (epd.width, epd.height), 0)  # 255: clear the frame
    draw = ImageDraw.Draw(Limage)
    draw.text((20, 0), "GRAY1", font = font35, fill = epd.GRAY1)
    draw.text((20, 35), "GRAY2", font = font35, fill = epd.GRAY2)
    draw.text((20, 70), "GRAY3", font = font35, fill = epd.GRAY3)
    draw.text((40, 110), "GRAY1", font = font18, fill = epd.GRAY1)
    draw.line((10, 140, 60, 190), fill = epd.GRAY1)
    draw.line((60, 140, 10, 190), fill = epd.GRAY1)
    draw.rectangle((10, 140, 60, 190), outline = epd.GRAY1)
    draw.line((95, 140, 95, 190), fill = epd.GRAY1)
    draw.line((70, 165, 120, 165), fill = epd.GRAY1)
    draw.arc((70, 140, 120, 190), 0, 360, fill = epd.GRAY1)
    draw.rectangle((10, 200, 60, 250), fill = epd.GRAY1)
    draw.chord((70, 200, 120, 250), 0, 360, fill = epd.GRAY1)
    epd.display_4Gray(epd.getbuffer_4Gray(Limage))
    time.sleep(2)

    logging.info("Clear...")
    epd.init()
    epd.Clear()