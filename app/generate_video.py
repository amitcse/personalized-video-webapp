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

async def render_slide_to_video(html_path: Path, output_video: Path, 
                                wait_selector: str = None, wait_ms: int = 500, 
                                record_secs: float = 1.2):
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
        if wait_selector:
            # Wait for chart element and let animation play
            await page.wait_for_selector(wait_selector, timeout=wait_ms)
        
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
    tts = gTTS(text, lang='en', tld='co.in')
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

    # Copy assets into user_dir for relative loading
    assets_bg = Path(__file__).parent.parent / "assets" / "character.png"
    shutil.copy(assets_bg, user_dir / "character.png")
    assets_bg = Path(__file__).parent.parent / "assets" / "cards_clock.png"
    shutil.copy(assets_bg, user_dir / "cards_clock.png")
    assets_bg = Path(__file__).parent.parent / "assets" / "money_check_calendar.png"
    shutil.copy(assets_bg, user_dir / "money_check_calendar.png")
    assets_bg = Path(__file__).parent.parent / "assets" / "moneybag_clock.png"
    shutil.copy(assets_bg, user_dir / "moneybag_clock.png")

    # Prepare templates
    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    env.filters['tojson'] = json.dumps

    slide_images = []
    slide_audios = []
    slide_segments = []  # list of video file paths or static slide videos

    # 1. Slide 1
    slide_1_html_content = env.get_template("slide_1.html").render(user_name=data["name"], credit_score=data["credit_score"])
    slide_1_html_file = user_dir / "slide_1.html"
    slide_1_img = user_dir / "slide_1.png"
    slide_1_audio = user_dir / "audio_1.mp3"
    slide_1_video = user_dir / "video_1.mp4"
    slide_1_video_final = user_dir / "video_1_final.mp4"

    slide_1_html_file.write_text(slide_1_html_content, encoding="utf-8")
    await render_slide_file_to_image(slide_1_html_file, slide_1_img)
    generate_audio(f"Hi {data['name']}, Your credit score is {data['credit_score']}.\n"
                   f" This is a good credit score. I have analysed your credit report and I have few suggestions for you to improve your credit score.\n"
                   f" Watch this video till the end and follow the steps diligently.", slide_1_audio)

    # Create a silent video for intro_img matching audio duration
    dur = get_audio_duration(slide_1_audio)
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-i", str(slide_1_img), "-c:v", "libx264", "-t", str(dur), "-pix_fmt", "yuv420p", str(slide_1_video)
    ], check=True)

    # Merge audio
    subprocess.run([
        "ffmpeg", "-y", "-i", str(slide_1_video), "-i", str(slide_1_audio), "-c:v", "copy", "-c:a", "aac", str(slide_1_video_final)], check=True)
    slide_segments.append(slide_1_video_final)


    # 2. Slide 2 - Active Accounts
    slide_2_html_content = env.get_template("slide_2.html").render(accounts=data["accounts_active"], more_count=data["more_count_active"])
    slide_2_html_file = user_dir / "slide_2.html"
    slide_2_img = user_dir / "slide_2.png"
    slide_2_audio = user_dir / "audio_2.mp3"
    slide_2_video = user_dir / "video_2.mp4"
    slide_2_video_final = user_dir / "video_2_final.mp4"

    slide_2_html_file.write_text(slide_2_html_content, encoding="utf-8")
    await render_slide_file_to_image(slide_2_html_file, slide_2_img)
    generate_audio(f"I can check that you currently have {data['total_count_active']} active accounts in your profile.\n"
                   f" There are no missed payments recorded on these accounts yet. This is a great thing. Continue this and ensure that no E.M.I. payments gets missed.\n"
                   f" Missing payments leads to lowering of credit score by 50 to 100 points. This will badly affect your good payment history. Avoid this.\n"
                   f"Timely payments is a financially sound behaviour and leads to good credit score.\n", slide_2_audio)
    
    # Create a silent video for intro_img matching audio duration
    dur = get_audio_duration(slide_2_audio)
    subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", str(slide_2_img), "-c:v", "libx264", "-t", str(dur), "-pix_fmt", "yuv420p", str(slide_2_video)], check=True)

    # Merge audio
    subprocess.run(["ffmpeg", "-y", "-i", str(slide_2_video), "-i", str(slide_2_audio), "-c:v", "copy", "-c:a", "aac", str(slide_2_video_final)], check=True)
    slide_segments.append(slide_2_video_final)


    # 3. Slide 3 - Closed Accounts
    slide_3_html_content = env.get_template("slide_3.html").render(accounts=data["accounts_closed"], more_count=data["more_count_closed"])
    slide_3_html_file = user_dir / "slide_3.html"
    slide_3_img = user_dir / "slide_3.png"
    slide_3_audio = user_dir / "audio_3.mp3"
    slide_3_video = user_dir / "video_3.mp4"
    slide_3_video_final = user_dir / "video_3_final.mp4"

    slide_3_html_file.write_text(slide_3_html_content, encoding="utf-8")
    await render_slide_file_to_image(slide_3_html_file, slide_3_img)
    generate_audio(f"I can check that you currently have {data['total_count_closed']} closed accounts in your profile.\n"
                   f" There are no missed payments recorded on these accounts yet. This is a great thing.\n"
                   f"Timely payments is a financially sound behaviour and leads to good credit score.\n", slide_3_audio)
    
    # Create a silent video for intro_img matching audio duration
    dur = get_audio_duration(slide_3_audio)
    subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", str(slide_3_img), "-c:v", "libx264", "-t", str(dur), "-pix_fmt", "yuv420p", str(slide_3_video)], check=True)

    # Merge audio
    subprocess.run(["ffmpeg", "-y", "-i", str(slide_3_video), "-i", str(slide_3_audio), "-c:v", "copy", "-c:a", "aac", str(slide_3_video_final)], check=True)
    slide_segments.append(slide_3_video_final)


    # 4. Slide 4 - Congratulations
    slide_4_html_content = env.get_template("slide_4.html").render(accounts=data["accounts_closed"], more_count=data["more_count_closed"])
    slide_4_html_file = user_dir / "slide_4.html"
    slide_4_img = user_dir / "slide_4.png"
    slide_4_audio = user_dir / "audio_4.mp3"
    slide_4_video = user_dir / "video_4.mp4"
    slide_4_video_final = user_dir / "video_4_final.mp4"

    slide_4_html_file.write_text(slide_4_html_content, encoding="utf-8")
    await render_slide_file_to_image(slide_4_html_file, slide_4_img)
    generate_audio(f"I wanted to take a moment to congratulate you on your stellar credit history.\n", slide_4_audio)
    
    # Create a silent video for intro_img matching audio duration
    dur = get_audio_duration(slide_4_audio)
    subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", str(slide_4_img), "-c:v", "libx264", "-t", str(dur), "-pix_fmt", "yuv420p", str(slide_4_video)], check=True)

    # Merge audio
    subprocess.run(["ffmpeg", "-y", "-i", str(slide_4_video), "-i", str(slide_4_audio), "-c:v", "copy", "-c:a", "aac", str(slide_4_video_final)], check=True)
    slide_segments.append(slide_4_video_final)


    # 5. Slide 5 - On time payments
    slide_5_html_content = env.get_template("slide_5.html").render()
    slide_5_html_file = user_dir / "slide_5.html"
    # slide_5_img = user_dir / "slide_5.png"
    slide_5_audio = user_dir / "audio_5.mp3"
    slide_5_video = user_dir / "video_5.mp4"
    slide_5_video_final = user_dir / "video_5_final.mp4"

    slide_5_html_file.write_text(slide_5_html_content, encoding="utf-8")
    generate_audio(f"Its clear that you have been diligently making payments on time.\n" 
                   f" And your account's long history reflects your commitments to financial responsibility.\n", slide_5_audio)
    
    # Create a silent video for intro_img matching audio duration
    dur = get_audio_duration(slide_5_audio)
    await render_slide_to_video(slide_5_html_file, slide_5_video, record_secs=dur)

    # Merge audio
    subprocess.run(["ffmpeg", "-y", "-i", str(slide_5_video), "-i", str(slide_5_audio), "-c:v", "copy", "-c:a", "aac", str(slide_5_video_final)], check=True)
    slide_segments.append(slide_5_video_final)


    # # 2. Bank slides
    # for idx, bank in enumerate(data["banks"], start=1):
    #     html_file = user_dir / f"slide_{idx}.html"
    #     img_file = user_dir / f"slide_{idx}.png"
    #     anim_video = user_dir / f"slide_{idx}.mp4"
    #     audio_file = user_dir / f"audio_{idx}.mp3"
    #     final_seg = user_dir / f"{idx:03d}_bank_{idx}.mp4"
    #     # video_file = user_dir / f"slide_{idx}.mp4"
        
    #     # Render bank HTML with relative background.jpg
    #     html_content = env.get_template("bank_slide_template.html").render(
    #         bank_name=bank.get("bank_name"),
    #         bank_logo=bank.get("bank_logo", ""),
    #         high_spend=bank["high_spend"],
    #         monthly_spend=bank["monthly_spend"],
    #         category_breakdown=bank.get("category_breakdown", {}),
    #         background_image="background.jpg"
    #     )
    #     html_file.write_text(html_content, encoding="utf-8")

    #     # await render_slide_file_to_image(html_file, img_file, wait_selector="canvas#spendChart", wait_ms=1200)
    #     # Record animated chart video
    #     await render_slide_to_video(html_file, anim_video, record_secs=1.2)

    #     # Generate audio
    #     narration = (
    #         f"In your {bank['bank_name']} account, your highest spend was "
    #         f"{bank['high_spend']['amount']} rupees at {bank['high_spend']['merchant']}. "
    #         f"Your monthly spend was {bank['monthly_spend']} rupees."
    #     )
    #     generate_audio(narration, audio_file)

    #     # Merge video and audio
    #     subprocess.run([
    #         "ffmpeg", "-y", "-i", str(anim_video), "-i", str(audio_file),
    #         "-c:v", "copy", "-c:a", "aac", str(final_seg)
    #     ], check=True)

    #     slide_segments.append(final_seg)
    #     # slide_images.append(img_file)
    #     # slide_audios.append(audio_file)

    # # 3. Outro slide
    # outro_idx = len(data["banks"]) + 1
    # outro_html_file = user_dir / f"slide_{outro_idx}_outro.html"
    # outro_img = user_dir / f"slide_{outro_idx}_outro.png"
    # outro_audio = user_dir / f"audio_{outro_idx}_outro.mp3"
    # outro_video = user_dir / f"slide_{outro_idx}.mp4"
    # outro_final = user_dir / f"{outro_idx:03d}_outro.mp4"

    # outro_content = env.get_template("outro.html").render()
    # outro_html_file.write_text(outro_content, encoding="utf-8")
    # await render_slide_file_to_image(outro_html_file, outro_img)
    # generate_audio(
    #     "Hope this was helpful. Explore more features in our app!",
    #     outro_audio
    # )

    # dur2 = get_audio_duration(outro_audio)
    # subprocess.run([
    #     "ffmpeg", "-y", "-loop", "1", "-i", str(outro_img), "-c:v", "libx264", "-t", str(dur2), "-pix_fmt", "yuv420p", str(outro_video)
    # ], check=True)
    # subprocess.run([
    #     "ffmpeg", "-y", "-i", str(outro_video), "-i", str(outro_audio), "-c:v", "copy", "-c:a", "aac", str(outro_final)
    # ], check=True)
    # slide_segments.append(outro_final)
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
