
from dotenv import load_dotenv
load_dotenv()

import os
import time
import io
import re
import traceback
from xml.sax.saxutils import escape

import streamlit as st
from groq import Groq
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib import colors

# -------------------------
# Config: Official CrewAI
# -------------------------
USE_OFFICIAL_CREW_ENV = os.getenv("USE_OFFICIAL_CREW", "false").lower() in ("1", "true", "yes")
USE_CREWAI = False
if USE_OFFICIAL_CREW_ENV:
    try:
        from crewai import Agent, Task, Crew, Process
        from crewai.project import CrewBase, agent, crew, llm
        USE_CREWAI = True
    except Exception:
        USE_CREWAI = False

# -------------------------
# Streamlit page config
# -------------------------
st.set_page_config(page_title="AI Startup Crew — Pitch Generator", page_icon="🚀", layout="wide")

# -------------------------
# Groq client
# -------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    st.warning("GROQ_API_KEY not set. Create a .env with GROQ_API_KEY if you want Groq LLM access.")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# -------------------------
# Session defaults
# -------------------------
defaults = {
    "idea": "",
    "names": [],
    "research": "",
    "draft_pitch": "",
    "polished_pitch": "",
    "selected_name": None,
    "last_generated_for": None,
    "history": [],
    "runs_count": 0,
    "crew_log": []
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# -------------------------
# Styles
# -------------------------
st.markdown("""
<style>
:root { --accent: #0b3d91; --bg: #F6F9FF; --card: #FFFFFF; }
body { background: var(--bg); }
.header { font-size:28px; font-weight:800; color:var(--accent); margin-bottom:6px; }
.tagline { font-size:13px; color:#4b5563; margin-bottom:12px; }
.card { background:var(--card); border-radius:12px; padding:14px; border:1px solid #E6EEF8; }
.name-card { background:#F8FBFF; padding:10px 12px; border-radius:10px; border:1px solid #D9E8FB; margin-bottom:8px; font-size:15px; }
.muted { color:#6b7280; font-size:13px; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='header'>🚀 AI Startup Crew — Pitch Generator</div>", unsafe_allow_html=True)
st.markdown("<div class='tagline'>Crew-style multi-agent flow (Name → Research → Pitch → Edit) — Groq + optional CrewAI</div>", unsafe_allow_html=True)

# -------------------------
# Helpers: Groq + PDF
# -------------------------
def groq_chat(prompt: str, model="llama-3.1-8b-instant", temperature=0.6, max_retries=2):
    if not client:
        return ""
    for attempt in range(max_retries + 1):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature
            )
            choice = resp.choices[0]
            message = getattr(choice, "message", None)
            if message:
                try: return message.content
                except: return message.get("content", "")
            for attr in ("text","content"):
                if hasattr(choice, attr):
                    return getattr(choice, attr)
            return str(resp)
        except Exception as e:
            if attempt < max_retries:
                time.sleep(0.6 + attempt*0.5)
                continue
            st.error("Groq request failed: "+str(e))
            st.error(traceback.format_exc())
            return ""

def extract_sections(full_text):
    sections = ["Executive Summary","Problem","Solution","Target Market","Unique Value Proposition",
                "Key Features","Business Model","Technology Stack","Market Opportunity","30-second Investor Pitch"]
    pat = r"(?:\*{0,2}\s*)?(?P<h>" + "|".join([re.escape(s) for s in sections]) + r")\s*:"
    matches = list(re.finditer(pat, full_text, flags=re.IGNORECASE))
    out = {}
    if not matches:
        out["Full Pitch"] = full_text.strip()
        return out
    for i,m in enumerate(matches):
        title = m.group("h").strip()
        start = m.end()
        end = matches[i+1].start() if i+1 < len(matches) else len(full_text)
        content = full_text[start:end].strip().replace("**","").replace("##","").strip()
        if not content:
            content = full_text[start:start+800].strip()
        out[title] = content
    return out

def build_pdf_bytes(name, pitch_text, subtitle=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=25*mm, bottomMargin=20*mm)
    title_style = ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=colors.HexColor("#0b3d91"))
    sub_style = ParagraphStyle("sub", fontName="Helvetica", fontSize=10, leading=12, textColor=colors.grey)
    sec_style = ParagraphStyle("sec", fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=colors.HexColor("#0b3d91"))
    normal = ParagraphStyle("normal", fontName="Helvetica", fontSize=11, leading=14)

    story = []
    story.append(Paragraph(escape(name), title_style))
    story.append(Spacer(1,6))
    if subtitle:
        story.append(Paragraph(escape(subtitle), sub_style))
        story.append(Spacer(1,10))

    secs = extract_sections(pitch_text or "")
    for title, body in secs.items():
        story.append(Paragraph(escape(title), sec_style))
        story.append(Spacer(1,4))
        story.append(Paragraph(escape(body).replace("\n","<br/>"), normal))
        story.append(Spacer(1,12))

    doc.build(story)
    buffer.seek(0)
    return buffer

# -------------------------
# Official CrewAI
# -------------------------
if USE_CREWAI:
    try:
        from crewai import Agent
        from crewai.project import CrewBase, agent, crew, llm

        @CrewBase
        class StartupCrew:
            @llm
            def groq_llm(self): return {"provider":"groq"}

            @agent
            def name_generator(self):
                return Agent(role="Name Generator",
                             goal="Produce 6 short brandable names for the idea",
                             llm="groq/llama3-8b-8192")

            @agent
            def researcher(self):
                return Agent(role="Researcher", goal="Provide concise market research summary")

            @agent
            def pitch_writer(self):
                return Agent(role="Pitch Writer", goal="Write investor-ready pitch with labeled sections")

            @agent
            def editor(self):
                return Agent(role="Editor", goal="Polish pitch for clarity and investor tone")

            @crew
            def crew(self):
                return Crew(agents=self.agents, process=Process.sequential, verbose=False)

        def run_official_crew(idea, selected_name=None):
            sc = StartupCrew()
            crew_obj = sc.crew()
            result = crew_obj.kickoff(inputs={"idea":idea,"name":selected_name})
            # normalize keys
            out = {}
            out["names"] = result.get("names") or result.get("name_generator") or result.get("name_generator.output")
            out["research"] = result.get("research") or result.get("researcher")
            out["draft_pitch"] = result.get("draft_pitch") or result.get("pitch_writer") or result.get("pitch")
            out["polished_pitch"] = result.get("polished_pitch") or result.get("edited") or result.get("polished")
            return out
    except Exception:
        USE_CREWAI = False

# -------------------------
# LocalCrew fallback
# -------------------------
class LocalCrew:
    def __init__(self, idea:str):
        self.idea = idea.strip()
        self.outputs = {}
        self.log = []

    def name_agent(self):
        prompt=f'Generate 6 unique short brandable startup names for: "{self.idea}". One per line.'
        out = groq_chat(prompt, temperature=0.7)
        if not out:
            fallback=["SkyPads","RoofRent","TopVenue","Rooftopify","RoofReserve","AeroEvents"]
            self.outputs["names"]=fallback
        else:
            names=[n.strip(" -•.") for n in out.splitlines() if n.strip()]
            self.outputs["names"]=list(dict.fromkeys(names))[:6]
        self.log.append("NameAgent done")
        return self.outputs["names"]

    def research_agent(self):
        prompt=f'Provide concise market research summary for: "{self.idea}". Mention top competitors.'
        out=groq_chat(prompt,temperature=0.5)
        if not out: out="No research available."
        self.outputs["research"]=out.strip()
        self.log.append("Researcher done")
        return self.outputs["research"]

    def pitch_writer(self, chosen_name=None):
        name_instr=f'Use the name "{chosen_name}".' if chosen_name else "Do not use a name."
        prompt=f"""
You are a professional startup strategist. {name_instr}
Write an investor-ready pitch with labeled sections:
Executive Summary
Problem
Solution
Target Market
Unique Value Proposition
Key Features
Business Model
Technology Stack
Market Opportunity
30-second Investor Pitch

Idea: {self.idea}
"""
        out=groq_chat(prompt,temperature=0.5)
        if not out: out=f"Executive Summary\nA short pitch for: {self.idea}\nProblem\nTBD\nSolution\nTBD"
        self.outputs["draft_pitch"]=out.strip()
        self.log.append("PitchWriter done")
        return self.outputs["draft_pitch"]

    def editor_agent(self):
        draft=self.outputs.get("draft_pitch","")
        prompt=f'Polish the following pitch for clarity and investor tone. Keep headings.\n\n{draft}'
        out=groq_chat(prompt,temperature=0.3)
        if not out: out=draft
        self.outputs["polished"]=out.strip()
        self.log.append("Editor done")
        return self.outputs["polished"]

# -------------------------
# Streamlit UI
# -------------------------
st.markdown("### 💡 Describe your startup idea")
st.session_state.idea = st.text_area("", value=st.session_state.idea, height=120,
                                     placeholder="Example: A platform that rents unused rooftops for events")

c1,c2,c3=st.columns([1.3,1,1])
with c1: run_full=st.button("🚀 Run Crew (Names, Research, Draft, Polish)", use_container_width=True)
with c2: gen_names_only=st.button("✨ Generate Names Only", use_container_width=True)
with c3: clear_btn=st.button("🧹 Clear")

if clear_btn:
    for k in ("names","research","draft_pitch","polished_pitch","selected_name","last_generated_for"):
        st.session_state[k]=defaults.get(k,"")

# -------------------------
# Run Name Generation
# -------------------------
def run_names(idea):
    if USE_CREWAI:
        try: parsed=run_official_crew(idea); names=parsed.get("names") or []
        except: crew=LocalCrew(idea); names=crew.name_agent()
    else:
        crew=LocalCrew(idea); names=crew.name_agent()
    return names

if gen_names_only and st.session_state.idea:
    st.session_state.names=run_names(st.session_state.idea)
    st.session_state.selected_name=None
    st.session_state.last_generated_for=None

if run_full and st.session_state.idea:
    crew_log=[]
    if USE_CREWAI:
        try: parsed=run_official_crew(st.session_state.idea)
        except: parsed={}
    else: parsed={}
    # fallback local crew for any missing
    crew=LocalCrew(st.session_state.idea)
    st.session_state.names=parsed.get("names") or crew.name_agent()
    st.session_state.research=parsed.get("research") or crew.research_agent()
    st.session_state.draft_pitch=parsed.get("draft_pitch") or crew.pitch_writer()
    st.session_state.polished_pitch=parsed.get("polished_pitch") or crew.editor_agent()

# -------------------------
# Names display & selection
# -------------------------
if st.session_state.names:
    st.markdown("## 🎯 Name Suggestions & Selection")
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    for i,nm in enumerate(st.session_state.names):
        key=f"name_btn_{i}"
        if st.button(nm,key=key):
            cleaned=re.sub(r"^\d+\.\s*","",nm).strip()
            st.session_state.selected_name=cleaned
            crew2=LocalCrew(st.session_state.idea)
            st.session_state.draft_pitch=crew2.pitch_writer(chosen_name=cleaned)
            st.session_state.polished_pitch=crew2.editor_agent()
    if st.button("🔄 Regenerate Names"):
        st.session_state.names=run_names(st.session_state.idea)
        st.session_state.selected_name=None
        st.session_state.last_generated_for=None
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# Research + Draft + Polished
# -------------------------
if st.session_state.research:
    st.markdown("## 🔎 Market Research Snapshot")
    st.markdown(f"<div class='card'><div class='muted'>Research Summary</div><br>{st.session_state.research.replace(chr(10),'<br><br>')}</div>", unsafe_allow_html=True)

if st.session_state.draft_pitch:
    st.markdown("## ✍️ Draft Pitch (pre-edit)")
    st.markdown(f"<div class='card'>{st.session_state.draft_pitch.replace(chr(10),'<br><br>')}</div>", unsafe_allow_html=True)

if st.session_state.polished_pitch:
    st.markdown("## ✅ Polished Pitch")
    st.markdown(f"<div class='card'>{st.session_state.polished_pitch.replace(chr(10),'<br><br>')}</div>", unsafe_allow_html=True)

# -------------------------
# PDF Export
# -------------------------
if st.session_state.selected_name and st.session_state.polished_pitch:
    st.markdown("### 📦 Exports")
    pdf_bytes=build_pdf_bytes(st.session_state.selected_name, st.session_state.polished_pitch)
    st.download_button("📄 Download Polished Pitch (PDF)", data=pdf_bytes,
                       file_name=f"{st.session_state.selected_name.lower().replace(' ','_')}_pitch.pdf",
                       mime="application/pdf", use_container_width=True)

st.markdown("---")
