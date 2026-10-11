"""
edge-tts (100% free, no API key) se Urdu voiceover banata hai.
"""
import asyncio
import edge_tts
import config


async def _speak(text: str, out_path: str):
    communicate = edge_tts.Communicate(
        text, voice=config.VOICE, rate=config.VOICE_RATE
    )
    await communicate.save(out_path)


def make_voiceover(text: str, out_path: str) -> str:
    """Text -> mp3 file. Returns path."""
    asyncio.run(_speak(text, out_path))
    return out_path
