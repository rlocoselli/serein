/* Generation is admin-only, asynchronous, and requires review before activation. */
let neuralJob=null,neuralPoll=null,neuralConfigured=false;
const neuralErrorKeys={not_configured:'naturalSetup',provider_auth:'naturalAuth',provider_quota:'naturalQuota',voice_not_found:'naturalNoVoices',provider_unavailable:'naturalUnavailable',generation_busy:'naturalBusy',source_changed:'naturalChanged',audio_too_long:'naturalLong',interrupted:'naturalInterrupted'};
function neuralError(error){return t(neuralErrorKeys[error]||'naturalFailed')}
function showNeuralJob(job){neuralJob=job;clearTimeout(neuralPoll);$('neural-previews').replaceChildren();$('neural-publish').classList.toggle('hidden',!['ready','published'].includes(job.status));$('neural-generate').disabled=!neuralConfigured||job.status==='running';
 const label=items.find(item=>item.id===job.session_id)?.title||'#'+job.session_id;$('neural-status').textContent=label+' · '+job.lang.toUpperCase()+' — '+(job.status==='failed'?neuralError(job.error):t({running:'naturalRunning',ready:'naturalReady',published:'naturalPublished'}[job.status]||'naturalFailed'));
 for(const [index,segment] of (job.manifest?.segments||[]).entries()){const label=document.createElement('label');label.textContent=t('naturalPreview')+' '+(index+1);const audio=document.createElement('audio');audio.controls=true;audio.preload='none';audio.src=segment.audio_path;audio.onplay=()=>{resetAudio();for(const other of $('neural-previews').querySelectorAll('audio'))if(other!==audio)other.pause()};label.append(audio);$('neural-previews').append(label)}
 if(job.status==='running')neuralPoll=setTimeout(()=>pollNeuralJob(job.id),1500)
}
async function pollNeuralJob(id){if(!csrf)return;try{showNeuralJob(await api('/api/admin/narration/'+encodeURIComponent(id)))}catch(error){$('neural-status').textContent=neuralError(error.message);$('neural-generate').disabled=!neuralConfigured}}
const beforeNaturalAdmin=refreshAdmin;
refreshAdmin=async function(){await beforeNaturalAdmin();$('neural-session').innerHTML=[...$('audio-session').options].map(option=>`<option value="${esc(option.value)}">${esc(items.find(item=>String(item.id)===option.value)?.title||option.textContent)}</option>`).join('');$('neural-language').value=lang;
 try{const options=await api('/api/admin/narration/options');neuralConfigured=options.configured&&options.voices.length>0;$('neural-voice').innerHTML=options.voices.map(v=>`<option value="${esc(v.id)}">${esc(v.name)}</option>`).join('');$('neural-config').textContent=t(neuralConfigured?'naturalConfigured':options.configured?'naturalNoVoices':'naturalSetup');$('neural-generate').disabled=!neuralConfigured||neuralJob?.status==='running';
 const saved=localStorage.getItem('serein-narration-job');if(saved&&!neuralJob)pollNeuralJob(saved)
 }catch(error){neuralConfigured=false;$('neural-generate').disabled=true;$('neural-config').textContent=neuralError(error.message)}
};
$('neural-form').onsubmit=async event=>{event.preventDefault();$('neural-generate').disabled=true;$('neural-status').textContent=t('naturalRunning');
 try{const job=await api('/api/admin/narration',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:Number($('neural-session').value),lang:$('neural-language').value,voice:$('neural-voice').value,speed:Number($('neural-speed').value)})});localStorage.setItem('serein-narration-job',job.id);showNeuralJob(job)}catch(error){$('neural-status').textContent=neuralError(error.message);$('neural-generate').disabled=!neuralConfigured}
};
$('neural-publish').onclick=async()=>{if(!neuralJob)return;$('neural-publish').disabled=true;try{await api('/api/admin/narration/'+encodeURIComponent(neuralJob.id)+'/publish',{method:'POST'});showNeuralJob({...neuralJob,status:'published'});await load()}catch(error){$('neural-status').textContent=neuralError(error.message)}finally{$('neural-publish').disabled=false}};
const beforeNaturalLogout=$('logout-btn').onclick;$('logout-btn').onclick=async()=>{clearTimeout(neuralPoll);for(const audio of $('neural-previews').querySelectorAll('audio'))audio.pause();neuralJob=null;await beforeNaturalLogout()};
const beforeNaturalAdminClose=$('admin-close').onclick;$('admin-close').onclick=()=>{for(const audio of $('neural-previews').querySelectorAll('audio'))audio.pause();beforeNaturalAdminClose()};
document.addEventListener('visibilitychange',()=>{if(document.hidden)for(const audio of $('neural-previews').querySelectorAll('audio'))audio.pause()});
