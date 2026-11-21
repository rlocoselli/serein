const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');

function player(session){
 const elements=new Map(),calls={audio:[],speech:[]};
 const element=id=>{if(!elements.has(id))elements.set(id,{value:'',checked:true,textContent:'',innerHTML:'',classList:{toggle(){}},closest(){return {classList:{toggle(){}}}},onchange(){}});return elements.get(id)};
 const audio={src:'',paused:true,currentTime:0,duration:20,volume:1,getAttribute(){return this.src},pause(){this.paused=true;this.onpause?.()},play(){this.paused=false;calls.audio.push({path:this.src,offset:this.currentTime});this.onplay?.();return Promise.resolve()}};
 const voice={voiceURI:'local',name:'Local voice',lang:'en-US',localService:true};
 const context=vm.createContext({current:session,activeStep:0,elapsed:0,playing:true,lang:'en',nativeApp:false,music:[],soundKey:'ocean',previewKey:null,narration:audio,bg:{volume:0,pause(){}},$:element,copy:{pt:{},en:{},fr:{},it:{},es:{}},esc:String,t(key){return context.copy.en[key]||key},localStorage:{getItem(){return null},setItem(){}},document:{querySelectorAll(){return []}},speechSynthesis:{getVoices(){return [voice]},cancel(){},addEventListener(){},speak(speech){calls.speech.push(speech.text)}},SpeechSynthesisUtterance:class{constructor(text){this.text=text}},setTimeout(){return 1},clearTimeout(){},setInterval(){return 1},clearInterval(){},requestAnimationFrame(){return 1},cancelAnimationFrame(){},performance:{now(){return 0}},applyLang(){},resetAudio(){context.playing=false;audio.pause()},renderSounds(){},openPlayer(){},previewSound(){},selectedSound(){},setMusic(){}});
 context.window=context;
 for(const file of ['audio-core.js','natural-voice.js','sound-studio.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,'../static',file),'utf8'),context,{filename:file});
 return {calls,audio,context,element,run:code=>vm.runInContext(code,context)};
}

test('missing recordings never fall back to browser speech',()=>{const p=player({script:'Breathe.',protocol:{steps:[{text:'Breathe.',seconds:30}]}});p.run('setVoice(); speak("Breathe.")');assert.equal(p.calls.speech.length,0);assert.equal(p.calls.audio.length,0);assert.equal(p.element('tts-preview').disabled,true)});
test('natural step narration seeks within the step and stops on pause',()=>{const p=player({protocol:{steps:[{text:'One.',seconds:30,audio_path:'/one.mp3'},{text:'Two.',seconds:30,audio_path:'/two.mp3'}]}});p.run('setVoice();activeStep=1;elapsed=35;speak("Two.")');p.audio.onloadedmetadata();assert.equal(p.audio.src,'/two.mp3');assert.equal(p.audio.currentTime,5);const late=p.audio.onloadedmetadata;p.run('resetAudio()');late();assert.equal(p.audio.paused,true);assert.equal(p.calls.speech.length,0);assert.equal(p.calls.audio.length,2)});
test('a full uploaded recording suppresses device speech at step changes',()=>{const p=player({audio_path:'/full.mp3',protocol:{steps:[{text:'One.',seconds:30}]}});p.run('setVoice();speak("One.")');assert.equal(p.calls.audio.length,1);assert.equal(p.calls.speech.length,0)});
test('recording previews and volume changes cannot invoke device TTS',()=>{const p=player({audio_path:'/full.mp3'});p.context.playing=false;p.element('tts-preview').onclick();p.run('changeVoice()');assert.equal(p.calls.audio.length,2);assert.equal(p.calls.speech.length,0)});
test('device speech requires explicitly choosing the device source',()=>{const p=player({script:'Breathe.'});p.element('voice-source').onchange({target:{value:'device'}});assert.deepEqual(p.calls.speech,['Breathe.'])});
