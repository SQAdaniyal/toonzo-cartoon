"""
ToonZo cartoon production pipeline.
Flow: story ideas -> scene scripts -> voiceover -> 2D animation -> optional upload
"""
import json
import hashlib
import os
import re
import traceback
from difflib import SequenceMatcher
from datetime import datetime, timedelta, timezone

import config
import script_gen
import tts
import cartoon

if config.UPLOAD_TO_YOUTUBE:
    import upload


def load_used() -> list:
    if os.path.exists(config.USED_TOPICS_FILE):
        with open(config.USED_TOPICS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_used(used: list):
    with open(config.USED_TOPICS_FILE, "w", encoding="utf-8") as f:
        json.dump(used, f, ensure_ascii=False, indent=1)


def load_video_history() -> list:
    if os.path.exists(config.VIDEO_HISTORY_FILE):
        with open(config.VIDEO_HISTORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_video_history(history: list):
    with open(config.VIDEO_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=1)


def load_content_history() -> list:
    if os.path.exists(config.CONTENT_HISTORY_FILE):
        with open(config.CONTENT_HISTORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_content_history(history: list):
    with open(config.CONTENT_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=1)


def normalize_text(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.casefold()).strip()


def _is_duplicate_title(title: str, content_history: list) -> bool:
    candidate = normalize_text(title)
    candidate_words = set(candidate.split())
    for item in content_history:
        previous_title = item.get("title", "")
        if not isinstance(previous_title, str):
            continue
        previous = normalize_text(previous_title)
        previous_words = set(previous.split())
        shared_words = candidate_words & previous_words
        union_words = candidate_words | previous_words
        if previous and (
            candidate == previous
            or SequenceMatcher(None, candidate, previous).ratio() >= 0.92
            or (union_words and len(shared_words) / len(union_words) >= 0.8)
        ):
            return True
    return False


def _script_fingerprint(script: str) -> str:
    normalized = normalize_text(script)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get_daily_upload_counts(history: list, recent_uploads: list,
                            run_date) -> dict:
    """Count this Pakistan-local day's uploads from saved and live channel data."""
    uploads_by_id = {}
    for item in (recent_uploads or []) + (history or []):
        if not isinstance(item, dict):
            continue
        video_id = item.get("video_id")
        uploaded_at = item.get("uploaded_at")
        kind = item.get("kind")
        if (not video_id or not isinstance(uploaded_at, str)
                or kind not in {"long", "short"}):
            continue
        try:
            timestamp = datetime.fromisoformat(uploaded_at.replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            continue
        local_date = (timestamp.astimezone(timezone.utc) + timedelta(hours=5)).date()
        if local_date == run_date:
            uploads_by_id[video_id] = kind
    counts = {"long": 0, "short": 0}
    for kind in uploads_by_id.values():
        counts[kind] += 1
    return counts


def generate_unique_topics(count: int, kind: str, used: list,
                           performance: dict, additional_topics: list = None,
                           research: list = None) -> list:
    selected = []
    seen = {normalize_text(topic) for topic in used}
    seen.update(normalize_text(topic) for topic in (additional_topics or []))
    for _ in range(4):
        if len(selected) == count:
            break
        candidates = script_gen.generate_topics(
            count - len(selected),
            kind,
            used + (additional_topics or []) + selected,
            performance,
            research,
        )
        for topic in candidates:
            normalized = normalize_text(topic)
            if normalized and normalized not in seen:
                selected.append(topic)
                seen.add(normalized)
                if len(selected) == count:
                    break
    if len(selected) != count:
        raise RuntimeError(
            f"Could not generate {count} unique {kind} topics after 4 attempts"
        )
    return selected


def get_topic_performance(history: list) -> dict:
    if not history:
        return {}
    try:
        views = upload.get_video_statistics([item["video_id"] for item in history])
    except Exception as exc:
        print(f"  Performance data unavailable; using fresh topic generation: {exc}")
        return {}

    now = datetime.now(timezone.utc)
    ranked = {"long": [], "short": []}
    for item in history:
        uploaded_at = datetime.fromisoformat(item["uploaded_at"])
        hours = max((now - uploaded_at).total_seconds() / 3600, 1)
        counts = views.get(item["video_id"], {})
        view_count = counts.get("views", 0)
        likes = counts.get("likes", 0)
        comments = counts.get("comments", 0)
        ranked.setdefault(item["kind"], []).append({
            "topic": item["topic"],
            "views_per_day": round(view_count * 24 / hours, 1),
            "likes_per_100_views": round(likes * 100 / view_count, 2) if view_count else 0,
            "comments_per_1000_views": round(comments * 1000 / view_count, 2) if view_count else 0,
        })

    return {
        kind: {
            "top": sorted(items, key=lambda item: item["views_per_day"], reverse=True)[:5],
            "low": sorted(items, key=lambda item: item["views_per_day"])[:5],
            "top_engagement": sorted(
                items,
                key=lambda item: item["likes_per_100_views"] + item["comments_per_1000_views"],
                reverse=True,
            )[:5],
        }
        for kind, items in ranked.items()
    }


def make_one(topic: str, kind: str, idx: int, history: list,
             content_history: list) -> bool:
    workdir = os.path.join(config.WORK_DIR, f"{kind}_{idx}")
    os.makedirs(workdir, exist_ok=True)
    try:
        print(f"\n=== [{kind} #{idx}] {topic} ===")

        print("1) Unique cartoon script aur title generate ho rahe hain...")
        pkg = None
        fingerprint = ""
        previous_titles = [item.get("title", "") for item in content_history]
        for attempt in range(3):
            candidate = script_gen.generate_script(topic, kind, previous_titles)
            candidate_fingerprint = _script_fingerprint(candidate["script"])
            if (
                not _is_duplicate_title(candidate["title"], content_history)
                and all(
                    item.get("script_sha256") != candidate_fingerprint
                    for item in content_history
                )
            ):
                pkg = candidate
                fingerprint = candidate_fingerprint
                break
            print(f"  Duplicate title or script; retrying ({attempt + 1}/3)...")
            previous_titles.append(candidate["title"])
        if pkg is None:
            raise RuntimeError("Could not produce a unique title and script after 3 attempts")
        if kind == "short" and "#shorts" not in pkg["title"].lower():
            pkg["title"] = pkg["title"].rstrip() + " #Shorts"
        hook_text = pkg.get("hook_text", topic.upper()[:40])

        print("2) Natural voiceover ban raha hai (Gemini TTS / Edge Neural)...")
        audio = tts.make_voiceover(
            pkg["script"], os.path.join(workdir, "voice.mp3")
        )

        print("3) Original 2D cartoon scenes render ho rahe hain...")
        out = cartoon.render_video(
            pkg["scenes"], audio, pkg["title"], kind,
            os.path.join(workdir, "final.mp4"),
            hook_text=hook_text
        )

        if config.UPLOAD_TO_YOUTUBE:
            print("4) YouTube par upload ho rahi hai...")
            desc = pkg["description"]
            if "toonzo official" not in desc.lower():
                desc = f"ToonZo Official presents: {desc}"
            if kind == "short" and "#shorts" not in desc.lower():
                desc += "\n#Shorts"
            video_id = upload.upload_video(out, pkg["title"], desc, pkg.get("tags", []))
            history.append({
                "topic": topic,
                "title": pkg["title"],
                "kind": kind,
                "video_id": video_id,
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
            })
            save_video_history(history)
        else:
            print(f"  (Preview mode) Video saved: {out}")
        content_history.append({
            "topic": topic,
            "title": pkg["title"],
            "script_sha256": fingerprint,
            "kind": kind,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "video_id": video_id if config.UPLOAD_TO_YOUTUBE else None,
        })
        save_content_history(content_history)
        return True

    except Exception:
        print(f"❌ FAIL [{kind} #{idx}]:")
        traceback.print_exc()
        return False


def main():
    os.makedirs(config.WORK_DIR, exist_ok=True)
    used = load_used()
    history = load_video_history()
    content_history = load_content_history()
    used.extend(
        item["topic"] for item in content_history
        if item.get("topic") and item["topic"] not in used
    )
    used.extend(
        item["topic"] for item in history
        if item.get("topic") and item["topic"] not in used
    )
    ok = fail = 0

    missing = [name for name in ("GEMINI_API_KEY",) if not getattr(config, name)]
    if config.UPLOAD_TO_YOUTUBE:
        if config.PRIVACY_STATUS not in {"private", "unlisted", "public"}:
            raise RuntimeError(
                "YOUTUBE_PRIVACY_STATUS must be private, unlisted, or public"
            )
        if config.YOUTUBE_MADE_FOR_KIDS not in {"true", "false"}:
            raise RuntimeError(
                "Set YOUTUBE_MADE_FOR_KIDS to true or false based on the channel's actual audience"
            )
        missing.extend(
            name for name in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN")
            if not getattr(config, name)
        )
    if missing:
        raise RuntimeError("Missing required environment secrets: " + ", ".join(missing))

    if config.UPLOAD_TO_YOUTUBE:
        channel_title, recent_uploads = upload.get_channel_identity_and_recent_uploads()
        if channel_title != config.CHANNEL_NAME:
            raise RuntimeError(
                f"Authorized YouTube channel is {channel_title!r}; "
                f"expected {config.CHANNEL_NAME!r}. No videos were uploaded."
            )
        content_history.extend({"title": item["title"]} for item in recent_uploads)

        local_date = (datetime.now(timezone.utc) + timedelta(hours=5)).date()
        uploaded_today = get_daily_upload_counts(history, recent_uploads, local_date)
        long_count = max(config.LONG_VIDEOS_PER_DAY - uploaded_today["long"], 0)
        short_count = max(config.SHORTS_PER_DAY - uploaded_today["short"], 0)
        if long_count + short_count == 0:
            print("Today's YouTube upload target is already complete; skipping.")
            return
        print(
            f"Today's recovery target: {long_count} long video(s), "
            f"{short_count} Short(s) remaining."
        )
    else:
        long_count = config.LONG_VIDEOS_PER_DAY
        short_count = config.SHORTS_PER_DAY

    performance = get_topic_performance(history) if config.UPLOAD_TO_YOUTUBE else {}
    research = []
    if os.path.exists(config.RESEARCH_NOTES_FILE):
        try:
            with open(config.RESEARCH_NOTES_FILE, encoding="utf-8") as f:
                research = json.load(f)
            if not isinstance(research, list):
                research = []
            print(f"YouTube research notes loaded: {len(research)} video(s).")
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Research notes unavailable; continuing without them: {exc}")
    print("ToonZo ke original cartoon ideas generate ho rahe hain...")
    long_topics = generate_unique_topics(
        long_count, "long", used, performance, research=research
    ) if long_count else []
    short_topics = generate_unique_topics(
        short_count, "short", used, performance, long_topics, research
    ) if short_count else []
    print("Long :", long_topics)
    print("Short:", short_topics)
    missing_topics = max(long_count - len(long_topics), 0) + max(
        short_count - len(short_topics), 0
    )
    if missing_topics:
        print(f"  Topic generation returned {missing_topics} fewer topic(s) than requested.")
        fail += missing_topics

    for i, t in enumerate(long_topics, 1):
        if make_one(t, "long", i, history, content_history):
            ok += 1
            used.append(t)
        else:
            fail += 1
        save_used(used)

    for i, t in enumerate(short_topics, 1):
        if make_one(t, "short", i, history, content_history):
            ok += 1
            used.append(t)
        else:
            fail += 1
        save_used(used)

    print(f"\n===== DONE: {ok} success, {fail} fail =====")
    if fail:
        raise SystemExit(1)
    if ok == 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
