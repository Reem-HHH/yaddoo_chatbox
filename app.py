from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, requests, time, re, traceback
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODELS = [m.strip() for m in os.getenv("GROQ_MODELS","mixtral-8x7b-32768,llama-3.1-8b-instant").split(",") if m.strip()]
TIMEOUT = 45; RETRIES = 2; SLEEP = 1.0

app = Flask(__name__, static_url_path='', static_folder=str(BASE_DIR))
CORS(app)

SYSTEM_AR = ("أنتِ «يدّوه» من الإمارات: جدة طيبة وحكيمة.\\n"
             "الأسلوب: لهجة إماراتية/خليجية خفيفة، كلمات بسيطة، جُمل قصيرة وواضحة (1–2 سطر).\\n"
             "الهدف: جواب مفيد وعملي. إذا السؤال مب واضح، اسألي سؤال توضيحي *واحد* فقط.\\n"
             "لا تكررين كلام السائل، ولا تخلطين إنجليزي إلا للضرورة.\\n"
             "تعابير ممكنة (باعتدال): يا وليدي/يا وليدتي، لا تشيل هم، عفيه، يزاك الله خير، شو، ليش.\\n"
             "رمز تعبيري اختياري واحد في نهاية الجواب إذا لزم: 🫖🤍✨🌸\\n"
             "تجنّبي المواضيع الخطرة أو الطبية/القانونية الدقيقة.")

FEW_SHOTS = [
    {"role": "user", "content": "يدّوه، أنا متوتر قبل الامتحان، شو أسوي؟"},
    {"role": "assistant", "content": "لا تشيل هم يا وليدي. سوّ جدول بسيط: 25 دقيقة مذاكرة و5 دقايق راحة، ونم زين الليلة. تبيني أرتب لك خطة سريعة للمادة الأصعب؟ 🤍"},
    {"role": "user", "content": "أبغي أتمرن في البيت بس ما عندي وقت."},
    {"role": "assistant", "content": "ابدأ خفيف: 10 دقايق مشي أو سكوات يوميًا، وزيدها شوي شوي. خلّ التمرين بعد وجبة خفيفة عشان تتذكر. تبيني جدول أسبوعي؟"},
    {"role": "user", "content": "شرّحي لي البرمجة بطريقة سهلة."},
    {"role": "assistant", "content": "البرمجة مثل خطوات طبخة: تعليمات للكمبيوتر. نبدأ بلغة وحدة (مثل بايثون) وتمارين صغيرة. هدفك مواقع ولا بيانات؟ عشان أوجّهك."}
]

GREETINGS = ("هلا","مرحبا","السلام","السلام عليكم","هاي","اهلين","هلو","شلونج","شلونك")
SMALL_TALK = {
    "كيفك": "بخير يا وليدي، يزاك الله خير على السؤال. كيف أمورك انت؟",
    "كيف الحال": "تمام ولله الحمد. بشّرني عنك؟",
    "من انتي": "أنا يدّوه، جدة إماراتية أساعدك بنصيحة بسيطة من القلب. شو بخاطرك؟",
}

def rule_based_reply(text: str):
    t = re.sub(r"\\s+", " ", text).strip().lower()
    if any(g in t for g in GREETINGS) and len(t.split()) <= 3:
        return "هلا وغلا يا وليدي، نوّرت المجلس. شو بخاطرك اليوم؟ 🫖"
    for k,v in SMALL_TALK.items():
        if k in t: return v
    if re.fullmatch(r"[a-zA-Z\\d\\W_]+", t) or re.search(r"(.)\\1{3,}", t):
        return "ما فهمت الكلام زين. حطّه بجملة أو سؤال واضح عشان أساعدك."
    if len(t.split()) <= 2:
        return "وضّح لي أكثر يا وليدي: عن أي موضوع تبيني أتكلم؟ دراسة؟ صحة عامة؟ تنظيم وقت؟"
    return None

def postprocess(text: str) -> str:
    if not text: return "هاه يا وليدي، عيد سؤالك لو سمحت 🌸"
    text = re.sub(r"<\\|[^>]+?\\|>", "", text).strip()
    for a,b in [("لا تقلق","لا تشيل هم"),("لا تقلقي","لا تشيلين هم"),("نعم","ايه"),("حسناً","تمام"),("جداً","وايد"),("لماذا","ليش"),("ماذا","شو")]:
        text = text.replace(a,b)
    lines=text.splitlines()
    if len(lines)>3: text="\\n".join(lines[:3])
    return text or "يزاك الله خير يا وليدي، وضّح لي أكثر عشان أخدمك 😊"

def groq_chat(model: str, user_msg: str, history=None):
    if not GROQ_API_KEY: return False, "مفقود GROQ_API_KEY في .env"
    msgs=[{"role":"system","content":SYSTEM_AR}]; msgs+=FEW_SHOTS
    if history: msgs+=history[-12:]
    msgs.append({"role":"user","content":user_msg})
    url="https://api.groq.com/openai/v1/chat/completions"
    headers={"Authorization":f"Bearer {GROQ_API_KEY}","Content-Type":"application/json"}
    payload={"model":model,"messages":msgs,"temperature":0.35,"top_p":0.9,"max_tokens":260,"presence_penalty":0.1,"frequency_penalty":0.4,"stop":["\\n\\n\\n"]}
    try:
        r=requests.post(url,headers=headers,json=payload,timeout=TIMEOUT)
    except requests.exceptions.RequestException as e:
        return False, f"شبكة/اتصال: {e}"
    if r.status_code!=200:
        try: err=r.json()
        except Exception: err={"error": r.text[:300]}
        return False, f"خطأ Groq {r.status_code}: {err}"
    data=r.json()
    try: text=data["choices"][0]["message"]["content"]
    except Exception: text=""
    return True, postprocess(text)

def query_with_fallbacks(user_msg: str, history=None) -> str:
    last_err=None
    for model in GROQ_MODELS:
        for attempt in range(RETRIES+1):
            ok,out=groq_chat(model,user_msg,history=history)
            if ok: return out
            last_err=out; time.sleep(SLEEP*(attempt+1))
    return last_err or "صار شي بالخدمة يا وليدي. تأكد من المفتاح والإنترنت."

@app.route('/api/chat', methods=['POST'])
def chat():
    data=request.get_json(silent=True) or {}
    # FIX: no .trim() in Python
    msg = data.get('message')
    if not isinstance(msg, str):
        msg = '' if msg is None else str(msg)
    msg = msg.strip()

    history=data.get('history') or []
    if not msg: return jsonify({"reply":"قول شي يا وليدي 😊"})
    canned=rule_based_reply(msg)
    if canned: return jsonify({"reply":canned})
    return jsonify({"reply":query_with_fallbacks(msg,history=history)})

@app.errorhandler(Exception)
def handle_err(e):
    code = getattr(e, 'code', 500)
    return jsonify({"error": f"خطب بالخادم: {type(e).__name__}: {e}"}), code

@app.route('/')
def index(): return send_from_directory(str(BASE_DIR),'index.html')
@app.route('/<path:path>')
def static_proxy(path): return send_from_directory(str(BASE_DIR),path)
@app.route('/health')
def health(): return jsonify({"ok":True,"groq_models":GROQ_MODELS,"has_key":bool(GROQ_API_KEY)})

if __name__=="__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
