# ToonZo Official

Free-first cartoon production project for original family-friendly ToonZo stories. The current production path generates Milo-and-Tilly scene scripts, English narration, original lightweight 2D scenes, and SRT subtitles.

## Current status

- Configured production target: **1 long video and 4 Shorts per run**.
- The GitHub Action is **manual preview only**; scheduled publishing is paused until cartoon previews are reviewed.
- YouTube upload is disabled by default. No credential is required to render a preview; only `GEMINI_API_KEY` is needed.
- The preview action saves MP4 and SRT files as a 7-day Actions artifact.
- Frames are branded **ToonZo Official**. Upload mode verifies the authorized channel title is exactly `ToonZo Official` and checks recent YouTube titles plus saved topic, title, and script history before uploading.
- This is a lightweight 2D animation MVP, not a full generative-image or character lip-sync system.

## Pipeline

1. Generate original, non-franchise story ideas and scene-by-scene scripts.
2. Create English narration using `edge-tts`.
3. Draw original vector-like cartoon scenes locally with Pillow.
4. Add subtle character motion, story captions, and SRT subtitles.
5. Render horizontal long videos and vertical Shorts with MoviePy/FFmpeg.
6. Review the generated artifact before enabling any publishing.

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

## GitHub preview setup

Add a rotated `GEMINI_API_KEY` under **Settings → Secrets and variables → Actions**. Run **Actions → ToonZo Cartoon Preview → Run workflow**, then download the resulting preview artifact.

Do not add API keys or OAuth JSON files to the repository. Any keys shared in chat should be revoked and replaced before use.

## Daily publishing

Daily scheduling is intentionally paused while the cartoon output is reviewed. When enabling production later, set `UPLOAD_TO_YOUTUBE=true` only after preview approval and add these GitHub Actions secrets:

- `YT_CLIENT_ID`
- `YT_CLIENT_SECRET`
- `YT_REFRESH_TOKEN`

Set the intended `YOUTUBE_PRIVACY_STATUS` deliberately (`private` for a final test, then `public` when ready), and set `YOUTUBE_MADE_FOR_KIDS` accurately to `true` or `false`; upload mode refuses to run if the audience designation is omitted. Rename the actual YouTube channel to **ToonZo Official** in YouTube Studio first; the uploader checks the authorized channel name but does not rename it. GitHub secrets must be entered by the repository owner; this project does not upload credentials. The requested target is already configurable as 1 long video and 4 Shorts in [config.py](./config.py).

## Important

YouTube API quotas, OAuth permissions, account eligibility, content suitability, and monetization approval are controlled by YouTube and cannot be guaranteed by this project. Human review is required for copyright, audience classification, and public release decisions.

## License

MIT
