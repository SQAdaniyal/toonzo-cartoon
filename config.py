"""
Saari settings — sirf yeh file edit karein.
"""
import os

# ---------- API KEYS ----------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
YT_CLIENT_ID = os.environ.get("YT_CLIENT_ID", "")
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET", "")
YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN", "")

# ---------- CONTENT ----------
NICHE = "original, family-friendly 2D cartoon adventures featuring ToonZo's recurring characters"
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
UPLOAD_TO_YOUTUBE = os.environ.get("UPLOAD_TO_YOUTUBE", "false").lower() == "true"
PRIVACY_STATUS = os.environ.get("YOUTUBE_PRIVACY_STATUS", "private")
YOUTUBE_MADE_FOR_KIDS = os.environ.get("YOUTUBE_MADE_FOR_KIDS", "").lower()
CATEGORY_ID = "1"
CHANNEL_NAME = "ToonZo Official"

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
CONTENT_HISTORY_FILE = "content_history.json"
