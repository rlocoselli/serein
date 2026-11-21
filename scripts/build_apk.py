"""Reproducible debug APK using installed Android SDK tools; Gradle alternative in android/."""
import os,subprocess,shutil,zipfile,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--output',default='dist/serein-calm-audio-debug.apk');args=parser.parse_args()
SDK=Path(os.getenv('ANDROID_HOME',Path.home()/'Android/Sdk'));TOOLS=SDK/'build-tools/35.0.0';PLATFORM=SDK/'platforms/android-35/android.jar'
JAVA=Path(os.getenv('JAVA_HOME','/usr/lib/jvm/java-17-openjdk-amd64'))
OUT=ROOT/'android/app/build/local';OUT.mkdir(parents=True,exist_ok=True)
ENV=os.environ.copy();ENV['JAVA_HOME']=str(JAVA);ENV['PATH']=str(JAVA/'bin')+os.pathsep+ENV['PATH']
def run(args):subprocess.run([str(a) for a in args],check=True,cwd=ROOT,env=ENV)
run(['python3',ROOT/'scripts/export_android_assets.py'])
run([TOOLS/'aapt2','compile','--dir',ROOT/'android/app/src/main/res','-o',OUT/'res.zip'])
run([TOOLS/'aapt2','link','-I',PLATFORM,'--manifest',ROOT/'android/app/src/main/AndroidManifest.xml','--min-sdk-version','26','--target-sdk-version','35','--version-code','3','--version-name','1.2.0','--debug-mode','-A',ROOT/'android/app/src/main/assets','-o',OUT/'unsigned.apk',OUT/'res.zip'])
classes=OUT/'classes';classes.mkdir(exist_ok=True)
sources=list((ROOT/'android/app/src/main/java').rglob('*.java'))
run([JAVA/'bin/javac','--release','8','-classpath',PLATFORM,'-d',classes,*sources])
dex=OUT/'dex';dex.mkdir(exist_ok=True)
run([TOOLS/'d8','--min-api','26','--lib',PLATFORM,'--output',dex,*classes.rglob('*.class')])
with zipfile.ZipFile(OUT/'unsigned.apk','a',compression=zipfile.ZIP_DEFLATED) as apk:
 for file in dex.glob('*.dex'):apk.write(file,file.name)
run([TOOLS/'zipalign','-f','4',OUT/'unsigned.apk',OUT/'aligned.apk'])
key=ROOT/'.local-signing/serein-debug.jks'
key.parent.mkdir(exist_ok=True,mode=0o700)
legacy=Path('/tmp/serein-local-debug.jks')
if not key.exists() and legacy.exists():shutil.copy2(legacy,key)
if not key.exists():run([JAVA/'bin/keytool','-genkeypair','-keystore',key,'-storepass','android','-keypass','android','-alias','androiddebugkey','-dname','CN=Android Debug,O=Serein,C=PT','-keyalg','RSA','-keysize','2048','-validity','10000','-noprompt'])
if key.exists():key.chmod(0o600)
final=ROOT/args.output
final.parent.mkdir(parents=True,exist_ok=True)
run([TOOLS/'apksigner','sign','--ks',key,'--ks-pass','pass:android','--key-pass','pass:android','--out',final,OUT/'aligned.apk'])
run([TOOLS/'apksigner','verify','--verbose',final])
print('APK:',final,'bytes:',final.stat().st_size)
