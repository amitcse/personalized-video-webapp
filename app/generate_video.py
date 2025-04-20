import os
import json
import shutil
import uuid
import asyncio
import subprocess
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from gtts import gTTS
from pydub.utils import mediainfo
from playwright.async_api import async_playwright

# Helper to render HTML file via URL and screenshot
# async def render_slide_file_to_image(html_path: Path, image_path: Path):
#     async with async_playwright() as p:
#         browser = await p.chromium.launch()
#         page = await browser.new_page(viewport={"width": 1280, "height": 720})
#         await page.goto(html_path.resolve().as_uri())
#         await page.wait_for_timeout(500)
#         await page.screenshot(path=str(image_path))
#         await browser.close()

async def render_slide_file_to_image(
    html_path: Path,
    image_path: Path,
    wait_selector: str = None,
    wait_ms: int = 500
):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width":1280,"height":720})
        await page.goto(html_path.resolve().as_uri())

        # If the caller asked us to wait for some selector (e.g. the chart), do so
        if wait_selector:
            await page.wait_for_selector(wait_selector, timeout=wait_ms * 3)

        # Always give a small pause to let CSS/backgrounds settle
        await page.wait_for_timeout(wait_ms)
        await page.screenshot(path=str(image_path))
        await browser.close()

async def render_slide_to_video(html_path: Path, output_video: Path, record_secs: float = 1.2):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        # Note: record_video_dir & record_video_size are the correct params
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=str(html_path.parent),
            record_video_size={"width": 1280, "height": 720},
        )
        page = await context.new_page()
        await page.goto(html_path.resolve().as_uri())
        # Wait for chart element and let animation play
        await page.wait_for_selector("canvas#spendChart")
        await page.wait_for_timeout(int(record_secs * 1000))
        await context.close()   # this flushes the recording
        await browser.close()

    # Playwright writes a .webm in the folder; find it and transcode
    webm_file = next(html_path.parent.glob("*.webm"))
    subprocess.run([
        "ffmpeg", "-y", "-i", str(webm_file),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(output_video)
    ], check=True)
    webm_file.unlink()


# Generate TTS audio
def generate_audio(text: str, audio_path: Path):
    tts = gTTS(text)
    tts.save(str(audio_path))

# Get duration in seconds of an audio file
def get_audio_duration(audio_path: Path) -> float:
    info = mediainfo(str(audio_path))
    return float(info['duration'])

async def generate_video_from_data(data: dict, output_video_path: str):
    # Setup user directory
    user_name = data["name"].replace(' ', '_').lower()
    user_dir = Path("output") / f"{user_name}_{uuid.uuid4().hex[:6]}"
    user_dir.mkdir(parents=True, exist_ok=True)

    # Copy background asset into user_dir for relative loading
    assets_bg = Path(__file__).parent.parent / "assets" / "background.jpg"
    shutil.copy(assets_bg, user_dir / "background.jpg")

    # Prepare templates
    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    env.filters['tojson'] = json.dumps

    slide_images = []
    slide_audios = []
    slide_segments = []  # list of video file paths or static slide videos
    intro_idx = 0
    # 1. Intro slide
    intro_html_content = env.get_template("intro.html").render(
        user_name=data["name"]
    )
    intro_html_file = user_dir / "slide_0_intro.html"
    intro_img = user_dir / "slide_0_intro.png"
    intro_audio = user_dir / "audio_0_intro.mp3"
    intro_video = user_dir / "video_0_intro.mp4"
    intro_final = user_dir / f"{intro_idx:03d}_intro.mp4"

    intro_html_file.write_text(intro_html_content, encoding="utf-8")
    await render_slide_file_to_image(intro_html_file, intro_img)
    generate_audio(f"Hi {data['name']}, let's take a look at your bank account summary.", intro_audio)

    # Create a silent video for intro_img matching audio duration
    dur = get_audio_duration(intro_audio)
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-i", str(intro_img), "-c:v", "libx264", "-t", str(dur), "-pix_fmt", "yuv420p", str(intro_video)
    ], check=True)

    # Merge audio
    subprocess.run([
        "ffmpeg", "-y", "-i", str(intro_video), "-i", str(intro_audio), "-c:v", "copy", "-c:a", "aac", str(intro_final)], check=True)
    slide_segments.append(intro_final)
    # slide_images.append(intro_img)
    # slide_audios.append(intro_audio)

    # 2. Bank slides
    for idx, bank in enumerate(data["banks"], start=1):
        html_file = user_dir / f"slide_{idx}.html"
        img_file = user_dir / f"slide_{idx}.png"
        anim_video = user_dir / f"slide_{idx}.mp4"
        audio_file = user_dir / f"audio_{idx}.mp3"
        final_seg = user_dir / f"{idx:03d}_bank_{idx}.mp4"
        # video_file = user_dir / f"slide_{idx}.mp4"
        
        # Render bank HTML with relative background.jpg
        html_content = env.get_template("bank_slide_template.html").render(
            bank_name=bank.get("bank_name"),
            bank_logo=bank.get("bank_logo", ""),
            high_spend=bank["high_spend"],
            monthly_spend=bank["monthly_spend"],
            category_breakdown=bank.get("category_breakdown", {}),
            background_image="background.jpg"
        )
        html_file.write_text(html_content, encoding="utf-8")

        # await render_slide_file_to_image(html_file, img_file, wait_selector="canvas#spendChart", wait_ms=1200)
        # Record animated chart video
        await render_slide_to_video(html_file, anim_video, record_secs=1.2)

        # Generate audio
        narration = (
            f"In your {bank['bank_name']} account, your highest spend was "
            f"{bank['high_spend']['amount']} rupees at {bank['high_spend']['merchant']}. "
            f"Your monthly spend was {bank['monthly_spend']} rupees."
        )
        generate_audio(narration, audio_file)

        # Merge video and audio
        subprocess.run([
            "ffmpeg", "-y", "-i", str(anim_video), "-i", str(audio_file),
            "-c:v", "copy", "-c:a", "aac", str(final_seg)
        ], check=True)

        slide_segments.append(final_seg)
        # slide_images.append(img_file)
        # slide_audios.append(audio_file)

    # 3. Outro slide
    outro_idx = len(data["banks"]) + 1
    outro_html_file = user_dir / f"slide_{outro_idx}_outro.html"
    outro_img = user_dir / f"slide_{outro_idx}_outro.png"
    outro_audio = user_dir / f"audio_{outro_idx}_outro.mp3"
    outro_video = user_dir / f"slide_{outro_idx}.mp4"
    outro_final = user_dir / f"{outro_idx:03d}_outro.mp4"

    outro_content = env.get_template("outro.html").render()
    outro_html_file.write_text(outro_content, encoding="utf-8")
    await render_slide_file_to_image(outro_html_file, outro_img)
    generate_audio(
        "Hope this was helpful. Explore more features in our app!",
        outro_audio
    )

    dur2 = get_audio_duration(outro_audio)
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-i", str(outro_img), "-c:v", "libx264", "-t", str(dur2), "-pix_fmt", "yuv420p", str(outro_video)
    ], check=True)
    subprocess.run([
        "ffmpeg", "-y", "-i", str(outro_video), "-i", str(outro_audio), "-c:v", "copy", "-c:a", "aac", str(outro_final)
    ], check=True)
    slide_segments.append(outro_final)
    # slide_images.append(outro_img)
    # slide_audios.append(outro_audio)

    # # 4. Create concat list with durations
    # inputs_txt = user_dir / "inputs.txt"
    # with open(inputs_txt, "w") as f:
    #     for img, audio in zip(slide_images, slide_audios):
    #         dur = get_audio_duration(audio)
    #         f.write(f"file '{img.resolve()}'\n")
    #         f.write(f"duration {dur}\n")
    #     # repeat last
    #     f.write(f"file '{slide_images[-1].resolve()}'\n")

    # # 5. Generate silent video segments
    # silent_video = user_dir / "video_silent.mp4"
    # subprocess.run([
    #     "ffmpeg", "-y",
    #     "-f", "concat", "-safe", "0",
    #     "-i", str(inputs_txt),
    #     "-vsync", "vfr", "-pix_fmt", "yuv420p",
    #     str(silent_video)
    # ], check=True)

    # # 6. Mix audio tracks
    # final_audio = user_dir / "video_audio.mp3"
    # inputs = []
    # for audio in slide_audios:
    #     inputs.extend(["-i", str(audio)])
    # labels = ''.join(f"[{i}:a]" for i in range(len(slide_audios)))
    # filter_c = f"{labels}concat=n={len(slide_audios)}:v=0:a=1[out]"
    # cmd_audio = ["ffmpeg", "-y", *inputs, "-filter_complex", filter_c, "-map", "[out]", str(final_audio)]
    # subprocess.run(cmd_audio, shell=False, check=True)

    # # 7. Combine video and audio
    # subprocess.run([
    #     "ffmpeg", "-y",
    #     "-i", str(silent_video),
    #     "-i", str(final_audio),
    #     "-c:v", "copy", "-c:a", "aac",
    #     output_video_path
    # ], check=True)

    # print(f"✅ Video ready at {output_video_path}")

    # 4. Concatenate all segments
    concat_list = user_dir / "concat_list.txt"
    with open(concat_list, "w") as f:
        for seg in slide_segments:
            f.write(f"file '{seg.resolve()}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list), "-c", "copy", output_video_path
    ], check=True)

    print(f"✅ Video ready at {output_video_path}")

# If used as a script
if __name__ == "__main__":
    with open("data.json") as f:
        user_data = json.load(f)
    asyncio.run(generate_video_from_data(user_data, "output/final_video.mp4"))
