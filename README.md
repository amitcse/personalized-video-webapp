# Personalized Video Webapp

> Generate and serve personalized 5-minute videos showing users their bank account summaries, high‑spend transactions, and category breakdowns—all with dynamic text, slides, and AI‑generated voice.

---

## 🚀 Features

- **Dynamic Slides**: Renders HTML/CSS templates for intro, per‑bank summary, and outro.
- **Background Images & Logos**: Supports custom background images and bank logos.
- **Text‑to‑Speech**: Generates user‑specific narration using gTTS.
- **Video Composition**: Stitches slides and audio into a single MP4 via FFmpeg.
- **Web Interface**: FastAPI backend and simple HTML/JS frontend to collect input and preview results.

## 🛠 Tech Stack

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) + Python 3.12
- **Templating**: [Jinja2](https://palletsprojects.com/p/jinja/) for HTML slides
- **TTS**: [gTTS](https://pypi.org/project/gTTS/) (Google Text‑to‑Speech)
- **Browser Rendering**: [Playwright](https://playwright.dev/) for headless Chromium screenshots
- **Audio/Video**: [FFmpeg](https://ffmpeg.org/) via subprocess, [pydub](https://github.com/jiaaro/pydub) for metadata
- **Frontend**: Simple HTML + JavaScript form served by FastAPI

## ⚙️ Prerequisites

- **Python 3.10+**
- **FFmpeg** installed and available on your PATH
- **Playwright** browsers installed

## 📥 Installation

```bash
# Clone the repo
git clone git@github.com:YOUR_USERNAME/personalized-video-webapp.git
cd personalized-video-webapp

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Linux / macOS
venv\\Scripts\\activate   # Windows

# Install dependencies
pip install -r requirements.txt
playwright install
```

## 🚀 Running Locally

```bash
# Start the FastAPI server
uvicorn app.main:app --reload
```

Then open your browser to `http://127.0.0.1:8000`, fill in the form (name + bank JSON array), and click **Generate Video**. The personalized MP4 will appear below the form.

## 📂 Project Structure

```
personalized-video-webapp/
├── app/
│   ├── main.py                # FastAPI endpoints
│   ├── generate_video.py      # Video pipeline logic
│   └── templates/             # Jinja2 HTML slide templates
│       ├── index.html         # Frontend form
│       ├── intro.html         # Intro slide
│       ├── bank_slide_template.html
│       └── outro.html         # Outro slide
├── assets/
│   └── background.jpg         # Default background image
├── static/
│   └── videos/                # Served MP4 files
├── output/                    # Temporary slide, audio, and HTML assets
├── requirements.txt
├── data.json                  # Sample input for testing
└── README.md                  # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/YourFeature`)
3. Commit your changes (`git commit -m 'feat: add XYZ'`)
4. Push to the branch (`git push origin feat/YourFeature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

