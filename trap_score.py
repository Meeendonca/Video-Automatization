"""Original action-oriented American-style trap, synthesized without recordings or samples."""
import math
import wave
import numpy as np


def create_score(path, duration, bpm=152):
    rate=24000; beat=60/bpm; bar=4*beat
    if not 0 < duration <= 901:
        raise ValueError('Invalid score duration')
    roots=[30,30,26,28]
    with wave.open(str(path),'wb') as stream:
        stream.setparams((2,2,rate,0,'NONE','not compressed'))
        for offset in range(0,math.ceil(duration*rate),rate):
            t=np.arange(offset,min(offset+rate,math.ceil(duration*rate)))/rate
            x=np.zeros((len(t),2))
            for b in range(max(0,int(t[0]/bar)-2),int(t[-1]/bar)+1):
                root=roots[(b//2)%4]; start=b*bar
                age=t-start; safe=np.maximum(age,0)
                env=np.where(age>=0,np.clip(safe/.006,0,1)*np.exp(-safe/.22),0)
                for n in [root+24,root+31,root+36]:
                    f=440*2**((n-69)/12)
                    for side in range(2):
                        x[:,side]+=.055*env*(np.sin(2*np.pi*f*age)+.35*np.sin(4*np.pi*f*age)+.12*np.sin(6*np.pi*f*age))
                # Rounded 808, pitched kick and restrained clap on halftime backbeat.
                for pos in ([0,.75,1.5,2.75,3.5] if b%2 else [0,1.25,2.5,3.25]):
                    a=t-start-pos*beat; u=np.maximum(a,0)
                    e=np.where(a>=0,(1-np.exp(-u/.004))*np.exp(-u/.25),0)
                    x += (.42*e*np.sin(2*np.pi*(46*u+55*.024*(1-np.exp(-u/.024)))))[:,None]
                    f=440*2**((root-69)/12)
                    phase=2*np.pi*f*(u+.08*.06*(1-np.exp(-u/.06)))
                    bass=.31*np.where(a>=0,(1-np.exp(-u/.004))*np.exp(-u/.48),0)*np.tanh(2.2*(np.sin(phase)+.15*np.sin(2*phase)))
                    x+=bass[:,None]
                for pos in [2]:
                    a=t-start-pos*beat;u=np.maximum(a,0)
                    rng=np.random.default_rng(5701+b)
                    noise=rng.uniform(-1,1,len(t));noise=np.convolve(noise,[.25,.5,.25],mode='same')
                    e=np.where(a>=0,(1-np.exp(-u/.002))*np.exp(-u/.085),0)
                    x+=(.38*noise*e + .09*e*np.sin(2*np.pi*185*u))[:,None]
                # Dry noise hats, accented eighths and one short triplet fill.
                # Avoid the previous pitched, metallic oscillator stack.
                positions=list(np.arange(0,4,.5)) + ([3+1/6,3+1/3] if b%2 else [1.75,3.75])
                for j,pos in enumerate(positions):
                    a=t-start-pos*beat;u=np.maximum(a,0)
                    e=np.where(a>=0,(1-np.exp(-u/.0015))*np.exp(-u/.016),0)
                    rng=np.random.default_rng(9107+b*101+j)
                    raw=rng.uniform(-1,1,len(t)+4)
                    # Broad filtered noise rather than a ringing note.
                    tone=np.convolve(raw,[-.18,-.32,1,-.32,-.18],mode='valid')
                    velocity=.85 if pos%1==0 else .55
                    x[:,j%2]+=.075*velocity*e*tone
                    x[:,1-j%2]+=.06*velocity*e*tone
                # Sparse minor-key bell motif, leaving space for speech.
                for j,pos in enumerate([0,.75,1.5,2.75,3.5]):
                    a=t-start-pos*beat;u=np.maximum(a,0)
                    f=440*2**((root+36+[0,7,12,3,7][j]-69)/12)
                    e=np.where(a>=0,(1-np.exp(-u/.009))*np.exp(-u/.32),0)
                    x+=(.047*e*(np.sin(2*np.pi*f*u)+.18*np.sin(2*np.pi*2*f*u)))[:,None]
            fade=np.minimum(t/.25,1)*np.clip((duration-t)/.7,0,1)
            x=np.tanh(x*1.15)*.8*fade[:,None]
            stream.writeframes((x*32767).astype('<i2').tobytes())
