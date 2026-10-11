# ToonZo Official

ToonZo Official is a GitHub-ready YouTube cartoon automation starter project. It helps generate a regular pipeline of cartoon-style episodes and Shorts using free tools, local processing, and official platform APIs where available.

## Project Focus
- Original cartoon storytelling
- Repeatable publishing pipeline
- Free-first automation setup
- YouTube upload integration
- Channel analytics and optimization

## Repo Structure
- `main.py` — orchestrates the production pipeline
- `config.py` — channel, voice, upload, and content configuration
- `script_gen.py` — generates topics and scripts
- `tts.py` — text-to-speech generation
- `footage.py` — downloads stock footage
- `render.py` — assembles and renders video output
- `upload.py` — uploads to YouTube
- `.github/workflows/daily.yml` — scheduled GitHub Action
- `SETUP_GUIDE.md` — quickstart and environment setup

## Core Workflow
1. Generate topic ideas and scripts
2. Create voiceover audio
3. Download supporting footage
4. Render video with FFmpeg
5. Run QA checks
6. Upload approved content to YouTube
7. Track history and improve future content

## Quick Start
1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and add your secrets.
3. Edit `config.py` for your specific niche, voice, and output settings.
4. Run the pipeline:
   ```bash
   python main.py
   ```

## Required Secrets
- `GEMINI_API_KEY`
- `PEXELS_API_KEY`
- `YT_CLIENT_ID`
- `YT_CLIENT_SECRET`
- `YT_REFRESH_TOKEN`

## Recommended GitHub Setup
- Add the secrets listed above in GitHub repository settings.
- Keep `PRIVACY_STATUS` as `private` during testing.
- Use the GitHub Action to schedule daily publishing.

## Important Notes
- This repo is designed for automation and experimentation.
- YouTube eligibility, quota limits, and content quality still depend on platform policies and your channel history.
- Human review is still recommended before public publication.

## License
MIT

