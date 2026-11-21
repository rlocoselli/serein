"""Original stereo soundscapes with periodic synthesis and restrained peaks. No samples."""
import json, wave
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'static/audio';OUT.mkdir(exist_ok=True)
RATE=22050;SECONDS=32;N=RATE*SECONDS;t=np.arange(N)/RATE;rng=np.random.default_rng(20261120)

def noise(power=.5,lo=40,hi=4000):
 frequencies=np.fft.rfftfreq(N,1/RATE)
 weights=np.maximum(frequencies,lo)**(-power)
 weights*=1/(1+(lo/np.maximum(frequencies,1))**6)/(1+(frequencies/hi)**6)
 spectrum=(rng.normal(size=len(frequencies))+1j*rng.normal(size=len(frequencies)))*weights;spectrum[0]=0
 a=np.fft.irfft(spectrum,n=N);return a/np.std(a)

def event(target,start,frequency,duration,level=.1,decay=None,chirp=0):
 count=int(duration*RATE);u=np.arange(count)/RATE
 env=np.sin(np.pi*np.arange(count)/max(1,count-1))**2
 if decay:env=np.minimum(1,u/.035)*np.exp(-u/decay)
 wavepart=np.sin(2*np.pi*(frequency*u+chirp*u*u/2))*env*level
 indices=(int(start*RATE)+np.arange(count))%N
 target[indices]+=wavepart

def stereo(left,right):return np.column_stack([left,right])
def reverb(a):return a+.18*np.roll(a,int(.19*RATE),axis=0)+.1*np.roll(a,int(.37*RATE),axis=0)

def save(key,a):
 a=np.asarray(a);a=stereo(a,a) if a.ndim==1 else a
 a-=np.mean(a,axis=0);rms=np.sqrt(np.mean(a*a));a*=.09/max(rms,1e-6)
 peak=np.max(np.abs(a));a*=min(1,.48/max(peak,1e-6))
 # Tiny seam crossfade prevents discontinuity even after quantization.
 edge=int(.02*RATE);join=(a[:edge]+a[-edge:])/2
 w=np.linspace(0,1,edge)[:,None];a[:edge]=join*(1-w)+a[:edge]*w;a[-edge:]=a[-edge:]*(1-w)+join*w
 a[-1]=a[0]
 pcm=np.clip(a*32767,-32767,32767).astype('<i2')
 with wave.open(str(OUT/(key+'.wav')),'wb') as f:f.setparams((2,2,RATE,0,'NONE','not compressed'));f.writeframes(pcm.tobytes())
 return {'key':key,'seconds':SECONDS,'rms':float(np.sqrt(np.mean(a*a))),'peak':float(np.max(np.abs(a))),'seam_delta':float(np.max(np.abs(a[-1]-a[0])))}

metrics=[]
for key in ['ocean','rain','forest','stream','fireplace','night','brown','piano','pad']:
 channels=[]
 for channel in range(2):
  phase=channel*.24
  if key=='ocean':a=noise(.6,45,1800)*(.6+.25*np.sin(2*np.pi*t/8+phase)+.12*np.sin(2*np.pi*t/16))
  elif key=='rain':a=noise(.25,180,6500)*(.8+.06*np.sin(2*np.pi*t/16+phase))
  elif key=='forest':
   a=noise(.8,75,1500)*.18*(.8+.2*np.sin(2*np.pi*t/16+phase))
   for at,freq in [(3,1450),(10,1800),(18,1250),(27,1650)]:
    for offset in [0,.34,.8]:event(a,at+offset+channel*.07,freq,.24,.055,chirp=500)
  elif key=='stream':a=noise(.15,180,5000)*(.65+.06*np.sin(2*np.pi*t*1.5+phase))+.18*noise(.8,65,800)
  elif key=='fireplace':
   a=noise(.7,50,1900)*.4
   for at in [2.3,6.8,12.4,20.7,25.6,30.2]:event(a,at+channel*.03,350,.13,.06)
  elif key=='night':
   a=noise(.9,40,1000)*.08
   for at in np.arange(1,32,4):
    for off in [0,.18,.36]:event(a,at+off,2300+channel*40,.1,.018)
  elif key=='brown':a=noise(1,28,1800)
  elif key=='piano':
   a=np.zeros(N)
   for at,chord in zip([0,8,16,24],[[48,55,59,64,67],[45,52,55,60,64],[41,48,52,57,60],[43,50,57,62,67]]):
    for i,midi in enumerate(chord):
     freq=440*2**((midi-69)/12);start=at+i*.7+channel*.012
     event(a,start,freq,7,.16,decay=2.4);event(a,start,2*freq,5,.025,decay=1.6)
   a=reverb(a)
  else:
   a=np.zeros(N)
   for at,chord in [(0,[48,55,59,64]),(16,[45,52,55,60])]:
    for midi in chord:event(a,at+channel*.04,440*2**((midi-69)/12),24,.12)
   a=reverb(a)
  channels.append(a)
 metrics.append(save(key,stereo(*channels)))
# Public-domain Beethoven theme, a new original mellow keyboard rendering.
a=np.zeros(N);notes=[64,64,65,67,67,65,64,62,60,60,62,64,64,62,62,64,64,65,67,67,65,64,62,60,60,62,64,62,60,60]
for at,midi in enumerate(notes):
 freq=440*2**((midi-69)/12);event(a,at+.15,freq,4,.18,decay=1.6);event(a,at+.15,freq*2,3,.025,decay=1)
metrics.append(save('beethoven-joy',reverb(stereo(a,np.roll(a,int(.012*RATE))))))
titles={'ocean':'Mar suave','rain':'Chuva leve','forest':'Floresta ao amanhecer','stream':'Riacho tranquilo','fireplace':'Lareira acolhedora','night':'Noite no jardim','brown':'Ruído marrom','piano':'Piano suave','pad':'Atmosfera serena','classical':'Beethoven · Ode to Joy'}
metadata=[]
for i,(key,title) in enumerate(titles.items()):
 classical=key=='classical';metadata.append({'id':-(i+1),'key':key,'title':title,'category':'music' if key in ['piano','pad','classical'] else ('noise' if key=='brown' else 'nature'),'audio_path':'/audio/'+('beethoven-joy' if classical else key)+'.wav','composer':'Ludwig van Beethoven' if classical else 'Serein','performer':'Serein · original stereo synthesis','license':'CC0 1.0 (recording); public-domain composition' if classical else 'CC0 1.0','license_url':'https://creativecommons.org/publicdomain/zero/1.0/','source_url':'https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=528' if classical else 'scripts/generate_soundscapes.py','attribution':'Original stereo synthesis for Serein; CC0 1.0.'+(' Beethoven, Ode to Joy theme; original synthetic keyboard arrangement, score context: Mutopia #528.' if classical else ''),'published':1})
(OUT/'credits.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
(OUT/'audio-validation.json').write_text(json.dumps(metrics,indent=2)+'\n')
print('Generated 10 stereo loops: 32 seconds each, normalized with matched seams.')
