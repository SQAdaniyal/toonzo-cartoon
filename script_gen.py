"""Generate original ToonZo story ideas and scene-by-scene cartoon scripts."""
import json
import random
import re
import time
import requests
import config

MODELS = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-3.5-flash-lite"]
BASE = "https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent"
_QUOTA_BLOCKED_MODELS = set()
_UNAVAILABLE_MODELS = set()

_LOCAL_OBJECTS = (
    "a paper kite",
    "a tiny toy boat",
    "a bright red apple",
    "a shiny soap bubble",
    "a little blue backpack",
    "a wooden music box",
    "a striped garden umbrella",
    "a round pumpkin",
    "a colorful pinwheel",
    "a small basket of berries",
    "a friendly ladybug",
    "a soft yellow scarf",
)
_LOCAL_EVENTS = (
    "has drifted into a patch of tall grass",
    "keeps rolling toward a shallow stream",
    "is bobbing gently across a puddle",
    "has become tangled in a low branch",
    "is making a funny echo in the meadow",
    "is hiding beneath a pile of autumn leaves",
    "keeps spinning whenever the breeze returns",
    "has landed beside a sleepy field mouse",
    "is surrounded by a trail of sparkling dew",
    "is wobbling along a quiet garden path",
    "has slipped just out of easy reach",
    "is blocking the path to a patch of flowers",
)
_LOCAL_PLACES = (
    "the sunny meadow",
    "the little garden",
    "the clover field",
    "the edge of the pond",
    "the woodland path",
    "the hilltop",
)


def _ask_gemini(prompt: str, starting_model: int = 0) -> str:
    model_order = MODELS[starting_model:] + MODELS[:starting_model]
    for model in model_order:
        if model in _QUOTA_BLOCKED_MODELS or model in _UNAVAILABLE_MODELS:
            continue
        for attempt in range(3):
            try:
                r = requests.post(
                    BASE.format(m=model),
                    params={"key": config.GEMINI_API_KEY},
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "temperature": 0.8,
                            "responseMimeType": "application/json",
                            "maxOutputTokens": 8192,
                        },
                    },
                    timeout=90,
                )
                if r.status_code == 200:
                    payload = r.json()
                    candidates = payload.get("candidates", [])
                    if not candidates:
                        raise ValueError("Gemini returned no candidates")
                    candidate = candidates[0]
                    finish_reason = candidate.get("finishReason")
                    if finish_reason == "MAX_TOKENS":
                        raise ValueError(
                            f"Gemini response was truncated by the token limit for {model}"
                        )
                    parts = candidate.get("content", {}).get("parts", [])
                    text = "".join(
                        part.get("text", "") for part in parts if "text" in part
                    )
                    if not text:
                        raise ValueError(
                            f"Gemini returned no text (finish reason: {finish_reason})"
                        )
                    return text
                response_text = r.text[:200]
                quota_exhausted = (
                    r.status_code == 429
                    and "exceeded your current quota" in response_text.lower()
                )
                print(f"  [{model}] HTTP {r.status_code}: {response_text}", flush=True)
                if quota_exhausted:
                    _QUOTA_BLOCKED_MODELS.add(model)
                    _UNAVAILABLE_MODELS.add(model)
                    break
                if r.status_code in (429, 500, 502, 503, 504) and attempt < 2:
                    time.sleep(min(15 * (2**attempt), 60) + random.uniform(0, 3))
                    continue
                break
            except (requests.RequestException, ValueError, KeyError) as e:
                print(f"  [{model}] error (attempt {attempt+1}): {e}", flush=True)
                if attempt < 2:
                    time.sleep(min(15 * (2**attempt), 60) + random.uniform(0, 3))
        _UNAVAILABLE_MODELS.add(model)
        print(f"  [{model}] fail — next model...", flush=True)
    raise RuntimeError("Gemini API failed (all models tried)")


def _local_topics(count: int, used: list) -> list:
    candidates = [
        f"{obj.capitalize()} that {event} in {place}"
        for obj in _LOCAL_OBJECTS
        for event in _LOCAL_EVENTS
        for place in _LOCAL_PLACES
    ]
    used_normalized = {
        re.sub(r"[^a-z0-9]+", " ", item.casefold()).strip()
        for item in used
        if isinstance(item, str)
    }
    random.shuffle(candidates)
    topics = [
        topic for topic in candidates
        if re.sub(r"[^a-z0-9]+", " ", topic.casefold()).strip() not in used_normalized
    ][:count]
    if len(topics) != count:
        raise RuntimeError(
            f"Local fallback has only {len(topics)} unused topics; needs {count}"
        )
    return topics


def _local_script(topic: str, kind: str) -> dict:
    object_phrase = topic.split(" that ", 1)[0]
    item = object_phrase[0].lower() + object_phrase[1:]
    if kind == "short":
        narrations = [
            f"One bright morning, Milo spotted {item} nearby and called, 'Tilly, come and see!'",
            "A gentle breeze nudged it farther away, and Milo hurried after it without a plan.",
            "Tilly watched carefully and said, 'Let's slow down and think of a safe way to help.'",
            "Milo held the path clear while Tilly carefully guided it back to a safe spot.",
            "Together they solved the little problem, shared a happy laugh, and celebrated as friends.",
        ]
    else:
        narrations = [
            f"One bright morning, Milo spotted {item} near the meadow path. 'Tilly, look!' he called, his curious ears lifting as he hurried over to investigate. Sunlight shimmered on the grass, and the friends wondered how it had arrived there as birds sang nearby.",
            "Tilly joined him and looked at the small surprise from a safe distance. The friends could see it needed help, but rushing might make the problem harder. They listened to the breeze and watched carefully before taking another step, then made a little plan.",
            "Milo tried to fix everything quickly. He stepped this way and that, but the surprise only moved farther away, and his first plan did not work. He nearly tried again, then noticed Tilly waiting calmly beside the path without disturbing the flowers.",
            "He stopped, took a breath, and listened as Tilly gently reminded him that careful thinking can be more useful than rushing ahead. Milo nodded, feeling proud that he could pause, learn, and try a kinder plan with a thoughtful little smile.",
            "Tilly studied the ground and noticed a clear, gentle route nearby. She explained her idea while Milo gathered a few soft leaves to keep the path tidy. Together they checked that there was room for everyone to move safely before they started together.",
            "Together they followed the plan one small step at a time. Milo stayed patient, and Tilly guided the surprise away from the tricky spot. They encouraged each other whenever it wobbled, and slowly their teamwork began to help with plenty of room to move.",
            "For a moment it wobbled again. The friends paused, checked that everything was safe, and adjusted their plan instead of giving up. Milo held still while Tilly showed him the best direction to try next, and they tried their gentle idea.",
            "Milo held the way open while Tilly carefully helped. At last the surprise reached a calm place where it could rest without trouble. The two friends smiled when they saw that their gentle plan had worked near a shady patch of clover.",
            "The meadow felt peaceful again. Milo and Tilly smiled at their teamwork and noticed how much easier the problem felt once they worked together. They thanked each other for listening, being patient, and sharing the helpful idea under the warm afternoon sun.",
            "They waved goodbye to their little adventure and headed home as the sun warmed the path. Milo promised to pause and think next time, and Tilly laughed. Thanks for joining Milo and Tilly; see you next time, ready for another kind adventure!",
        ]

    scenes = [
        {
            "narration": narration,
            "setting": "sunny meadow",
            "action": item,
            "mood": mood,
        }
        for narration, mood in zip(
            narrations,
            ("curious", "worried", "surprised", "curious", "happy",
             "excited", "worried", "happy", "happy", "happy"),
        )
    ]
    script = " ".join(scene["narration"] for scene in scenes)
    title = " ".join(word.capitalize() for word in topic.split())
    if kind == "short":
        title = f"{title[:60].rstrip()} #Shorts"
    return {
        "hook_text": "A MEADOW SURPRISE",
        "scenes": scenes,
        "script": script,
        "title": title[:100],
        "description": (
            f"Milo and Tilly solve a gentle meadow problem together. "
            f"#ToonZoOfficial #Cartoon{' #Shorts' if kind == 'short' else ''}"
        ),
        "tags": ["ToonZo Official", "cartoon", "Milo and Tilly", "family friendly"],
        "topic": topic,
        "kind": kind,
    }


def _condense_short_narrations(scenes: list, word_limit: int) -> list[str]:
    """Keep each story beat, using its first sentence within a Short-length budget."""
    per_scene_limit = max(1, word_limit // len(scenes))
    condensed = []
    for scene in scenes:
        narration = scene["narration"].strip()
        sentences = re.split(r"(?<=[.!?])\s+", narration)
        sentence = next((part.strip() for part in sentences if part.strip()), narration)
        words = sentence.split()
        if len(words) > per_scene_limit:
            sentence = " ".join(words[:per_scene_limit]).rstrip(",;:") + "…"
        condensed.append(sentence)
    return condensed


def _parse_json(text: str):
    cleaned = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", text.strip(), flags=re.I)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Gemini returned invalid JSON at line {exc.lineno}, "
            f"column {exc.colno} (response length {len(cleaned)} characters)"
        ) from exc


def _generate_json(prompt: str, context: str):
    last_error = None
    retry_prompt = prompt
    for attempt, starting_model in enumerate(range(len(MODELS))):
        try:
            return _parse_json(_ask_gemini(retry_prompt, starting_model))
        except ValueError as exc:
            last_error = exc
            if attempt < len(MODELS) - 1:
                print(
                    f"  {context} JSON invalid; retrying with model "
                    f"{MODELS[(starting_model + 1) % len(MODELS)]}.",
                    flush=True,
                )
                retry_prompt = (
                    prompt
                    + "\n\nThe previous response was invalid or incomplete. "
                    "Return one complete, syntactically valid JSON value only. "
                    "Keep every required field, but use concise scene descriptions."
                )
    raise RuntimeError(
        f"Could not generate valid {context} JSON after retry: {last_error}"
    )


def generate_topics(count: int, kind: str, used: list, performance: dict = None,
                    research: list = None) -> list:
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
- Use these optional YouTube research notes only for broad storytelling lessons. Never copy plots, characters, dialogue, titles, visuals, or creator styles. Create materially original premises:
{json.dumps(research or [], ensure_ascii=False)[:12000]}
- Short ideas need one simple conflict and a quick payoff; long ideas need a coherent beginning, middle, and end

Respond ONLY with a JSON array of strings. No other text."""
    try:
        topics = _generate_json(prompt, "story idea")
    except RuntimeError as exc:
        print(
            f"  Gemini unavailable for {kind} ideas; using original local ideas: {exc}",
            flush=True,
        )
        return _local_topics(count, used)
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

    try:
        data = _generate_json(prompt, f"{kind} cartoon script")
    except RuntimeError as exc:
        print(
            f"  Gemini unavailable for {kind} script; using the local story template: {exc}",
            flush=True,
        )
        data = _local_script(topic, kind)
    if not isinstance(data, dict):
        raise ValueError("Gemini cartoon package must be a JSON object")
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
        original_words = len(scene_script.split())
        print(
            f"  Short narration was {original_words} words; keeping each scene's "
            f"opening beat within {config.SHORT_TARGET_WORDS} words.",
            flush=True,
        )
        for scene, narration in zip(
            normalized_scenes,
            _condense_short_narrations(normalized_scenes, config.SHORT_TARGET_WORDS),
        ):
            scene["narration"] = narration
        scene_script = " ".join(scene["narration"] for scene in normalized_scenes)
        data["scenes"] = normalized_scenes
        data["script"] = scene_script
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
