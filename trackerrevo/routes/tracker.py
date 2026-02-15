"""
Aircraft Tracker Routes
Real-time aircraft tracking with map visualization for São Paulo region
"""
import os
from flask import Blueprint, jsonify, Response
from services.opensky_service import (
    get_opensky_service,
    SAO_PAULO_BOUNDS,
    TRACKED_AIRCRAFT,
    AIRPORTS,
)

tracker_bp = Blueprint('tracker', __name__)

# Cache the inline page
_cached_page = None


def _build_page():
    """Build the tracker page with Leaflet inlined"""
    global _cached_page
    if _cached_page:
        return _cached_page

    # Read Leaflet files
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    leaflet_css = ''
    leaflet_js = ''

    css_path = os.path.join(base, 'static', 'vendor', 'leaflet.css')
    js_path = os.path.join(base, 'static', 'vendor', 'leaflet.js')

    try:
        with open(css_path, 'r') as f:
            leaflet_css = f.read()
    except Exception:
        leaflet_css = '/* leaflet.css not found */'

    try:
        with open(js_path, 'r') as f:
            leaflet_js = f.read()
    except Exception:
        leaflet_js = '/* leaflet.js not found */'

    html = _get_html(leaflet_css, leaflet_js)
    _cached_page = html
    return html


def _get_html(leaflet_css, leaflet_js):
    return '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Radar de Aeronaves</title>
<style>
''' + leaflet_css + '''
</style>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #0a0e17;
    color: #e0e0e0;
    overflow: hidden;
    height: 100vh;
    width: 100vw;
}
#loading-screen {
    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    background: #0a0e17;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    z-index: 9999;
}
.spinner {
    width: 40px; height: 40px;
    border: 3px solid #1e293b; border-top-color: #38bdf8;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 20px;
}
@keyframes spin { to { transform: rotate(360deg); } }
.loader-text { color: #38bdf8; font-size: 20px; font-weight: 700; margin-bottom: 8px; }
.loader-sub { color: #64748b; font-size: 13px; }
#error-msg { color: #ef4444; font-size: 13px; margin-top: 16px; display: none; }
#topbar {
    position: fixed; top: 0; left: 0; right: 0; height: 48px;
    background: rgba(10,14,23,0.95); border-bottom: 1px solid #1e293b;
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 16px; z-index: 1000;
}
#topbar .left { display: flex; align-items: center; gap: 12px; }
#topbar .title { font-size: 16px; font-weight: 700; color: #38bdf8; }
#topbar .stats { font-size: 12px; color: #64748b; }
#topbar .stats span { color: #38bdf8; font-weight: 600; }
#topbar .right { display: flex; align-items: center; gap: 10px; }
.btn {
    background: #1e293b; border: 1px solid #334155; color: #94a3b8;
    padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px;
}
.btn:hover { background: #334155; color: #e2e8f0; }
.btn.active { background: #0ea5e9; color: white; border-color: #0ea5e9; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.status-dot.online { background: #22c55e; box-shadow: 0 0 6px #22c55e; }
.status-dot.offline { background: #ef4444; }
.status-dot.loading { background: #f59e0b; animation: blink 1s infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }
#map {
    position: fixed; top: 48px; left: 0; right: 0; bottom: 0;
    z-index: 1; background: #0a0e17;
}
#tracked-panel {
    position: fixed; top: 60px; left: 12px; width: 260px;
    background: rgba(10,14,23,0.92); border: 1px solid #1e293b;
    border-radius: 10px; z-index: 900; overflow: hidden;
}
.panel-header {
    background: rgba(30,41,59,0.8); padding: 10px 14px;
    font-size: 13px; font-weight: 600; color: #38bdf8;
    border-bottom: 1px solid #1e293b;
}
.tracked-item {
    padding: 10px 14px; border-bottom: 1px solid rgba(30,41,59,0.5);
    cursor: pointer;
}
.tracked-item:hover { background: rgba(30,41,59,0.6); }
.tracked-item:last-child { border-bottom: none; }
.tracked-item .reg { font-size: 15px; font-weight: 700; letter-spacing: 1px; }
.tracked-item .reg.detected { color: #22c55e; }
.tracked-item .reg.no-signal { color: #64748b; }
.tracked-item .ti { font-size: 11px; margin-top: 3px; }
.tracked-item .ti.em-voo { color: #38bdf8; }
.tracked-item .ti.no-solo { color: #f59e0b; }
.tracked-item .ti.sem-sinal { color: #64748b; }
.tracked-item .details { font-size: 10px; color: #64748b; margin-top: 2px; }
#events-panel {
    position: fixed; bottom: 12px; left: 12px; width: 340px; max-height: 250px;
    background: rgba(10,14,23,0.92); border: 1px solid #1e293b;
    border-radius: 10px; z-index: 900; overflow: hidden;
    display: flex; flex-direction: column;
}
#events-panel .panel-header { color: #f59e0b; }
#events-list { overflow-y: auto; flex: 1; padding: 4px 0; }
.event-item { padding: 6px 14px; font-size: 12px; border-bottom: 1px solid rgba(30,41,59,0.3); }
.event-item .event-time { color: #64748b; font-size: 10px; }
.event-item.takeoff { border-left: 3px solid #22c55e; }
.event-item.landing { border-left: 3px solid #3b82f6; }
.event-item.detected { border-left: 3px solid #f59e0b; }
.event-item.lost_signal { border-left: 3px solid #ef4444; }
.event-item .event-msg { color: #e2e8f0; font-weight: 500; }
.no-events { padding: 16px; text-align: center; color: #475569; font-size: 12px; }
#notification-popup {
    position: fixed; top: 60px; right: 12px; z-index: 1100;
    display: flex; flex-direction: column; gap: 8px; pointer-events: none;
}
.notif {
    background: rgba(10,14,23,0.95); border: 2px solid #f59e0b;
    border-radius: 10px; padding: 14px 18px; min-width: 280px; pointer-events: auto;
}
.notif.takeoff { border-color: #22c55e; }
.notif.landing { border-color: #3b82f6; }
.notif.detected { border-color: #f59e0b; }
.notif .notif-title { font-size: 16px; font-weight: 700; margin-bottom: 4px; }
.notif.takeoff .notif-title { color: #22c55e; }
.notif.landing .notif-title { color: #3b82f6; }
.notif.detected .notif-title { color: #f59e0b; }
.notif .notif-body { font-size: 12px; color: #94a3b8; }
.leaflet-popup-content-wrapper { background: rgba(15,23,42,0.95)!important; color:#e2e8f0!important; border:1px solid #334155!important; border-radius:8px!important; }
.leaflet-popup-tip { background: rgba(15,23,42,0.95)!important; }
.leaflet-popup-content { margin: 10px 14px!important; font-size: 12px!important; line-height: 1.6!important; }
.popup-reg { font-size: 16px; font-weight: 700; color: #38bdf8; }
.popup-tracked { color: #22c55e; font-size: 10px; font-weight: 600; text-transform: uppercase; }
.popup-field { color: #94a3b8; }
.popup-value { color: #e2e8f0; font-weight: 500; }
.airport-label { background: rgba(15,23,42,0.8); border: 1px solid #334155; border-radius: 4px; padding: 2px 6px; font-size: 10px; font-weight: 600; color: #94a3b8; white-space: nowrap; }
.back-link { color: #64748b; text-decoration: none; font-size: 12px; }
.back-link:hover { color: #94a3b8; }
.leaflet-div-icon { background: transparent; border: none; }
@media (max-width: 640px) { #tracked-panel { width: 200px; } #events-panel { width: calc(100% - 24px); } }
</style>
</head>
<body>

<div id="loading-screen">
    <div class="spinner"></div>
    <div class="loader-text">RADAR DE AERONAVES</div>
    <div class="loader-sub" id="loading-status">Carregando...</div>
    <div id="error-msg"></div>
</div>

<div id="topbar">
    <div class="left">
        <a href="/" class="back-link">&#8592; Dashboard</a>
        <div class="title">RADAR AO VIVO</div>
        <div class="stats">
            <span class="status-dot loading" id="status-dot"></span>
            <span id="aircraft-count">0</span> aeronaves |
            <span id="last-update">--:--:--</span>
        </div>
    </div>
    <div class="right">
        <button class="btn active" id="btn-sound" onclick="window.toggleSound()">Som ON</button>
        <button class="btn" onclick="window.refreshNow()">Atualizar</button>
    </div>
</div>

<div id="map"></div>

<div id="tracked-panel">
    <div class="panel-header">AERONAVES RASTREADAS</div>
    <div id="tracked-list">
        <div class="tracked-item"><div class="reg no-signal">PR-OMB</div><div class="ti sem-sinal">Aguardando...</div></div>
        <div class="tracked-item"><div class="reg no-signal">PR-OMH</div><div class="ti sem-sinal">Aguardando...</div></div>
        <div class="tracked-item"><div class="reg no-signal">PR-OOE</div><div class="ti sem-sinal">Aguardando...</div></div>
    </div>
</div>

<div id="events-panel">
    <div class="panel-header">EVENTOS</div>
    <div id="events-list">
        <div class="no-events">Aguardando eventos...</div>
    </div>
</div>

<div id="notification-popup"></div>

<script>
''' + leaflet_js + '''
</script>

<script>
(function() {
    var CONFIG = {
        bounds: {lamin:-25.0, lamax:-21.5, lomin:-48.5, lomax:-43.0},
        tracked: ['PR-OMB','PR-OMH','PR-OOE'],
        airports: [],
        interval: 15,
        center: {lat:-23.55, lon:-46.63}
    };
    var map=null, markers={}, boundsRect=null, timer=null, events=[], loading=false, sound=true, audioCtx=null;
    var LABELS = {takeoff:'DECOLAGEM', landing:'POUSO', detected:'DETECTADO', lost_signal:'SINAL PERDIDO'};

    function $(id){return document.getElementById(id);}
    function hide(id){var e=$(id);if(e)e.style.display='none';}
    function showErr(m){var e=$('error-msg');if(e){e.textContent=m;e.style.display='block';} var s=$('loading-status');if(s)s.textContent='Erro';}

    function getAudio(){
        if(!audioCtx)try{audioCtx=new(window.AudioContext||window.webkitAudioContext)();}catch(e){}
        return audioCtx;
    }
    function beep(type){
        if(!sound)return;var c=getAudio();if(!c)return;
        try{if(c.state==='suspended')c.resume();
        if(type==='detected'){
            [0,0.2,0.4].forEach(function(d,i){var o=c.createOscillator(),g=c.createGain();o.connect(g);g.connect(c.destination);o.frequency.value=600+i*200;o.type='sine';g.gain.setValueAtTime(0.3,c.currentTime+d);g.gain.exponentialRampToValueAtTime(0.01,c.currentTime+d+0.15);o.start(c.currentTime+d);o.stop(c.currentTime+d+0.15);});
        }else if(type==='takeoff'){
            var o=c.createOscillator(),g=c.createGain();o.connect(g);g.connect(c.destination);o.frequency.setValueAtTime(400,c.currentTime);o.frequency.exponentialRampToValueAtTime(1200,c.currentTime+0.5);o.type='sine';g.gain.setValueAtTime(0.3,c.currentTime);g.gain.exponentialRampToValueAtTime(0.01,c.currentTime+0.6);o.start(c.currentTime);o.stop(c.currentTime+0.6);
        }else if(type==='landing'){
            var o2=c.createOscillator(),g2=c.createGain();o2.connect(g2);g2.connect(c.destination);o2.frequency.setValueAtTime(1000,c.currentTime);o2.frequency.exponentialRampToValueAtTime(300,c.currentTime+0.5);o2.type='sine';g2.gain.setValueAtTime(0.3,c.currentTime);g2.gain.exponentialRampToValueAtTime(0.01,c.currentTime+0.6);o2.start(c.currentTime);o2.stop(c.currentTime+0.6);
        }}catch(e){}
    }

    function initMap(){
        if(typeof L==='undefined')throw new Error('Leaflet nao carregou');
        map=L.map('map',{center:[CONFIG.center.lat,CONFIG.center.lon],zoom:8});
        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'OSM',maxZoom:19}).addTo(map);
        boundsRect=L.rectangle([[CONFIG.bounds.lamin,CONFIG.bounds.lomin],[CONFIG.bounds.lamax,CONFIG.bounds.lomax]],{color:'#38bdf8',weight:1,opacity:0.3,fill:false,dashArray:'5,5'}).addTo(map);
        setTimeout(function(){map.invalidateSize();},300);
    }

    function addAirports(list){
        if(!map)return;
        list.forEach(function(a){
            L.marker([a.lat,a.lon],{icon:L.divIcon({className:'airport-marker',html:'<div class="airport-label">'+a.icao+'</div>',iconSize:[50,16],iconAnchor:[25,8]}),zIndexOffset:-100}).addTo(map).bindPopup('<b>'+a.icao+'</b><br>'+a.name);
        });
    }

    function acIcon(hdg,tracked,ground){
        var r=hdg||0,c=tracked?(ground?'#f59e0b':'#22c55e'):(ground?'#475569':'#64748b'),s=tracked?28:18,op=tracked?1:0.7,sw=tracked?1:0,st=tracked?'#fff':'none';
        return L.divIcon({className:'aircraft-icon',html:'<svg width="'+s+'" height="'+s+'" viewBox="0 0 24 24" style="transform:rotate('+r+'deg);opacity:'+op+';"><path d="M12 2 L10 9 L3 12 L10 13 L10 20 L8 22 L12 21 L16 22 L14 20 L14 13 L21 12 L14 9 Z" fill="'+c+'" stroke="'+st+'" stroke-width="'+sw+'"/></svg>',iconSize:[s,s],iconAnchor:[s/2,s/2]});
    }

    function updateMap(list){
        if(!map)return;var cur={};
        for(var i=0;i<list.length;i++){
            var a=list[i];if(!a.latitude||!a.longitude)continue;cur[a.icao24]=1;
            var ic=acIcon(a.heading,a.is_tracked,a.on_ground);
            if(markers[a.icao24]){markers[a.icao24].setLatLng([a.latitude,a.longitude]);markers[a.icao24].setIcon(ic);}
            else{markers[a.icao24]=L.marker([a.latitude,a.longitude],{icon:ic,zIndexOffset:a.is_tracked?1000:0}).addTo(map);}
            var reg=a.registration||a.callsign||a.icao24;
            var alt=(a.altitude_ft!=null)?a.altitude_ft.toLocaleString()+' ft':'-';
            var spd=(a.velocity_kt!=null)?a.velocity_kt+' kt':'-';
            var st=a.on_ground?'<span style="color:#f59e0b">Solo</span>':'<span style="color:#22c55e">Voo</span>';
            var tr=a.is_tracked?'<div class="popup-tracked">RASTREADO</div>':'';
            markers[a.icao24].bindPopup('<div class="popup-reg">'+reg+'</div>'+tr+'<div style="margin-top:6px"><span class="popup-field">ICAO:</span> <span class="popup-value">'+a.icao24+'</span><br><span class="popup-field">Call:</span> <span class="popup-value">'+(a.callsign||'-')+'</span><br><span class="popup-field">Status:</span> '+st+'<br><span class="popup-field">Alt:</span> <span class="popup-value">'+alt+'</span><br><span class="popup-field">Vel:</span> <span class="popup-value">'+spd+'</span></div>');
        }
        var keys=Object.keys(markers);
        for(var j=0;j<keys.length;j++){if(!cur[keys[j]]){map.removeLayer(markers[keys[j]]);delete markers[keys[j]];}}
    }

    function updateTracked(data){
        var c=$('tracked-list');if(!c||!data)return;var h='';
        CONFIG.tracked.forEach(function(reg){
            var inf=data[reg]||{status:'sem sinal',details:null};
            var rc=(inf.status==='sem sinal'||inf.status==='sinal perdido')?'no-signal':'detected';
            var sc=inf.status.replace(/ /g,'-');
            var det='',oc='';
            if(inf.details){
                var p=[];
                if(inf.details.altitude_ft!=null)p.push('ALT:'+inf.details.altitude_ft+'ft');
                if(inf.details.velocity_kt!=null)p.push('VEL:'+inf.details.velocity_kt+'kt');
                det='<div class="details">'+p.join(' | ')+'</div>';
                oc=' onclick="window._fly('+inf.details.lat+','+inf.details.lon+')"';
            }
            h+='<div class="tracked-item"'+oc+'><div class="reg '+rc+'">'+reg+'</div><div class="ti '+sc+'">'+inf.status.toUpperCase()+'</div>'+det+'</div>';
        });
        c.innerHTML=h;
    }
    window._fly=function(lat,lon){if(map)map.flyTo([lat,lon],12,{duration:1});};

    function addEvts(evts){
        if(!evts||!evts.length)return;
        for(var i=0;i<evts.length;i++){
            events.unshift(evts[i]);beep(evts[i].type);
            var np=$('notification-popup');if(np){
                var d=document.createElement('div');d.className='notif '+(evts[i].type||'');
                d.innerHTML='<div class="notif-title">'+(LABELS[evts[i].type]||'')+'</div><div class="notif-body">'+(evts[i].message||'')+'</div>';
                np.appendChild(d);setTimeout((function(el){return function(){if(el.parentNode)el.parentNode.removeChild(el);};})(d),5500);
            }
        }
        if(events.length>50)events=events.slice(0,50);
        var el=$('events-list');if(!el)return;
        if(!events.length){el.innerHTML='<div class="no-events">Aguardando eventos...</div>';return;}
        var h='';
        for(var j=0;j<events.length;j++){
            var e=events[j],t='--:--';
            try{t=new Date(e.time).toLocaleTimeString('pt-BR');}catch(x){}
            h+='<div class="event-item '+(e.type||'')+'"><div class="event-msg">'+(LABELS[e.type]||e.type)+' - '+(e.registration||'')+'</div><div class="event-time">'+t+' - '+(e.message||'')+'</div></div>';
        }
        el.innerHTML=h;
    }

    window.toggleSound=function(){
        sound=!sound;var b=$('btn-sound');
        if(sound){b.className='btn active';b.textContent='Som ON';getAudio();}
        else{b.className='btn';b.textContent='Som OFF';}
    };

    function fetch_data(){
        if(loading)return;loading=true;
        var dot=$('status-dot');if(dot)dot.className='status-dot loading';
        var x=new XMLHttpRequest();
        x.open('GET','/api/tracker/aircraft',true);x.timeout=20000;
        x.onload=function(){
            loading=false;
            if(x.status===200){try{
                var d=JSON.parse(x.responseText);
                if(d.error){if(dot)dot.className='status-dot offline';}else{if(dot)dot.className='status-dot online';}
                var ce=$('aircraft-count');if(ce)ce.textContent=d.total||0;
                var te=$('last-update');if(te)te.textContent=new Date().toLocaleTimeString('pt-BR');
                if(d.aircraft)updateMap(d.aircraft);
                if(d.tracked_aircraft)updateTracked(d.tracked_aircraft);
                if(d.tracked_events&&d.tracked_events.length)addEvts(d.tracked_events);
            }catch(e){if(dot)dot.className='status-dot offline';}}
            else{if(dot)dot.className='status-dot offline';}
        };
        x.onerror=function(){loading=false;if(dot)dot.className='status-dot offline';};
        x.ontimeout=function(){loading=false;if(dot)dot.className='status-dot offline';};
        x.send();
    }

    function loadCfg(cb){
        var x=new XMLHttpRequest();x.open('GET','/api/tracker/config',true);x.timeout=10000;
        x.onload=function(){
            if(x.status===200){try{var d=JSON.parse(x.responseText);
            if(d.bounds)CONFIG.bounds=d.bounds;if(d.center)CONFIG.center=d.center;
            if(d.tracked_registrations)CONFIG.tracked=d.tracked_registrations;
            if(d.airports)CONFIG.airports=d.airports;if(d.refresh_interval)CONFIG.interval=d.refresh_interval;
            }catch(e){}}cb();
        };
        x.onerror=function(){cb();};x.ontimeout=function(){cb();};x.send();
    }

    window.refreshNow=function(){if(timer)clearInterval(timer);fetch_data();timer=setInterval(fetch_data,CONFIG.interval*1000);};

    function init(){
        try{
            var ls=$('loading-status');if(ls)ls.textContent='Carregando configuracao...';
            loadCfg(function(){
                try{
                    if(ls)ls.textContent='Inicializando mapa...';
                    initMap();
                    if(CONFIG.airports.length)addAirports(CONFIG.airports);
                    if(boundsRect)boundsRect.setBounds([[CONFIG.bounds.lamin,CONFIG.bounds.lomin],[CONFIG.bounds.lamax,CONFIG.bounds.lomax]]);
                    hide('loading-screen');
                    fetch_data();
                    timer=setInterval(fetch_data,CONFIG.interval*1000);
                }catch(e){showErr('Erro: '+e.message);}
            });
        }catch(e){showErr('Erro: '+e.message);}
    }

    if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){setTimeout(init,100);});
    else setTimeout(init,100);
})();
</script>
</body>
</html>'''


@tracker_bp.route('/tracker')
@tracker_bp.route('/api/tracker/page')
def tracker_page():
    """Serve the self-contained tracker page"""
    html = _build_page()
    return Response(html, mimetype='text/html')


@tracker_bp.route('/api/tracker/aircraft')
def get_aircraft():
    """Get all aircraft in the monitored region"""
    service = get_opensky_service()
    data = service.get_aircraft_in_region()
    return jsonify(data)


@tracker_bp.route('/api/tracker/events')
def get_events():
    """Get the event log"""
    service = get_opensky_service()
    events = service.get_event_log()
    return jsonify({'events': events})


@tracker_bp.route('/api/tracker/config')
def get_config():
    """Get tracker configuration"""
    return jsonify({
        'bounds': SAO_PAULO_BOUNDS,
        'tracked_registrations': list(TRACKED_AIRCRAFT.keys()),
        'airports': AIRPORTS,
        'refresh_interval': 15,
        'center': {
            'lat': -23.55,
            'lon': -46.63
        }
    })
