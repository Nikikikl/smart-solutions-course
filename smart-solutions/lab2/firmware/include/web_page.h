#pragma once

static const char LAB2_INDEX_HTML[] PROGMEM = R"HTML(
<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AtomS3 Lab 2</title>
<style>body{font:15px sans-serif;max-width:42rem;margin:2rem auto;padding:0 1rem}
label{display:block;margin:.8rem 0}input{width:100%;box-sizing:border-box;padding:.4rem}
button{margin:.4rem .4rem .4rem 0;padding:.5rem}.note{color:#555}.error{color:#a00}
.values{display:grid;grid-template-columns:repeat(3,1fr);gap:.5rem}.value{border:1px solid #bbb;padding:.6rem}
.value strong,.value span{display:block}.value span{font-variant-numeric:tabular-nums;margin-top:.3rem}</style>
</head><body><h1>AtomS3 · Lab 2</h1>
<p class="note">Post-office settings foundation. Hardware validation is TODO.</p>
<label>Wi-Fi SSID<input id="ssid" autocomplete="off"></label>
<label>Wi-Fi password<input id="wifiPass" type="password" autocomplete="new-password"></label>
<label>Post-office URL<input id="serverUrl" placeholder="https://lab.example"></label>
<label>Atom API key<input id="atomKey" type="password" autocomplete="new-password"
 placeholder="leave blank to keep stored key"></label>
<label>Polling interval (ms)<input id="pollMs" type="number" min="250" max="60000"></label>
<label><input id="devHttp" type="checkbox" style="width:auto"> Allow HTTP for local development only</label>
<button onclick="save()">SAVE SETTINGS</button><button onclick="testServer()">TEST SERVER HEALTH</button>
<p id="status"></p><hr>
<p class="note">The test performs one GET /health request. It never polls or claims a robot job.</p>
<hr><h2>Pressure sensor</h2>
<p class="note">Defaults come from Data Acquisition Lab 2: G5 ADC 3.70 V / 4095, LM358N gain 1 + 10k/54k,
 Vref 0.69 V, MPX5700AP at 5.0 V. Pressure is absolute kPa. Edit and save to replace them.</p>
<label><input id="pressureCalibrated" type="checkbox" style="width:auto"> Calibration verified and enabled</label>
<label><input id="sensorConfirmed" type="checkbox" style="width:auto"> Andur on ühendatud ja juhtmestik kontrollitud (kuni taaskäivituseni)</label>
<label>ADC voltage scale (V/count)<input id="voltsPerCount" inputmode="decimal" placeholder="not calibrated"></label>
<label>ADC voltage offset (V)<input id="voltageOffset" inputmode="decimal" placeholder="not calibrated"></label>
<label>Pressure scale (kPa/V)<input id="kpaPerVolt" inputmode="decimal" placeholder="not calibrated"></label>
<label>Pressure offset (kPa)<input id="pressureOffset" inputmode="decimal" placeholder="not calibrated"></label>
<button onclick="savePressure()">SAVE PRESSURE SETTINGS</button><button onclick="fillPressureDefaults()">FILL DA LAB 2 DEFAULTS</button><button onclick="testPressure()">TEST PRESSURE SENSOR</button>
<p id="pressureStatus" class="note">Not calibrated.</p>
<div class="values">
  <div class="value"><strong>Raw ADC</strong><span id="rawAdc">—</span></div>
  <div class="value"><strong>Voltage (V)</strong><span id="voltageV">not calibrated</span></div>
  <div class="value"><strong>Pressure (kPa)</strong><span id="pressureKpa">not calibrated</span></div>
</div>
<script>
const statusEl=document.getElementById('status');
async function load(){try{const r=await fetch('/settings');const s=await r.json();
ssid.value=s.ssid||'';serverUrl.value=s.server_url||'';pollMs.value=s.poll_interval_ms||1000;
devHttp.checked=!!s.dev_http;statusEl.textContent='Mode: '+s.wifi_mode+' · '+s.post_office_status;
}catch(e){statusEl.textContent='Load failed: '+e.message;statusEl.className='error'}
await loadPressure()}
async function save(){const f=new URLSearchParams();f.set('ssid',ssid.value.trim());
f.set('wifi_pass',wifiPass.value);f.set('server_url',serverUrl.value.trim());
f.set('atom_key',atomKey.value);f.set('poll_interval_ms',pollMs.value);
f.set('dev_http',devHttp.checked?'1':'0');const r=await fetch('/settings',{method:'POST',
headers:{'Content-Type':'application/x-www-form-urlencoded'},body:f});const t=await r.text();
statusEl.textContent=t;statusEl.className=r.ok?'':'error';wifiPass.value='';atomKey.value=''}
async function testServer(){statusEl.textContent='Testing health endpoint…';try{const r=await fetch('/test/post-office',{method:'POST'});
const p=await r.json();statusEl.textContent=p.result+' · HTTP '+(p.http_status??'—')+' · server answered: '+(p.server_response||'(no response)');
statusEl.className=r.ok?'':'error'}catch(e){statusEl.textContent='Server test failed: '+e.message;statusEl.className='error'}}
let pressureDefaults=null;
async function loadPressure(){try{const r=await fetch('/pressure/settings');const p=await r.json();pressureDefaults=p.defaults||null;
pressureCalibrated.checked=!!p.calibrated;sensorConfirmed.checked=!!p.sensor_confirmed;voltsPerCount.value=p.volts_per_count??'';
voltageOffset.value=p.voltage_offset_v??'';kpaPerVolt.value=p.kpa_per_volt??'';
pressureOffset.value=p.pressure_offset_kpa??'';pressureStatus.textContent=(p.calibrated?'Calibration loaded':'Not calibrated')+(p.source==='saved'?' (saved).':' (Data Acquisition Lab 2 defaults).');
pressureStatus.className='note'}catch(e){pressureStatus.textContent='Pressure settings load failed: '+e.message;pressureStatus.className='error'}}
async function savePressure(){const f=new URLSearchParams();f.set('pressure_calibrated',pressureCalibrated.checked?'1':'0');
f.set('sensor_confirmed',sensorConfirmed.checked?'1':'0');
f.set('volts_per_count',voltsPerCount.value);f.set('voltage_offset_v',voltageOffset.value);
f.set('kpa_per_volt',kpaPerVolt.value);f.set('pressure_offset_kpa',pressureOffset.value);
const r=await fetch('/pressure/settings',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:f});
const t=await r.text();pressureStatus.textContent=t;pressureStatus.className=r.ok?'note':'error';if(r.ok)await loadPressure()}
function fillPressureDefaults(){if(!pressureDefaults)return;pressureCalibrated.checked=true;
voltsPerCount.value=pressureDefaults.volts_per_count;voltageOffset.value=pressureDefaults.voltage_offset_v;
kpaPerVolt.value=pressureDefaults.kpa_per_volt;pressureOffset.value=pressureDefaults.pressure_offset_kpa;
pressureStatus.textContent='Defaults filled; press SAVE PRESSURE SETTINGS to store them.';pressureStatus.className='note'}
function pressureValue(value,digits){return value===null||value===undefined?'not calibrated':Number(value).toFixed(digits)}
async function testPressure(){pressureStatus.textContent='Reading pressure input…';try{const r=await fetch('/test/pressure',{method:'POST'});
const p=await r.json();rawAdc.textContent=p.raw_adc??'—';voltageV.textContent=pressureValue(p.voltage_v,4);
pressureKpa.textContent=pressureValue(p.pressure_kpa,3);pressureStatus.textContent=p.status||'pressure test failed';
pressureStatus.className=r.ok?'note':'error'}catch(e){pressureStatus.textContent='Pressure test failed: '+e.message;pressureStatus.className='error'}}
load();
</script></body></html>)HTML";
