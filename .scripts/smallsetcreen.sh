#!/bin/bash
: '
set screen to creen resolution adjuster
'

xrandr --newmode "1360x768_60.00"   84.75  1360 1432 1568 1776  768 771 781 798 -hsync +vsync
xrandr --addmode Virtual1 "1360x768_60.00"
xrandr --output Virtual1 --mode "1360x768_60.00"
