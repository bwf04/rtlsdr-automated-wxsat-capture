#!/usr/bin/python
import time
import datetime
from time import gmtime, strftime
import pypredict
import subprocess
import os

# Satellite names in TLE plus their frequency
satellites = ['NOAA 18','NOAA 15','NOAA 19']
freqs = [137912500, 137620000, 137100000]
# Dongle gain
dongleGain='50'
#
# Dongle PPM shift, hopefully this will change to reflect different PPM on freq
dongleShift='52'
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
wxAddOverlay='no'
# Image outputs
wxEnhHVC='no'
wxEnhHVCT='no'
wxEnhMSA='no'
wxEnhMCIR='no'
# Other tunables
wxQuietOutput='no'
wxDecodeAll='yes'
wxJPEGQuality='75'
# Adding overlay text
wxAddTextOverlay='no'
wxOverlayText='text'
#
# Various options
# Should this script create spectrogram : yes/no
createSpectro='yes'
# Use doppler shift for correction, not used right now - leave as is
runDoppler='no'

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


def runForDuration(cmdline, duration):
    try:
        child = subprocess.Popen(cmdline)
        time.sleep(duration)
        child.terminate()
    except OSError as e:
        print "OS Error during command: "+" ".join(cmdline)
        print "OS Error: "+e.strerror

def recordFM(freq, fname, duration, xfname):
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

def writeStatus(freq, aosTime, losTime, losTimeUnix, recordTime, xfName, status):
    statFile=open('/tmp/rec_info', 'r+')
    if status in ('RECORDING'):
	statFile.write(str(xfName)+' | '+'AOS.'+str(aosTime)+'REC:'+str(recordTime)+'s | LOS.'+str(losTime)+'\nR\n'+str(losTimeUnix)+'\n')
    elif status in ('DECODING'):
	statFile.write('FINISHED PASS OF '+str(xfName)+' AT '+str(losTime)+'\n'+'DECODING IMAGE'+'\n'+str(losTimeUnix)+'\n')
    elif status in ('WAITING'):
	statFile.write('NXT: '+str(xfName)+' (AOS.'+str(aosTime)+') \nW\n'+str(losTimeUnix)+'\n')
    statFile.close


def transcode(fname):
    xfNoSpace=xfname.replace(" ","")
    print 'Transcoding...'
    cmdline = ['sox','-t','raw','-r',sample,'-es','-b','16','-c','1','-V1',recdir+'/'+xfNoSpace+'-'+fname+'.raw',recdir+'/'+xfNoSpace+'-'+fname+'.wav','rate',wavrate]
    subprocess.call(cmdline)
    if removeRAW in ('yes', 'y', '1'):
	print 'Removing RAW data'
	os.remove(recdir+'/'+xfNoSpace+'-'+fname+'.raw')

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

def createoverlay(fname,aosTime,satName):
    print 'Creating Map Overlay...'
    cmdline = ['wxmap',
    '-T',satName,\
    '-G',stationFileDir+'/.predict/',\
    '-H','predict.tle',\
    '-M','0',\
    '-L',stationLat+'/'+str(stationLonNeg)+'/'+stationAlt,\
    str(aosTime), mapDir+'/'+str(fname)+'-map.png']
    print cmdline
    subprocess.call(cmdline)

def decode(fname,aosTime,satName):
    xfNoSpace=xfname.replace(" ","")
    satTimestamp = int(fname)
    fileNameC = datetime.datetime.fromtimestamp(satTimestamp).strftime('%Y%m%d-%H%M')
    if wxAddOverlay in ('yes', 'y', '1'):
	print 'Creating basic image with overlay'
	createoverlay(fname,aosTime,satName)
	cmdline = [ wxInstallDir+'/wxtoimg',wxQuietOpt,wxDecodeOpt,wxAddText,'-Q '+wxJPEGQuality,recdir+'/'+xfNoSpace+'-'+fname+'.wav',imgdir+'/'+satName+'/'+fileNameC+'-normal.jpg']
	print cmdline
	subprocess.call(cmdline)
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
	    cmdline_mcir = [ wxInstallDir+'/wxtoimg',wxQuietOpt,wxDecodeOpt,wxAddText,'-Q '+wxJPEGQuality,'-e','MCIR','-m',mapDir+'/'+fname+'-map.png',recdir+'/'+xfNoSpace+'-'+fname+'.wav',imgdir+'/'+satName+'/'+fileNameC+'-mcir.jpg']
	    subprocess.call(cmdline_mcir)
    else:
	print 'Creating basic image without map'
	cmdline = [ wxInstallDir+'/wxtoimg',wxQuietOpt,wxDecodeOpt,wxAddText,'-Q '+wxJPEGQuality,recdir+'/'+xfNoSpace+'-'+fname+'.wav', imgdir+'/'+satName+'/'+fileNameC+'-normal.jpg']
	subprocess.call(cmdline)
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

def recordWAV(freq,fname,duration,xfname):
    #print xfname
    if xfname in ('NOAA 15', 'NOAA 19', 'NOAA 18'):
	recordFM(freq,fname,duration,xfname)
#	recordDOP(freq,fname,duration,xfname)
	transcode(fname)
	if createSpectro in ('yes', 'y', '1'):
	    spectrum(fname)
    elif xfname in ('METEOR-M2'):
	recordMETEOR(freq,fname,duration,xfname)
	if createSpectro in ('yes', 'y', '1'):
	    spectrum(fname)

def spectrum(fname):
    xfNoSpace=xfname.replace(" ","")
    # Changed spectrum generation, now it creates spectrogram from recorded WAV file
    # Optional
    print 'Creating flight spectrum'
    cmdline = ['sox',recdir+'/'+xfNoSpace+'-'+fname+'.wav', '-n', 'spectrogram','-o',specdir+'/'+xfNoSpace+'-'+fname+'.png']
    subprocess.call(cmdline)

def findNextPass():
    predictions = [pypredict.aoslos(s) for s in satellites]
    aoses = [p[0] for p in predictions]
    nextIndex = aoses.index(min(aoses))
    return (satellites[nextIndex],\
            freqs[nextIndex],\
            predictions[nextIndex]) 

while True:
    (satName, freq, (aosTime, losTime)) = findNextPass()
    now = time.time()
    towait = aosTime-now
    aosTimeCnv=strftime('%H:%M:%S', time.localtime(aosTime))
    emergeTimeUtc=strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(aosTime))
    losTimeCnv=strftime('%H:%M:%S', time.localtime(losTime))
    dimTimeUtc=strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(losTime))
    if towait>0:
        print "waiting "+str(towait).split(".")[0]+" seconds (emerging "+aosTimeCnv+") for "+satName
        writeStatus(freq,aosTimeCnv,losTimeCnv,aosTime,towait,satName,'WAITING')
    	time.sleep(towait)
    # If the script broke and sat is passing by - change record time to reflect time change
    if aosTime<now:
	recordTime=losTime-now
        if recordTime<1:
	    recordTime=1
    elif aosTime>=now:
	recordTime=losTime-aosTime
        if recordTime<1:
	    recordTime=1
    # Go on, for now we'll name recordings and images by Unix timestamp.
    fname=str(aosTime)
    xfname=satName
    print "Beginning pass of "+satName+". Predicted start "+aosTimeCnv+" and end "+losTimeCnv+". Will record for "+str(recordTime).split(".")[0]+" seconds."
    writeStatus(freq,aosTimeCnv,losTimeCnv,str(losTime),str(recordTime).split(".")[0],satName,'RECORDING')
    recordWAV(freq,fname,recordTime,xfname)
    #recordDOP(freq,fname,recordTime,xfname)
    print "Decoding data"
    if xfname in ('NOAA 15', 'NOAA 19', 'NOAA 18'):
	writeStatus(freq,aosTimeCnv,losTimeCnv,str(losTime),str(recordTime).split(".")[0],satName,'DECODING')
	decode(fname,aosTime,satName) # make picture
    print "Finished pass of "+satName+" at "+losTimeCnv+". Sleeping for 10 seconds"
    # Is this really needed?
    time.sleep(10.0)

