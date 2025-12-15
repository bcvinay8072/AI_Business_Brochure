import os
import json
from dotenv import load_dotenv
from scraper import fetch_website_links, fetch_website_contents
from openai import OpenAI
import markdown
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Request

from fastapi.responses import FileResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
import tempfile




import os
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse
from validator import validate_url, UrlNotValid

import uuid
import asyncio

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///brochures.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Brochure(Base):
    __tablename__ = "brochures"

    id = Column(Integer, primary_key=True, index=True)
    company = Column(String, nullable=False)
    url = Column(String, nullable=False)
    tone = Column(String, nullable=False)
    markdown = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


progress_store = {}  # task_id → list of messages
result_store = {}    # task_id → markdown result


load_dotenv(override=True)
api_key = os.getenv('OPENAI_API_KEY')

MODEL = 'gpt-5-nano'
openai = OpenAI()

# links = fetch_website_links("https://edwarddonner.com")

# print(links)

# First step: Have GPT-5-nano figure out which links are relevant

link_system_prompt = """
You are provided with a list of links found on a webpage.
You are able to decide which of the links would be most relevant to include in a brochure about the company,
such as links to an About page, or a Company page, or Careers/Jobs pages.
You should respond in JSON as in this example:

{
    "links": [
        {"type": "about page", "url": "https://full.url/goes/here/about"},
        {"type": "careers page", "url": "https://another.full.url/careers"}
    ]
}
"""

def get_links_user_prompt(url):
    user_prompt = f"""
Here is the list of links on the website {url} -
Please decide which of these are relevant web links for a brochure about the company, 
respond with the full https URL in JSON format.
Do not include Terms of Service, Privacy, email links.

Links (some might be relative links):

"""
    links = fetch_website_links(url)
    user_prompt += "\n".join(links)
    return user_prompt


# print(get_links_user_prompt("https://edwarddonner.com"))

def select_relevant_links(url):
    print(f"Selecting relevant links for {url} by calling {MODEL}")
    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": link_system_prompt},
            {"role": "user", "content": get_links_user_prompt(url)}
        ],
        response_format={"type": "json_object"}
    )
    result = response.choices[0].message.content
    links = json.loads(result)
    print(f"Found {len(links['links'])} relevant links")
    return links

# links = select_relevant_links("https://huggingface.co")

# print(links)

def fetch_page_and_all_relevant_links(url):
    contents = fetch_website_contents(url)
    relevant_links = select_relevant_links(url)
    result = f"## Landing Page:\n\n{contents}\n## Relevant Links:\n"
    for link in relevant_links['links']:
        result += f"\n\n### Link: {link['type']}\n"
        result += fetch_website_contents(link["url"])
    return result

# print(fetch_page_and_all_relevant_links("https://huggingface.co"))

BROCHURE_PROMPTS = {
    "professional": """
You are a professional marketing assistant that analyzes company website content
and creates a polished, formal business brochure for customers and investors.
Use clear sections, professional tone, and concise language.
Respond in markdown without code blocks.
""",

    "humorous": """
You are a witty, humorous, entertaining assistant that analyzes company website content
and creates a fun, light-hearted brochure while still being informative.
Respond in markdown without code blocks.
Include culture, careers, and personality.
"""
}

def create_brochure(company_name, content, tone):
    system_prompt = BROCHURE_PROMPTS.get(tone, BROCHURE_PROMPTS["professional"])

    response = openai.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""
Company: {company_name}

Website content:
{content}

Create a brochure in markdown.
"""
            }
        ],
    )

    result = response.choices[0].message.content

    with open("brochure.md", "w", encoding="utf-8") as f:
        f.write(result)

    return result

    
    
# create_brochure("HuggingFace", "https://huggingface.co")
async def generate_brochure_with_progress(task_id, company, url, tone):
    def log(msg):
        progress_store[task_id].append(msg)

    progress_store[task_id] = []

    try:
        log("🔎 Scraping website content...")
        content = fetch_page_and_all_relevant_links(url)

        log("✍️ Generating brochure with AI...")
        markdown_text = create_brochure(company, content, tone)

        log("💾 Saving brochure...")
        result_store[task_id] = markdown_text

        db = SessionLocal()
        db.add(Brochure(
            company=company,
            url=url,
            tone=tone,
            markdown=markdown_text
        ))
        db.commit()
        db.close()

        log("✅ Done!")

    except Exception as e:
        log(f"❌ Error: {str(e)}")
        log("DONE_ERROR")

    





load_dotenv()

app = FastAPI()

init_db()


app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")



@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/history", response_class=HTMLResponse)
async def history(request: Request):
    db = SessionLocal()
    brochures = db.query(Brochure).order_by(Brochure.created_at.desc()).all()
    db.close()

    return templates.TemplateResponse(
        "history.html",
        {
            "request": request,
            "brochures": brochures
        }
    )


@app.get("/history/{brochure_id}", response_class=HTMLResponse)
async def history_detail(request: Request, brochure_id: int):
    db = SessionLocal()
    brochure = db.query(Brochure).get(brochure_id)
    db.close()

    if not brochure:
        return HTMLResponse("Not found", status_code=404)

    html_preview = markdown.markdown(
        brochure.markdown,
        extensions=["extra", "sane_lists"]
    )

    html_preview = html_preview.replace(
        "<a ",
        '<a target="_blank" rel="noopener noreferrer" '
    )

    return templates.TemplateResponse(
        "preview.html",
        {
            "request": request,
            "company": brochure.company,
            "tone": brochure.tone,
            "preview": html_preview,
            "history_id": brochure.id
        }
    )


@app.post("/brochure/start")
async def start_brochure(
    company: str = Form(...),
    url: str = Form(...),
    tone: str = Form(...)
):
    validate_url(url)

    task_id = str(uuid.uuid4())
    asyncio.create_task(
        generate_brochure_with_progress(task_id, company, url, tone)
    )

    return {"task_id": task_id}

from fastapi.responses import StreamingResponse
import time

@app.get("/progress/{task_id}")
async def progress(task_id: str):
    async def event_stream():
        last_index = 0
        while True:
            if task_id not in progress_store:
                await asyncio.sleep(0.2)
                continue

            messages = progress_store[task_id]
            while last_index < len(messages):
                yield f"data: {messages[last_index]}\n\n"
                last_index += 1

            if messages and messages[-1] == "✅ Done!":
                break

            await asyncio.sleep(0.3)

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.get("/result/{task_id}", response_class=HTMLResponse)
async def result(request: Request, task_id: str):
    markdown_text = result_store.get(task_id)

    if not markdown_text:
        return HTMLResponse("Still processing...", status_code=202)

    html_preview = markdown.markdown(
    markdown_text,
    extensions=["extra", "sane_lists", "smarty"]
)

    html_preview = html_preview.replace(
        "<a ",
        '<a target="_blank" rel="noopener noreferrer" '
    )

    return templates.TemplateResponse(
        "preview.html",
        {
            "request": request,
            "company": "Generated",
            "tone": "",
            "preview": html_preview
        }
    )




@app.post("/brochure", response_class=HTMLResponse)
async def brochure(
    request: Request,
    company: str = Form(...),
    url: str = Form(...),
    tone: str = Form(...)
):
    try:
        validate_url(url)
    except UrlNotValid as e:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "message": str(e)
            },
            status_code=400
        )

    markdown_text = create_brochure(company, url, tone)
    html_preview = markdown.markdown(
    markdown_text,
    extensions=["extra", "sane_lists", "smarty"]
    )

    html_preview = html_preview.replace(
    "<a ",
    '<a target="_blank" rel="noopener noreferrer" '
    )


    return templates.TemplateResponse(
        "preview.html",
        {
            "request": request,
            "company": company,
            "tone": tone,
            "preview": html_preview
        }
    )
    
    
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT

TITLE_COLOR = HexColor("#0f172a")
TEXT_COLOR = HexColor("#1f2937")
ACCENT_COLOR = HexColor("#2563eb")

def get_pdf_styles():
    return {
        "title": ParagraphStyle(
            "Title",
            fontSize=20,
            leading=24,
            spaceAfter=12,
            textColor=TITLE_COLOR,
            alignment=TA_LEFT,
        ),
        "h1": ParagraphStyle(
            "Heading1",
            fontSize=16,
            leading=20,
            spaceBefore=12,
            spaceAfter=6,
            textColor=ACCENT_COLOR,
        ),
        "h2": ParagraphStyle(
            "Heading2",
            fontSize=14,
            leading=18,
            spaceBefore=10,
            spaceAfter=4,
            textColor=ACCENT_COLOR,
        ),
        "body": ParagraphStyle(
            "Body",
            fontSize=11,
            leading=15,
            spaceAfter=4,
            textColor=TEXT_COLOR,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            fontSize=11,
            leading=15,
            leftIndent=14,
            bulletIndent=6,
            spaceAfter=2,
            textColor=TEXT_COLOR,
        ),
    }

def markdown_to_pdf(markdown_text: str, output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=48,
        leftMargin=48,
        topMargin=48,
        bottomMargin=48,
    )

    styles = get_pdf_styles()
    story = []

    for line in markdown_text.split("\n"):
        line = line.strip()

        if not line:
            continue  # ❌ no huge empty gaps

        if line.startswith("# "):
            story.append(Paragraph(line[2:], styles["title"]))

        elif line.startswith("## "):
            story.append(Paragraph(line[3:], styles["h1"]))

        elif line.startswith("### "):
            story.append(Paragraph(line[4:], styles["h2"]))

        elif line.startswith("- "):
            story.append(
                Paragraph(line[2:], styles["bullet"], bulletText="•")
            )

        else:
            story.append(Paragraph(line, styles["body"]))

    doc.build(story)


    
    
def html_to_pdf(html_text: str, output_path: str):
    # Convert HTML back to text-ish, but preserve structure
    import re

    text = re.sub("</p>", "\n", html_text)
    text = re.sub("<br\\s*/?>", "\n", text)
    text = re.sub("<[^<]+?>", "", text)

    markdown_to_pdf(text, output_path)


    
from fastapi.responses import FileResponse

@app.get("/download/markdown/{task_id}")
async def download_markdown_pdf(task_id: str):
    markdown_text = result_store.get(task_id)
    if not markdown_text:
        raise HTTPException(status_code=404, detail="Brochure not found")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    markdown_to_pdf(markdown_text, tmp.name)

    return FileResponse(
        tmp.name,
        filename="brochure_raw.pdf",
        media_type="application/pdf"
    )


@app.get("/download/preview/{task_id}")
async def download_preview_pdf(task_id: str):
    markdown_text = result_store.get(task_id)
    if not markdown_text:
        raise HTTPException(status_code=404, detail="Brochure not found")

    html_preview = markdown.markdown(markdown_text)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    html_to_pdf(html_preview, tmp.name)

    return FileResponse(
        tmp.name,
        filename="brochure_preview.pdf",
        media_type="application/pdf"
    )






