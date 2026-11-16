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
  pay: 0.5, mf: 1.0, mh: 0.4, ms: 0.3, fore: 'curved', sho: 0, abd: 0, roll: 0, wristOn: true, limbs: true, wt: 0, wstall: '20', wlim: 80, wvmax: 400, chest: true, torso: true, mu: 0.8, lf: 0.25, lh: 0.195, share: 50, kill: false, sweep: false,
};

// ---------------------------------------------------------------- 3D scene (Z up, mm)
const view = $('view');
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.domElement.id = 'three';
view.prepend(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0e1116);
const camera = new THREE.PerspectiveCamera(40, 1, 5, 6000);
camera.up.set(0, 0, 1);
camera.position.set(900, 640, 300);
const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(60, 0, 20);
controls.update();
scene.add(new THREE.HemisphereLight(0xffffff, 0x334455, 1.0));
const dl = new THREE.DirectionalLight(0xffffff, 1.4); dl.position.set(300, 500, 600); scene.add(dl);
const grid = new THREE.GridHelper(800, 40, 0x2a313c, 0x1a1f27); grid.rotation.x = Math.PI / 2; grid.position.z = -330; scene.add(grid);

// kinematic chain (assembly frame, mm): chest (fixed) -> abduction about the yoke's Y pin -> shoulder flexion about the strut's X bolt -> arm module
const PIN = new THREE.Vector3(73.2, 0, 312);      // yoke pin (Y axis), from make_aegis_v13.py: bxc, zs+22
const SHB = new THREE.Vector3(73.2, 0, 290);      // shoulder bolt (X axis): bxc, zs
const chestGroup = new THREE.Group(); scene.add(chestGroup);            // yoke, chest plate, torso model (fixed to the wearer's chest)
const abdGroup = new THREE.Group(); abdGroup.position.copy(PIN); scene.add(abdGroup);
const blockGroup = new THREE.Group(); blockGroup.position.copy(PIN).negate(); abdGroup.add(blockGroup);   // gimbal block
const shoGroup = new THREE.Group(); shoGroup.position.copy(SHB).sub(PIN); abdGroup.add(shoGroup);
const armRoot = new THREE.Group(); armRoot.position.copy(SHB).negate(); shoGroup.add(armRoot);          // strut, saddle, servo, forearm
const rollGroup = new THREE.Group(); armRoot.add(rollGroup);   // upper-arm roll: rotates about the arm's long axis (world Z through the origin); the strut stays with the chest link
const fixedGroup = new THREE.Group();          // upper saddle, servo, roll rail
const movingGroup = new THREE.Group();         // link plate + forearm part (+ wrist), rotates about the X axis through the origin
rollGroup.add(fixedGroup, movingGroup);
// wrist module (assembly frame, mm): hand piece pivots on the wrist pin P; the crank on the wrist servo shaft S; the rod joins crank pin C to hand pin A
const WP = { Pz: -250, Sz: -187.5, RC: 30, ROD: 67, LEV: 28, xCrank: 102.914, xRod: 106.914 };
const wristMod = new THREE.Group(); movingGroup.add(wristMod);               // everything that belongs to the optional wrist module (toggle)
const handGroup = new THREE.Group(); handGroup.position.set(0, 0, WP.Pz); wristMod.add(handGroup);
const crankGroup = new THREE.Group(); crankGroup.position.set(WP.xCrank, 0, WP.Sz); wristMod.add(crankGroup);
const rodGroup = new THREE.Group(); wristMod.add(rodGroup);
const handRef = new THREE.Group(); handRef.position.set(0, 0, WP.Pz); movingGroup.add(handRef);   // the wearer's hand (reference), follows the wrist angle
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
const strutMat = mat(0xd2a8ff), blockMat = mat(0xf0883e), yokeMat = mat(0x3fb950), plateMat = mat(0x2ea043), torsoMat = mat(0x8899aa, 0.12);
addSTL('./stl/14_shoulder_strut.stl', armRoot, strutMat);                 // strut + carriage foot: fixed to the chest link, not to the rolling arm
const railMat = mat(0xffa657), wristMat = mat(0x79c0ff), wristPartMat = mat(0xe3b341);
addSTL('./stl/20_roll_rail.stl', fixedGroup, railMat);
addSTL('./stl/04_wrist_mount.stl', wristMod, wristMat);
addSTL('./stl/12_wrist_servo_placeholder.stl', wristMod, servoMat);
addSTL('./stl/09_hand_piece.stl', handGroup, wristPartMat);
addSTL('./stl/10_wrist_crank.stl', crankGroup, wristPartMat);
addSTL('./stl/11_wrist_rod.stl', rodGroup, wristPartMat);
addSTL('./stl/15_gimbal_block.stl', blockGroup, blockMat);
addSTL('./stl/16_chest_yoke_arch.stl', chestGroup, yokeMat);
// the plate file is a print-frame copy of the plate: sits on the torso axis at x=-165, z=115 in the assembly frame (CHEST_AXIS_X, CHEST_PLATE_Z0)
const plateGroup = new THREE.Group(); plateGroup.position.set(-165, 0, 115); chestGroup.add(plateGroup);
addSTL('./stl/06_chest_plate_RIGHT_ARM.stl', plateGroup, plateMat);
addSTL('./stl/17_BODY_torso_not_printable.stl', chestGroup, torsoMat);
addSTL('./stl/01_upper_saddle.stl', fixedGroup, upperMat);
addSTL('./stl/05_servo_placeholder.stl', fixedGroup, servoMat);
addSTL('./stl/03_link_plate.stl', movingGroup, moveMat);
addSTL('./stl/02_forearm_saddle.stl', movingGroup, moveMat, 'curved');
addSTL('./stl/02B_forearm_bar.stl', movingGroup, moveMat, 'bar');
function applyForearmChoice() {
  for (const k in forearmMeshes) forearmMeshes[k].visible = (k === P.fore);
}
// translucent limbs
const limbMat = mat(0x8899aa, 0.10);
const upperArm = new THREE.Mesh(new THREE.CylinderGeometry(38, 38, 290, 32), limbMat);
upperArm.rotation.x = Math.PI / 2; upperArm.position.z = 145; fixedGroup.add(upperArm);
let foreLimb = new THREE.Mesh(new THREE.CylinderGeometry(36, 27, 250, 32), limbMat);   // elbow end r36, wrist end r27 (forearm tapers)
foreLimb.rotation.x = Math.PI / 2; foreLimb.position.z = -125; movingGroup.add(foreLimb);
// hand model (right hand, palm toward -Y, back of hand toward +Y where the dorsal plate sits; thumb on the -X side). z=0 is the wrist pin.
const skinMat = mat(0xd9a98a, 0.35);
const handShape = new THREE.Group(); handRef.add(handShape);
const palm = new THREE.Mesh(new THREE.BoxGeometry(80, 26, 100), skinMat); palm.position.set(0, 0, -50); handShape.add(palm);
[[-30, 78], [-10, 88], [10, 84], [29, 70]].forEach(([x, len]) => {           // four fingers (little finger on +X)
  const f = new THREE.Mesh(new THREE.CapsuleGeometry(8.5, len, 6, 16), skinMat);
  f.rotation.x = Math.PI / 2; f.position.set(x, -2, -100 - len / 2 - 6); handShape.add(f);
});
const thumb = new THREE.Mesh(new THREE.CapsuleGeometry(10, 45, 6, 16), skinMat);
thumb.rotation.set(Math.PI / 2, 0, -0.55); thumb.position.set(-52, -6, -62); handShape.add(thumb);
function resizeLimbs() {
  const lf = P.lf * 1000, lh = P.lh * 1000;
  foreLimb.scale.y = lf / 250; foreLimb.position.z = -lf / 2;
  handShape.scale.z = lh / 195;
}
// stop markers: show where contact happens
const flash = new THREE.PointLight(0xf85149, 0, 400); flash.position.set(60, 40, 30); scene.add(flash);

function resize() {
  const w = view.clientWidth, h = view.clientHeight;
  renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
}
addEventListener('resize', resize); resize();

// ---------------------------------------------------------------- physics
const S = { th: 0, w: 0, thc: 0, tauNow: 0, stopTau: 0, peakStop: 0, atStop: '', ph: 0, pw: 0, phc: 0, al: null, wTau: 0, wStop: '' };
S.al = null;

function masses() {
  // [mass kg, distance from elbow axis m]  (straight-wrist approximation; used for the hold-torque summary and the graph)
  return [
    [P.ms, 0.12],
    [P.mf, 0.45 * P.lf],
    [P.mh, P.lf + 0.40 * P.lh],
    [P.pay, P.lf + 0.50 * P.lh],
  ];
}
const momentSum = () => masses().reduce((s, [m, d]) => s + m * d, 0);          // kg*m
const D2R = Math.PI / 180;
const qSho = () => new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1, 0, 0), P.sho * D2R);
const qAbd = () => new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), -P.abd * D2R);   // +abd lifts the arm out to +X
const qRoll = () => new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 0, 1), P.roll * D2R);  // about the arm's own long axis
const qArm = () => qAbd().multiply(qSho()).multiply(qRoll());
// point masses in the elbow frame (y,z), for elbow angle th and wrist angle ph (rad). Both flexions rotate toward +Y.
function pointMasses(th, ph) {
  const f = (d, a) => [d * Math.sin(a), -d * Math.cos(a)];
  const out = [];
  out.push([P.ms, ...f(0.12, th)]);
  out.push([P.mf, ...f(0.45 * P.lf, th)]);
  const w = f(P.lf, th), h1 = f(0.40 * P.lh, th + ph), h2 = f(0.50 * P.lh, th + ph);
  out.push([P.mh, w[0] + h1[0], w[1] + h1[1]]);
  out.push([P.pay, w[0] + h2[0], w[1] + h2[1]]);
  return out;
}
// gravity moment about an axis a (world) of mass m at world position rw, positive = resists rotation in the +axis direction
const gmoment = (m, rw, a) => G * m * (rw.y * a.x - rw.x * a.y);
// torque about the elbow axis from gravity in the current shoulder/roll pose (positive = resists flexion); equals G*sum(m d)*sin(th) at sho=abd=roll=0, straight wrist
function gravTorque(th, ph = S.ph) {
  const q = qArm(), a = new THREE.Vector3(1, 0, 0).applyQuaternion(q);
  let t = 0;
  for (const [m, y, z] of pointMasses(th, ph)) t += gmoment(m, new THREE.Vector3(0, y, z).applyQuaternion(q), a);
  return t;
}
// gravity torque about the wrist axis (hand + payload), positive = resists +ph
function gravWrist(th, ph) {
  const q = qArm(), a = new THREE.Vector3(1, 0, 0).applyQuaternion(q);
  const f = (d, ang) => new THREE.Vector3(0, d * Math.sin(ang), -d * Math.cos(ang)).applyQuaternion(q);
  return gmoment(P.mh, f(0.40 * P.lh, th + ph), a) + gmoment(P.pay, f(0.50 * P.lh, th + ph), a);
}
// gravity torque about the shoulder axis that the wearer's own shoulder must supply (the printed pivot is free); N*m
function shoulderTorque(th, ph = S.ph) {
  const qa = qAbd(), qs = qSho(), qr = qRoll(), ax = new THREE.Vector3(1, 0, 0).applyQuaternion(qa);
  const place = (r) => r.clone().applyQuaternion(qr).add(new THREE.Vector3(0, 0, -0.29)).applyQuaternion(qs).applyQuaternion(qa);
  let t = gmoment(P.mu, place(new THREE.Vector3(0, 0, 0.15)), ax);          // exo upper saddle + strut + upper-arm share, centre 140 mm below the shoulder bolt (assumed)
  for (const [m, y, z] of pointMasses(th, ph)) t += gmoment(m, place(new THREE.Vector3(0, y, z)), ax);
  return t;
}
const inertia = () => masses().reduce((s, [m, d]) => s + m * d * d, 0) + J_EXTRA;
const wInertia = () => P.mh * (0.40 * P.lh) ** 2 + P.pay * (0.50 * P.lh) ** 2 + 0.0008;   // hand + payload about the wrist pin, + hand piece (assumed 0.0008)

// ---- wrist linkage (planar, y,z): hand angle ph -> crank angle al. Planar linkage solution.
const WSTALL = { '10': 10, '20': 20, '25': 25 };            // kg*cm, ASSUMED servo class (placeholder body 40.7 x 19.7 x 42.9 mm)
const WLO = -55 * D2R, WHI = 45 * D2R;                       // hand-piece arc-slot stops
function crankAngle(ph, prev) {
  const A = [WP.LEV * Math.cos(ph), WP.Pz + WP.LEV * Math.sin(ph)], Sx = [0, WP.Sz];
  const dy = A[0] - Sx[0], dz = A[1] - Sx[1], d = Math.hypot(dy, dz);
  if (d > WP.RC + WP.ROD || d < Math.abs(WP.ROD - WP.RC)) return null;
  const base = Math.atan2(dz, dy), psi = Math.acos((WP.RC * WP.RC + d * d - WP.ROD * WP.ROD) / (2 * WP.RC * d));
  const wrap = x => Math.atan2(Math.sin(x), Math.cos(x));
  const ref = prev === undefined || prev === null ? base + 60 * D2R : prev;
  const c = [base + psi, base - psi].sort((p, q) => Math.abs(wrap(p - ref)) - Math.abs(wrap(q - ref)));
  return c[0];
}
function wristRatio(ph, al) {                                  // d(crank)/d(hand): wrist torque = servo torque * ratio
  const e = 0.5 * D2R, a1 = crankAngle(ph + e, al), a0 = crankAngle(ph - e, al);
  if (a1 === null || a0 === null) return 1;
  const wrap = x => Math.atan2(Math.sin(x), Math.cos(x));
  return Math.abs(wrap(a1 - a0) / (2 * e));
}
const wStall = () => WSTALL[P.wstall] * KGCM;
const stallTorque = () => STALL_KGCM[P.volt] * KGCM;
const limTorque = () => stallTorque() * P.lim / 100;

const WSTOP_K = 150;                                          // N*m/rad, hand-piece arc-slot stop (printed, assumed)
function stepWrist(dt) {
  if (!P.wristOn) { S.ph = 0; S.pw = 0; S.phc = 0; S.wTau = 0; S.wStop = ''; S.wLim = 0; return; }
  const vmax = P.wvmax * D2R, I = wInertia();
  const tgt = P.kill ? S.ph : Math.max(WLO, Math.min(WHI, P.wt * D2R));
  const d = tgt - S.phc; S.phc += Math.max(-vmax * dt, Math.min(vmax * dt, d));
  if (S.al === null) S.al = crankAngle(S.ph, null);
  const ratio = wristRatio(S.ph, S.al);                        // crank rad per hand rad
  const tl = wStall() * P.wlim / 100 * ratio;                  // servo torque limit referred to the wrist pin
  const Kp = tl / 0.06, Kd = 2 * 0.8 * Math.sqrt(Kp * I);
  const tau = P.kill ? 0 : Math.max(-tl, Math.min(tl, Kp * (S.phc - S.ph) - Kd * S.pw));
  let ts = 0, st = '';
  if (S.ph > WHI) { ts = -WSTOP_K * (S.ph - WHI) - 2 * 0.3 * Math.sqrt(WSTOP_K * I) * Math.max(S.pw, 0); st = 'wrist stop (+)'; }
  if (S.ph < WLO) { ts = WSTOP_K * (WLO - S.ph) - 2 * 0.3 * Math.sqrt(WSTOP_K * I) * Math.min(S.pw, 0); st = 'wrist stop (-)'; }
  const net = tau - gravWrist(S.th, S.ph) - 0.004 * S.pw + ts;
  S.pw += net / I * dt; S.ph += S.pw * dt;
  const nal = crankAngle(S.ph, S.al); if (nal !== null) S.al = nal;
  S.wTau = tau; S.wStop = st; S.wRatio = ratio; S.wLim = tl;
}
function step(dt) {
  stepWrist(dt);
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
bindRange('sho', 'sho', v => v.toFixed(0) + '°');
bindRange('roll', 'roll', v => v.toFixed(0) + '°');
bindRange('wt', 'wt', v => v.toFixed(0) + '°');
bindRange('wlim', 'wlim', v => v + ' %');
bindRange('wvmax', 'wvmax', v => v + ' °/s');
$('wristOn').addEventListener('change', e => { P.wristOn = e.target.checked; if (P.wristOn) { S.al = null; } });
$('limbs').addEventListener('change', e => { P.limbs = e.target.checked; });
$('wstall').addEventListener('change', e => { P.wstall = e.target.value; });
$('b-wsweep').onclick = () => { P.wsweep = !P.wsweep; P.kill = false; if (P.wsweep) setWTarget(40); };
function setWTarget(a) { P.wt = a; $('wt').value = a; $('v-wt').textContent = a.toFixed(0) + '°'; }
bindRange('abd', 'abd', v => v.toFixed(0) + '°');
bindRange('mu', 'mu', v => v.toFixed(2) + ' kg');
$('chest').addEventListener('change', e => { P.chest = e.target.checked; });
$('torso').addEventListener('change', e => { P.torso = e.target.checked; });
$('volt').addEventListener('change', e => { P.volt = e.target.value; });
$('fore').addEventListener('change', e => { P.fore = e.target.value; applyForearmChoice(); });
$('b-reset').onclick = () => { S.ph = 0; S.pw = 0; S.phc = 0; S.al = null; P.wsweep = false; setWTarget(0); S.th = 0; S.w = 0; S.thc = 0; S.peakStop = 0; P.kill = false; P.sweep = false; $('target').value = 45; P.target = 45; $('v-target').textContent = '45.0°'; $('b-kill').textContent = 'Kill (e-stop)'; };
$('b-kill').onclick = () => { P.kill = !P.kill; $('b-kill').textContent = P.kill ? 'Release e-stop' : 'Kill (e-stop)'; $('b-kill').style.borderColor = P.kill ? '#f85149' : ''; };
$('b-sweep').onclick = () => { P.sweep = !P.sweep; P.kill = false; if (P.sweep) setTarget(90); };
function setTarget(a) { P.target = a; $('target').value = a; $('v-target').textContent = a.toFixed(1) + '°'; }
function onParams() { resizeLimbs(); }
// moving a target slider by hand takes over from a running sweep
$('target').addEventListener('input', () => { P.sweep = false; });
$('wt').addEventListener('input', () => { P.wsweep = false; });
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
  const wn = Math.abs(gravWrist(th, S.ph)), wl = S.wLim || 0;
  $('w-need').textContent = fmtN(wn, 'N·m', 3) + ' (' + (wn / KGCM).toFixed(2) + ' kg·cm)';
  $('w-avail').textContent = fmtN(wl, 'N·m', 3) + ' at wrist pin';
  const wm = wl - wn; $('w-margin').textContent = fmtN(wm, 'N·m', 3); $('w-margin').className = wm < 0 ? 'bad' : wm < 0.15 * wl ? 'warn' : 'ok';
  $('w-now').textContent = fmtN(S.wTau, 'N·m', 3);
  $('w-ang').textContent = (S.ph / D2R).toFixed(1) + '° (crank ' + (S.al === null ? '–' : ((S.al / D2R) % 360).toFixed(0) + '°') + ')';
  $('w-ratio').textContent = (S.wRatio || 0).toFixed(2) + ' : 1';
  $('w-stop').textContent = S.wStop || 'free'; $('w-stop').className = S.wStop ? 'bad' : '';
  const st_ = shoulderTorque(th);
  $('c-S').textContent = fmtN(Math.abs(st_), 'N·m', 2);
  $('c-Sd').textContent = Math.abs(st_) < 0.05 ? 'balanced (arm hangs free)' : 'your shoulder holds this';
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
  shoGroup.rotation.x = P.sho * D2R; abdGroup.rotation.y = -P.abd * D2R; rollGroup.rotation.z = P.roll * D2R;
  if (P.wsweep && Math.abs(S.ph / D2R - P.wt) < 2) setWTarget(P.wt > 0 ? -45 : 40);
  wristMod.visible = P.wristOn; handRef.rotation.x = S.ph;
  foreLimb.visible = P.limbs; handShape.visible = P.limbs; upperArm.visible = P.limbs;
  handGroup.rotation.x = S.ph;
  if (S.al !== null) {
    crankGroup.rotation.x = S.al;
    const Cy = WP.RC * Math.cos(S.al), Cz = WP.Sz + WP.RC * Math.sin(S.al);
    const Ay = WP.LEV * Math.cos(S.ph), Az = WP.Pz + WP.LEV * Math.sin(S.ph);
    rodGroup.position.set(WP.xRod, Cy, Cz); rodGroup.rotation.x = Math.atan2(Az - Cz, Ay - Cy);
  }
  chestGroup.visible = P.chest; blockGroup.visible = P.chest;
  torsoMat.opacity = P.torso ? 0.12 : 0.0; armRoot.children.forEach(c => { if (c.geometry && c.material === strutMat) c.visible = P.chest; });
  movingGroup.rotation.x = S.th;                         // positive = flexion (forearm swings toward +Y and up)
  flash.intensity = S.atStop ? 40000 : 0;
  readouts(); drawGraph(); controls.update(); renderer.render(scene, camera);
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
window.__sim = { camera, controls, S, P, step, gravTorque, gravWrist, shoulderTorque, crankAngle, wristRatio, limTorque, stallTorque, shoGroup, abdGroup };   // for tests
