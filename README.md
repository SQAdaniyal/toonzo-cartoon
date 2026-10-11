# ToonZo Official

Free-first cartoon production project for original family-friendly ToonZo stories. The current production path generates Milo-and-Tilly scene scripts, English narration, original lightweight 2D scenes, and SRT subtitles.

## Current status

- Configured production target: **1 long video and 4 Shorts per run**.
- Scheduled GitHub Action runs target **1 long cartoon + 4 Shorts daily**, and upload them publicly, starting at 3:00 AM Pakistan time. The overnight time is a trial to avoid peak demand; Gemini availability is not guaranteed. GitHub schedule timing is best-effort.
- Clicking **Run workflow** manually also publishes the generated videos publicly. Each run can upload up to five videos; avoid starting extra runs if you only want the daily batch.
- Local runs default to preview-only. Only `GEMINI_API_KEY` is needed for a local preview; Actions uploads also require the YouTube secrets below.
- If Gemini's free quota is exhausted or all configured models are unavailable, the pipeline switches to original local story templates so a run can continue without more Gemini requests. These fallback episodes are simpler and less varied than AI-generated scripts.
- Frames are branded **ToonZo Official**. Upload mode verifies the authorized channel title is exactly `ToonZo Official` and checks recent YouTube titles plus saved topic, title, and script history before uploading.
- This is a lightweight 2D animation MVP, not a full generative-image or character lip-sync system.

## Pipeline

1. Generate original, non-franchise story ideas and scene-by-scene scripts.
2. Create English narration using `edge-tts`.
3. Draw original vector-like cartoon scenes locally with Pillow.
4. Add subtle character motion, story captions, and SRT subtitles.
5. Render horizontal long videos and vertical Shorts with MoviePy/FFmpeg.
6. Scheduled and manually started GitHub workflow runs publish the generated videos automatically.

## Run locally

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Set `GEMINI_API_KEY` in the current PowerShell session (`.env.example` is a reference; the app does not auto-load `.env`), then run:

```powershell
$env:GEMINI_API_KEY = "your_rotated_key"
python main.py
```

Generated videos and subtitles are saved under `output/`.

## GitHub Actions setup

Add `GEMINI_API_KEY`, `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, and `YT_REFRESH_TOKEN` under **Settings → Secrets and variables → Actions**. Both scheduled runs and **Run workflow** publish up to five videos publicly. Review a previously generated preview locally or from an earlier Actions artifact before starting a manual upload.

Do not add API keys or OAuth JSON files to the repository. Any keys shared in chat should be revoked and replaced before use.

## Daily publishing

- `YT_CLIENT_ID`
- `YT_CLIENT_SECRET`
- `YT_REFRESH_TOKEN`

The workflow uses public visibility and `Made for Kids = true`, as selected by the channel owner. It uploads only if the OAuth-authorized channel name is exactly **ToonZo Official**; rename the actual channel in YouTube Studio first if needed. The target is configurable as 1 long video and 4 Shorts in [config.py](./config.py).

## Important

The repo is public, so standard GitHub-hosted Actions runners are used without private-repository minute overage. Scheduled runs still depend on Actions availability, valid secrets, YouTube quota/OAuth permissions, and platform policies; uploads can fail and are not guaranteed. Review the first generated videos after the first run. Monetization approval is not guaranteed.

## License

MIT
