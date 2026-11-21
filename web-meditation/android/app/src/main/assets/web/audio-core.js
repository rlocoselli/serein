/* Pure audio settings and cancellation-safe narration sequencing. */
(function(root){
 const clamp=(n,min,max,fallback)=>Number.isFinite(Number(n))?Math.min(max,Math.max(min,Number(n))):fallback;
 function settings(input={}){if(!input||typeof input!=='object')input={};return {source:input.source==='device'?'device':'recorded',rate:clamp(input.rate,.6,1,.74),pitch:clamp(input.pitch,.85,1.15,.97),voiceVolume:clamp(input.voiceVolume,0,1,.95),gap:clamp(input.gap,300,2500,1400),soundVolume:clamp(input.soundVolume,0,.5,.18),soundKey:typeof input.soundKey==='string'?input.soundKey:'ocean',voices:input.voices&&typeof input.voices==='object'?input.voices:{},duck:input.duck!==false}}
 function recording(session,step=0,elapsed=0){if(!session)return null;if(session.audio_path)return {path:session.audio_path,offset:Math.max(0,elapsed),whole:true};const steps=session.protocol?.steps||[],index=Math.max(0,step),clip=steps[index];if(!clip?.audio_path)return null;const start=steps.slice(0,index).reduce((sum,s)=>sum+s.seconds,0);return {path:clip.audio_path,offset:Math.max(0,elapsed-start),whole:false}}
 function sentences(text){return (String(text).match(/[^.!?]+(?:[.!?]+|$)/g)||[]).map(s=>s.trim()).filter(Boolean)}
 class NarrationQueue {
  constructor(transport,schedule=(fn,ms)=>setTimeout(fn,ms),unschedule=id=>clearTimeout(id)){this.transport=transport;this.schedule=schedule;this.unschedule=unschedule;this.serial=0;this.timer=null;this.busy=false}
  cancel(){this.serial++;this.unschedule(this.timer);this.timer=null;this.busy=false;this.transport.cancel()}
  start(text,options={}){this.cancel();const serial=this.serial,parts=sentences(text);let index=0;this.busy=parts.length>0;options.onStart?.();
   const next=()=>{if(serial!==this.serial)return;if(index>=parts.length){this.busy=false;options.onEnd?.();return}const id=`serein-${serial}-${index}`;const part=parts[index++];let settled=false;const finish=(error)=>{if(settled||serial!==this.serial)return;settled=true;if(error){this.busy=false;options.onError?.(error);return}this.timer=this.schedule(next,Math.max(0,options.gap||0))};try{this.transport.speak(part,id,()=>finish(),error=>finish(error||'speech-error'))}catch(error){finish(error)}};
   if(parts.length)next();else{this.busy=false;options.onEnd?.()}
  }
 }
 const api={settings,sentences,recording,NarrationQueue};root.SereinAudioCore=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
