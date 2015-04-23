#!/bin/env python
"""pythonista therminsim - a simple theramin style simulator

X axis: frequency
Y axis: volume

Eventually: multitouch

Inspired by http://ptheremin.sourceforge.net, but completely rewritten for numpy/pythonista
"""

import numpy as np
import threading
import time
import wave
import tempfile

SCALES = ("chromatic", "diatonic major", "pentatonic major", "pentatonic minor", "blues")
INIT_FREQ = 20

NAME="PTheremin"
VERSION="0.2.1"


# from "Musical Instrument Design" by Bart Hopkin
sharp = 1.05946
equal_temp_freqs = [16.352, 16.352*sharp, 18.354, 18.354*sharp, 20.602, 21.827, 21.827*sharp, 24.500, 24.500*sharp, 27.500, 27.500*sharp, 30.868]
equal_temp_labels = ['C*', 'C*#', 'D*', 'D*#', 'E*', 'F*', 'F*#', 'G*', 'G*#', 'A*', 'A*#', 'B*']

equal_temp_tuning = zip(equal_temp_labels, equal_temp_freqs)

diatonic_major_intervals = (0, 2, 4, 5, 7, 9, 11)
pentatonic_major_intervals = (0, 2, 4, 7, 9)
pentatonic_minor_intervals = (0, 3, 5, 7, 10)
blues_intervals = (0, 3, 5, 6, 7, 10)

# build up several octaves of notes
NOTES = []
for octave in range(11):
    for label,freq in equal_temp_tuning:
        NOTES.append((label.replace('*', "%d" % octave), (2**octave)*freq))

def just_freqs(notes):
    return [freq for label,freq in notes]

class PlaybackThread(threading.Thread):
    """A thread that continually generates audio."""

    def __init__(self, name, dt):
        self.name = name

        self.fs = 8000.0 # the sample frequency
        self.ft = INIT_FREQ # the base frequency of the instrument
        self.vol = 1

        # setup ping pong file/players
        self.filelist = [tempfile.NamedTemporaryFile(delete=False),
                         tempfile.NamedTemporaryFile(delete=False)]
        #
        self.paused = True
        self.alive = True
        
        threading.Thread.__init__(self, name=name)
        self.dt = 0.1
        self.idx = 0
        self.t = numpy.linspace(0,self.dt,np.round(self.dt*self.fs))
    def run(self):
        def tone_gen():            
            """Generate approximately dt's worth of tone.  Start/stop when signal is near zero, to avoid glitches."""
            ft = self.ft
            dt = self.dt
            fs = self.fs
            twopift = 2*numpy.pi*ft
            sin = numpy.sin
            
            vol = self.vol
            numCycles = floor(ft.*dt)
            numSamples = floor(numCycles/ft*fs)
            return  ( 127 + 128*0.95*vol * sin(twopift*self.t[0:numSamples])).astype('u1').tostring()

        def gen_file(file):
            tone=tone_gen()
            wf=wave.open(file,'w')
            wf.setparams((1, 1, self.fs, 0, 'NONE', 'not compressed'))
            wf.writeframes(tone)
            wf.close()
        
        # to optimize loop performance, dereference everything ahead of time
        
        filelist = self.filelist
        playerlist = []
        idx = self.idx
        dt = self.dt

        gen_file(filelist[idx])
        playerlist[idx] = sound.Player(filelist[idx])
        
        tic = time.time
        while self.alive:
            t0=tic()
            #1) play
            playerlist[idx].play()
            idx = (idx+1)%2
            #2) generate
            gen_file(filelist[idx])
            #3) load
            playerlist[idx] = sound.Player(filelist[idx])
            #4) sleep
            time.sleep(t0+dt-tic())

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


if __name__ == '__main__':
t=PlaybackThread(name="test")
t.start()

