import os
import html
import json
import uuid
import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
from streamlit_mic_recorder import speech_to_text

# -------------------------------------------------------------------
# Abdur AI Assistant — Voice-first AI assistant for Streamlit
# -------------------------------------------------------------------

st.set_page_config(
    page_title="Abdur AI Assistant",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root { --violet:#8b5cf6; --pink:#d946ef; --cyan:#22d3ee; }
    .stApp {
        background:
          radial-gradient(ellipse at 50% 0%, rgba(91,33,182,.22), transparent 42%),
          linear-gradient(145deg, #090b1a 0%, #101027 52%, #090b18 100%);
        color: #f8fafc;
        font-family: 'DM Sans', sans-serif;
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] {
        background: rgba(10,12,30,.92);
        border-right: 1px solid rgba(167,139,250,.16);
    }
    .hero { text-align:center; padding: 1.2rem 0 .4rem; }
    .brand {
        font-family:'Space Grotesk',sans-serif; font-weight:700;
        font-size:clamp(2rem,5vw,3.35rem); letter-spacing:-.06em;
        background:linear-gradient(90deg,#fff 15%,#c4b5fd 55%,#67e8f9);
        -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    }
    .sub { color:#a5a6c7; font-size:1rem; margin-top:.25rem; }
    .orb-wrap { display:flex; justify-content:center; margin:1.2rem auto 1.4rem; }
    .orb {
        width:130px;height:130px;border-radius:50%;position:relative;
        display:grid;place-items:center;
        background:radial-gradient(circle at 35% 28%,#f0abfc 0%,#a855f7 24%,#2563eb 58%,#07152d 78%);
        box-shadow:0 0 28px #9333ea88,0 0 75px #7c3aed55, inset 0 0 22px #fff7;
        animation:float 4s ease-in-out infinite;
    }
    .orb:before,.orb:after {content:"";position:absolute;inset:-13px;border-radius:50%;border:1px solid #a78bfa55;animation:pulse 3s ease-out infinite;}
    .orb:after {inset:-26px;animation-delay:1.5s;}
    .orb span {font-size:2.6rem;filter:drop-shadow(0 2px 9px #fff8);}
    @keyframes pulse {0%{transform:scale(.88);opacity:.8}100%{transform:scale(1.25);opacity:0}}
    @keyframes float {0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}
    .panel {
        background:linear-gradient(145deg,rgba(24,25,55,.88),rgba(13,17,39,.92));
        border:1px solid rgba(167,139,250,.2);border-radius:22px;
        padding:1.1rem 1.2rem;box-shadow:0 18px 55px #0003;
    }
    .muted { color:#a5a6c7; }
    .user-bubble {
        margin:.8rem 0 .8rem auto;max-width:88%;width:fit-content;
        background:linear-gradient(120deg,#6d28d9,#7c3aed);
        padding:.85rem 1rem;border-radius:18px 18px 5px 18px;color:white;
    }
    .assistant-bubble {
        margin:.8rem auto .8rem 0;max-width:94%;
        background:rgba(30,35,67,.9);border:1px solid #8b5cf633;
        padding:1rem 1.1rem;border-radius:18px 18px 18px 5px;color:#f1f0ff;
    }
    div.stButton > button {
        border-radius:14px;border:1px solid #a78bfa55;
        background:linear-gradient(100deg,#6d28d9,#9333ea);
        color:white;font-weight:700;min-height:2.8rem;
    }
    div.stButton > button:hover {border-color:#c4b5fd;color:white;filter:brightness(1.12);}
    .stTextArea textarea,.stTextInput input {
        background:#10152d!important;color:#f8fafc!important;
        border:1px solid #8b5cf655!important;border-radius:14px!important;
    }
    .small-note {color:#9295b8;font-size:.82rem;text-align:center;}
    </style>
    """,
    unsafe_allow_html=True,
)

def get_secret(name: str, default: str = "") -> str:
    """Read Streamlit Cloud secrets first, then local environment variables."""
    try:
        value = st.secrets.get(name, default)
        if value:
            return str(value)
    except Exception:
        pass
    return os.getenv(name, default)

def speak_text(text: str, language: str, voice_style: str = "Natural browser voice") -> None:
    """Speak text in the browser using its installed speech-synthesis voices."""
    safe_text = html.escape(text).replace("\n", " ")
    lang = "ur-PK" if language.lower().startswith("urdu") else "en-US"
    utterance_id = str(uuid.uuid4())
    page = f"""
    <div id="voice-{utterance_id}" style="color:#c4b5fd;font:13px sans-serif;text-align:center;padding:4px">
      <span>🔊 Preparing voice reply…</span>
    </div>
    <script>
    (() => {{
      const text = {json.dumps(text, ensure_ascii=False)};
      const lang = {lang!r};
      const status = document.getElementById("voice-{utterance_id}");
      if (!("speechSynthesis" in window)) {{
        status.textContent = "Your browser does not support speech playback.";
        return;
      }}
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = lang;
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      utterance.volume = 1.0;
      const chooseVoice = () => {{
        const voices = window.speechSynthesis.getVoices();
        const prefix = lang.toLowerCase().split("-")[0];
        const matches = voices.filter(v => v.lang.toLowerCase().startsWith(prefix));
        if (matches.length) utterance.voice = matches[0];
        status.textContent = matches.length
          ? "Speaking your answer…"
          : "Speaking with the browser's default voice…";
        utterance.onend = () => status.textContent = "Voice reply finished";
        utterance.onerror = () => status.textContent = "Voice playback was unavailable. Try Replay voice.";
        window.speechSynthesis.speak(utterance);
      }};
      if (window.speechSynthesis.getVoices().length) chooseVoice();
      else {{
        window.speechSynthesis.onvoiceschanged = chooseVoice;
        setTimeout(chooseVoice, 900);
      }}
    }})();
    </script>
    """
    components.html(page, height=42)

# Header
st.markdown(
    """
    <div class="hero">
      <div class="brand">Abdur AI Assistant</div>
      <div class="sub">Your voice-powered AI companion · Speak naturally, get answers instantly</div>
    </div>
    <div class="orb-wrap"><div class="orb"><span>✦</span></div></div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## ✦ Assistant settings")
    language_choice = st.selectbox(
        "Conversation language",
        ["English", "Urdu"],
        help="Choose the language for speech recognition and spoken answers.",
    )
    model = st.text_input(
        "Groq model",
        value=get_secret("GROQ_MODEL", "openai/gpt-oss-20b"),
        help="You can change this to another model available in your Groq account.",
    )
    auto_speak = st.toggle("Automatically speak AI answers", value=True)
    st.divider()
    st.markdown("### How to use")
    st.caption("1. Allow microphone access in your browser.")
    st.caption("2. Choose English or Urdu.")
    st.caption("3. Tap the microphone and speak.")
    st.caption("4. Your question is sent to Groq; the answer is spoken automatically.")
    st.caption("You can also type a message below.")
    st.divider()
    if st.button("＋ New conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_spoken_id = None
        st.rerun()
    st.caption("API keys stay on the server. Never place your Groq key in frontend code.")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_spoken_id" not in st.session_state:
    st.session_state.last_spoken_id = None

api_key = get_secret("GROQ_API_KEY")
if not api_key:
    st.warning(
        "Add your Groq API key to Streamlit Secrets as `GROQ_API_KEY` before sending messages."
    )
    with st.expander("How to add your API key"):
        st.markdown(
            """
            In Streamlit Cloud, open **App settings → Secrets** and add:

            ```toml
            GROQ_API_KEY = "your_groq_api_key_here"
            GROQ_MODEL = "openai/gpt-oss-20b"
            ```

            For local testing, create `.streamlit/secrets.toml` with the same values.
            Do not upload that secrets file or your API key to GitHub.
            """
        )

# Conversation history
st.markdown("### Conversation")
if not st.session_state.messages:
    st.markdown(
        '<div class="panel"><div style="font-size:1.05rem;font-weight:700">What would you like to ask?</div>'
        '<div class="muted" style="margin-top:6px">Tap the microphone to speak, or type your message below.</div></div>',
        unsafe_allow_html=True,
    )

for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(
            f'<div class="user-bubble">{html.escape(message["content"]).replace(chr(10), "<br>")}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="assistant-bubble"><b>✦ Abdur AI</b><br><br>{html.escape(message["content"]).replace(chr(10), "<br>")}</div>',
            unsafe_allow_html=True,
        )

def get_answer(prompt: str) -> str:
    client = Groq(api_key=api_key)
    language_instruction = (
        "Reply in natural Urdu. Use Urdu script, not Hindi/Devanagari."
        if language_choice == "Urdu"
        else "Reply in clear, natural English."
    )
    system_prompt = (
        "You are Abdur AI Assistant, a helpful, accurate, friendly voice assistant. "
        "Keep spoken answers clear and conversational. Avoid markdown tables and excessive formatting. "
        + language_instruction
    )
    response = client.chat.completions.create(
        model=model.strip() or "openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": system_prompt},
            *[
                {"role": item["role"], "content": item["content"]}
                for item in st.session_state.messages[-12:]
            ],
            {"role": "user", "content": prompt},
        ],
        temperature=0.6,
        max_completion_tokens=1200,
    )
    return response.choices[0].message.content or "I couldn't generate an answer. Please try again."

def process_prompt(prompt: str) -> None:
    prompt = prompt.strip()
    if not prompt:
        return
    if not api_key:
        st.error("Please add GROQ_API_KEY in Streamlit Secrets first.")
        return
    st.session_state.messages.append({"role": "user", "content": prompt})
    try:
        with st.spinner("Abdur AI is thinking…"):
            answer = get_answer(prompt)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.pending_voice = {
            "id": str(uuid.uuid4()),
            "text": answer,
            "language": language_choice,
        }
    except Exception as exc:
        st.error(f"Could not get an answer from Groq: {exc}")
        # Keep the question in history so the user can retry or edit it.

# Voice input
st.markdown("### 🎙️ Speak to Abdur AI")
st.caption("Select the language above, then press the microphone button and speak clearly.")
speech_language = "ur-PK" if language_choice == "Urdu" else "en-US"
voice_text = speech_to_text(
    language=speech_language,
    start_prompt="🎙️ Start speaking",
    stop_prompt="⏹️ Stop recording",
    just_once=True,
    use_container_width=True,
    key=f"speech_{speech_language}",
)

if voice_text:
    st.markdown(
        f'<div class="panel"><b>Recognized speech</b><br>{html.escape(voice_text)}</div>',
        unsafe_allow_html=True,
    )
    if st.button("Send voice question", key="send_voice", use_container_width=True):
        process_prompt(voice_text)
        st.rerun()

st.divider()
st.markdown("### ⌨️ Or type your question")
with st.form("text_message_form", clear_on_submit=True):
    typed_prompt = st.text_area(
        "Your message",
        placeholder="Type a question here…",
        label_visibility="collapsed",
        height=90,
    )
    submitted = st.form_submit_button("Send message  ➜", use_container_width=True)
if submitted and typed_prompt.strip():
    process_prompt(typed_prompt)
    st.rerun()

# Automatic speech playback for the newest answer
pending = st.session_state.get("pending_voice")
if pending and pending["id"] != st.session_state.last_spoken_id:
    st.markdown("### 🔊 Voice reply")
    speak_text(pending["text"], pending["language"])
    st.session_state.last_spoken_id = pending["id"]

# Replay latest answer on demand
latest_answer = next(
    (m["content"] for m in reversed(st.session_state.messages) if m["role"] == "assistant"),
    None,
)
if latest_answer:
    st.markdown("### Answer controls")
    if st.button("🔊 Replay latest answer", use_container_width=True):
        speak_text(latest_answer, language_choice)
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_voice = None
        st.session_state.last_spoken_id = None
        st.rerun()

st.markdown(
    '<p class="small-note">Abdur AI Assistant · Powered by Groq · Voice features use your browser</p>',
    unsafe_allow_html=True,
)
