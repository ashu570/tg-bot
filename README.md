# tg_orchestrator

A Telegram bot + userbot pipeline for ingesting media from a Telegram channel, organizing it by season/quality, processing it, and publishing the results to shadow and ready channels.

## What this project does

This app:

- starts a Telegram bot and a Telegram userbot
- watches a raw source channel for media files
- parses filenames and extracts metadata such as title, year, season, episode, quality, and language
- builds season/quality selection cards for the user in Telegram
- downloads and processes files, generates thumbnails, and uploads them to a shadow channel
- optionally bridges the published batch to a link bot and sends a final message to a ready channel

## Requirements

Before running the project, make sure you have:

- Python 3.10+ (the project is written for Python 3.x)
- FFmpeg installed and available on your PATH
- A Telegram account for the userbot
- A Telegram bot token for the bot
- Telegram API credentials: API ID and API hash
- Access to the source/raw channel, shadow channel, and ready channel

### FFmpeg

The processing pipeline uses FFmpeg to generate thumbnails.

On Windows, install it and ensure the binary is available in PATH.

Example:

- winget install Gyan.dev.FFmpeg

Verify the installation:

```bash
ffmpeg -version
```

## Project setup

### 1. Clone and enter the project

```bash
cd tg_orchestrator
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv myenv
.\myenv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python3 -m venv myenv
source myenv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create a .env file

Create a file named `.env` in the project

### 5. Start the bot

```bash
python app.py
```

On first launch, Telethon will create session files:

- `bot_session.session`
- `userbot_session.session`

These files are used to authenticate the bot and userbot.

## Usage

Once the bot is running, message the bot in Telegram with a command like:

```text
/process some movie title
```

The bot will:

1. search the configured raw channel for matching media
2. present season/quality selection cards
3. process the selected batch and upload the results

## Important notes

- The app expects the Telegram sessions to be available and valid.
- The processing pipeline writes temporary files into the `downloads/` directory.
- The bot depends on Telegram channel IDs and valid permissions for reading and posting to those channels.
- If you see errors related to FFmpeg, thumbnails, or Telegram upload failures, confirm that FFmpeg is installed and the channel permissions are correct.

## Troubleshooting

### Module import errors

Make sure you activated the virtual environment and installed the requirements:

```bash
pip install -r requirements.txt
```

### Session errors

If Telethon throws authentication/session errors, delete the session files and start the app again after re-authenticating:

```bash
rm bot_session.session userbot_session.session
```

### Missing environment variables

If the app exits with a missing configuration error, verify the `.env` file contains all required keys.

## License

This project is currently unlicensed unless otherwise specified by the repository owner.

## Todo: Give information about setup.sh (chmod +x ./setup.sh)
