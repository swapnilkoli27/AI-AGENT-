🚀 AI Startup Crew — Pitch Generator

A Streamlit-based multi-agent startup idea generator powered by Groq LLMs and optional CrewAI.
It takes a user’s startup idea and automatically generates:

6 brandable startup names

Market research summary

Investor-style draft pitch

Polished pitch

PDF export with proper formatting


The system simulates a Crew-style workflow:
Name Agent → Research Agent → Pitch Writer → Editor, with fallback logic when CrewAI is unavailable.


---

🌟 Features

🔹 1. Multi-Agent Workflow (Crew-style)

Name Generator

Research Analyst

Pitch Writer

Pitch Editor
Uses CrewAI automatically if installed & enabled via .env.


🔹 2. Groq-Powered LLM Responses

Uses Llama 3.1 models via Groq API for fast, cheap completions.

🔹 3. Streamlit UI

Beautiful UI with:

Idea input

Name suggestions

Pitch sections

PDF export

Re-run options


🔹 4. Automatic PDF Generation

Using reportlab to build a clean, structured pitch deck PDF.

🔹 5. Complete Local Fallback

If CrewAI isn't installed, a custom LocalCrew agent system takes over.


---

📦 Tech Stack

Python 3.10+

Streamlit

Groq LLM API

CrewAI (optional)

Reportlab (PDF generation)

Dotenv (environment config)



---

🔧 Installation Guide

1. Clone the Repository

git clone https://github.com/your-repo/startup-crew-pitch-generator.git
cd startup-crew-pitch-generator

2. Create Your Virtual Environment

python -m venv venv
source venv/bin/activate       # Linux/Mac
venv\Scripts\activate          # Windows

3. Install Dependencies

pip install -r requirements.txt

4. Set Up .env

Create a .env file with:

GROQ_API_KEY=your_groq_api_key_here
USE_OFFICIAL_CREW=true   # optional, set false to disable CrewAI

CrewAI is optional — if it fails to import, the program continues with the local agents.


---

▶️ Run the App

streamlit run app.py

Streamlit UI will open in your browser.


---

🧠 How It Works (Pipeline)

1. Name Generator Agent

Creates 6 short, brandable names.

2. Research Agent

Produces a market snapshot + competitors.

3. Pitch Writer

Writes investor-ready pitch with:

Executive Summary

Problem

Solution

UVP

Features

Business model

Tech Stack

30-sec pitch


4. Editor Agent

Polishes the pitch into a professional final version.

5. PDF Renderer

Exports polished pitch into a proper typeset PDF.


---

🗂 Project Structure

📦 project-root
 ┣ 📜 app.py                # Main Streamlit application
 ┣ 📜 requirements.txt      # Python dependencies
 ┣ 📜 README.md             # Documentation
 ┗ 📜 .env                  # API keys & config


---

⚙️ Environment Variables

Variable	Description

GROQ_API_KEY	Required — Groq LLM API key
USE_OFFICIAL_CREW	Optional — enable CrewAI if installed



---

📄 PDF Export

The generated PDF includes:

Title

Subtitle (optional)

All labeled pitch sections

Clean layout

Proper spacing & formatting


Generated via reportlab.platypus.


---

🧪 Troubleshooting

❌ Groq key not set

Check .env:

GROQ_API_KEY=xxxx

❌ CrewAI import error

Set:

USE_OFFICIAL_CREW=false

Local agents will work automatically.

❌ PDF not downloading

Ensure reportlab installed:

pip install reportlab


---

🤝 Contributions

PRs and issues are welcome!
If you'd like new features (like saving history, CSV export, more agents), feel free to open a request.


---

📜 License

MIT License — free to use, modify, and distribute.
