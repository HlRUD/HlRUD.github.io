import asyncio
import os
import subprocess
import tempfile
import requests

from splusthon import SoroushClient, events
from splusthon.sessions import StringSession

# Talkbot API
API_KEY = "sk-s68980b7df06c90b558092fawebff9as"
API_URL = "https://api.talkbot.ir/v1/media/text-to-speech/REQ"

# Session file
SESSION_FILE = "/storage/emulated/0/splus.session"

if not os.path.isfile(SESSION_FILE):
    raise FileNotFoundError(
        f"Session file not found: {SESSION_FILE}"
    )

with open(SESSION_FILE, "r", encoding="utf-8") as f:
    session_string = f.read().strip()

client = SoroushClient(StringSession(session_string))


def text_to_voice(text):
    with tempfile.TemporaryDirectory() as tmp:
        mp3_path = os.path.join(tmp, "speech.mp3")
        ogg_path = os.path.join(tmp, "speech.ogg")

        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {API_KEY}"
            },
            data={
                "text": text,
                "gender": "male",
                "lang": "english"
            },
            timeout=120
        )
        response.raise_for_status()

        # Handle either binary audio or JSON response.
        content_type = response.headers.get(
            "Content-Type", ""
        ).lower()

        if "json" in content_type:
            result = response.json()
            audio_url = (
                result.get("url")
                or result.get("audio_url")
                or result.get("data", {}).get("url")
            )

            if not audio_url:
                raise RuntimeError(
                    f"Audio URL not found in API response: {result}"
                )

            audio_response = requests.get(
                audio_url, timeout=120
            )
            audio_response.raise_for_status()
            audio_data = audio_response.content
        else:
            audio_data = response.content

        with open(mp3_path, "wb") as f:
            f.write(audio_data)

        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", mp3_path,
                "-c:a", "libopus",
                "-b:a", "32k",
                "-vbr", "on",
                "-application", "voip",
                "-ac", "1",
                "-ar", "48000",
                ogg_path
            ],
            check=True,
            capture_output=True,
            text=True
        )

        with open(ogg_path, "rb") as f:
            return f.read()


@client.on(events.NewMessage)
async def handler(event):
    if not event.is_private or not event.out:
        return

    message = (event.raw_text or "").strip()

    if not message.startswith("/voice "):
        return

    text = message[len("/voice "):].strip()

    if not text:
        await event.reply(
            "Usage: /voice your text here"
        )
        return

    try:
        await event.reply("Creating voice...")

        audio_data = await asyncio.to_thread(
            text_to_voice, text
        )

        with tempfile.NamedTemporaryFile(
            suffix=".ogg", delete=False
        ) as f:
            f.write(audio_data)
            audio_path = f.name

        try:
            await client.send_file(
                "me",
                audio_path,
                voice_note=True
            )
        finally:
            if os.path.exists(audio_path):
                os.remove(audio_path)

    except Exception as exc:
        await event.reply(f"Error: {exc}")


client.start()
client.run_until_disconnected()