#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import datetime
from time import gmtime, strftime
import pypredict
import subprocess
import os
import re

##
## Config header, sorry
## TODO: Better config system
##

# Satellite names in TLE plus their frequency
satellites = ['NOAA 18','NOAA 15','NOAA 19']
freqs = [137912500, 137620000, 137100000]
# Dongle gain
dongleGain='48.0'
#
# Dongle PPM shift, hopefully this will change to reflect different PPM on freq
dongleShift='53'
#
# Dongle index, is there any rtl_fm allowing passing serial of dongle? Unused right now
dongleIndex='0'
#
# Sample rate, width of recorded signal - should include few kHz for doppler shift
sample ='44100'
sampleMeteor='200000'
# Sample rate of the wav file. Shouldn't be changed
wavrate='11025'
#
# Should I remove RAWs after transcoding?
removeRAW='yes'
# Directories used in this program
# wxtoimg install dir
wxInstallDir='/usr/local/bin'
# Recording dir, used for RAW and WAV files
#
recdir='/opt/wxsat/rec'
#
# Spectrogram directory, this would be optional in the future
#
specdir='/opt/wxsat/spectro'
#  
# Output image directory
#
imgdir='/opt/wxsat/img'
#
# Map file directory
#
mapDir='/opt/wxsat/maps'
# Options for wxtoimg
# Create map overlay?
wxAddOverlay='yes'
# Image outputs
wxEnhHVC='no'
wxEnhHVCT='no'
wxEnhMSA='no'
wxEnhMCIR='yes'
# Other tunables
wxQuietOutput='no'
wxDecodeAll='yes'
wxJPEGQuality='75'
# Adding overlay text
wxAddTextOverlay='yes'
wxOverlayText='ATOMUS autowxsat'
#
# Various options
# Should this script create spectrogram : yes/no
createSpectro='yes'
# Use doppler shift for correction, not used right now - leave as is
runDoppler='no'
# Minimum elevation
minElev='8'

##
# SCP Config, works for key autorization
#
SCP_USER='m'
SCP_HOST='costam.mydevil.net'
SCP_DIR='/home/syfjakc'
# Send LOG with imagefile?
LOG_SCP='y'
# Send image to remote server?
IMG_SCP='y'


	###############################
	###                          ##
	###     Here be dragons.     ##
	###                          ##
	###############################


# Read qth file for station data
stationFileDir=os.path.expanduser('~')
stationFilex=stationFileDir+'/.predict/predict.qth'
stationFile=open(stationFilex, 'r')
stationData=stationFile.readlines()
stationName=str(stationData[0]).rstrip().strip()
stationLat=str(stationData[1]).rstrip().strip()
stationLon=str(stationData[2]).rstrip().strip()
stationAlt=str(stationData[3]).rstrip().strip()
stationFile.close()

stationLonNeg=float(stationLon)*-1

##
## Color output declarations
## 

class bcolors:
    HEADER = '\033[95m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[97m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    GRAY = '\033[37m'
    UNDERLINE = '\033[4m'

logLineStart=bcolors.BOLD+bcolors.HEADER+"***>\t"+bcolors.ENDC+bcolors.OKGREEN
logLineEnd=bcolors.ENDC

## 
## Other stuff
##

if wxQuietOutput in ('yes', 'y', '1'):
    wxQuietOpt='-q'
else:
    wxQuietOpt='-C wxQuiet:no'

if wxDecodeAll in ('yes', 'y', '1'):
    wxDecodeOpt='-A'
else:
    wxDecodeOpt='-C wxDecodeAll:no'

if wxAddTextOverlay in ('yes', 'y', '1'):
    wxAddText='-k '+wxOverlayText
else:
    wxAddText='-C wxOther:noOverlay'

##
## Execution loop declaration
##

def runForDuration(cmdline, duration):
    try:
        child = subprocess.Popen(cmdline)
        time.sleep(duration)
        child.terminate()
    except OSError as e:
        print "OS Error during command: "+" ".join(cmdline)
        print "OS Error: "+e.strerror

##
## FM Recorder definition
##

def recordFM(freq, fname, duration, xfname):
    print bcolors.GRAY
    xfNoSpace=xfname.replace(" ","")
    cmdline = ['rtl_fm',\
		'-f',str(freq),\
		'-s',sample,\
		'-g',dongleGain,\
		'-F','9',\
		'-A','fast',\
		'-E','dc',\
		'-E','offset',\
		'-p',dongleShift,\
		recdir+'/'+xfNoSpace+'-'+fname+'.raw' ]
    runForDuration(cmdline, duration)

##
## Recorder with doppler shift correction.
## Absolutely TODO! 
##

def recordDOP(freq, fname, duration, xfname):
    xfNoSpace=xfname.replace(" ","")

    cmdline = ['iqrecord.sh', \
	'-f', str(freq), \
	'-s', str('1024000'), \
	'-g', dongleGain, \
	'-p', dongleShift, \
#	'-m', stationFileDir+'/.predict/predict.tle', \
	'-m', '/tmp/weather.txt', \
	'-r', xfname, \
	'-T', stationLat, \
	'-L', str(stationLonNeg), \
	'-A', stationAlt, \
	'-d', wavrate, \
	'-z', recdir+'/'+xfNoSpace+'-'+fname+'.wav']

    runForDuration(cmdline, duration)

##
## TODO: Meteor M2 tests, no luck
##

def recordMETEOR(freq, fname, duration, xfname):
    xfNoSpace=xfname.replace(" ","")
    cmdline = ['rtl_fm',\
		'-f',str(freq),\
		'-s',sampleMeteor,\
		'-g',dongleGain,\
		'-F','9',\
		'-A','fast',\
		'-E','dc',\
		'-E','offset',\
		'-p',dongleShift,\
		recdir+'/'+xfNoSpace+'-'+fname+'.raw' ]

    runForDuration(cmdline, duration)

##
## Very simple remote display support
##

def writeStatus(freq, aosTime, losTime, losTimeUnix, recordTime, xfName, status):
    statFile=open('/tmp/rec_info', 'w+')
    if status in ('RECORDING'):
	statFile.write("ODBIOR;tak;"+str(xfName)+' AOS@'+str(aosTime)+'REC@'+str(recordTime)+'s LOS@'+str(losTime))
    elif status in ('DECODING'):
	statFile.write('ODBIOR;nie;Dekodowanie '+str(xfName))
    elif status in ('WAITING'):
	statFile.write('ODBIOR;nie;'+str(xfName)+' (AOS@'+str(aosTime)+')')
    statFile.close

##
## Transcoding module
##

def transcode(fname):
    xfNoSpace=xfname.replace(" ","")
    print logLineStart+'Transcoding...'+bcolors.YELLOW
    cmdline = ['sox','-t','raw','-r',sample,'-es','-b','16','-c','1','-V1',recdir+'/'+xfNoSpace+'-'+fname+'.raw',recdir+'/'+xfNoSpace+'-'+fname+'.wav','rate',wavrate]
    subprocess.call(cmdline)
    if removeRAW in ('yes', 'y', '1'):
	print logLineStart+bcolors.ENDC+bcolors.RED+'Removing RAW data'+logLineEnd
	os.remove(recdir+'/'+xfNoSpace+'-'+fname+'.raw')

##
## Doppler calculation
##

def doppler(fname,emergeTime):
    cmdline = ['doppler', 
    '-d','',\
    '--tlefile', '~/.predict/predict.tle',\
    '--tlename', xfname,\
    '--location', 'lat='+stationLat+',lon='+stationLon+',alt='+stationAlt,\
    '--freq ', +str(freq),\
    '-i', 'i16',\
    '-s', sample ]
    subprocess.call(cmdline)

##
## Overlay map creator, still buggy
## TODO: ?
##

def createoverlay(fname,aosTime,satName):
    print logLineStart+'Creating Map Overlay...'+logLineEnd
    aosTimeO=int(aosTime)+int('2')
    cmdline = ['wxmap',
    '-T',satName,\
    '-G',stationFileDir+'/.predict/',\
    '-H','predict.tle',\
    '-M','0',\
    '-L',stationLat+'/'+str(stationLonNeg)+'/'+stationAlt,\
    str(aosTimeO), mapDir+'/'+str(fname)+'-map.png']
    #print cmdline
    overlay_log = open(mapDir+'/'+str(fname)+'-map.png.txt',"w+")
    subprocess.call(cmdline, stderr=overlay_log, stdout=overlay_log)
    overlay_log.close()
#    for line in open(mapDir+'/'+str(fname)+'-map.png.txt',"r").readlines():
#        res=line.replace("\n", "")
#        res2=re.sub(r"(\d)", r"\033[96m\1\033[94m", res)
#        print logLineStart+bcolors.OKBLUE+res2+logLineEnd

##
## Various NOAA picture decoders
## This uses wxtoimg and predict (too!), so these need to be running well!!
##

def decode(fname,aosTime,satName,maxElev):
    xfNoSpace=xfname.replace(" ","")
    satTimestamp = int(fname)
    fileNameC = datetime.datetime.fromtimestamp(satTimestamp).strftime('%Y%m%d-%H%M')
    if wxAddOverlay in ('yes', 'y', '1'):
	print logLineStart+bcolors.OKBLUE+'Creating overlay map'+logLineEnd
	createoverlay(fname,aosTime,satName)
	print logLineStart+'Creating basic image with overlay map'+logLineEnd

	m = open(imgdir+'/'+satName+'/'+fileNameC+'-normal-map.jpg.txt',"w+")
    ### header
	m.write('\nSAT: '+str(xfNoSpace)+', Elevation max: '+str(maxElev)+', Date: '+str(fname)+'\n')
##
## Copy file contents
##
	for psikus in open(mapDir+'/'+str(fname)+'-map.png.txt',"r").readlines():
	    res=psikus.replace("\n", " \n")
	    m.write(res)

	cmdline = [ wxInstallDir+'/wxtoimg',wxQuietOpt,wxDecodeOpt,wxAddText,'-Q '+wxJPEGQuality,recdir+'/'+xfNoSpace+'-'+fname+'.wav',imgdir+'/'+satName+'/'+fileNameC+'-normal-map.jpg']
	subprocess.call(cmdline, stderr=m, stdout=m)

	m.write('\nMax elevation was: '+str(maxElev)+'\n')
	m.close()

	for line in open(imgdir+'/'+satName+'/'+fileNameC+'-normal-map.jpg.txt',"r").readlines():
	    res=line.replace("\n", "")
	    res2=re.sub(r"(\d)", r"\033[96m\1\033[94m", res)
	    print logLineStart+bcolors.OKBLUE+res2+logLineEnd

	if wxEnhHVC in ('yes', 'y', '1'):
	    print 'Creating HVC image'
	    cmdline_hvc = [ wxInstallDir+'/wxtoimg',wxQuietOpt,wxDecodeOpt,wxAddText,'-Q '+wxJPEGQuality,'-e','HVC','-m',mapDir+'/'+fname+'-map.png',recdir+'/'+xfNoSpace+'-'+fname+'.wav', imgdir+'/'+satName+'/'+fileNameC+'-hvc.jpg']
	    subprocess.call(cmdline_hvc)
	if wxEnhHVCT in ('yes', 'y', '1'):
	    print 'Creating HVCT image'
	    cmdline_hvct = [ wxInstallDir+'/wxtoimg',wxQuietOpt,wxDecodeOpt,wxAddText,'-Q '+wxJPEGQuality,'-e','HVCT','-m',mapDir+'/'+fname+'-map.png',recdir+'/'+xfNoSpace+'-'+fname+'.wav',imgdir+'/'+satName+'/'+fileNameC+'-hvct.jpg']
	    subprocess.call(cmdline_hvct)
	if wxEnhMSA in ('yes', 'y', '1'):
	    print 'Creating MSA image'
	    cmdline_msa = [ wxInstallDir+'/wxtoimg',wxQuietOpt,wxDecodeOpt,wxAddText,'-Q '+wxJPEGQuality,'-e','MSA','-m',mapDir+'/'+fname+'-map.png',recdir+'/'+xfNoSpace+'-'+fname+'.wav',imgdir+'/'+satName+'/'+fileNameC+'-msa.jpg']
	    subprocess.call(cmdline_msa)
	if wxEnhMCIR in ('yes', 'y', '1'):
	    print 'Creating MCIR image'
	    mcir_log = open(imgdir+'/'+satName+'/'+fileNameC+'-mcir-map.jpg.txt',"w+")
	    mcir_log.write('\nMCIR SAT: '+str(xfNoSpace)+', Elevation max: '+str(maxElev)+', Date: '+str(fname)+'\n')
	    cmdline_mcir = [ wxInstallDir+'/wxtoimg',wxQuietOpt,wxDecodeOpt,wxAddText,'-Q '+wxJPEGQuality,'-e','MCIR','-m',mapDir+'/'+fname+'-map.png',recdir+'/'+xfNoSpace+'-'+fname+'.wav',imgdir+'/'+satName+'/'+fileNameC+'-mcir-map.jpg']
	    subprocess.call(cmdline_mcir, stderr=mcir_log, stdout=mcir_log)
	    if LOG_SCP in ('yes', 'y', '1'):
		print logLineStart+"Sending MCIR flight and decode logs..."+bcolors.YELLOW
		for psikus in open(mapDir+'/'+str(fname)+'-map.png.txt',"r").readlines():
		    res=psikus.replace("\n", " \n")
		    mcir_log.write(res)
		cmdline_scp_log = [ '/usr/bin/scp',imgdir+'/'+satName+'/'+fileNameC+'-mcir-map.jpg.txt',SCP_USER+'@'+SCP_HOST+':'+SCP_DIR+'/'+satName.replace(" ","\ ")+'-'+fileNameC+'-mcir-map.jpg.txt' ] 
		subprocess.call(cmdline_scp_log)
	    if IMG_SCP in ('yes', 'y', '1'):
		print logLineStart+"Sending MCIR image with overlay map... "+bcolors.YELLOW
		cmdline_scp_img = [ '/usr/bin/scp',imgdir+'/'+satName+'/'+fileNameC+'-mcir-map.jpg',SCP_USER+'@'+SCP_HOST+':'+SCP_DIR+'/'+satName.replace(" ","\ ")+'-'+fileNameC+'-mcir-map.jpg' ] 
		subprocess.call(cmdline_scp_img)
		print logLineStart+"Wysłano, przechodzę dalej"+logLineEnd

	if LOG_SCP in ('yes', 'y', '1'):
	    print logLineStart+"Sending flight and decode logs..."+bcolors.YELLOW
	    cmdline_scp_log = [ '/usr/bin/scp',imgdir+'/'+satName+'/'+fileNameC+'-normal-map.jpg.txt',SCP_USER+'@'+SCP_HOST+':'+SCP_DIR+'/'+satName.replace(" ","\ ")+'-'+fileNameC+'-normal-map.jpg.txt' ] 
	    subprocess.call(cmdline_scp_log)
	if IMG_SCP in ('yes', 'y', '1'):
	    print logLineStart+"Sending base image with map: "+bcolors.YELLOW
	    cmdline_scp_img = [ '/usr/bin/scp',imgdir+'/'+satName+'/'+fileNameC+'-normal-map.jpg',SCP_USER+'@'+SCP_HOST+':'+SCP_DIR+'/'+satName.replace(" ","\ ")+'-'+fileNameC+'-normal-map.jpg' ] 
	    subprocess.call(cmdline_scp_img)
	    print logLineStart+"Sending OK, go on..."+logLineEnd
    else:
	print logLineStart+'Creating basic image without map'+logLineEnd
	r = open(imgdir+'/'+satName+'/'+fileNameC+'-normal.jpg.txt',"w+")
	cmdline = [ wxInstallDir+'/wxtoimg',wxQuietOpt,wxDecodeOpt,wxAddText,'-Q '+wxJPEGQuality,'-t','NOAA',recdir+'/'+xfNoSpace+'-'+fname+'.wav', imgdir+'/'+satName+'/'+fileNameC+'-normal.jpg']
	r.write('\nSAT: '+str(xfNoSpace)+', Elevation max: '+str(maxElev)+', Date: '+str(fname)+'\n')
	subprocess.call(cmdline, stderr=r, stdout=r)
	r.close()
	for line in open(imgdir+'/'+satName+'/'+fileNameC+'-normal.jpg.txt',"r").readlines():
	    res=line.replace("\n", "")
	    res2=re.sub(r"(\d)", r"\033[96m\1\033[94m", res)
	    print logLineStart+bcolors.OKBLUE+res2+logLineEnd
	if wxEnhHVC in ('yes', 'y', '1'):
	    print 'Creating HVC image'
	    cmdline_hvc = [ wxInstallDir+'/wxtoimg',wxQuietOpt,wxDecodeOpt,wxAddText,'-Q '+wxJPEGQuality,'-e','HVC',recdir+'/'+xfNoSpace+'-'+fname+'.wav', imgdir+'/'+satName+'/'+fileNameC+'-hvc.jpg']
	    subprocess.call(cmdline_hvc)
	if wxEnhHVCT in ('yes', 'y', '1'):
	    print 'Creating HVCT image'
	    cmdline_hvct = [ wxInstallDir+'/wxtoimg',wxQuietOpt,wxDecodeOpt,wxAddText,'-Q '+wxJPEGQuality,'-e','HVCT',recdir+'/'+xfNoSpace+'-'+fname+'.wav', imgdir+'/'+satName+'/'+fileNameC+'-hvct.jpg']
	    subprocess.call(cmdline_hvct)
	if wxEnhMSA in ('yes', 'y', '1'):
	    print 'Creating MSA image'
	    cmdline_msa = [ wxInstallDir+'/wxtoimg',wxQuietOpt,wxDecodeOpt,wxAddText,'-Q '+wxJPEGQuality,'-e','MSA',recdir+'/'+xfNoSpace+'-'+fname+'.wav', imgdir+'/'+satName+'/'+fileNameC+'-msa.jpg']
	    subprocess.call(cmdline_msa)
	if wxEnhMCIR in ('yes', 'y', '1'):
	    print 'Creating MCIR image'
	    cmdline_mcir = [ wxInstallDir+'/wxtoimg',wxQuietOpt,wxDecodeOpt,wxAddText,'-Q '+wxJPEGQuality,'-e','MCIR',recdir+'/'+xfNoSpace+'-'+fname+'.wav', imgdir+'/'+satName+'/'+fileNameC+'-mcir.jpg']
	    subprocess.call(cmdline_mcir)
	if LOG_SCP in ('yes', 'y', '1'):
	    print logLineStart+"Sending flight and decode logs..."+bcolors.YELLOW
	    cmdline_scp_log = [ '/usr/bin/scp',imgdir+'/'+satName+'/'+fileNameC+'-normal.jpg.txt',SCP_USER+'@'+SCP_HOST+':'+SCP_DIR+'/'+satName.replace(" ","\ ")+'-'+fileNameC+'-normal.jpg.txt' ] 
	    subprocess.call(cmdline_scp_log)
	if IMG_SCP in ('yes', 'y', '1'):
	    print logLineStart+"Sending base image without overlay map... "+bcolors.YELLOW
	    cmdline_scp_img = [ '/usr/bin/scp',imgdir+'/'+satName+'/'+fileNameC+'-normal.jpg',SCP_USER+'@'+SCP_HOST+':'+SCP_DIR+'/'+satName.replace(" ","\ ")+'-'+fileNameC+'-normal.jpg' ] 
	    subprocess.call(cmdline_scp_img)
	    print logLineStart+"Sent, go on..."+logLineEnd

##
## Record and transcode wave file
##

def recordWAV(freq,fname,duration,xfname):
    if xfname in ('NOAA 15', 'NOAA 19', 'NOAA 18'):
	recordFM(freq,fname,duration,xfname)
	transcode(fname)
	if createSpectro in ('yes', 'y', '1'):
	    spectrum(fname)
    elif xfname in ('METEOR-M2'):
	recordMETEOR(freq,fname,duration,xfname)
	if createSpectro in ('yes', 'y', '1'):
	    spectrum(fname)

##
## Spectrum creation module
##

def spectrum(fname):
    xfNoSpace=xfname.replace(" ","")
    print logLineStart+'Creating flight spectrum'+logLineEnd
    cmdline = ['sox',recdir+'/'+xfNoSpace+'-'+fname+'.wav', '-n', 'spectrogram','-o',specdir+'/'+xfNoSpace+'-'+fname+'.png']
    subprocess.call(cmdline)

##
## Passage finder loop
##

def findNextPass():
    predictions = [pypredict.aoslos(s) for s in satellites]
    aoses = [p[0] for p in predictions]
    nextIndex = aoses.index(min(aoses))
    return (satellites[nextIndex],\
            freqs[nextIndex],\
            predictions[nextIndex]) 

##
## Now magic
##

while True:

    (satName, freq, (aosTime, losTime,maxElev)) = findNextPass()
    now = time.time()
    towait = aosTime-now

    aosTimeCnv=strftime('%H:%M:%S', time.localtime(aosTime))
    emergeTimeUtc=strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(aosTime))
    losTimeCnv=strftime('%H:%M:%S', time.localtime(losTime))
    dimTimeUtc=strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(losTime))
##
## OK, now we have to decide what if recording or sleeping
##
    if towait>0:
        print logLineStart+"waiting "+bcolors.CYAN+str(towait).split(".")[0]+bcolors.OKGREEN+" seconds (emerging "+bcolors.CYAN+aosTimeCnv+bcolors.OKGREEN+") for "+bcolors.YELLOW+satName+bcolors.OKGREEN+" @ "+bcolors.CYAN+str(maxElev)+bcolors.OKGREEN+"° el."+logLineEnd
        writeStatus(freq,aosTimeCnv,losTimeCnv,aosTime,towait,satName,'WAITING')
## Disable sleeper below to test
    	time.sleep(towait)
##
## If the script broke - or it was recording other one - and a bird is already passing by - change record time to real one
##
    if aosTime<now:
        recordTime=losTime-now
        if recordTime<1:
	    recordTime=1
    elif aosTime>=now:
	recordTime=losTime-aosTime
    	if recordTime<1:
	    recordTime=1
##
## Dirty, but for now we'll name recordings and images by Unix timestamp.
##
    if maxElev>int(minElev):
	fname=str(aosTime)
	xfname=satName

## Own place scripts.
## TODO: Own process
##
#	subprocess.call('sudo /etc/init.d/pymultimonaprs stop', shell=True)

	print logLineStart+"Beginning pass of "+bcolors.YELLOW+satName+bcolors.OKGREEN+" at "+bcolors.CYAN+str(maxElev)+"°"+bcolors.OKGREEN+" elev.\n"+logLineStart+"Predicted start "+bcolors.CYAN+aosTimeCnv+bcolors.OKGREEN+" and end "+bcolors.CYAN+losTimeCnv+bcolors.OKGREEN+".\n"+logLineStart+"Will record for "+bcolors.CYAN+str(recordTime).split(".")[0]+bcolors.OKGREEN+" seconds."+logLineEnd
	writeStatus(freq,aosTimeCnv,losTimeCnv,str(losTime),str(recordTime).split(".")[0],satName,'RECORDING')

##
## Let's record
##
	recordWAV(freq,fname,recordTime,xfname)

## DEBUG
##
##	recordWAV(freq,fname,5,xfname)
##	recordDOP(freq,fname,recordTime,xfname)
##
	print logLineStart+"Decoding data"+logLineEnd
####
	if xfname in ('NOAA 15', 'NOAA 19', 'NOAA 18'):
	    writeStatus(freq,aosTimeCnv,losTimeCnv,str(losTime),str(recordTime).split(".")[0],satName,'DECODING')
	    decode(fname,aosTime,satName,maxElev) # make picture
###
	print logLineStart+"Finished pass of "+bcolors.YELLOW+satName+bcolors.OKGREEN+" at "+bcolors.CYAN+losTimeCnv+bcolors.OKGREEN+". Sleeping for"+bcolors.CYAN+" 10"+bcolors.OKGREEN+" seconds"+logLineEnd
##
## Is this really needed?
##
## TODO: Call custom script
#	subprocess.call('sudo /etc/init.d/pymultimonaprs start', shell=True)
#
    else:
###
### Satellite is too low...
### Let's sleep and just wait..
###
	print logLineStart+bcolors.ENDC+bcolors.WARNING+"Too low for good reception ("+bcolors.CYAN+str(minElev)+"°"+bcolors.WARNING+" > max: "+bcolors.CYAN+str(maxElev)+"°"+bcolors.WARNING+" elev. )\n\tSleeping for "+bcolors.CYAN+str(recordTime)+bcolors.WARNING+" seconds..."+logLineEnd
	time.sleep(recordTime)

## Main loop done
## 
## Sleep for a moment...
## And do everything again

    time.sleep(10.0)

