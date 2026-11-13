import * as THREE from 'three';
import { OrbitControls } from './vendor/OrbitControls.js';
import { STLLoader } from './vendor/STLLoader.js';

// ---------------------------------------------------------------- constants (SI)
const G = 9.80665;
const KGCM = 0.0980665;                       // kg*cm -> N*m
const STALL_KGCM = { '10': 125, '12': 142, '12.6': 150 };   // DS51150 vendor page
const STALL_AMPS = v => 7.4 + (v - 10) * 0.35;               // vendor range 7.4-8.3 A, interpolated (assumed)
const THETA_MIN = -1 * Math.PI / 180;         // printed extension stop
const THETA_MAX = 91 * Math.PI / 180;         // printed flexion stop
const STOP_K = 1500;                          // N*m/rad, printed stop stiffness (assumed)
const STOP_ARM = 0.040;                       // m, lever from elbow axis to stop contact (assumed)
const FRICTION = 0.06;                        // N*m*s/rad passive joint damping (assumed)
const J_EXTRA = 0.01;                         // kg*m^2, servo + hardware rotating inertia (assumed)

const $ = id => document.getElementById(id);
const P = {                                   // live parameters
  target: 45, volt: '12', lim: 60, vmax: 300,
  pay: 0.5, mf: 1.0, mh: 0.4, ms: 0.3, fore: 'curved', lf: 0.25, lh: 0.195, share: 50, kill: false, sweep: false,
};

// ---------------------------------------------------------------- 3D scene (Z up, mm)
const view = $('view');
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.domElement.id = 'three';
view.prepend(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0e1116);
const camera = new THREE.PerspectiveCamera(40, 1, 5, 4000);
camera.up.set(0, 0, 1);
camera.position.set(520, 380, 120);
const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(40, 0, -60);
controls.update();
scene.add(new THREE.HemisphereLight(0xffffff, 0x334455, 1.0));
const dl = new THREE.DirectionalLight(0xffffff, 1.4); dl.position.set(300, 500, 600); scene.add(dl);
const grid = new THREE.GridHelper(800, 40, 0x2a313c, 0x1a1f27); grid.rotation.x = Math.PI / 2; grid.position.z = -330; scene.add(grid);

const fixedGroup = new THREE.Group();          // upper saddle, servo
const movingGroup = new THREE.Group();         // link plate + forearm part, rotates about the X axis through the origin
scene.add(fixedGroup, movingGroup);
const mat = (c, o = 1) => new THREE.MeshStandardMaterial({ color: c, metalness: 0.1, roughness: 0.55, transparent: o < 1, opacity: o });
const loader = new STLLoader();
const forearmMeshes = {};
function addSTL(url, group, material, key) {
  loader.load(url, geo => {
    geo.computeVertexNormals();
    const m = new THREE.Mesh(geo, material); group.add(m);
    if (key) forearmMeshes[key] = m;
    applyForearmChoice();
  }, undefined, err => { console.error('STL load failed', url, err); document.getElementById('h-stat').textContent = 'STL load failed'; });
}
const upperMat = mat(0xc9a24a), moveMat = mat(0x58a6ff), servoMat = mat(0x8b949e, 0.5);
addSTL('./stl/01_upper_saddle.stl', fixedGroup, upperMat);
addSTL('./stl/05_servo_placeholder.stl', fixedGroup, servoMat);
addSTL('./stl/03_link_plate.stl', movingGroup, moveMat);
addSTL('./stl/02_forearm_saddle.stl', movingGroup, moveMat, 'curved');
addSTL('./stl/02B_forearm_bar.stl', movingGroup, moveMat, 'bar');
function applyForearmChoice() {
  for (const k in forearmMeshes) forearmMeshes[k].visible = (k === P.fore);
}
// translucent reference limbs
const limbMat = mat(0x8899aa, 0.10);
const upperArm = new THREE.Mesh(new THREE.CylinderGeometry(38, 38, 290, 32), limbMat);
upperArm.rotation.x = Math.PI / 2; upperArm.position.z = 145; fixedGroup.add(upperArm);
let foreLimb = new THREE.Mesh(new THREE.CylinderGeometry(33, 33, 250, 32), limbMat);
foreLimb.rotation.x = Math.PI / 2; foreLimb.position.z = -125; movingGroup.add(foreLimb);
let handBox = new THREE.Mesh(new THREE.BoxGeometry(85, 30, 195), limbMat);
handBox.position.set(0, 0, -250 - 97); movingGroup.add(handBox);
function resizeLimbs() {
  const lf = P.lf * 1000, lh = P.lh * 1000;
  foreLimb.scale.y = lf / 250; foreLimb.position.z = -lf / 2;
  handBox.scale.z = lh / 195; handBox.position.z = -lf - lh / 2;
}
// stop markers: show where contact happens
const flash = new THREE.PointLight(0xf85149, 0, 400); flash.position.set(60, 40, 30); scene.add(flash);

function resize() {
  const w = view.clientWidth, h = view.clientHeight;
  renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
}
addEventListener('resize', resize); resize();

// ---------------------------------------------------------------- physics
const S = { th: 0, w: 0, thc: 0, tauNow: 0, stopTau: 0, peakStop: 0, atStop: '' };

function masses() {
  // [mass kg, distance from elbow axis m]
  return [
    [P.ms, 0.12],
    [P.mf, 0.45 * P.lf],
    [P.mh, P.lf + 0.40 * P.lh],
    [P.pay, P.lf + 0.50 * P.lh],
  ];
}
const momentSum = () => masses().reduce((s, [m, d]) => s + m * d, 0);          // kg*m
const inertia = () => masses().reduce((s, [m, d]) => s + m * d * d, 0) + J_EXTRA;
const gravTorque = th => G * momentSum() * Math.sin(th);
const stallTorque = () => STALL_KGCM[P.volt] * KGCM;
const limTorque = () => stallTorque() * P.lim / 100;

function step(dt) {
  const I = inertia(), vmax = P.vmax * Math.PI / 180;
  const tgt = P.kill ? S.th : P.target * Math.PI / 180;
  // command trajectory: the setpoint moves toward the target at the servo's max speed
  const d = tgt - S.thc; const mv = Math.max(-vmax * dt, Math.min(vmax * dt, d)); S.thc += mv;
  // servo: PD on the setpoint, torque saturated at the software limit
  const tl = limTorque();
  const Kp = tl / 0.06;                                    // full torque at ~3.4 deg error
  const Kd = 2 * 0.8 * Math.sqrt(Kp * I);
  let tau = P.kill ? 0 : Math.max(-tl, Math.min(tl, Kp * (S.thc - S.th) - Kd * S.w));
  // printed stops: stiff spring + damper once past the limit
  let tstop = 0, atStop = '';
  if (S.th > THETA_MAX) { tstop = -STOP_K * (S.th - THETA_MAX) - 2 * 0.3 * Math.sqrt(STOP_K * I) * S.w * (S.w > 0 ? 1 : 0); atStop = 'flexion stop'; }
  if (S.th < THETA_MIN) { tstop = STOP_K * (THETA_MIN - S.th) - 2 * 0.3 * Math.sqrt(STOP_K * I) * S.w * (S.w < 0 ? 1 : 0); atStop = 'extension stop'; }
  const net = tau - gravTorque(S.th) - FRICTION * S.w + tstop;
  S.w += net / I * dt; S.th += S.w * dt;
  S.tauNow = tau; S.stopTau = Math.abs(tstop); S.atStop = atStop;
  if (S.stopTau > S.peakStop) S.peakStop = S.stopTau;
}

// ---------------------------------------------------------------- UI wiring
function bindRange(id, key, fmt, conv = x => x) {
  const el = $(id), out = $('v-' + id);
  const upd = () => { P[key] = conv(+el.value); out.textContent = fmt(+el.value); };
  el.addEventListener('input', () => { upd(); onParams(); }); upd();
}
bindRange('target', 'target', v => v.toFixed(1) + '°');
bindRange('lim', 'lim', v => v + ' %');
bindRange('vmax', 'vmax', v => v + ' °/s');
bindRange('pay', 'pay', v => v.toFixed(1) + ' kg');
bindRange('mf', 'mf', v => v.toFixed(1) + ' kg');
bindRange('mh', 'mh', v => v.toFixed(2) + ' kg');
bindRange('ms', 'ms', v => v.toFixed(2) + ' kg');
bindRange('lf', 'lf', v => v + ' mm', v => v / 1000);
bindRange('lh', 'lh', v => v + ' mm', v => v / 1000);
bindRange('share', 'share', v => v + ' %');
$('volt').addEventListener('change', e => { P.volt = e.target.value; });
$('fore').addEventListener('change', e => { P.fore = e.target.value; applyForearmChoice(); });
$('b-reset').onclick = () => { S.th = 0; S.w = 0; S.thc = 0; S.peakStop = 0; P.kill = false; P.sweep = false; $('target').value = 45; P.target = 45; $('v-target').textContent = '45.0°'; $('b-kill').textContent = 'Kill (e-stop)'; };
$('b-kill').onclick = () => { P.kill = !P.kill; $('b-kill').textContent = P.kill ? 'Release e-stop' : 'Kill (e-stop)'; };
$('b-sweep').onclick = () => { P.sweep = !P.sweep; P.kill = false; if (P.sweep) setTarget(90); };
function setTarget(a) { P.target = a; $('target').value = a; $('v-target').textContent = a.toFixed(1) + '°'; }
function onParams() { resizeLimbs(); }
resizeLimbs();

// ---------------------------------------------------------------- readouts + graph
const fmtN = (v, u, d = 2) => v.toFixed(d) + ' ' + u;
function readouts() {
  const th = S.th, need = Math.abs(gravTorque(th)), avail = limTorque(), stall = stallTorque();
  $('r-need').textContent = fmtN(need, 'N·m') + ' (' + (need / KGCM).toFixed(1) + ' kg·cm)';
  $('r-avail').textContent = fmtN(avail, 'N·m');
  $('r-stall').textContent = fmtN(stall, 'N·m') + ' (' + STALL_KGCM[P.volt] + ' kg·cm)';
  const margin = avail - need;
  $('r-margin').textContent = fmtN(margin, 'N·m'); $('r-margin').className = margin < 0 ? 'bad' : margin < 0.15 * avail ? 'warn' : 'ok';
  $('r-now').textContent = fmtN(S.tauNow, 'N·m');
  const amps = 0.4 + STALL_AMPS(+P.volt) * Math.min(1, Math.abs(S.tauNow) / stall);
  $('r-cur').textContent = fmtN(amps, 'A', 1); $('r-cur').className = amps > STALL_AMPS(+P.volt) * 0.9 ? 'warn' : '';
  const ms = momentSum() * G;
  const sMax = Math.min(1, avail / ms);
  const maxAng = Math.asin(sMax) * 180 / Math.PI;
  $('r-maxang').textContent = sMax >= 1 ? 'any angle' : maxAng.toFixed(0) + '°'; $('r-maxang').className = maxAng < 90 && sMax < 1 ? 'bad' : 'ok';
  $('r-stop').textContent = fmtN(S.stopTau / STOP_ARM, 'N', 0);
  $('r-peak').textContent = fmtN(S.peakStop / STOP_ARM, 'N', 0);
  // chest load path
  const exoMass = P.ms + 0.175 + 0.3;                    // forearm part + servo + upper saddle/strut/etc (assumed)
  const F = (exoMass + P.pay * P.share / 100) * G;
  const M = F * 0.12;
  $('c-F').textContent = fmtN(F, 'N', 1);
  $('c-M').textContent = fmtN(M, 'N·m', 2);
  $('c-V').textContent = fmtN(F / 4, 'N', 1);
  $('c-T').textContent = fmtN(M / (4 * 0.011), 'N', 0);
  $('h-ang').textContent = (th * 180 / Math.PI).toFixed(1) + '°';
  $('h-tgt').textContent = (P.kill ? 'E-STOP' : P.target.toFixed(1) + '°');
  const st = P.kill ? 'e-stop (servo off)' : S.atStop || (Math.abs(S.tauNow) >= limTorque() * 0.98 ? 'servo saturated' : 'free');
  const hs = $('h-stat'); hs.textContent = st; hs.className = (S.atStop || st.startsWith('servo sat')) ? 'bad' : P.kill ? 'warn' : '';
}

const gc = $('graph'), gx = gc.getContext('2d');
function drawGraph() {
  const W = gc.width, H = gc.height, pad = { l: 46, r: 12, t: 18, b: 30 };
  gx.clearRect(0, 0, W, H);
  const a0 = -10, a1 = 100, stall = stallTorque();
  const ymax = Math.max(stall * 1.1, gravTorque(Math.PI / 2) * 1.1, 1);
  const X = a => pad.l + (a - a0) / (a1 - a0) * (W - pad.l - pad.r);
  const Y = t => H - pad.b - t / ymax * (H - pad.t - pad.b);
  gx.font = '20px system-ui'; gx.fillStyle = '#8b949e'; gx.strokeStyle = '#2a313c'; gx.lineWidth = 1;
  for (let a = 0; a <= 100; a += 20) { gx.beginPath(); gx.moveTo(X(a), pad.t); gx.lineTo(X(a), H - pad.b); gx.stroke(); gx.fillText(a + '°', X(a) - 12, H - 8); }
  gx.fillText('N·m', 4, 16);
  gx.fillStyle = 'rgba(248,81,73,.12)'; gx.fillRect(X(a0), pad.t, X(-1) - X(a0), H - pad.t - pad.b); gx.fillRect(X(91), pad.t, X(a1) - X(91), H - pad.t - pad.b);
  gx.strokeStyle = '#d29922'; gx.setLineDash([8, 6]); gx.beginPath(); gx.moveTo(X(a0), Y(limTorque())); gx.lineTo(X(a1), Y(limTorque())); gx.stroke(); gx.setLineDash([]);
  gx.strokeStyle = '#3fb950'; gx.beginPath(); gx.moveTo(X(a0), Y(stall)); gx.lineTo(X(a1), Y(stall)); gx.stroke();
  gx.strokeStyle = '#58a6ff'; gx.lineWidth = 3; gx.beginPath();
  for (let a = a0; a <= a1; a += 2) { const t = Math.max(0, gravTorque(a * Math.PI / 180)); a === a0 ? gx.moveTo(X(a), Y(t)) : gx.lineTo(X(a), Y(t)); }
  gx.stroke(); gx.lineWidth = 1;
  const ca = S.th * 180 / Math.PI; gx.strokeStyle = '#e6edf3'; gx.beginPath(); gx.moveTo(X(ca), pad.t); gx.lineTo(X(ca), H - pad.b); gx.stroke();
  gx.font = '18px system-ui';
  gx.fillStyle = '#58a6ff'; gx.fillText('needed to hold', 60, 40);
  gx.fillStyle = '#d29922'; gx.fillText('limit', 220, 40);
  gx.fillStyle = '#3fb950'; gx.fillText('stall', 290, 40);
}

// ---------------------------------------------------------------- main loop
let last = performance.now();
function frame(now) {
  const dt = Math.min(0.05, (now - last) / 1000); last = now;
  const sub = Math.ceil(dt / 0.0005);
  for (let i = 0; i < sub; i++) step(dt / sub);
  if (P.sweep && Math.abs(S.th * 180 / Math.PI - P.target) < 1.5) setTarget(P.target > 45 ? 0 : 90);
  movingGroup.rotation.x = S.th;                         // positive = flexion (forearm swings toward +Y and up)
  flash.intensity = S.atStop ? 40000 : 0;
  readouts(); drawGraph(); controls.update(); renderer.render(scene, camera);
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
window.__sim = { S, P, step, gravTorque, limTorque, stallTorque };   // for tests
