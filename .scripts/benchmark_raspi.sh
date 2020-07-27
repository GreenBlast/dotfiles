#!/bin/bash

vcgencmd measure_temp
sysbench --test=cpu --cpu-max-prime=20000 --num-threads=4 run > /dev/null 2>&1
vcgencmd measure_temp
sysbench --test=cpu --cpu-max-prime=20000 --num-threads=4 run > /dev/null 2>&1
vcgencmd measure_temp
sysbench --test=cpu --cpu-max-prime=20000 --num-threads=4 run > /dev/null 2>&1
vcgencmd measure_temp
sysbench --test=cpu --cpu-max-prime=20000 --num-threads=4 run > /dev/null 2>&1
vcgencmd measure_temp
sysbench --test=cpu --cpu-max-prime=20000 --num-threads=4 run > /dev/null 2>&1
vcgencmd measure_temp
