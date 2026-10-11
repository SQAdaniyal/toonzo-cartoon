"""Generate original ToonZo story ideas and scene-by-scene cartoon scripts."""
import json
import re
import time
import requests
import config

MODELS = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.5-flash-lite"]
BASE = "https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent"


def _ask_gemini(prompt: str) -> str:
    for model in MODELS:
        for attempt in range(4):
            try:
                r = requests.post(
                    BASE.format(m=model),
                    params={"key": config.GEMINI_API_KEY},
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"temperature": 0.92},
                    },
                    timeout=90,
                )
                if r.status_code == 200:
                    return r.json()["candidates"][0]["content"]["parts"][0]["text"]
                print(f"  [{model}] HTTP {r.status_code}: {r.text[:200]}", flush=True)
                if r.status_code in (429, 503):
                    time.sleep(20 * (attempt + 1))
                    continue
                break
            except Exception as e:
                print(f"  [{model}] error (attempt {attempt+1}): {e}", flush=True)
                time.sleep(10)
        print(f"  [{model}] fail — next model...", flush=True)
    raise RuntimeError("Gemini API failed (all models tried)")


def _parse_json(text: str):
    text = re.sub(r"```json|```", "", text).strip()
    dec = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch in "[{":
            try:
                obj, _ = dec.raw_decode(text[i:])
                return obj
            except json.JSONDecodeError:
                continue
    raise ValueError("No valid JSON: " + text[:120])


def generate_topics(count: int, kind: str, used: list, performance: dict = None) -> list:
    style = (
        "3-5 minute cartoon episode"
        if kind == "long"
        else "under-60-second cartoon Short"
    )
    prompt = f"""You are the story editor for ToonZo Official, an original English-language cartoon channel.

Generate exactly {count} fresh, specific story ideas for a {style}. Privately compare candidate ideas, then return only the strongest ones.

Use the recurring original characters Milo the curious orange fox and Tilly the kind teal turtle.
Create imaginative, warm, funny adventures with a clear problem, teamwork, and a satisfying ending.

RULES:
- Make every idea original, child-safe, easy to understand, and straightforward to show in a simple 2D cartoon
- Do not use existing copyrighted characters, franchises, catchphrases, or storylines
- Give each story a distinct premise; do not repeat these previous topics: {json.dumps(used[-150:], ensure_ascii=False)}
- Use this performance signal only as a directional guide; create fresh ideas:
{json.dumps((performance or {}).get(kind, {}), ensure_ascii=False)}
- Short ideas need one simple conflict and a quick payoff; long ideas need a coherent beginning, middle, and end

Respond ONLY with a JSON array of strings. No other text."""
    topics = _parse_json(_ask_gemini(prompt))
    if not isinstance(topics, list) or not all(
        isinstance(topic, str) and topic.strip() for topic in topics
    ):
        raise ValueError("Gemini must return a JSON array of non-empty story ideas")
    return [topic.strip() for topic in topics[:count]]


def generate_script(topic: str, kind: str, used_titles: list = None) -> dict:
    if kind == "short":
        structure = """
SHORT CARTOON RULES:
- Tell one complete mini-story with a clear opening, small problem, teamwork, and funny or warm payoff
- Use short, natural spoken English and simple child-safe language
- Keep narration under 80 words; no greeting, filler, or subscribe prompt"""
    else:
        structure = f"""
LONG CARTOON RULES:
- Tell a complete 3-5 minute adventure with a strong opening, escalating problem, teamwork, and satisfying ending
- Use simple, natural spoken English, expressive dialogue, and clear scene transitions
- Aim for about {config.LONG_TARGET_WORDS} narration words; do not pad or repeat
- End with a brief, natural subscribe prompt"""

    scene_count = "4 to 6" if kind == "short" else "8 to 12"
    prompt = f"""Write an original ToonZo Official cartoon package for this story idea: "{topic}"

{structure}
Previously used video titles (do not repeat or closely rephrase): {json.dumps((used_titles or [])[-100:], ensure_ascii=False)}
For a Short, keep the complete narration under {config.SHORT_TARGET_WORDS} words.

DELIVER a JSON object with these exact keys:

"hook_text": A short, child-safe opening hook of at most 8 words, in ALL CAPS.

"scenes": An array of {scene_count} objects. Each object has:
  "narration": the exact spoken narration for this scene,
  "setting": a concise visual setting (for example forest, beach, city, cave, or space),
  "action": a simple visual action or prop for the scene,
  "mood": one of happy, worried, surprised, curious, sad, or excited.
"script": The complete narration in scene order, joined into one natural voiceover. It must exactly match the scene narration.

"title": A compelling, specific, family-friendly title under 70 characters. Use normal title case, not ALL CAPS. Build curiosity around this story's unique problem or payoff; avoid generic/repeated templates such as "The Magic Adventure" and do not put the channel name in the title. {"End with ' #Shorts'" if kind == 'short' else ""}

"description": A short, accurate summary of this original cartoon, followed by relevant hashtags including #ToonZoOfficial and #Cartoon. Include #Shorts for a Short.

"tags": Up to 15 relevant English tags.
QUALITY: Keep the story original and suitable for a general family audience. Do not mention or imitate existing copyrighted characters or franchises. Do not include unsafe instructions, frightening details, or misleading metadata.

Respond ONLY with the JSON object. No other text."""

    data = _parse_json(_ask_gemini(prompt))
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("Generated cartoon package must contain a non-empty scenes array")
    min_scenes, max_scenes = (4, 6) if kind == "short" else (8, 12)
    if not min_scenes <= len(scenes) <= max_scenes:
        raise ValueError(
            f"Generated {kind} must have {min_scenes}-{max_scenes} scenes; got {len(scenes)}"
        )
    normalized_scenes = []
    for index, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict):
            raise ValueError(f"Generated scene {index} must be a JSON object")
        narration = scene.get("narration")
        if not isinstance(narration, str) or not narration.strip():
            raise ValueError(f"Generated scene {index} has no narration")
        normalized_scenes.append({
            "narration": narration.strip(),
            "setting": str(scene.get("setting", "forest")),
            "action": str(scene.get("action", "")),
            "mood": str(scene.get("mood", "curious")).lower(),
        })
    data["scenes"] = normalized_scenes
    scene_script = " ".join(scene["narration"] for scene in normalized_scenes)
    provided_script = data.get("script")
    if not isinstance(provided_script, str) or provided_script.strip() != scene_script:
        data["script"] = scene_script
    if kind == "short" and len(scene_script.split()) > config.SHORT_TARGET_WORDS:
        raise ValueError(
            f"Generated Short script exceeds {config.SHORT_TARGET_WORDS} words"
        )
    data.setdefault("title", topic[:90])
    data.setdefault("description", "An original ToonZo Official cartoon adventure. #ToonZoOfficial #Cartoon")
    data.setdefault("tags", ["ToonZo Official", "cartoon", "animation"])
    data.setdefault("hook_text", topic.upper()[:40])
    if not isinstance(data["title"], str) or not data["title"].strip():
        raise ValueError("Generated cartoon package must contain a non-empty title")
    data["title"] = data["title"].strip()
    if len(data["title"]) > 100:
        raise ValueError("Generated title exceeds YouTube's 100-character title limit")
    if not isinstance(data.get("description"), str):
        raise ValueError("Generated package description must be text")
    if not isinstance(data.get("tags"), list) or not all(
        isinstance(tag, str) for tag in data["tags"]
    ):
        raise ValueError("Generated package tags must be an array of strings")
    data["topic"] = topic
    data["kind"] = kind
    return data
