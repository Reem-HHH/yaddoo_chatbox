// app.js — Yaddoo kid-friendly chat (fixed avatar wiring)
// -------------------------------------------------------
// - Login overlay (name + gender) -> saved to localStorage
// - Updates #yaddoo-avatar and #user-avatar (img + name)
// - Clean chat flow with error surfacing in Arabic
// - If page isn’t served on :3000, calls http://localhost:3000

// ---------- Elements ----------
const chat = document.getElementById('chat');
const input = document.getElementById('input');
const send = document.getElementById('send');
const debugBtn = document.getElementById('debugBtn');   // may be absent
const switchBtn = document.getElementById('switchBtn');
const logoutBtn = document.getElementById('logoutBtn');

const gate = document.getElementById('gate');
const gateForm = document.getElementById('gateForm');
const gateName = document.getElementById('gateName');

// Avatars in your HTML (img + label span)
const yaddooImg = document.querySelector('#yaddoo-avatar img');
const yaddooLabel = document.querySelector('#yaddoo-avatar span');
const userImg = document.querySelector('#user-avatar img');
const userLabel = document.querySelector('#user-avatar span');

// ---------- Storage ----------
const PROFILE_KEY = 'yaddoo:profile:v1';
const saveProfile = (p) => localStorage.setItem(PROFILE_KEY, JSON.stringify(p));
const loadProfile = () => { try { return JSON.parse(localStorage.getItem(PROFILE_KEY) || 'null'); } catch { return null; } };
const clearProfile = () => localStorage.removeItem(PROFILE_KEY);

// ---------- Small UI helpers ----------
const el = (tag, cls, text) => { const n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; };
const timeStr = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

/* function addRow({ who, text }) {
  const r = el('div', 'row' + (who === 'me' ? ' me' : ''));
  const b = el('div', 'bubble ' + (who === 'me' ? 'me' : 'bot'), text);
  const m = el('div', 'meta', timeStr());
  r.append(b, m);
  chat.appendChild(r);
  chat.scrollTop = chat.scrollHeight;
} */

  function addRow({ who, text }) {
  const r = el('div', 'row' + (who === 'me' ? ' me' : ''));

  // pick avatar image paths
  const mySrc   = document.querySelector('#user-avatar img')?.src || 'assets/girl.png';
  const botSrc  = 'assets/yaddoo.png';
  const avatarSrc = (who === 'me') ? mySrc : botSrc;

  // build nodes
  const avatar = document.createElement('img');
  avatar.className = 'msg-avatar';
  avatar.alt = (who === 'me') ? 'أنت' : 'يَدّوه';
  avatar.src = avatarSrc;

  const b = el('div', 'bubble ' + (who === 'me' ? 'me' : 'bot'), text);
  const m = el('div', 'meta', timeStr());

  // order: for me → [bubble, avatar], for bot → [avatar, bubble]
  if (who === 'me') {
    r.append(b, avatar, m);
  } else {
    r.append(avatar, b, m);
  }

  chat.appendChild(r);
  chat.scrollTop = chat.scrollHeight;
}


// Map gender -> avatar asset used for the child
const AVATARS = {
  yaddoo: 'assets/yaddoo.png',
  female: 'assets/girl.png',
  male: 'assets/boy.png',
};

// Update the two profile badges (top Yaddoo, bottom child)
function updateProfileUI(profile) {
  // Yaddoo is static
  if (yaddooImg) yaddooImg.src = AVATARS.yaddoo;
  if (yaddooLabel) yaddooLabel.textContent = 'يَدّوه';

  // Child depends on saved profile
  const name = profile?.name || 'ضيف';
  const gender = (profile?.gender === 'male') ? 'male' : 'female';
  if (userImg) userImg.src = AVATARS[gender];
  if (userLabel) userLabel.textContent = name;
}

// Friendly greeting from Yaddoo
function greet(profile) {
  const name = profile?.name || 'ولدي';
  addRow({ who: 'bot', text: `أهلًا يا ${name} في مجلس يَدّوه 👵🏽 — سولف وياي!` });
}

// ---------- API base ----------
const API_BASE = (location.port === '3000') ? '' : 'http://localhost:3000';

async function generateReply(userText, history) {
  const r = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: userText, history })
  });
  let payload = {};
  try { payload = await r.json(); } catch { }
  if (!r.ok) {
    throw new Error(payload.error || JSON.stringify(payload) || ('HTTP ' + r.status));
  }
  return payload.reply || '…';
}

// ---------- Chat flow ----------
const history = [];

async function handleSend() {
  const text = (input.value || '').trim();
  if (!text) return;

  input.value = '';
  addRow({ who: 'me', text });
  history.push({ role: 'user', content: text });
  send.disabled = true;

  try {
    const reply = await generateReply(text, history);
    addRow({ who: 'bot', text: reply });
    history.push({ role: 'assistant', content: reply });
  } catch (e) {
    addRow({ who: 'bot', text: 'صار شي بالخدمة يا وليدي: ' + (e.message || e) });
  } finally {
    send.disabled = false;
    input.focus();
  }
}

// ---------- Login / Profile gate ----------
function openGate() { gate.classList.remove('hide'); setTimeout(() => gateName?.focus(), 0); }
function closeGate() { gate.classList.add('hide'); }

gateForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const data = new FormData(gateForm);
  const name = (gateName.value || '').trim();
  const gender = data.get('gender');     // 'female' or 'male'
  if (!name || !gender) return;

  const profile = { name, gender };
  saveProfile(profile);
  updateProfileUI(profile);
  closeGate();
  greet(profile);
});

// Switch profile (keep chat)
switchBtn?.addEventListener('click', openGate);

// Logout (clear profile + chat)
logoutBtn?.addEventListener('click', () => {
  clearProfile();
  chat.innerHTML = '';
  openGate();
});

// ---------- Boot ----------
debugBtn?.addEventListener('click', () => window.open(`${API_BASE}/health`, '_blank'));
send.addEventListener('click', handleSend);
input.addEventListener('keydown', (e) => { if (e.key === 'Enter') handleSend(); });

// Set initial UI
const profile = loadProfile();
updateProfileUI(profile);
if (profile) {
  closeGate();
  greet(profile);
} else {
  openGate();
}

// Mobile 100vh fix
function setVH() { document.documentElement.style.setProperty('--vh', (window.innerHeight * 0.01) + 'px'); }
setVH(); window.addEventListener('resize', setVH);
