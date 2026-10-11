# ToonZo Official — Setup Guide

## Current workflow status

The GitHub Action is configured to schedule **one long video and four Shorts daily**, starting at 3:00 AM Pakistan time (22:00 UTC). Scheduled and manually started workflow runs publish publicly and mark videos Made for Kids, as selected by the channel owner. The overnight time is a trial to avoid peak demand, not a guarantee of Gemini availability. GitHub's schedule is best-effort and may start late.

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

## 2. Start a GitHub upload

1. Confirm all four Actions secrets are set: `GEMINI_API_KEY`, `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, and `YT_REFRESH_TOKEN`.
2. Review a local preview before publishing if you have not already reviewed the cartoon style.
3. Open **Actions → ToonZo Daily Cartoons → Run workflow** to publish a batch immediately.

Each manual run can publish one long video and four Shorts publicly. Do not start another run unless you want another batch; manual runs require the same YouTube credentials as scheduled runs.

## 3. Scheduled YouTube publishing

Uploads are public, so review a local preview before the first upload if you have not already done so. Set the actual YouTube channel name to **ToonZo Official** in YouTube Studio. Upload mode verifies the OAuth account's exact channel name and checks its latest 50 video titles and saved history before uploading. For authorized YouTube uploads, create OAuth credentials locally and generate a refresh token with `get_refresh_token.py`; the script saves the token under the ignored `local_secrets/` folder rather than printing the credential. Never commit the OAuth JSON or token file.

For scheduled YouTube publishing, these repository Actions secrets are required:

- `YT_CLIENT_ID`
- `YT_CLIENT_SECRET`
- `YT_REFRESH_TOKEN`

All GitHub workflow runs are configured for public visibility and Made for Kids. The OAuth-authorized channel must be named exactly **ToonZo Official** or the pipeline stops before generating/uploading. Ensure the actual channel name in YouTube Studio is correct. YouTube API quota, OAuth access and account permissions can still prevent uploads.

## Target and schedule

The configured target is `LONG_VIDEOS_PER_DAY = 1` and `SHORTS_PER_DAY = 4`. The daily schedule starts at 3:00 AM Pakistan time to try a different API-demand window; Google does not guarantee that this time has lower demand. GitHub-hosted standard runners are free for this public repository; GitHub schedule timing is best-effort.

## Limitations

- The current artwork is locally drawn lightweight 2D animation, not AI-generated cinematic animation or lip-sync.
- Generated content still needs human review; technical checks cannot guarantee copyright clearance or monetization eligibility.
- Daily runs, API quotas, third-party services, and monetization outcomes are not guaranteed.
