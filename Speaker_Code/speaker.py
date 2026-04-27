import os
import subprocess


class Speaker:
    """Blocking WAV playback via ALSA aplay.

    Wraps aplay so the rest of the pipeline doesn't need to know which
    audio subsystem is in use. play() blocks until the audio finishes,
    which is the lock that prevents the page-flipper from being signalled
    while narration is still running.
    """

    def __init__(self, device: str = "default") -> None:
        self.device = device

    def play(self, audio_path: str) -> None:
        if not audio_path or not os.path.exists(audio_path):
            print(f"WARNING: audio file not found at {audio_path!r}, skipping playback")
            return
        result = subprocess.run(
            ["aplay", "-D", self.device, audio_path], check=False
        )
        if result.returncode != 0:
            print(f"WARNING: aplay exited with code {result.returncode} for {audio_path!r}")

    def is_available(self) -> bool:
        """Return True if aplay can enumerate at least one audio device."""
        result = subprocess.run(["aplay", "-l"], capture_output=True)
        return result.returncode == 0
