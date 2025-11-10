# 🎙️ Whisper Pedal for macOS  
### Local push-to-talk transcription with Faster-Whisper + USB foot pedal

This project turns any USB foot pedal (mapped to **F13**) into a local, privacy-preserving **push-to-talk voice-to-text system** using [Faster-Whisper](https://github.com/guillaumekln/faster-whisper).

---

## ✨ Features
- **Hold pedal → record → release → transcribe → paste**
- Ultra-low latency (sub-second with the *tiny* model)
- Works entirely offline on Apple Silicon (Metal backend)
- Double-tap pedal to re-paste the last transcript
- Long-hold (≥ 2 s) while idle to clear last transcript
- Works in any focused text field or app
- Optional OSC / HTTP routing (disabled by default)
- Tested on macOS (M2 / M3) with a Rode PodMic USB

---

## 🧩 Requirements
| Component | Purpose |
|------------|----------|
| macOS 12 + | Host system |
| Python 3.9 + | Interpreter |
| `faster-whisper` | Transcription backend |
| `sounddevice` | Microphone capture |
| `pynput`, `pyperclip` | Pedal + paste control |
| **Karabiner-Elements** | Map pedal key to F13 |

---

## ⚙️ Installation
```bash
# 1.  Create venv
python3 -m venv ~/fw-venv
source ~/fw-venv/bin/activate

# 2.  Install deps
pip install --upgrade pip
pip install faster-whisper sounddevice pynput pyperclip python-osc requests
```

---

## 🎛️ Hardware setup
1. Plug in your USB pedal.  
2. Open **Karabiner-Elements → Devices** → enable *Modify events from this device*.  
3. In **Simple Modifications**, map the pedal’s key (e.g. `b`) → `f13`.  
4. Verify in **Karabiner EventViewer** you see  
   ```
   {"key_code":"f13"}
   ```

---

## 🎤 Microphone setup
List available inputs:
```bash
python -c "import sounddevice as sd; print(sd.query_devices())"
```
Find your **Rode PodMic USB** index (e.g. 1) and edit in `pedal_whisper_mac.py`:
```python
MIC_INDEX   = 1
SAMPLE_RATE = 48000
```
Faster-Whisper will down-sample automatically—no loss or issue.

---

## ▶️ Usage
Activate venv, then run:
```bash
python pedal_whisper_mac.py
```

### Controls
| Action | Result |
|---------|---------|
| **Hold F13** | Start recording |
| **Release F13** | Stop + transcribe + paste |
| **Double-tap F13** | Re-paste last transcript |
| **Long-hold F13 (≥ 2 s)** | Clear last transcript |

Focus any editable field (Notes, browser, text editor) and speak.

---

## 🚀 Performance guide
| Model | Accuracy | Speed (M2) | Typical use |
|--------|-----------|-------------|--------------|
| `tiny` | lower | ~4 × real-time | instant notes |
| `base` | good | ~2 × real-time | quick drafts |
| `small` | very good | ≈ 1 × real-time | balanced |
| `medium` | high | < real-time | precise dictation |

Change the line:
```python
MODEL_NAME = "small"
```

---

## 🧠 Security & permissions
macOS → **Privacy & Security**
- **Microphone** → allow your terminal or IDE  
- **Accessibility** → allow terminal (for pedal/paste control)  
- **Input Monitoring** → allow terminal (for `pynput`)

---

## 🔧 Troubleshooting
| Symptom | Fix |
|----------|-----|
| `objc_msgSendSuper_stret` error | remove `pyautogui`, use pynput-based paste (already patched) |
| Pedal types text (`^[[25~`) | Accessibility permission missing for terminal |
| No sound recorded | check `MIC_INDEX` and `SAMPLE_RATE`; verify with `sd.query_devices()` |
| Slow transcription | switch to `base` or `tiny` model |
| Permission denied cache error | `sudo chown -R $USER ~/.cache/huggingface` |

---

## 🧰 Optional extensions
- OSC output → route to Max/MSP or SuperCollider  
- HTTP POST → forward transcript to a local LLM (e.g. Ollama)  
- LaunchAgent plist → auto-start on login (contact me if you want the example)

---

## 📄 License
MIT License – Use and modify freely.  
Created 2025 by Sebastian Tomczak + ChatGPT (GPT-5).
