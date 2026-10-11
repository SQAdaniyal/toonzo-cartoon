"""
Gemini API — viral English scripts optimized for organic reach.
"""
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
        "3-4 minute viral facts video"
        if kind == "long"
        else "45-second viral YouTube Short (ONE shocking fact)"
    )
    prompt = f"""You are an audience-first YouTube strategist for a worldwide English facts channel.

Generate exactly {count} fresh, specific topics for a {style}. Privately compare candidate ideas, then return only the strongest ones.

Pick ONLY from these proven viral categories:
- Science facts that sound impossible but are true
- Dark or shocking history most people never learned in school  
- Space & universe facts with mind-bending scale
- Human body / psychology facts that feel personal
- Animal abilities that seem like superpowers
- World records that sound fake
- "You've been doing X wrong your whole life" revelations
- FIFA World Cup 2026 shocking stats, records, untold stories
- Famous things that have a completely different secret origin

RULES:
- Prefer a concrete, surprising claim that creates an immediate question, not a broad subject such as "space facts"
- Favor novelty, broad relevance, clear stakes, and a visual idea viewers understand instantly
- Use the performance signal to explore adjacent angles to topics that earned more views; do not repeat their wording or assume views prove why they worked
- Facts must be specific and checkable; never invent numbers, quotes, records, or scientific explanations
- Avoid recycled trivia, vague superlatives, fabricated mystery, and claims framed as current trends without live evidence
- Visually supportable by stock footage, with original explanation that adds value beyond generic footage
- Each topic completely different from: {json.dumps(used[-150:], ensure_ascii=False)}
- Use this recent performance signal as a directional guide; create fresh topics, do not copy:
{json.dumps((performance or {}).get(kind, {}), ensure_ascii=False)}
- For Shorts, choose one singular fact with a fast payoff; for long videos, choose a focused subject that supports a coherent 5-7 point story
- For Shorts: ONE singular fact, not a list

Respond ONLY with a JSON array of strings. No other text."""
    return _parse_json(_ask_gemini(prompt))[:count]


def generate_script(topic: str, kind: str) -> dict:
    words = config.LONG_TARGET_WORDS if kind == "long" else config.SHORT_TARGET_WORDS

    if kind == "short":
        structure = """
SHORTS SCRIPT RULES (every rule is critical):
- First sentence delivers the specific, accurate payoff immediately; no greeting, filler, or generic "did you know"
- Explain why it is surprising in a simple mini-story, then end on a satisfying implication or reveal
- Use short natural sentences and concrete details; do not repeat the hook in different words
- End with a brief, natural follow prompt only if it fits without weakening the payoff
- Under 80 words total. Every word earns its place."""
    else:
        structure = """
LONG VIDEO SCRIPT RULES:
- Open with the central surprising fact and the question the video will answer; no greeting or filler intro
- Build a coherent story through 5-7 connected facts, with useful context and clear transitions
- Vary sentence rhythm and explain unfamiliar terms in plain English; do not pad or repeat claims
- Resolve the opening question with a strong, accurate payoff
- End with a brief, natural subscribe prompt
- ~400 words, conversational and energetic"""

    prompt = f"""Write a YouTube {'Short' if kind == 'short' else 'video'} package for: "{topic}"

{structure}

DELIVER a JSON object with these exact keys:

"hook_text": MAX 8 WORDS. The single most shocking sentence from this topic — written for display ON SCREEN in big text. Must work WITHOUT sound context. No punctuation except !. Examples: "YOUR DNA MATCHES A BANANA 60 PERCENT", "VENUS DAY IS LONGER THAN VENUS YEAR", "CLEOPATRA LIVED CLOSER TO IPHONE THAN PYRAMIDS". ALL CAPS.

"script": The full voiceover script following the rules above. Natural spoken English, energetic tone. No emojis, no stage directions.

"title": Specific, concise, curiosity-building title that accurately promises the video's real payoff. Avoid fake percentages, unsupported superlatives, and stock phrases such as "scientists can't explain" unless literally true. Under 90 characters. {"End with ' #Shorts'" if kind == 'short' else ""}

"description": Line 1 = hook (same shocking opener as script). Line 2 = "Subscribe for daily mind-blowing facts! 🔔". Line 3 = 12 hashtags: #Facts #MindBlowing #DidYouKnow #Science #History #Amazing #FunFacts #Shorts #FactsBaaz17 #LearnOnYouTube + 2 topic-specific tags.

"tags": 15 SEO English tags, mix of broad and specific.

"keywords": 5 simple English words for stock footage (e.g. "space", "ocean", "lion").

QUALITY: Do not fabricate facts or certainty. Keep every claim consistent with the topic, and make the title and hook accurately match the script. No medical advice or misleading clickbait.

Respond ONLY with the JSON object. No other text."""

    data = _parse_json(_ask_gemini(prompt))
    data["topic"] = topic
    data["kind"] = kind
    if "hook_text" not in data:
        data["hook_text"] = topic.upper()[:40]
    return data
