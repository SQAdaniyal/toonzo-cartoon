# ToonZo Official — Setup Guide

## Current workflow status

The GitHub Action currently runs **manually for preview only**. It does not schedule uploads and YouTube upload is disabled by default. The target is configured to render one long video and four Shorts per run, using original Milo-and-Tilly 2D scenes.

## 1. Install locally

Install Python 3.12 and FFmpeg, then in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Set `GEMINI_API_KEY` in the environment, then start a preview:

```powershell
$env:GEMINI_API_KEY = "your_rotated_key"
python main.py
```

The output MP4 and SRT files are created in `output/`.

## 2. Render a GitHub preview

1. Revoke and replace any API key that was shared in chat.
2. In the GitHub repository, open **Settings → Secrets and variables → Actions**.
3. Add `GEMINI_API_KEY` with the rotated key.
4. Open **Actions → ToonZo Cartoon Preview → Run workflow**.
5. Download the run's `toonzo-preview-*` artifact and review the videos and subtitles.

The preview workflow does not need Pexels or YouTube credentials.

## 3. YouTube publishing — later, after preview approval

Do not enable public uploads until the cartoon appearance, scripts, subtitles, audience classification, and permissions have been reviewed. Set the actual YouTube channel name to **ToonZo Official** in YouTube Studio. Upload mode verifies the OAuth account's exact channel name and checks its latest 50 video titles against generated titles. For authorized YouTube uploads, create OAuth credentials locally and generate a refresh token with `get_refresh_token.py`. Never commit the OAuth JSON file.

When production publishing is intentionally enabled, add these repository Actions secrets:

- `YT_CLIENT_ID`
- `YT_CLIENT_SECRET`
- `YT_REFRESH_TOKEN`

Set `UPLOAD_TO_YOUTUBE=true`, choose `YOUTUBE_PRIVACY_STATUS` deliberately, and set `YOUTUBE_MADE_FOR_KIDS` to `true` or `false` according to the actual intended audience. Upload mode refuses to start without that audience decision. Before enabling a daily schedule, verify YouTube API quotas, OAuth access, and GitHub Actions usage.

## Target and schedule

The configured target is `LONG_VIDEOS_PER_DAY = 1` and `SHORTS_PER_DAY = 4`. The daily schedule remains paused until preview review; when enabled, the planned publishing time is 6:30 PM Pakistan time (13:30 UTC).

## Limitations

- The current artwork is locally drawn lightweight 2D animation, not AI-generated cinematic animation or lip-sync.
- Generated content still needs human review; technical checks cannot guarantee copyright clearance or monetization eligibility.
- Daily runs, API quotas, third-party services, and monetization outcomes are not guaranteed.
