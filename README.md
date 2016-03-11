rtlsdr-automated-wxsat-capture
==============================
This is a fork of dr. Paul Brewer awesome program.

Automate Recording of Low Earth Orbit NOAA Weather Satellites

These are some automation scripts dr. Paul Brewer done in python for weather satellite hobbyist use.

I just added few options adapted it to recent tools.

License:  GPLv2 or any later version

assumptions: Linux-based computer, rtl-sdr usb dongle, stationary antenna, experienced python user

goal:  record wav files for later processing, postprocess wav file and generate image

prerequistes:  working rtl-sdr, predict (text based, not gpredict) setup with correct ground station coordinates, sox

NO WARRANTY:  ALL USE IS AT THE RISK OF THE USER.  These are scripts I use for hobbyist purposes.  There may
be pre-requisites or system configuration differences which you will need to resolve in order to make use of these scripts in your project.  To do so requires patience and and, quite often, previous experience programming python 
and/or maintaining Linux-based rtl-sdr software.

This program also uses software which has no clear licensing information (wx).

##FILES

###LICENSE 
General Public License version 2.0, or any later version

###dotpredict-predict.tle
Modification of PREDICT's TLE file to provide orbit data for weather satellites NOAA-15, NOAA-18, NOAA-19
to get coverage of missing satellites into predict's default config. Please edit qth to reflect your station position.
Example values are provided.
    
Copy as follows:  
```
cp tles/predict.qth ~/.predict/predict.qth
cp tles/predict.tle ~/.predict/predict.tle
cp tles/predict.db ~/.predict/predict.db

```

    
###noaacapture.py
This is the main python script.  It will calculate the time
of the next pass for recording.  It expects to call rtl_fm to do the
recording and sox to convert the file to .wav. It can create spectrogram of the pass using sox (not the RTL_POWER!)


A few words about the options.

satellites - this is a list of satellites you want to capture, this needs to be the same name as in TLE file
freqs - frequencies of centre of the APT signal

dongleGain - set this to the desired gain of the dongle, leave "0" if you want AGC
dongleShift - set this to the dongle PPM shift, can be negative
dongleIndex - set this to the index of your dongle, of you have only one - leave it unchanged.
sample - "sample rate", option "-s" for rtl_fm - this is the width of the recorded signal. Please keep in mind that APT is 34kHz but you should include few kHz for doppler shift. This will change when the doppler tool is used.
wavrate - sample rate of the WAV file used to generate JPEGs. Should be 11025.

Station options for doppler tool (not used right now).
stationLat - latitude of the station in degrees NORTH, negative value for SOUTH
stationLon - longtitude of the station in degress WEST, negative for EAST
stationAlt - your altitude above sea level (in metres) 

Directories: directories used for misc. files
recdir - this is a directory containing RAW and WAV files
specdir - this is a directory holding spectrogram files created from the pass (PNG)
imgdir - output JPG images

Misc options, not all are used right now
createSpectro - should program create spectrogram files for the pass? Useful for debugging images. Possible values are "yes", "y" and "1" for YES, any other value will not create spectro.
runDoppler - should we do the doppler shift using "doppler" tool? Not needed for wxtoimg as it seems it does the correction itself.

###pypredict.py
This is a short python module for extracting the AOS/LOS times
of the next pass for a specified satellite.  It calls predict -p and extracts
the times from the first and last lines.

###update-keps.sh
This is a short shell script to update the keps, which are orbital
parameters needed by the predict program.  It is mostly copied from the PREDICT man
page. PREDICT was written by John Magliacane, KD2BD and released under the
GPL license.
