import os
import json
import subprocess
from gtts import gTTS
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from playwright.sync_api import sync_playwright

# --- Setup ---
env = Environment(loader=FileSystemLoader('templates'))
OUTPUT_BASE = "output"
WIDTH, HEIGHT = 1280, 720

# --- Helpers ---
def render_html(template_name, context, output_file):
    template = env.get_template(template_name)
    html = template.render(context)
    with open(output_file, 'w') as f:
        f.write(html)

def take_screenshot(html_path, image_path):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': WIDTH, 'height': HEIGHT})
        page.goto(Path(html_path).resolve().as_uri())
        page.screenshot(path=image_path)
        browser.close()

def generate_audio(text, audio_path):
    tts = gTTS(text=text, lang='en')
    tts.save(audio_path)

def make_video(image_path, audio_path, video_path):
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", image_path,
        "-i", audio_path, "-c:v", "libx264", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k", "-shortest",
        "-pix_fmt", "yuv420p", "-vf", f"scale={WIDTH}:{HEIGHT}",
        video_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

def concat_videos(video_list, output_path):
    txt_path = "concat_list.txt"
    with open(txt_path, "w") as f:
        for video in video_list:
            f.write(f"file '{video}'\n")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", txt_path, "-c", "copy", output_path
    ])
    os.remove(txt_path)

# --- Main ---
def generate_user_video(user_data):
    user_name = user_data["name"]
    banks = user_data["banks"]
    user_dir = os.path.join(OUTPUT_BASE, user_name.lower().replace(" ", "_"))
    Path(user_dir).mkdir(parents=True, exist_ok=True)

    videos = []

    # --- Intro ---
    intro_html = os.path.join(user_dir, "intro.html")
    intro_img = os.path.join(user_dir, "intro.png")
    intro_audio = os.path.join(user_dir, "intro.mp3")
    intro_video = os.path.join(user_dir, "intro.mp4")

    render_html("intro_template.html", {"user_name": user_name}, intro_html)
    take_screenshot(intro_html, intro_img)
    generate_audio(f"Hi {user_name}, let's walk through your bank account insights.", intro_audio)
    make_video(intro_img, intro_audio, intro_video)
    videos.append(intro_video)

    # --- Per Bank ---
    for i, bank in enumerate(banks):
        html_path = os.path.join(user_dir, f"bank_{i}.html")
        img_path = os.path.join(user_dir, f"bank_{i}.png")
        audio_path = os.path.join(user_dir, f"bank_{i}.mp3")
        video_path = os.path.join(user_dir, f"bank_{i}.mp4")

        context = {
            "bank_name": bank["bank_name"],
            "high_spend": bank["high_spend"],
            "monthly_spend": bank["monthly_spend"],
            "category_breakdown": bank["category_breakdown"],
            "bank_logo": bank.get("bank_logo", ""),
            "background_image": Path("assets/background.jpg").resolve().as_uri()
        }
        render_html("bank_slide_template.html", context, html_path)
        take_screenshot(html_path, img_path)

        audio_text = (
            f"Here’s your {bank['bank_name']} account. "
            f"Your highest spend was ₹{bank['high_spend']['amount']} at {bank['high_spend']['merchant']} "
            f"on {bank['high_spend']['date']}. This month, you spent ₹{bank['monthly_spend']}, "
            f"mostly on {', '.join(bank['category_breakdown'].keys())}."
        )
        generate_audio(audio_text, audio_path)
        make_video(img_path, audio_path, video_path)
        videos.append(video_path)

    # --- Outro ---
    outro_html = os.path.join(user_dir, "outro.html")
    outro_img = os.path.join(user_dir, "outro.png")
    outro_audio = os.path.join(user_dir, "outro.mp3")
    outro_video = os.path.join(user_dir, "outro.mp4")

    render_html("outro_template.html", {}, outro_html)
    take_screenshot(outro_html, outro_img)
    generate_audio("Hope this was helpful. Use our app to discover more interesting features!", outro_audio)
    make_video(outro_img, outro_audio, outro_video)
    videos.append(outro_video)

    # --- Final Video ---
    final_video = os.path.join(user_dir, "final_video.mp4")
    concat_videos(videos, final_video)
    print(f"✅ Final video created: {final_video}")

# --- Entry Point ---
if __name__ == "__main__":
    with open("data.json") as f:
        user_data = json.load(f)
    generate_user_video(user_data)
