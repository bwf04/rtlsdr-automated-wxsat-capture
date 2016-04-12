#!/bin/bash
#rm /tmp/weather.txt
#wget -qr www.celestrak.com/NORAD/elements/weather.txt -O /tmp/weather.txt

rm /tmp/noaa.txt
wget -qr https://www.celestrak.com/NORAD/elements/noaa.txt -O /tmp/noaa.txt

rm /tmp/amateur.txt
wget -qr https://www.celestrak.com/NORAD/elements/amateur.txt -O /tmp/amateur.txt

rm /tmp/cubesat.txt
wget -qr https://www.celestrak.com/NORAD/elements/cubesat.txt -O /tmp/cubesat.txt

rm /tmp/weather.txt
wget -qr https://www.celestrak.com/NORAD/elements/weather.txt -O /tmp/weather.txt

/usr/bin/predict -u /tmp/noaa.txt /tmp/amateur.txt /tmp/weather.txt /tmp/cubesat.txt
