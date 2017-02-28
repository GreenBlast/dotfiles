#!/bin/bash
: '
OriB ITH
set screen to creen resolution adjuster
'

xrandr --newmode "1920x1080" 173.00  1920 2048 2280 2576  1080 1083 1088 1120 -hsync +vsync
xrandr --addmode Virtual1 "1920x1080"
xrandr --output Virtual1 --mode "1920x1080"

