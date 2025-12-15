# 🚀 AI Business Brochure Generator

> **Turn any company website into a beautiful, AI-generated business brochure — instantly.**

An end-to-end **AI-powered web application** that scrapes a company’s website, intelligently understands its content, and generates a **professionally structured brochure** with live progress updates, preview, PDF export, and history tracking.

🌐 **Live Demo**: *https://ai-powered-business-brochure.onrender.com/*  
📦 **Tech Stack**: FastAPI · OpenAI · SQLAlchemy · SQLite · HTML/CSS · SSE

---

## ✨ Features

### 🧠 AI-Powered Content Generation
- Uses LLMs to understand website content
- Generates **clean, structured brochures in Markdown**
- Supports different **tones** (Professional, Humorous, etc.)

### 🔎 Intelligent Website Scraping
- Validates URLs
- Scrapes only relevant pages
- Avoids unnecessary content noise

### ⏱️ Live Progress Updates (SSE)
Real-time status updates while generation runs:
```
🔎 Scraping website content...
✍️ Generating brochure with AI...
💾 Saving brochure...
✅ Done!
```

### 👀 Rich Preview Experience
- Clean Markdown → HTML preview
- Fully clickable external links
- Opens links in new tabs for better UX

### 📄 PDF Export (Two Formats)
- **Raw Markdown PDF** – clean & readable
- **Preview-Styled PDF** – brochure-like layout

### 📚 Brochure History
- All generated brochures are saved
- View previous brochures anytime
- Re-download previews and PDFs

### 🎨 Clean, Modern UI
- Dark themed interface
- Loading spinner & status messages
- User-friendly, minimal design

---

## 🛠️ Tech Stack

| Layer | Technology |
|-----|-----------|
| Backend | **FastAPI** |
| AI | **OpenAI API** |
| Database | **SQLite + SQLAlchemy** |
| Frontend | **HTML + CSS + Jinja2** |
| Realtime | **Server-Sent Events (SSE)** |
| PDFs | **ReportLab** |
| Deployment | **Render** |

---

## 🧩 Project Architecture

```
.
├── app.py              # FastAPI application
├── scraper.py          # Website scraping logic
├── validator.py        # URL validation
├── templates/          # Jinja2 HTML templates
├── static/             # CSS & assets
├── requirements.txt    # Dependencies
└── brochures.db        # SQLite database (runtime)
```

---

## 🚀 Getting Started (Local Setup)

### 1️⃣ Clone the repository
```bash
git clone https://github.com/<your-username>/AI_Business_Brochure.git
cd AI_Business_Brochure
```

### 2️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 3️⃣ Set environment variables
Create a `.env` file:
```env
OPENAI_API_KEY=your_openai_key_here
```

### 4️⃣ Run the app
```bash
uvicorn app:app --reload
```

Visit: **http://127.0.0.1:8000**

---

## 🌍 Deployment

This project is deployed on **Render** using:
```bash
uvicorn app:app --host 0.0.0.0 --port $PORT
```

All environment variables are managed securely via Render.

---

## 🧠 Key Engineering Highlights

- Asynchronous background tasks
- Graceful error handling for API limits
- Separation of concerns (scraping, AI, UI, DB)
- Production-safe dependency management
- No notebook-only or dev-only code in deployment

---

## 🔮 Future Improvements
- User authentication & per-user history
- Custom brochure sections
- Brand themes & styling options
- PostgreSQL for persistent cloud storage
- Rate limiting & cost controls

---

## 🙌 Why This Project Matters

This project demonstrates:
- **Full-stack engineering**
- **AI integration**
- **Production deployment**
- **Real-time UX patterns**
- **Clean backend architecture**

It’s not just a demo — it’s a **deployable AI product**.

---

## 👨‍💻 Author

**Chenchu Vinay Boga**  
💡 AI · Backend · Full-Stack  

---

⭐ If you like this project, give it a star — it really helps!
