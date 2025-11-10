# source ~/fw-venv/bin/activate

import time, queue, platform, json, argparse, sys
from pathlib import Path
import numpy as np
import sounddevice as sd
from pynput import keyboard
from faster_whisper import WhisperModel
import pyperclip
from pynput.keyboard import Controller, Key

# ============== USER SETTINGS ==============
MODEL_NAME   = "tiny"     # try "tiny" for fastest, "small" for balance
DEVICE       = "auto"      # "auto" picks Metal on Apple Silicon
COMPUTE_TYPE = "auto"      # let CTranslate2 choose (usually float16/int8 on Mac)
LANGUAGE     = "en"        # set to None for auto language; "en" is faster if English
MIC_INDEX    = None        # None = default. Use --list-mics to see indexes.
SAMPLE_RATE  = 48000
BLOCK_SIZE   = 1024

PTT_KEY = keyboard.Key.f13  # your pedal mapped to F13
DOUBLE_TAP_WINDOW = 0.45    # seconds
LONG_HOLD_CLEAR   = 2.0     # seconds (hold while idle to clear last)

PASTE_AFTER_TRANSCRIBE = True
PASTE_DELAY_SEC = 0.05      # tiny delay to let focus settle
# ===========================================

IS_MAC = platform.system() == "Darwin"
kb = Controller()
PASTE_COMBO = ["command","v"] if IS_MAC else ["ctrl","v"]

audio_q = queue.Queue()
recording = False
last_text = ""
last_release_time = 0.0
last_press_time = 0.0

def list_mics_and_exit():
    print(sd.query_devices())
    sys.exit(0)

def audio_cb(indata, frames, time_info, status):
    if recording:
        audio_q.put(indata.copy())

def input_stream():
    return sd.InputStream(channels=1, samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE,
                          dtype="int16", callback=audio_cb, device=MIC_INDEX)

def flush_audio_to_wav(path: Path):
    frames = []
    while True:
        try:
            frames.append(audio_q.get_nowait())
        except queue.Empty:
            break
    if not frames:
        return None
    data = np.concatenate(frames, axis=0)
    import wave
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SAMPLE_RATE)
        wf.writeframes(data.tobytes())
    return path

def route_text(text: str):
    if not text:
        return
    if PASTE_AFTER_TRANSCRIBE:
        time.sleep(PASTE_DELAY_SEC)
        pyperclip.copy(text)
    # Cmd+V on Mac, Ctrl+V elsewhere
    if IS_MAC:
        with kb.pressed(Key.cmd):
            kb.press('v'); kb.release('v')
    else:
        with kb.pressed(Key.ctrl):
            kb.press('v'); kb.release('v')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--list-mics", action="store_true", help="List audio devices and exit")
    parser.add_argument("--model", default=MODEL_NAME)
    parser.add_argument("--mic", type=int, default=None, help="Override MIC_INDEX")
    args = parser.parse_args()

    if args.list_mics:
        list_mics_and_exit()

    global MIC_INDEX
    if args.mic is not None:
        MIC_INDEX = args.mic

    print("Loading Faster-Whisper model…")
    model = WhisperModel(args.model, device=DEVICE, compute_type=COMPUTE_TYPE)

    def on_press(key):
        nonlocal_state = {}
        global recording, last_press_time, last_text, last_release_time
        if key == PTT_KEY:
            now = time.time()
            # Double-tap to resend last transcript (when idle)
            if not recording and (now - last_release_time) <= DOUBLE_TAP_WINDOW and last_text:
                print("Resending last transcript.")
                route_text(last_text)
                return
            if not recording:
                recording = True
                last_press_time = now
                print("Listening… (hold pedal)")

    def on_release(key):
        global recording, last_text, last_release_time
        if key == PTT_KEY:
            now = time.time()
            # Long hold while idle clears memory
            if recording is False:
                if (now - last_press_time) >= LONG_HOLD_CLEAR:
                    last_text = ""
                    print("Cleared last transcript.")
                last_release_time = now
                return

            # Normal case: stop & transcribe
            recording = False
            tmp = Path.cwd() / "whisper_temp.wav"
            path = flush_audio_to_wav(tmp)
            if path is None:
                print("No audio captured.")
                last_release_time = now
                return
            print("Transcribing…")
            t0 = time.time()
            segments, info = model.transcribe(str(path), language=LANGUAGE)
            text = "".join(s.text for s in segments).strip()
            dt = time.time() - t0
            rtf = (info.duration or 0.0001) / dt
            last_text = text
            print(f"{text}")
            print(f"Speed: audio {info.duration:.2f}s, proc {dt:.3f}s, RTF≈{rtf:.2f}×")
            route_text(text)
            last_release_time = now

    print("Ready.\n"
          "- Hold pedal (F13) to speak; release to paste.\n"
          "- Double-tap F13 to resend last transcript.\n"
          "- Long-hold F13 (≥2s) while idle to clear last.\n"
          "Tip: `python pedal_whisper_mac.py --list-mics` to see device indexes.\n")

    with input_stream():
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
