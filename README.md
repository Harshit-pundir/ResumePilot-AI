<div align="center">

# 🚀 AI Resume ATS Analyzer

### *Analyze. Improve. Get Shortlisted.*

An AI-powered Resume ATS Analyzer that evaluates your resume, compares it with a Job Description, detects missing skills, and generates actionable feedback to improve your chances of passing Applicant Tracking Systems (ATS).

<p align="center">

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.x-black?logo=flask)
![spaCy](https://img.shields.io/badge/NLP-spaCy-09A3D5)
![Supabase](https://img.shields.io/badge/Database-Supabase-3ECF8E?logo=supabase)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6-F7DF1E?logo=javascript)
![License](https://img.shields.io/badge/License-MIT-success)

</p>

<p align="center">
  <strong>Most resumes are rejected before a recruiter even reads them.</strong><br>
  This project helps you understand <strong>why</strong> and shows you <strong>how to improve.</strong>
</p>

</div>

---

# 📖 Overview

Applicant Tracking Systems (ATS) automatically scan resumes before they reach recruiters. A well-written resume can still be rejected if it lacks the right structure or keywords.

**AI Resume ATS Analyzer** helps job seekers evaluate their resumes by analyzing important sections, extracting technical skills, comparing resumes with job descriptions, and generating detailed ATS scores with personalized recommendations.

Whether you're applying for internships or full-time software engineering roles, this tool provides practical insights to improve your resume.

---

# 🌟 Project Highlights

- 📄 PDF Resume Parsing with PyPDF2
- 🧠 NLP-powered Skill Extraction using spaCy
- 🎯 ATS Resume & Job Description Matching
- 📊 Multi-factor ATS Scoring System
- 🗄️ Resume Analysis History with Supabase
- ⚡ Responsive Flask Web Application

# ✨ Features

## 📄 Resume Analysis

- 📑 Extract text from PDF resumes
- 📂 Detect resume sections automatically
- 📞 Extract contact information
- 🛠️ Extract technical skills using NLP
- 📊 Calculate resume completeness score
- 💡 Generate personalized ATS recommendations

---

## 🎯 ATS Job Match

Compare your resume against any Job Description.

- ✅ Match technical skills
- ✅ Detect missing keywords
- ✅ Calculate ATS Job Match Score
- ✅ Highlight improvement areas
- ✅ Improve ATS compatibility

---

## 🗄️ Analysis History

Every resume analysis is automatically stored in Supabase.

- 📜 View previous resume analyses
- 📊 Track ATS scores over time
- 🕒 Analysis timestamp
- 📁 Separate Resume Analysis & Job Match history
- ⚡ Beautiful history dashboard

---

## 📊 Detailed ATS Score

| Score | Description |
|--------|-------------|
| 🎯 Overall Score | Final Resume / ATS Score |
| 💻 Skill Match | Resume vs Job Description |
| 📂 Section Score | Skills, Projects, Education & Experience |
| 📞 Contact Score | Email, Phone, GitHub & LinkedIn |
| 📋 Completeness Score | Overall Resume Quality |

---

# 🧠 How It Works

```text
                   Resume (PDF)
                        │
                        ▼
              PDF Text Extraction
                  (PyPDF2)
                        │
                        ▼
               Resume Text Processing
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
 Resume Sections   Contact Details   Skill Extraction
        │               │               │
        └───────────────┼───────────────┘
                        ▼
                 ATS Scoring Engine
                        │
            ┌───────────┴────────────┐
            ▼                        ▼
     Resume Analysis           Job Match
            │                        │
            └───────────┬────────────┘
                        ▼
          Save Analysis History
               (Supabase)
                        │
                        ▼
            Interactive Dashboard
```

---

# 🏗️ Tech Stack

| Category | Technology |
|----------|------------|
| Backend | Python, Flask |
| NLP | spaCy |
| PDF Parsing | PyPDF2 |
| Database | Supabase (PostgreSQL) |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Version Control | Git & GitHub |

---

# 📂 Project Structure

```text
resume-ats-analyzer/
│
├── app.py
├── skills.json
├── requirements.txt
├── .env.example
├── README.md
│
├── static/
│   ├── css/
│   │   ├── style.css
│   │   └── history.css
│   ├── js/
│   └── images/
│
├── templates/
│   ├── index.html
│   └── history.html
│
└── screenshots/
```

---

# ⚙️ Installation

## 1️⃣ Clone Repository

```bash
git clone https://github.com/Harshit-pundir/resume-ats-analyzer.git
cd resume-ats-analyzer
```

---

## 2️⃣ Create Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4️⃣ Download spaCy Model

```bash
python -m spacy download en_core_web_sm
```

---

## 5️⃣ Configure Environment Variables

Create a `.env` file in the project root.

```env
SECRET_KEY=your_secret_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

---

## 6️⃣ Run the Application

```bash
python app.py
```

Open your browser and visit:

```text
http://127.0.0.1:5000
```

---

# 📸 Screenshots

## 🏠 Landing Page

![Landing Page](screenshots/landing.png)

---

## 📊 ATS Result Dashboard

![Result Dashboard](screenshots/result.png)

---

## 🗄️ Analysis History

![History Page](screenshots/history.png)

---

# 🚀 Roadmap

- [ ] Download ATS Report as PDF
- [x] Resume Analysis History
- [ ] Resume Comparison
- [ ] AI Resume Suggestions
- [x] Dark Mode
- [x] Live Deployment

---

# 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a new branch
3. Commit your changes
4. Open a Pull Request

---

# 👨‍💻 About the Developer

## Harshit Pundir

B.Tech CSE Student • Quantum University

Passionate about Backend Development, AI/ML, and building impactful software solutions.

### 🌐 Connect with Me

- **GitHub** — https://github.com/Harshit-pundir
- **LinkedIn** — https://www.linkedin.com/in/harshit-pundir-a5b112332/
- **LeetCode** — https://leetcode.com/Harshitpundir
- 📧 **Email** — harshitpundir36@gmail.com

---

<div align="center">

## ⭐ Support the Project

If you found this project useful, please consider giving it a **Star ⭐** on GitHub.

**Made with ❤️ by Harshit Pundir**

</div>
