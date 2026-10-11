"""Create original, lightweight 2D cartoon scenes with Pillow and MoviePy."""
import math
import os
import random
import textwrap

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    concatenate_videoclips,
)

import config

OUTLINE = (64, 48, 48, 255)
MOODS = {"happy", "worried", "surprised", "curious", "sad", "excited"}
FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:\\Windows\\Fonts\\arialbd.ttf",
]


def _font(size: int) -> ImageFont.ImageFont:
    for path in FONT_PATHS:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _draw_background(setting: str, size: tuple[int, int], seed: int) -> Image.Image:
    width, height = size
    key = setting.lower()
    if any(word in key for word in ("space", "moon", "star", "planet")):
        sky, ground = (33, 38, 91), (58, 53, 119)
    elif any(word in key for word in ("beach", "ocean", "sea", "island")):
        sky, ground = (115, 207, 244), (245, 207, 117)
    elif any(word in key for word in ("city", "town", "street", "school")):
        sky, ground = (145, 204, 238), (114, 184, 103)
    elif any(word in key for word in ("cave", "mountain", "underground")):
        sky, ground = (102, 116, 145), (100, 138, 113)
    else:
        sky, ground = (139, 213, 250), (112, 190, 105)

    image = Image.new("RGBA", size, sky + (255,))
    draw = ImageDraw.Draw(image, "RGBA")
    rng = random.Random(seed)

    if sky == (33, 38, 91):
        for _ in range(55):
            x, y = rng.randrange(width), rng.randrange(int(height * 0.68))
            radius = rng.randint(2, max(3, width // 260))
            draw.ellipse((x, y, x + radius, y + radius), fill=(255, 255, 220, 230))
        draw.ellipse((int(width * 0.72), int(height * 0.13),
                      int(width * 0.84), int(height * 0.24)),
                     fill=(255, 237, 164, 255))
    else:
        draw.ellipse((int(width * 0.76), int(height * 0.09),
                      int(width * 0.88), int(height * 0.21)),
                     fill=(255, 222, 105, 255))
        for cloud_x, cloud_y in ((0.12, 0.2), (0.47, 0.12), (0.73, 0.29)):
            x, y = int(width * cloud_x), int(height * cloud_y)
            r = max(15, width // 22)
            draw.ellipse((x, y, x + r * 2, y + r), fill=(255, 255, 255, 225))
            draw.ellipse((x + r // 2, y - r // 2, x + r * 2, y + r // 2),
                         fill=(255, 255, 255, 225))
            draw.ellipse((x + r, y, x + r * 3, y + r), fill=(255, 255, 255, 225))

    horizon = int(height * 0.68)
    draw.rectangle((0, horizon, width, height), fill=ground + (255,))
    draw.ellipse((-int(width * 0.18), int(height * 0.57),
                  int(width * 0.55), int(height * 0.79)),
                 fill=tuple(max(0, channel - 17) for channel in ground) + (255,))
    draw.ellipse((int(width * 0.4), int(height * 0.6),
                  int(width * 1.15), int(height * 0.83)),
                 fill=tuple(min(255, channel + 12) for channel in ground) + (255,))

    if "forest" in key or sky == (139, 213, 250):
        for x in (0.05, 0.91):
            trunk_x = int(width * x)
            trunk_w = max(12, width // 48)
            draw.rectangle((trunk_x, int(height * 0.32), trunk_x + trunk_w, horizon),
                           fill=(117, 76, 53, 255))
            for offset in (-0.035, 0, 0.035):
                cx = int(width * (x + offset))
                cy = int(height * 0.33)
                radius = int(width * 0.075)
                draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius),
                             fill=(53, 151, 83, 255))

    return image


def _fox_sprite(mood: str, size: tuple[int, int]) -> Image.Image:
    image = Image.new("RGBA", (280, 340), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.polygon([(57, 130), (22, 42), (104, 78)], fill=(239, 132, 57, 255), outline=OUTLINE)
    draw.polygon([(174, 78), (253, 40), (222, 145)], fill=(239, 132, 57, 255), outline=OUTLINE)
    draw.polygon([(56, 93), (43, 61), (81, 82)], fill=(255, 195, 158, 255))
    draw.polygon([(191, 82), (229, 60), (211, 107)], fill=(255, 195, 158, 255))
    draw.ellipse((45, 78, 235, 260), fill=(239, 132, 57, 255), outline=OUTLINE, width=6)
    draw.ellipse((58, 221, 223, 349), fill=(239, 132, 57, 255), outline=OUTLINE, width=6)
    draw.ellipse((86, 151, 198, 240), fill=(255, 235, 207, 255))
    eye_y = 145 if mood == "surprised" else 151
    draw.ellipse((91, eye_y, 110, eye_y + 27), fill=OUTLINE)
    draw.ellipse((169, eye_y, 188, eye_y + 27), fill=OUTLINE)
    draw.ellipse((99, eye_y + 5, 105, eye_y + 12), fill=(255, 255, 255, 255))
    draw.ellipse((177, eye_y + 5, 183, eye_y + 12), fill=(255, 255, 255, 255))
    draw.ellipse((128, 183, 155, 203), fill=(73, 53, 55, 255))
    if mood in {"happy", "excited"}:
        draw.arc((119, 188, 164, 220), start=0, end=180, fill=OUTLINE, width=5)
    elif mood == "sad":
        draw.arc((119, 201, 164, 228), start=180, end=350, fill=OUTLINE, width=5)
    else:
        draw.line((140, 199, 140, 212), fill=OUTLINE, width=4)
    draw.ellipse((47, 268, 111, 327), fill=(255, 235, 207, 255), outline=OUTLINE, width=4)
    draw.ellipse((167, 268, 231, 327), fill=(255, 235, 207, 255), outline=OUTLINE, width=4)
    return image.resize(size, Image.Resampling.LANCZOS)


def _turtle_sprite(mood: str, size: tuple[int, int]) -> Image.Image:
    image = Image.new("RGBA", (280, 340), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((40, 142, 241, 287), fill=(38, 142, 131, 255), outline=OUTLINE, width=6)
    draw.ellipse((73, 117, 212, 252), fill=(80, 173, 113, 255), outline=OUTLINE, width=6)
    draw.arc((91, 137, 194, 235), start=185, end=350, fill=(30, 111, 94, 255), width=5)
    draw.ellipse((179, 67, 267, 164), fill=(100, 205, 155, 255), outline=OUTLINE, width=6)
    for x, y in ((61, 259), (185, 255)):
        draw.ellipse((x, y, x + 58, y + 73), fill=(74, 182, 139, 255), outline=OUTLINE, width=5)
    eye_y = 103 if mood == "surprised" else 108
    draw.ellipse((211, eye_y, 224, eye_y + 21), fill=OUTLINE)
    draw.ellipse((244, eye_y, 257, eye_y + 21), fill=OUTLINE)
    draw.ellipse((214, eye_y + 3, 218, eye_y + 8), fill=(255, 255, 255, 255))
    draw.ellipse((247, eye_y + 3, 251, eye_y + 8), fill=(255, 255, 255, 255))
    if mood in {"happy", "excited"}:
        draw.arc((218, 122, 251, 146), start=5, end=175, fill=OUTLINE, width=4)
    elif mood == "sad":
        draw.arc((218, 132, 251, 153), start=190, end=345, fill=OUTLINE, width=4)
    else:
        draw.line((226, 135, 244, 135), fill=OUTLINE, width=4)
    return image.resize(size, Image.Resampling.LANCZOS)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def _caption_card(image: Image.Image, text: str, hook: str = "") -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    width, height = image.size
    if hook:
        hook_font = _font(max(20, width // 25))
        hook_lines = _wrap(draw, hook.upper(), hook_font, int(width * 0.82))[:2]
        top = int(height * 0.14)
        card_height = len(hook_lines) * int(hook_font.size * 1.25) + 26
        draw.rounded_rectangle((int(width * 0.06), top, int(width * 0.94), top + card_height),
                               radius=18, fill=(26, 33, 54, 210))
        for index, line in enumerate(hook_lines):
            tw = draw.textlength(line, font=hook_font)
            draw.text(((width - tw) / 2, top + 12 + index * int(hook_font.size * 1.25)),
                      line, font=hook_font, fill=(255, 255, 255, 255))

    caption_font = _font(max(18, width // 36))
    lines = _wrap(draw, " ".join(text.split()[:12]), caption_font, int(width * 0.84))[:3]
    line_height = int(caption_font.size * 1.25)
    card_height = line_height * len(lines) + 24
    bottom = int(height * 0.93)
    top = bottom - card_height
    draw.rounded_rectangle((int(width * 0.05), top, int(width * 0.95), bottom),
                           radius=18, fill=(22, 30, 45, 220))
    for index, line in enumerate(lines):
        tw = draw.textlength(line, font=caption_font)
        draw.text(((width - tw) / 2, top + 10 + index * line_height),
                  line, font=caption_font, fill=(255, 255, 255, 255))
    brand_font = _font(max(14, width // 54))
    brand = config.CHANNEL_NAME
    brand_width = int(draw.textlength(brand, font=brand_font) + 30)
    draw.rounded_rectangle((int(width * 0.04), int(height * 0.025),
                            int(width * 0.04) + brand_width, int(height * 0.025) + brand_font.size + 18),
                           radius=12, fill=(26, 33, 54, 205))
    draw.text((int(width * 0.04) + 15, int(height * 0.025) + 8),
              brand, font=brand_font, fill=(255, 255, 255, 255))


def _scene_clip(scene: dict, index: int, duration: float, size: tuple[int, int],
                hook: str = None):
    width, height = size
    mood = scene.get("mood", "curious").lower()
    if mood not in MOODS:
        mood = "curious"
    background = _draw_background(scene.get("setting", "forest"), size, index)
    draw = ImageDraw.Draw(background, "RGBA")
    action = scene.get("action", "")
    prop_font = _font(max(16, width // 32))
    prop_label = textwrap.shorten(action.strip(), width=32, placeholder="...")
    if prop_label:
        label_width = min(int(width * 0.68), int(draw.textlength(prop_label, font=prop_font) + 42))
        x0 = (width - label_width) // 2
        y0 = int(height * 0.38)
        draw.rounded_rectangle((x0, y0, x0 + label_width, y0 + int(height * 0.08)),
                               radius=18, fill=(255, 249, 217, 235),
                               outline=(95, 77, 61, 255), width=max(2, width // 360))
        draw.text((x0 + 20, y0 + int(height * 0.018)), prop_label,
                  font=prop_font, fill=(61, 57, 59, 255))
    _caption_card(background, scene["narration"], hook or "")

    is_vertical = height > width
    actor_height = int(height * (0.26 if is_vertical else 0.30))
    actor_width = int(actor_height * 0.82)
    left_center = 0.27 if is_vertical else 0.26
    right_center = 0.73 if is_vertical else 0.74
    actor_y = int(height * (0.56 if is_vertical else 0.49))
    actors = [
        (_fox_sprite(mood, (actor_width, actor_height)), left_center, 0.0),
        (_turtle_sprite(mood, (actor_width, actor_height)), right_center, 1.3),
    ]
    layers = [ImageClip(np.array(background)).with_duration(duration)]
    for sprite, x_ratio, phase in actors:
        x = int(width * x_ratio) - actor_width // 2
        y = actor_y
        layers.append(
            ImageClip(np.array(sprite))
            .with_duration(duration)
            .with_position(
                lambda t, x=x, y=y, phase=phase: (
                    x + int(4 * math.sin(t * 2.4 + phase)),
                    y + int(5 * math.sin(t * 4 + phase)),
                )
            )
        )
    return CompositeVideoClip(layers, size=size).with_duration(duration)


def _write_srt(scenes: list[dict], durations: list[float], path: str) -> None:
    def timestamp(seconds: float) -> str:
        milliseconds = int(round(seconds * 1000))
        hours, remainder = divmod(milliseconds, 3_600_000)
        minutes, remainder = divmod(remainder, 60_000)
        secs, millis = divmod(remainder, 1000)
        return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

    elapsed = 0.0
    with open(path, "w", encoding="utf-8") as subtitle_file:
        for index, (scene, duration) in enumerate(zip(scenes, durations), 1):
            subtitle_file.write(
                f"{index}\n{timestamp(elapsed)} --> {timestamp(elapsed + duration)}\n"
                f"{scene['narration'].strip()}\n\n"
            )
            elapsed += duration


def render_video(scenes: list[dict], audio_path: str, title: str, kind: str,
                 out_path: str, hook_text: str = "") -> str:
    if not scenes:
        raise ValueError("At least one cartoon scene is required")
    size = config.LONG_RESOLUTION if kind == "long" else config.SHORT_RESOLUTION
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    voice = AudioFileClip(audio_path)
    total_duration = voice.duration
    weights = [max(1, len(scene["narration"].split())) for scene in scenes]
    weight_total = sum(weights)
    durations = [total_duration * weight / weight_total for weight in weights]
    durations[-1] += total_duration - sum(durations)

    clips = []
    final = None
    try:
        for index, (scene, duration) in enumerate(zip(scenes, durations)):
            clips.append(_scene_clip(
                scene, index, duration, size, hook_text if index == 0 else None
            ))
        final = concatenate_videoclips(clips, method="compose").with_audio(voice)
        final.write_videofile(
            out_path, fps=config.FPS, codec="libx264", audio_codec="aac",
            preset="ultrafast", threads=2, logger=None,
        )
        _write_srt(scenes, durations, os.path.splitext(out_path)[0] + ".srt")
        return out_path
    finally:
        if final is not None:
            final.close()
        for clip in clips:
            clip.close()
        voice.close()
