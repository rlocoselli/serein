package io.serein.app;

import android.app.Activity;
import android.os.*;
import android.graphics.Color;
import android.media.*;
import android.webkit.*;
import android.net.Uri;
import android.speech.tts.*;
import android.view.View;
import java.io.*;
import java.util.*;
import org.json.*;

/** Bundled HTML at a virtual HTTPS origin. No INTERNET permission or remote server. */
public final class MainActivity extends Activity {
    private static final String HOST = "appassets.androidplatform.net";
    private WebView web;
    private TextToSpeech tts;
    private volatile boolean voiceReady = false;
    private Vibrator vibrator;
    private volatile boolean foreground = true;
    private AudioManager audio;
    private AudioFocusRequest focus;
    private long lastPulse = 0;
    private volatile String chosenVoiceId="";
    private volatile float calmRate=.74f,calmPitch=.97f,calmVolume=.95f;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        vibrator = (Vibrator)getSystemService(VIBRATOR_SERVICE);
        audio = (AudioManager)getSystemService(AUDIO_SERVICE);
        focus = new AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK)
            .setAudioAttributes(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA).setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build())
            .setOnAudioFocusChangeListener(change -> { if (change < 0) pausePlayback(); }).build();
        tts = new TextToSpeech(this, status -> { voiceReady = status == TextToSpeech.SUCCESS; });
        tts.setOnUtteranceProgressListener(new UtteranceProgressListener() {
            public void onStart(String id) {}
            public void onDone(String id) { speechEvent(id,"done"); }
            public void onError(String id) { speechEvent(id,"error"); }
        });
        web = new WebView(this);
        web.setBackgroundColor(Color.rgb(248,247,242));
        WebSettings settings = web.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setMediaPlaybackRequiresUserGesture(true);
        settings.setSupportMultipleWindows(false);
        web.addJavascriptInterface(new LocalBridge(), "SereinNative");
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest req) {
                return !HOST.equals(req.getUrl().getHost());
            }
            @Override public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest req) {
                return localResponse(req);
            }
        });
        // Apply actual system-bar insets, including Android 15 edge-to-edge enforcement.
        web.setOnApplyWindowInsetsListener((view, insets) -> {
            view.setPadding(insets.getSystemWindowInsetLeft(), insets.getSystemWindowInsetTop(), insets.getSystemWindowInsetRight(), insets.getSystemWindowInsetBottom());
            return insets.consumeSystemWindowInsets();
        });
        setContentView(web);
        web.loadUrl("https://" + HOST + "/index.html");
    }
    private WebResourceResponse localResponse(WebResourceRequest req) {
        Uri uri = req.getUrl();
        if (!HOST.equals(uri.getHost()) || !"https".equals(uri.getScheme())) return error(403);
        String path = uri.getPath();
        if (path == null || path.contains("..") || path.contains("\\")) return error(403);
        if (path.equals("/")) path = "/index.html";
        if (path.equals("/api/sessions")) {
            String lang = uri.getQueryParameter("lang");
            if (lang == null || !Arrays.asList("pt","en","fr","it","es").contains(lang)) lang="pt";
            path = "/data/sessions-" + lang + ".json";
        } else if (path.equals("/api/music")) path = "/data/music.json";
        else if (path.startsWith("/api/")) return error(403);
        try {
            InputStream in = getAssets().open("web" + path);
            String mime = mime(path);
            Map<String,String> headers = new HashMap<>();
            headers.put("Cache-Control", "no-cache");
            headers.put("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; media-src 'self'; font-src 'self'; connect-src 'self'; frame-src 'none'; object-src 'none'");
            return new WebResourceResponse(mime, (mime.startsWith("text/") || mime.equals("application/json"))?"UTF-8":null,200,"OK",headers,in);
        } catch(IOException ex) { return error(404); }
    }
    private static String mime(String path) {
        if(path.endsWith(".html")) return "text/html";
        if(path.endsWith(".js")) return "text/javascript";
        if(path.endsWith(".css")) return "text/css";
        if(path.endsWith(".json")) return "application/json";
        if(path.endsWith(".svg")) return "image/svg+xml";
        if(path.endsWith(".wav")) return "audio/wav";
        if(path.endsWith(".mp3")) return "audio/mpeg";
        if(path.endsWith(".ogg")) return "audio/ogg";
        if(path.endsWith(".m4a")) return "audio/mp4";
        if(path.endsWith(".mp4")) return "video/mp4";
        if(path.endsWith(".webm")) return "video/webm";
        if(path.endsWith(".ttf")) return "font/ttf";
        return "application/octet-stream";
    }
    private static WebResourceResponse error(int code) {
        return new WebResourceResponse("text/plain","UTF-8",code,"Blocked",Collections.emptyMap(),new ByteArrayInputStream(new byte[0]));
    }
    private void pausePlayback() {
        if(tts!=null) tts.stop();
        if(vibrator!=null) vibrator.cancel();
        if(web!=null) runOnUiThread(()->web.evaluateJavascript("window.sereinPause && window.sereinPause()",null));
    }
    public final class LocalBridge {
        @JavascriptInterface public boolean hasVibrator() { return vibrator!=null && vibrator.hasVibrator(); }
        @JavascriptInterface public void pulse() {
            if(!foreground || !hasVibrator())return;
            long now=SystemClock.elapsedRealtime();if(now-lastPulse<1000)return;lastPulse=now;
            vibrator.vibrate(VibrationEffect.createOneShot(35,vibrator.hasAmplitudeControl()?35:VibrationEffect.DEFAULT_AMPLITUDE));
        }
        @JavascriptInterface public void cancelVibration() { if(vibrator!=null)vibrator.cancel(); }
        @JavascriptInterface public boolean requestAudioFocus() { return audio.requestAudioFocus(focus)==AudioManager.AUDIOFOCUS_REQUEST_GRANTED; }
        @JavascriptInterface public void stopSpeech() { if(tts!=null)tts.stop(); }
        @JavascriptInterface public void releaseAudioFocus() { audio.abandonAudioFocusRequest(focus); }
        @JavascriptInterface public String getVoices(String lang) {
            JSONArray result=new JSONArray();
            if(!voiceReady || !validLanguage(lang))return result.toString();
            for(Voice voice:offlineVoices(lang))try{
                JSONObject item=new JSONObject();item.put("id",voice.getName());item.put("name",voice.getName());item.put("lang",voice.getLocale().toLanguageTag());item.put("quality",voice.getQuality());result.put(item);
            }catch(JSONException ignored){}
            return result.toString();
        }
        @JavascriptInterface public boolean configureVoice(String lang,String voiceId,double rate,double pitch,double volume) {
            if(!voiceReady || !validLanguage(lang))return false;
            chosenVoiceId=voiceId==null?"":voiceId;
            calmRate=bounded(rate,.6f,1f,.74f);calmPitch=bounded(pitch,.85f,1.15f,.97f);calmVolume=bounded(volume,0f,1f,.95f);
            return !offlineVoices(lang).isEmpty();
        }
        @JavascriptInterface public boolean speak(String text,String lang) {return speakWithId(text,lang,"legacy-"+SystemClock.elapsedRealtime());}
        @JavascriptInterface public boolean speakWithId(String text,String lang,String id) {
            if(!foreground || !voiceReady || text==null || text.length()>4000 || id==null || id.length()>100 || !validLanguage(lang))return false;
            List<Voice> voices=offlineVoices(lang);if(voices.isEmpty())return false;
            Voice chosen=voices.get(0);for(Voice candidate:voices)if(candidate.getName().equals(chosenVoiceId)){chosen=candidate;break;}
            tts.setVoice(chosen);tts.setSpeechRate(calmRate);tts.setPitch(calmPitch);
            Bundle params=new Bundle();params.putFloat(TextToSpeech.Engine.KEY_PARAM_VOLUME,calmVolume);
            return tts.speak(text,TextToSpeech.QUEUE_FLUSH,params,id)==TextToSpeech.SUCCESS;
        }
    }
    private static boolean validLanguage(String lang){return Arrays.asList("pt","en","fr","it","es").contains(lang);}
    private static float bounded(double n,float min,float max,float fallback){return Double.isNaN(n)||Double.isInfinite(n)?fallback:(float)Math.max(min,Math.min(max,n));}
    private List<Voice> offlineVoices(String lang){
        List<Voice> result=new ArrayList<>();Set<Voice> voices=tts.getVoices();
        if(voices!=null)for(Voice voice:voices)if(!voice.isNetworkConnectionRequired() && voice.getLocale().getLanguage().equals(lang))result.add(voice);
        Collections.sort(result,(a,b)->a.getQuality()!=b.getQuality()?Integer.compare(b.getQuality(),a.getQuality()):a.getName().compareTo(b.getName()));return result;
    }
    private void speechEvent(String id,String event){runOnUiThread(()->{if(web!=null && foreground)web.evaluateJavascript("window.sereinSpeechEvent && window.sereinSpeechEvent("+JSONObject.quote(id)+","+JSONObject.quote(event)+")",null);});}
    @Override protected void onPause() { foreground=false;pausePlayback();audio.abandonAudioFocusRequest(focus);super.onPause(); }
    @Override protected void onResume() { super.onResume();foreground=true; }
    @Override protected void onDestroy() { if(tts!=null){tts.stop();tts.shutdown();}if(vibrator!=null)vibrator.cancel();if(web!=null){web.removeJavascriptInterface("SereinNative");web.destroy();}super.onDestroy(); }
    @Override public void onBackPressed() { web.evaluateJavascript("window.sereinBack ? window.sereinBack() : false", result -> { if(!"true".equals(result))finish(); }); }
}
