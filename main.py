"""
Main pipeline — roz GitHub Actions chalata hai.
Flow: topics -> scripts -> voiceover -> footage -> render -> upload
"""
import json
import os
import shutil
import traceback
from datetime import datetime, timezone

import config
import script_gen
import tts
import footage
import render

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


def make_one(topic: str, kind: str, idx: int, history: list) -> bool:
    workdir = os.path.join(config.WORK_DIR, f"{kind}_{idx}")
    os.makedirs(workdir, exist_ok=True)
    try:
        print(f"\n=== [{kind} #{idx}] {topic} ===")

        print("1) Script generate ho raha hai...")
        pkg = script_gen.generate_script(topic, kind)
        hook_text = pkg.get("hook_text", topic.upper()[:40])

        print("2) Voiceover ban raha hai (edge-tts)...")
        audio = tts.make_voiceover(
            pkg["script"], os.path.join(workdir, "voice.mp3")
        )

        print("3) Footage download ho rahi hai (Pexels)...")
        need = 10 if kind == "long" else 4
        clips = footage.download_clips(
            pkg["keywords"], kind, os.path.join(workdir, "clips"), need
        )
        if not clips:
            clips = footage.download_clips(
                ["nature", "space", "ocean"], kind,
                os.path.join(workdir, "clips"), need
            )
        if not clips:
            raise RuntimeError("Footage nahi mili")

        print("4) Video render ho rahi hai...")
        out = render.render_video(
            clips, audio, pkg["title"], kind,
            os.path.join(workdir, "final.mp4"),
            hook_text=hook_text
        )

        if config.UPLOAD_TO_YOUTUBE:
            print("5) YouTube par upload ho rahi hai...")
            desc = pkg["description"]
            if kind == "short" and "#shorts" not in desc.lower():
                desc += "\n#Shorts"
            video_id = upload.upload_video(out, pkg["title"], desc, pkg.get("tags", []))
            shutil.rmtree(workdir, ignore_errors=True)
        else:
            print(f"  (Test mode) Video saved: {out}")
        if config.UPLOAD_TO_YOUTUBE:
            history.append({
                "topic": topic,
                "kind": kind,
                "video_id": video_id,
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
            })
            save_video_history(history)
        return True

    except Exception:
        print(f"❌ FAIL [{kind} #{idx}]:")
        traceback.print_exc()
        return False


def main():
    os.makedirs(config.WORK_DIR, exist_ok=True)
    used = load_used()
    history = load_video_history()
    ok = fail = 0

    missing = [
        name for name in ("GEMINI_API_KEY", "PEXELS_API_KEY")
        if not getattr(config, name)
    ]
    if config.UPLOAD_TO_YOUTUBE:
        missing.extend(
            name for name in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN")
            if not getattr(config, name)
        )
    if missing:
        raise RuntimeError("Missing required environment secrets: " + ", ".join(missing))

    performance = get_topic_performance(history) if config.UPLOAD_TO_YOUTUBE else {}
    print("Aaj ke topics generate ho rahe hain...")
    long_topics = script_gen.generate_topics(config.LONG_VIDEOS_PER_DAY, "long", used, performance)
    short_topics = script_gen.generate_topics(config.SHORTS_PER_DAY, "short", used, performance)
    print("Long :", long_topics)
    print("Short:", short_topics)

    for i, t in enumerate(long_topics, 1):
        if make_one(t, "long", i, history):
            ok += 1
            used.append(t)
        else:
            fail += 1
        save_used(used)

    for i, t in enumerate(short_topics, 1):
        if make_one(t, "short", i, history):
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
