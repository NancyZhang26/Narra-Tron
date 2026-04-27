from CameraCode.Camera_Feed import capture, preview
from narratron.services.tts import TTSService
from picamera2 import Picamera2
import time

from pathlib import Path
import subprocess
from PIL import Image
import pytesseract

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

IMAGE_PATH = OUTPUT_DIR / "page.jpg"
AUDIO_PATH = OUTPUT_DIR / "speech.wav"


def extract_text(image_path: Path) -> str:
    image = Image.open(image_path)
    return pytesseract.image_to_string(image)


def play_audio(path: Path):
    subprocess.run(["aplay", str(path)])  # blocks until done


def main():
    tts = TTSService(
        use_mock=False,
        piper_model_path="/home/pi/models/en_US-lessac-medium.onnx"
    )

    print("System ready.")

    while True:
        input("\nPress Enter to scan next page...")

        print("📸 Capturing image...")
        capture(str(IMAGE_PATH))

        print("🔍 Running OCR...")
        text = extract_text(IMAGE_PATH)

        if not text.strip():
            print("⚠️ No text detected, try again.")
            continue

        print("🗣 Generating speech...")
        tts.synthesize(text, str(AUDIO_PATH))

        print("🔊 Playing audio...")
        play_audio(AUDIO_PATH)

        print("✅ Done. Turn page.")


if __name__ == "__main__":
    main()
