import time
from time import gmtime, strftime
import pypredict
import subprocess

satellites = ['NOAA 18','NOAA 19','NOAA 15']
freqs = [137912500, 137100000, 137625000]
sample ='48000'
wavrate='11025'
location='lon=53.3404,lat=-15.0579,alt=20'
recdir='/opt/wxsat/rec'
specdir='/opt/wxsat/spectro'
imgdir='/opt/wxsat/img'

def runForDuration(cmdline, duration):
    try:
        #child = subprocess.Popen(cmdline, stdin=-subprocess.PIPE, shell=True)
        child = subprocess.Popen(cmdline)
        time.sleep(duration)
        child.terminate()
    except OSError as e:
        print "OS Error during command: "+" ".join(cmdline)
        print "OS Error: "+e.strerror

def recordFM(freq, fname, duration, xfname):
    # still experimenting with options - unsure as to best settings
    #print freq
    #print fname
    #print duration
    #print xfname

    cmdline = ['rtl_fm',\
		'-f',str(freq),\
		'-s',sample,\
		'-g','43',\
		'-F','9',\
		'-A','fast',\
		'-E','dc',\
		'-p','-135',\
		recdir+'/'+fname+'.raw' ]

    #print cmdline
    
    runForDuration(cmdline, duration)

def transcode(fname):
    cmdline = ['sox','-t','raw','-r',sample,'-es','-b','16','-c','1','-V1',recdir+'/'+fname+'.raw',recdir+'/'+fname+'.wav','rate',wavrate]
    subprocess.call(cmdline)

def doppler(fname,emergeTime):
    #cmdline = ['sox','-t','raw','-r',sample,'-es','-b','16','-c','1','-V1',recdir+'/'+fname+'.raw',recdir+'/'+fname+'.wav','rate',wavrate]
    cmdline = ['doppler', 
    '-d','',\
    '--tlefile', '~/.predict/predict.tle',\
    '--tlename', xfname,\
    '--location', location,\
    '--freq ', +str(freq),\
    '-i', 'i16',\
    '-s', sample ]
    subprocess.call(cmdline)

def decode(fname):
    cmdline = ['/usr/local/bin/wxtoimg','-A',recdir+'/'+fname+'.wav', imgdir+'/'+fname+'.jpg']
    subprocess.call(cmdline)

def recordWAV(freq,fname,duration):
    recordFM(freq,fname,duration,xfname)
    transcode(fname)
    spectrum(fname)

def spectrum(fname):
    #cmdline = ['rtl_power','-f','137000000:138000000:1000','-i','1m','-g','40',fname+'.csv']
    cmdline = ['sox',recdir+'/'+fname+'.wav', '-n', 'spectrogram','-o',specdir+'/'+fname+'.png']
    #runForDuration(cmdline,duration)
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
    #print emergeTimeUtc
    #aosTimeCnv=time.ctime(int(aosTime))
    #print freq
    if towait>0:
        print "waiting "+str(towait).split(".")[0]+" seconds (emerging "+aosTimeCnv+") for "+satName
        time.sleep(towait)
    # dir= sat name and filename = start time 
    if aosTime<now:
	recordTime=losTime-now
    elif aosTime>=now:
	recordTime=losTime-aosTime
    fname=str(aosTime)
    xfname=satName
    print "beginning pass "+fname+" predicted start "+aosTimeCnv+" and end "+losTimeCnv+". Will record for "+str(recordTime)+" seconds."
    recordWAV(freq,fname,recordTime)
    decode(fname) # make picture
    # spectrum(fname,losTime-aosTime)
    print "finished pass of "+satName+" at "+losTimeCnv+". Sleeping for 60 seconds"
    time.sleep(60.0)

