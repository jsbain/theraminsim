#!/bin/env python
"""pythonista therminsim - a simple theramin style simulator

X axis: frequency
Y axis: volume

Eventually: multitouch

Inspired by http://ptheremin.sourceforge.net, but completely rewritten for numpy/pythonista
"""

import numpy
import threading
import time
import wave
import tempfile
import sound
#set min and max frequencies (hz)
fmin=150.0
fmax=1000.0

class PlaybackThread(threading.Thread):
    """A thread that continually generates audio."""

    def __init__(self, name, dt):
        #self.name = name

        self.fs = 4000.0 # the sample frequency
        self.ft = fmin # the tone frequency of the instrument
        self.vol = 1  #0-1

        # setup ping pong file/players
        self.filelist = [tempfile.NamedTemporaryFile(),
                         tempfile.NamedTemporaryFile()]
        #
        self.alive = True    

        self.dt = dt #update interval
        self.idx = 0 # which buffer are we writing to
        self.t = numpy.linspace(0,self.dt,np.round(self.dt*self.fs))  
        threading.Thread.__init__(self, name=name)
        
    def run(self):
        def tone_gen():            
            """Generate approximately dt's worth of tone.  Start/stop when signal is near zero, to avoid glitches.  this doesnt really work"""
            ft = self.ft
            dt = self.dt
            fs = self.fs
            twopift = 2*numpy.pi*ft
            sin = numpy.sin
            floor=numpy.floor
            vol = self.vol
            numCycles = floor(ft*dt)
            numSamples = floor(numCycles/ft*fs)
            return  ( 127 + 128*0.95*vol * sin(twopift*self.t[0:numSamples])).astype('u1').tostring()

        def gen_file(file):
            tone=tone_gen()
            file.seek(0,0)
            wf=wave.open(file,'w')
            wf.setparams((1, 1, self.fs, 0, 'NONE', 'not compressed'))
            wf.writeframes(tone)
            wf.close()
        
        # to optimize loop performance, dereference everything ahead of time
        
        filelist = self.filelist
        playerlist = [None,None ]
        idx = self.idx
        dt = self.dt

        gen_file(filelist[idx])
        playerlist[idx] = sound.Player(filelist[idx].name)
        
        tic = time.time
        while self.alive:
            t0=tic()
            #1) play
            playerlist[idx].play()
            idx = (idx+1)%2
            #2) generate
            gen_file(filelist[idx])
            #3) load
            p=playerlist[idx] = sound.Player(filelist[idx].name)
            #4) sleep
            try:
               time.sleep((t0+dt-tic())-0.005)
               #time.sleep((p.duration-p.current_time))
            except:
                pass
        self.cleanup()
        
    def cleanup(self):
        try:
            [x.close() for x in self.filelist]
        except:
            pass
    def stop(self):
        self.alive = False

    def set_new_freq(self, freq, vol):
        """Updates the input frequency."""
        self.ft = freq
        self.vol = vol

    def get_wav_data(self):
        return self.recording

    def clear_wav_data(self):
        self.recording = []

class Theramin(ui.View):
    def __init__(self,dt):
        self.t={}
        self.dt=dt
    def touch_began(self,touch):
        self.t[touch.touch_id]=PlaybackThread(name="test",dt=self.dt)
        (x,y)=touch.location
        self.setfreq(touch.touch_id,y/self.height,x/self.width)
        self.t[touch.touch_id].start()
    def touch_moved(self,touch):
        (x,y)=touch.location
        self.setfreq(touch.touch_id,y/self.height,x/self.width)
    def touch_ended(self,touch):
        try:
            self.t[touch.touch_id].stop()
        except KeyError:
            pass
    def setfreq(self,touch_id,freq,vol):
        freq=fmin+(fmax-fmin)*(1-freq)
        self.t[touch_id].vol=vol
        self.t[touch_id].ft=freq
    def will_close(self):
        for t in self.t.values():
            try:
                t.stop()
            except:
                pass
if __name__ == '__main__':
    v=Theramin(0.1)
    v.present()


