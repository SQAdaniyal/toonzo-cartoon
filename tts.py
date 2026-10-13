"""Generate narration with Edge TTS and a local eSpeak NG fallback."""
import asyncio
import os
import shutil
import subprocess
import time

import edge_tts
import config


EDGE_TIMEOUT_SECONDS = 45


async def _speak(text: str, out_path: str):
    communicate = edge_tts.Communicate(
        text, voice=config.VOICE, rate=config.VOICE_RATE
    )
    await communicate.save(out_path)


def _remove_file(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def _is_forbidden(error: Exception) -> bool:
    pending = [error]
    seen = set()
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        if getattr(current, "status", None) == 403:
            return True
        pending.extend(
            cause for cause in (current.__cause__, current.__context__)
            if cause is not None
        )
    return False


def _offline_speak(text: str, out_path: str) -> str:
    executable = shutil.which("espeak-ng") or shutil.which("espeak")
    if not executable:
        raise RuntimeError("eSpeak NG is missing; install espeak-ng for offline TTS fallback")

    locale = config.VOICE.lower()[:5]
    wav_path = os.path.splitext(out_path)[0] + ".fallback.wav"
    os.makedirs(os.path.dirname(os.path.abspath(wav_path)), exist_ok=True)
    _remove_file(wav_path)
    subprocess.run(
        [executable, "-v", locale, "-s", "180", "-w", wav_path, text],
        check=True,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if not os.path.isfile(wav_path) or os.path.getsize(wav_path) < 128:
        raise RuntimeError("eSpeak NG did not create a usable narration file")
    return wav_path


def make_voiceover(text: str, out_path: str) -> str:
    """Return an MP3 from Edge TTS or a WAV from local eSpeak NG."""
    if not text or not text.strip():
        raise ValueError("Cannot synthesize an empty narration")

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    edge_path = out_path + ".edge-tmp"
    last_error = None

    for attempt in range(2):
        _remove_file(edge_path)
        try:
            asyncio.run(asyncio.wait_for(
                _speak(text, edge_path), timeout=EDGE_TIMEOUT_SECONDS
            ))
            if not os.path.isfile(edge_path) or os.path.getsize(edge_path) < 128:
                raise RuntimeError("Edge TTS returned an empty audio file")
            os.replace(edge_path, out_path)
            print("  Voiceover generated with Edge TTS.")
            return out_path
        except Exception as error:
            last_error = error
            _remove_file(edge_path)
            if _is_forbidden(error):
                break
            if attempt == 0:
                time.sleep(2)

    reason = "HTTP 403" if last_error and _is_forbidden(last_error) else type(last_error).__name__
    print(f"  Edge TTS unavailable ({reason}); switching to local eSpeak NG.")
    return _offline_speak(text, out_path)
