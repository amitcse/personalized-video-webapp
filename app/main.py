from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uuid
import os
import json
from app.generate_video import generate_video_from_data

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def form_get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate", response_class=HTMLResponse)
async def generate(request: Request, user_name: str = Form(...), bank_json: str = Form(...)):
    user_id = str(uuid.uuid4())[:8]
    data = {
        "name": user_name,
        "banks": json.loads(bank_json)
    }

    output_path = f"static/videos/{user_id}.mp4"
    os.makedirs("static/videos", exist_ok=True)

    await generate_video_from_data(data, output_path)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "video_url": f"/static/videos/{user_id}.mp4"
    })
