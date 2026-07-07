# 🔍 AI ATS Resume Checker

> Stop guessing. Know exactly why your resume isn't getting shortlisted.

Most resumes get rejected before a human even reads them — filtered out by ATS bots that scan for keywords. This tool tells you exactly where you stand.

---

## 🚀 What It Does

Upload your resume + paste a job description → get an instant ATS score with a full breakdown of what's working and what's not.

- **Overall Score** — how well your resume matches the JD
- **Section-wise Breakdown** — separate scores for Skills, Projects, and Education
- **Matched Keywords** — what's already in your resume
- **Missing Keywords** — what you need to add
- **History** — all your past checks saved automatically

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask |
| NLP | spaCy (en_core_web_sm) |
| PDF Parsing | PyPDF2 |
| Database | Supabase (PostgreSQL) |
| Frontend | HTML, CSS, Vanilla JS |

---

## ⚙️ Run Locally

```bash
# 1. Clone
git clone https://github.com/Harshit-pundir/resume-ats-analyzer.git
cd resume-ats-analyzer/backend

# 2. Setup virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 4. Create .env file in /backend
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# 5. Run
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

---

## 📁 Project Structure

```
resume-ats-analyzer/
├── backend/
│   ├── app.py              # Flask routes + NLP logic
│   ├── templates/
│   │   ├── index.html      # Main UI
│   │   └── history.html    # History page
│   ├── .env                # Supabase credentials (not committed)
│   └── requirements.txt
├── .gitignore
└── README.md
```

---

## 📸 Screenshots

*(Coming soon)*

---

## 🔮 Upcoming Features

- [ ] Resume tips based on missing keywords
- [ ] Multi-resume comparison
- [ ] Deploy on Render

---

## 👨‍💻 Built by

**Harshit Pundir** — 3rd year CSE @ Quantum University  
[LinkedIn](https://www.linkedin.com/in/harshit-pundir-a5b112332/) · [GitHub](https://github.com/Harshit-pundir) · [LeetCode](https://leetcode.com/Harshitpundir)
