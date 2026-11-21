"""Generate the original, silent guided loops bundled with Serein."""
import math, os, subprocess, shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
FFROOT=Path('/home/locoselli/.local/share/flatpak/runtime/org.kde.Platform/x86_64/6.11/9dabe0b80dee1a55def8e36c8bd52ba24cad65a8bce69a10912cda9846ee5740/files')
FF=FFROOT/'bin/ffmpeg';LOADER=FFROOT/'lib64/ld-linux-x86-64.so.2'
ENV=os.environ.copy();LIB=f'{FFROOT}/lib/x86_64-linux-gnu:{FFROOT}/lib/x86_64-linux-gnu/pulseaudio'
W,H,FPS,SECONDS=480,270,15,12
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font=ImageFont.truetype(FONT,15);small=ImageFont.truetype(FONT,10)
THEMES=[('respirar',(218,234,218),(107,151,117),(239,221,174),'Breathe in  ·  Breathe out'),('soltar',(244,225,211),(173,133,116),(247,204,175),'Soften  ·  Let go'),('sono',(33,45,70),(103,119,162),(222,214,190),'Rest  ·  Release')]

def blend(a,b,t):return tuple(int(x*(1-t)+y*t) for x,y in zip(a,b))

def make_frame(theme,n):
 slug,bg,land,sun,label=theme;t=n/(FPS*SECONDS);phase=2*math.pi*t;breath=(1-math.cos(phase))/2
 im=Image.new('RGB',(W,H));pix=im.load()
 for y in range(H):
  c=blend(bg,land,.18*y/H)
  for x in range(W):pix[x,y]=c
 d=ImageDraw.Draw(im,'RGBA')
 # Concentric guide rings move with a full, slow breath.
 cx,cy=(W//2,128);rad=int(57+22*breath)
 for extra,alpha in [(56,22),(38,30),(20,48)]:
  r=rad+extra;d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=(*sun,alpha))
 d.ellipse((cx-rad,cy-rad,cx+rad,cy+rad),fill=(*sun,230))
 if slug=='sono':
  d.ellipse((cx-32,cy-34,cx+31,cy+31),fill=(245,239,212,255))
  d.ellipse((cx-17,cy-44,cx+45,cy+20),fill=(*bg,255))
  for i in range(19):
   x=(i*73+37)%W;y=(i*41+23)%190;r=1+i%2;d.ellipse((x-r,y-r,x+r,y+r),fill=(245,238,214,170+int(70*abs(math.sin(phase+i)))))
 elif slug=='soltar':
  for i in range(7):
   a=phase*.2+i*2*math.pi/7;x=cx+math.cos(a)*(28+breath*20);y=cy+math.sin(a)*(28+breath*20)
   d.ellipse((x-10,y-15,x+10,y+15),fill=(255,247,232,125))
  d.ellipse((cx-16,cy-16,cx+16,cy+16),fill=(255,250,235,230))
 else:
  d.arc((cx-32,cy-32,cx+32,cy+32),35,145,fill=(255,253,240,210),width=3)
  d.arc((cx-32,cy-32,cx+32,cy+32),215,325,fill=(255,253,240,210),width=3)
 # Soft landscape and readable caption.
 d.ellipse((-70,208,W+75,420),fill=(*land,205))
 d.ellipse((-50,236,W+100,430),fill=(*blend(land,bg,.2),235))
 box=d.textbbox((0,0),label,font=font);tw=box[2]-box[0]
 d.text(((W-tw)/2,226),label,font=font,fill=(255,255,250,245))
 d.text((18,17),'SEREIN  ·  GUIDED VISUAL',font=small,fill=(*land,220) if slug!='sono' else (230,230,245,220))
 return im

for theme in THEMES:
 slug=theme[0];out=ROOT/'static'/'videos'/f'{slug}.webm'
 ffmpeg_cmd=[shutil.which('ffmpeg')] if shutil.which('ffmpeg') else [str(LOADER),'--library-path',LIB,str(FF)]
 cmd=ffmpeg_cmd+['-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libvpx-vp9','-b:v','0','-crf','33','-deadline','realtime','-cpu-used','6',str(out)]
 proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE,env=ENV)
 try:
  for n in range(FPS*SECONDS):proc.stdin.write(make_frame(theme,n).tobytes())
  proc.stdin.close();err=proc.stderr.read();code=proc.wait()
 except BrokenPipeError:
  err=proc.stderr.read();code=proc.wait()
 if code:raise RuntimeError(f'{slug}: {err.decode()}')
 print(slug,out.stat().st_size)
