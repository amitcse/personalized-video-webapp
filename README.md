# Personalized Video Generator Webapp

> A web application that generates fully personalized videos by combining custom user data with dynamic templates and text-to-speech narration.

---

## 🚀 Features

- **Dynamic Templates**: Define HTML/CSS templates for intro, content slides, and outro sections.
- **Custom Data Injection**: Inject user-provided JSON data into Jinja2 templates for fully personalized content.
- **Text-to-Speech**: Generate narration audio on the fly using gTTS (Google Text-to-Speech).
- **Headless Rendering**: Use Playwright and Chromium to render templates and capture high-quality screenshots.
- **Video Composition**: Stitch slides and audio into a single MP4 video using FFmpeg.
- **Web Interface**: Simple FastAPI backend and HTML/JavaScript frontend for input collection and video preview.

## 🛠 Tech Stack

- **Python 3.10+**
- **FastAPI** for web server and API endpoints
- **Jinja2** for HTML templating
- **gTTS** for text-to-speech
- **Playwright** for headless browser rendering
- **FFmpeg** for video and audio processing
- **pydub** for audio metadata handling

## ⚙️ Prerequisites

- **Python 3.10 or newer**
- **FFmpeg** installed and on your system PATH
- **Playwright** browsers installed via `playwright install`

## 📥 Installation

```bash
# Clone the repository
git clone git@github.com:YOUR_USERNAME/personalized-video-webapp.git
cd personalized-video-webapp

# Create and activate a virtual environment
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

Open `http://127.0.0.1:8000` in your browser, enter your custom JSON data in the form, and click **Generate Video** to see your personalized video.

## 📂 Project Structure

```
personalized-video-webapp/
├── app/
│   ├── main.py                # FastAPI endpoints
│   ├── generate_video.py      # Core video generation pipeline
│   └── templates/             # Jinja2 HTML slide templates
│       ├── index.html         # Frontend form template
│       ├── intro.html         # Intro slide template
│       ├── bank_slide_template.html  # Generic content slide template
│       └── outro.html         # Outro slide template
├── assets/                    # Static assets (backgrounds, logos)
├── static/
│   └── videos/                # Served MP4 output files
├── output/                    # Temporary slide, audio, and HTML assets
├── requirements.txt           # Python dependencies
├── data.json                  # Sample data for testing
└── README.md                  # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/YourFeature`)
3. Commit your changes (`git commit -m 'feat: add XYZ'`)
4. Push to the branch (`git push origin feat/YourFeature`)
5. Open a Pull Request

## 📜 License

Distributed under the MIT License.
