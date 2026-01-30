#!/usr/bin/python
# -*- coding:utf-8 -*-
from typing import Any


import sys
import os
import logging
from waveshare_epd import epd7in5_V2
import time
from PIL import Image,ImageDraw,ImageFont
import traceback

from train_status import get_arriving_trains

logging.basicConfig(level=logging.DEBUG)

helvetica18 = ImageFont.truetype("resources/Helvetica Roman.ttf", 18)
helvetica22 = ImageFont.truetype("resources/Helvetica Roman.ttf", 22)
helvetica24 = ImageFont.truetype("resources/Helvetica Roman.ttf", 24)
helvetica30 = ImageFont.truetype("resources/Helvetica Roman.ttf", 30)
helvetica32 = ImageFont.truetype("resources/Helvetica Roman.ttf", 32)
helvetica34 = ImageFont.truetype("resources/Helvetica Roman.ttf", 34)
helvetica35 = ImageFont.truetype("resources/Helvetica Roman.ttf", 35)

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

    [width,height] = text_size(train,helvetica32)
    fontX = x - (width/2)
    fontY = y - (height/2)

    draw.chord((x1,y1,x2,y2),0,360,fill=0)
    draw.text((fontX,fontY),train,font=helvetica32, fill = 1)

    distance_label = ""
    if min_away == 0:
        distance_label = "<1 min away"
    else:
        distance_label = str(min_away) + " min away"

    [distance_width, distance_height] = text_size(distance_label,helvetica22)
    distance_x = x + radius + 10
    distance_y = y - (distance_height/2) + 2
    draw.text((distance_x,distance_y),distance_label,font=helvetica22, fill = 0)


def display_trains(draw):
    AC_FEED_URL="https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace"
    BD_FEED_URL="https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm"
    FEED_URLS = [AC_FEED_URL, BD_FEED_URL]

    TARGET_ROUTES = {"A", "C", "B", "D"}
    TARGET_STOP = "A15"

    NUM_TRAINS = 3

    arriving_trains = get_arriving_trains(FEED_URLS,TARGET_STOP,TARGET_ROUTES,NUM_TRAINS)

    padding = 5
    radius = 18

    train3_y = 445
    train2_y = train3_y - (2*radius) - padding
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
    downtown_text = "Uptown:"
    [downtown_w, downtown_h] = text_size(downtown_text, helvetica24)

    if not uptown_trains:
        draw.text((uptownX,train1_y + (nu_h/2)),no_uptown,font=helvetica24,fill=0)
    else:
        draw.text((20, train1_y - radius - padding - padding - uptown_h),uptown_text,font=helvetica24,fill=0)

        for i, (route, mins) in enumerate(uptown_trains):
            if i == 0:
                add_train(draw,uptownX,train1_y,route,mins,radius)
            if i == 1:
                add_train(draw,uptownX,train2_y,route,mins,radius)
            if i == 2:
                add_train(draw,uptownX,train3_y,route,mins,radius)

    if not downtown_trains:
        draw.text((downtownX - nd_h,train1_y + (nd_h/2)),no_downtown,font=helvetica24,fill=0)
    else:
        draw.text((downtownX - 30, train1_y - radius - padding - padding - uptown_h),downtown_text,font=helvetica24,fill=0)

        for i, (route, mins) in enumerate(downtown_trains):
            if i == 0:
                add_train(draw,downtownX,train1_y,route,mins,radius)
            if i == 1:
                add_train(draw,downtownX,train2_y,route,mins,radius)
            if i == 2:
                add_train(draw,downtownX,train3_y,route,mins,radius) 

    line_y = train1_y - radius - padding - max(uptown_h,downtown_h) - padding - padding

    # station_label = "125th Street"
    # [station_width, station_height] = text_size(station_label,helvetica22)
    # draw.text((20,line_y - station_height - 3),station_label,font = helvetica22, fill = 0)

    if arriving_trains["error"]:
        error_msg = arriving_trains["error"]
        [error_width, error_height] = text_size(error_msg, helvetica18)
        draw.text((800 - 20 - error_width,line_y - error_height),error_msg,font = helvetica18, fill = 0)

    draw.line((0,line_y,800,line_y), fill=0)

try:
    logging.info("epd7in5_V2 Demo")
    epd = epd7in5_V2.EPD()
    
    logging.info("init and Clear")
    epd.init()
    epd.Clear()

    epd.init_fast()
    Himage = Image.new('1', (epd.width, epd.height), 255)  # 255: clear the frame
    draw = ImageDraw.Draw(Himage)

    [timeWidth,timeHeight] = text_size("3:55PM", helvetica35)
    draw.text((400 - (timeWidth/2),0), "3:55PM", font = helvetica35, fill = 0)   
    draw.line((400,50,400,200), fill = 0)

    add_train(draw,600,300,"D",5,21)

    epd.display(epd.getbuffer(Himage))
    time.sleep(10)


    logging.info("trying full update")
    epd.init()
    TrainImage = Image.new('1', (epd.width, epd.height), 255)
    TrainDraw = ImageDraw.Draw(TrainImage)
    display_trains(TrainDraw)
    epd.display(epd.getbuffer(TrainImage))
    time.sleep(10)

    # partial update
#     logging.info("5.show time")
#     epd.init_part()
#     # Himage = Image.new('1', (epd.width, epd.height), 0)
#     # draw = ImageDraw.Draw(Himage)
#     num = 0
#     while (True):
#         draw.rectangle((10, 120, 130, 170), fill = 255)
#         draw.text((10, 120), time.strftime('%H:%M:%S'), font = helvetica24, fill = 0)
#         epd.display_Partial(epd.getbuffer(Himage),0, 0, epd.width, epd.height)
#         num = num + 1
#         if(num == 10):
#             break
# 


    # # Drawing on the Vertical image
    # logging.info("2.Drawing on the Vertical image...")
    # epd.init()
    # Limage = Image.new('1', (epd.height, epd.width), 255)  # 255: clear the frame
    # draw = ImageDraw.Draw(Limage)
    # draw.text((2, 0), 'hello world', font = font18, fill = 0)
    # draw.text((2, 20), '7.5inch epd', font = font18, fill = 0)
    # draw.text((20, 50), u'微雪电子', font = font18, fill = 0)
    # draw.line((10, 90, 60, 140), fill = 0)
    # draw.line((60, 90, 10, 140), fill = 0)
    # draw.rectangle((10, 90, 60, 140), outline = 0)
    # draw.line((95, 90, 95, 140), fill = 0)
    # draw.line((70, 115, 120, 115), fill = 0)
    # draw.arc((70, 90, 120, 140), 0, 360, fill = 0)
    # draw.rectangle((10, 150, 60, 200), fill = 0)
    # draw.chord((70, 150, 120, 200), 0, 360, fill = 0)
    # epd.display(epd.getbuffer(Limage))
    # time.sleep(2)


    # '''4Gray display'''
    # # The feature will only be available on screens sold after 24/10/23
    # logging.info("4Gray display--------------------------------")
    # epd.init_4Gray()
    
    # Limage = Image.new('L', (epd.width, epd.height), 0)  # 255: clear the frame
    # draw = ImageDraw.Draw(Limage)
    # draw.text((20, 0), u'微雪电子', font = helvetica35, fill = epd.GRAY1)
    # draw.text((20, 35), u'微雪电子', font = helvetica35, fill = epd.GRAY2)
    # draw.text((20, 70), u'微雪电子', font = helvetica35, fill = epd.GRAY3)
    # draw.text((40, 110), 'hello world', font = font18, fill = epd.GRAY1)
    # draw.line((10, 140, 60, 190), fill = epd.GRAY1)
    # draw.line((60, 140, 10, 190), fill = epd.GRAY1)
    # draw.rectangle((10, 140, 60, 190), outline = epd.GRAY1)
    # draw.line((95, 140, 95, 190), fill = epd.GRAY1)
    # draw.line((70, 165, 120, 165), fill = epd.GRAY1)
    # draw.arc((70, 140, 120, 190), 0, 360, fill = epd.GRAY1)
    # draw.rectangle((10, 200, 60, 250), fill = epd.GRAY1)
    # draw.chord((70, 200, 120, 250), 0, 360, fill = epd.GRAY1)
    # epd.display_4Gray(epd.getbuffer_4Gray(Limage))
    # time.sleep(2)
    

#     logging.info("Clear...")
#     epd.init()
#     epd.Clear()

    logging.info("Goto Sleep...")
    epd.sleep()
    
except IOError as e:
    logging.info(e)
    
except KeyboardInterrupt:    
    logging.info("ctrl + c:")
    epd7in5_V2.epdconfig.module_exit(cleanup=True)
    exit()
