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

# ✨ Features

## 📄 Resume Analysis

- 📑 Extract text from PDF resumes
- 📂 Detect resume sections automatically
- 📞 Extract contact information
- 🛠️ Identify technical skills
- 📊 Calculate resume completeness
- 💡 Generate personalized improvement suggestions

---

## 🎯 ATS Job Match

Compare your resume against any Job Description.

- ✅ Match technical skills
- ✅ Detect missing keywords
- ✅ Calculate ATS Job Match Score
- ✅ Highlight improvement areas
- ✅ Improve ATS compatibility

---

## 📊 Detailed ATS Score

The analyzer evaluates multiple aspects of your resume instead of providing just a single score.

| Score | Description |
|--------|-------------|
| 🎯 ATS Score | Overall Resume Score |
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
      ┌──────────────────┼──────────────────┐
      ▼                  ▼                  ▼
Extract Sections   Extract Skills   Contact Details
      │                  │                  │
      └──────────────┬───┴──────────────────┘
                     ▼
              ATS Score Engine
                     │
                     ▼
          Feedback Generation Engine
                     │
                     ▼
             JSON Response (Flask)
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
| Database | Supabase |
| Frontend | HTML5, CSS3, JavaScript |
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
│   ├── js/
│   └── images/
│
├── templates/
│   └── index.html
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

> *(Coming Soon)*

---

## 📊 ATS Result Dashboard

> *(Coming Soon)*

---

# 🚀 Roadmap

- [ ] Download ATS Report as PDF
- [ ] Resume Analysis History
- [ ] Resume Comparison
- [ ] AI Resume Suggestions
- [ ] Dark Mode
- [ ] Live Deployment

---

# 🤝 Contributing

Contributions are welcome!

If you have suggestions or improvements:

1. Fork the repository
2. Create a new branch
3. Commit your changes
4. Open a Pull Request

---

# 👨‍💻 About the Developer

## Harshit Pundir

B.Tech CSE Student • Quantum University

Passionate about Artificial Intelligence, Machine Learning, Backend Development, and building impactful software solutions.

### 🌐 Connect with Me

- **GitHub**  
  https://github.com/Harshit-pundir

- **LinkedIn**  
  https://www.linkedin.com/in/harshit-pundir-a5b112332/

- **LeetCode**  
  https://leetcode.com/Harshitpundir

---

<div align="center">

## ⭐ Support the Project

If you found this project useful, please consider giving it a **Star ⭐** on GitHub.

It motivates me to build more open-source projects.

**Made with ❤️ by Harshit Pundir**

</div>