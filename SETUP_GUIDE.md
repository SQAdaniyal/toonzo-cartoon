# ToonZo Official — Setup Guide

## Current workflow status

The GitHub Action is configured to schedule **one long video and four Shorts daily**, targeting 6:30 PM Pakistan time (13:30 UTC). Scheduled runs publish publicly and mark videos Made for Kids, as selected by the channel owner. Manual **Run workflow** runs remain preview-only and do not upload. GitHub's schedule is best-effort and may start late.

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
4. Open **Actions → ToonZo Daily Cartoons → Run workflow**.
5. Download the run's `toonzo-preview-*` artifact and review the videos and subtitles.

Manual preview runs do not upload and do not need YouTube credentials. Scheduled runs do require the three YouTube secrets below.

## 3. Scheduled YouTube publishing

Scheduled uploads are public, so review a manual preview before the first scheduled run if you have not already done so. Set the actual YouTube channel name to **ToonZo Official** in YouTube Studio. Upload mode verifies the OAuth account's exact channel name and checks its latest 50 video titles and saved history before uploading. For authorized YouTube uploads, create OAuth credentials locally and generate a refresh token with `get_refresh_token.py`; the script saves the token under the ignored `local_secrets/` folder rather than printing the credential. Never commit the OAuth JSON or token file.

For scheduled YouTube publishing, these repository Actions secrets are required:

- `YT_CLIENT_ID`
- `YT_CLIENT_SECRET`
- `YT_REFRESH_TOKEN`

Scheduled runs are configured for public visibility and Made for Kids. The OAuth-authorized channel must be named exactly **ToonZo Official** or the pipeline stops before generating/uploading. Ensure the actual channel name in YouTube Studio is correct. YouTube API quota, OAuth access and account permissions can still prevent uploads.

## Target and schedule

The configured target is `LONG_VIDEOS_PER_DAY = 1` and `SHORTS_PER_DAY = 4`. GitHub-hosted standard runners are free for this public repository; GitHub schedule timing is best-effort.

## Limitations

- The current artwork is locally drawn lightweight 2D animation, not AI-generated cinematic animation or lip-sync.
- Generated content still needs human review; technical checks cannot guarantee copyright clearance or monetization eligibility.
- Daily runs, API quotas, third-party services, and monetization outcomes are not guaranteed.
