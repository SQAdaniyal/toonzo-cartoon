"""
Saari settings — sirf yeh file edit karein.
"""
import os

# ---------- API KEYS ----------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
YT_CLIENT_ID = os.environ.get("YT_CLIENT_ID", "")
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET", "")
YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN", "")

# ---------- CONTENT ----------
NICHE = "mind-blowing science facts, shocking history, space mysteries, human psychology, world records, animal kingdom, viral facts, dark history, FIFA World Cup 2026"
LANGUAGE = "English"
LONG_VIDEOS_PER_DAY = 1
SHORTS_PER_DAY = 4

# ---------- VOICE ----------
VOICE = "en-US-GuyNeural"
VOICE_RATE = "+18%"

# ---------- VIDEO ----------
LONG_TARGET_WORDS = 400
SHORT_TARGET_WORDS = 80
LONG_RESOLUTION = (1920, 1080)
SHORT_RESOLUTION = (1080, 1920)
FPS = 24

# ---------- UPLOAD ----------
UPLOAD_TO_YOUTUBE = True
PRIVACY_STATUS = "public"
CATEGORY_ID = "27"

# ---------- MODELS ----------
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

# ---------- PATHS ----------
WORK_DIR = "output"
USED_TOPICS_FILE = "used_topics.json"
VIDEO_HISTORY_FILE = "video_history.json"
