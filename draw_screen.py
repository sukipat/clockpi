#draw_screen.py
from typing import Any

import logging

from waveshare_epd import epd7in5_V2
import time
from PIL import Image,ImageDraw,ImageFont

from train_status import get_arriving_trains

logging.basicConfig(level=logging.DEBUG)

helvetica18 = ImageFont.truetype("resources/Helvetica Roman.ttf", 18)
helvetica22 = ImageFont.truetype("resources/Helvetica Roman.ttf", 22)
helvetica24 = ImageFont.truetype("resources/Helvetica Roman.ttf", 24)
helvetica31 = ImageFont.truetype("resources/Helvetica Roman.ttf", 31)

courier18 = ImageFont.truetype("resources/Courier New.ttf", 18)
courier22 = ImageFont.truetype("resources/Courier Medium.otf", 22)
courier24 = ImageFont.truetype("resources/Courier New.ttf", 24)
courier31 = ImageFont.truetype("resources/Courier New.ttf", 31)

courierbold35 = ImageFont.truetype("resources/Courier New Bold.ttf",35)
courierbold50 = ImageFont.truetype("resources/Courier New Bold.ttf",50)

# Font paths for dynamic sizing
COURIER_PATH = "resources/Courier New.ttf"
COURIER_BOLD_PATH = "resources/Courier New Bold.ttf"
COURIER_ITALIC_PATH = "resources/Courier New Italic.ttf"

def _quote_fonts(size):
    """Create quote, title, author fonts at given sizes. Title/author use 0.8x."""
    return {
        "quote": ImageFont.truetype(COURIER_PATH, size),
        "quote_bold": ImageFont.truetype(COURIER_BOLD_PATH, size),
        "title": ImageFont.truetype(COURIER_ITALIC_PATH, max(12, int(size * 0.8))),
        "author": ImageFont.truetype(COURIER_PATH, max(12, int(size * 0.8))),
    }

def text_size(text, font_type):
    left,top,right,bottom = font_type.getbbox(text)
    width = right - left
    height = bottom - top
    return [width, height]

def add_train(draw,x,y,train,min_away, rad):
    radius = rad
   
    x1 = x - radius
    y1 = y - radius
    x2 = x + radius
    y2 = y + radius

    [width,height] = text_size(train,helvetica31)
    fontX = x - (width/2)
    fontY = y - (height/2)

    draw.chord((x1,y1,x2,y2),0,360,fill=0)
    draw.text((fontX,fontY-1),train,font=helvetica31, fill = 1)

    distance_label = ""
    if min_away == 0:
        distance_label = "<1 min away"
    else:
        distance_label = str(min_away) + " min away"

    [distance_width, distance_height] = text_size(distance_label,courier22)
    distance_x = x + radius + 10
    distance_y = y - (distance_height/2) + 2
    draw.text((distance_x,distance_y),distance_label,font=courier22, fill = 0)

def draw_trains(draw):
    AC_FEED_URL="https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace"
    BD_FEED_URL="https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm"
    FEED_URLS = [AC_FEED_URL, BD_FEED_URL]

    TARGET_ROUTES = {"A", "C", "B", "D"}
    TARGET_STOP = "A15"

    NUM_TRAINS = 2

    arriving_trains = get_arriving_trains(FEED_URLS,TARGET_STOP,TARGET_ROUTES,NUM_TRAINS)

    padding = 5
    radius = 18

    train2_y = 455
    train1_y = train2_y - (2*radius) - padding

    uptownX = 50
    downtownX = 600


    uptown_trains = arriving_trains["uptown"]
    downtown_trains = arriving_trains["downtown"]

    no_uptown = "No uptown arrivals soon..."
    [nu_w,nu_h] = text_size(no_uptown,helvetica24)
    no_downtown = "No downtown arrivals soon..."
    [nd_w,nd_h] = text_size(no_downtown,helvetica24)

    uptown_text = "Uptown:"
    [uptown_w, uptown_h] = text_size(uptown_text, helvetica24)
    downtown_text = "Downtown:"
    [downtown_w, downtown_h] = text_size(downtown_text, helvetica24)

    if not uptown_trains:
        draw.text((uptownX,train1_y + (nu_h/2)),no_uptown,font=helvetica24,fill=0)
    else:
        draw.text((20, train1_y - radius - padding - uptown_h),uptown_text,font=helvetica24,fill=0)

        for i, (route, mins) in enumerate(uptown_trains):
            if i == 0:
                add_train(draw,uptownX,train1_y,route,mins,radius)
            if i == 1:
                add_train(draw,uptownX,train2_y,route,mins,radius)

    if not downtown_trains:
        draw.text((downtownX - (nd_w/2),train1_y + (nd_h/2)),no_downtown,font=helvetica24,fill=0)
    else:
        draw.text((downtownX - 30, train1_y - radius - padding - uptown_h),downtown_text,font=helvetica24,fill=0)

        for i, (route, mins) in enumerate(downtown_trains):
            if i == 0:
                add_train(draw,downtownX,train1_y,route,mins,radius)
            if i == 1:
                add_train(draw,downtownX,train2_y,route,mins,radius)

    line_y = train1_y - radius - padding - max(uptown_h,downtown_h) - padding - padding

    # station_label = "125th Street"
    # [station_width, station_height] = text_size(station_label,helvetica22)
    # draw.text((20,line_y - station_height - 3),station_label,font = helvetica22, fill = 0)

    if arriving_trains["error"]:
        error_msg = arriving_trains["error"]
        [error_width, error_height] = text_size(error_msg, helvetica18)
        draw.text((500 - (error_width/2),line_y+error_height),error_msg,font = helvetica18, fill = 0)

    # draw.line((0,line_y,800,line_y), fill=0)

def _measure_quote_layout(quote, fonts, max_width):
    """Measure total height of quote layout (no drawing). Returns (height, layout_info)."""
    quote_first = quote.get("quote_first") or ""
    quote_time_case = quote.get("quote_time_case") or ""
    quote_last = quote.get("quote_last") or ""
    title = quote.get("title") or ""
    author = quote.get("author") or ""

    qf, qb, tf, af = fonts["quote"], fonts["quote_bold"], fonts["title"], fonts["author"]

    segments = [(quote_first, qf), (quote_time_case, qb), (quote_last, qf)]
    tokens = []
    for i, (text, font) in enumerate(segments):
        words = text.split()
        for j, word in enumerate(words):
            is_last = i == len(segments) - 1 and j == len(words) - 1
            tokens.append((word if is_last else word + " ", font))

    [_, hq] = text_size("j", qf)
    [_, hqb] = text_size("j", qb)
    quote_line_height = max(hq, hqb) + 5

    x, y = 0, 0
    last_quote_line_bottom = 0
    for word, font in tokens:
        w, _ = text_size(word, font)
        if x + w > max_width and x > 0:
            x = 0
            y += quote_line_height
        x += w
        last_quote_line_bottom = y + quote_line_height

    total_height = last_quote_line_bottom + 10
    [_, title_h] = text_size("X", tf)
    title_line_height = title_h + 5

    title_lines = []
    if title:
        current_line, current_width = [], 0
        for word in title.split():
            word_w, _ = text_size(word + " ", tf)
            if current_line and current_width + word_w > max_width:
                title_lines.append(" ".join(current_line))
                current_line, current_width = [word], text_size(word + " ", tf)[0]
            else:
                current_line.append(word)
                current_width += word_w
        if current_line:
            title_lines.append(" ".join(current_line))
        total_height += len(title_lines) * title_line_height

    if author:
        [_, author_h] = text_size("X", af)
        total_height += author_h

    return total_height

def draw_quote(draw, quote):
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 480
    QUOTE_HEIGHT = int(SCREEN_HEIGHT * 2 / 3)
    PADDING_X = 50
    PADDING_TOP = 50
    max_width = SCREEN_WIDTH - 2 * PADDING_X
    box_right = SCREEN_WIDTH - PADDING_X
    box_bottom = PADDING_TOP + QUOTE_HEIGHT
    available_height = QUOTE_HEIGHT

    # Find largest font size that fits
    FONT_SIZES = [40, 36, 32, 28, 24, 20, 18, 16, 14, 12]
    fonts = None
    for size in FONT_SIZES:
        f = _quote_fonts(size)
        h = _measure_quote_layout(quote, f, max_width)
        if h <= available_height:
            fonts = f
            break
    if fonts is None:
        fonts = _quote_fonts(FONT_SIZES[-1])

    qf, qb, tf, af = fonts["quote"], fonts["quote_bold"], fonts["title"], fonts["author"]

    quote_first = quote.get("quote_first") or ""
    quote_time_case = quote.get("quote_time_case") or ""
    quote_last = quote.get("quote_last") or ""
    title = quote.get("title") or ""
    author = quote.get("author") or ""

    [_, hq] = text_size("j", qf)
    [_, hqb] = text_size("j", qb)
    quote_line_height = max(hq, hqb) + 5

    segments = [(quote_first, qf), (quote_time_case, qb), (quote_last, qf)]
    tokens = []
    for i, (text, font) in enumerate(segments):
        words = text.split()
        for j, word in enumerate(words):
            is_last = i == len(segments) - 1 and j == len(words) - 1
            tokens.append((word if is_last else word + " ", font))

    x, y = PADDING_X, PADDING_TOP
    last_quote_line_bottom = PADDING_TOP

    for word, font in tokens:
        w, h = text_size(word, font)
        if x + w > PADDING_X + max_width and x > PADDING_X:
            x = PADDING_X
            y += quote_line_height
        if y + quote_line_height > box_bottom:
            break
        draw.text((x, y), word, font=font, fill=0)
        x += w
        last_quote_line_bottom = y + quote_line_height

    [_, title_h] = text_size("X", tf)
    title_line_height = title_h + 5
    title_y = last_quote_line_bottom + 10

    if title:
        title_words = title.split()
        title_lines = []
        current_line, current_width = [], 0
        for word in title_words:
            word_w, _ = text_size(word + " ", tf)
            if current_line and current_width + word_w > max_width:
                title_lines.append(" ".join(current_line))
                current_line = [word]
                current_width = text_size(word + " ", tf)[0]
            else:
                current_line.append(word)
                current_width += word_w
        if current_line:
            title_lines.append(" ".join(current_line))

        for line in title_lines:
            line_w, _ = text_size(line, tf)
            draw.text((box_right - line_w, title_y), line, font=tf, fill=0)
            title_y += title_line_height

    if author:
        [author_w, _] = text_size(author, af)
        draw.text((box_right - author_w, title_y), author, font=af, fill=0)

def draw_time(draw, timestr):
    [timeWidth,timeHeight] = text_size(timestr, courierbold35)
    draw.text((400 - (timeWidth/2),0), timestr, font = courierbold35, fill = 0)

def draw_startup_status(draw, wifi_status):
    startup_text = "Starting Up..."
    [startup_width, startup_height] = text_size(startup_text,courierbold50)
    draw.text((400 - (startup_width/2),100), startup_text, font = courierbold50, fill = 0)

    status_text = "Wifi Connected!"
    if not wifi_status:
        status_text = "Connecting Wifi"
    
    [status_width, status_height] = text_size(status_text, courierbold35)
    draw.text((400 - (status_width/2),300),status_text, font = courierbold35, fill = 0)