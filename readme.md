# 🎵 Gesture Music Controller
### Human-Computer Interaction Project
Control MP3 playback using hand gestures detected via webcam.
Built with Python · OpenCV · MediaPipe · pygame

---

## 📁 Project Structure

```
gesture_music/
├── main.py              ← Entry point — run this
├── gesture_detector.py  ← MediaPipe hand tracking & gesture classification
├── music_player.py      ← pygame-based audio player with state management
├── overlay.py           ← OpenCV HUD drawing (skeleton, panels, guide)
├── requirements.txt     ← Python dependencies
└── README.md
```

---

## ⚙️ Setup

### 1. Install Python 3.9+
Download from https://python.org

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run
```bash
# Interactive file picker
python main.py

# Load one MP3 directly
python main.py mysong.mp3

# Load an entire folder
python main.py music/
```

---

## 🖐 Gesture Reference

| Gesture | Action |
|---|---|
| ✋ Open Palm (all fingers up) | Play / Pause |
| ☝ Index finger pointing UP | Volume Up (+10%) |
| 👇 Index finger pointing DOWN | Volume Down (-10%) |
| 👉 Index finger pointing RIGHT | Next track OR Skip +10s |
| 👈 Index finger pointing LEFT | Prev track OR Skip -10s |
| ✊ Fist (all fingers down) | Mute / Unmute |

---

## ⌨️ Keyboard Fallbacks

| Key | Action |
|---|---|
| Space | Play / Pause |
| + / = | Volume Up |
| - | Volume Down |
| Q / ESC | Quit |

---

## 💡 Tips for Best Gesture Detection

- Use in **good lighting** (face your light source)
- Keep your hand **clearly visible** against the background
- Hold gestures **steady for ~0.5s** before switching
- Stay **50–80cm** from the camera
- A **plain/dark background** improves accuracy

---

## 🔧 Configuration (main.py top)

```python
CAMERA_INDEX  = 0      # Change if using external camera
COOLDOWN_SEC  = 0.8    # Seconds between gesture triggers
```

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `opencv-python` | Webcam capture + frame drawing |
| `mediapipe` | Hand landmark detection (21 points) |
| `pygame` | Audio playback engine |

---



This project demonstrates **gesture-based natural user interfaces (NUI)**,
a key HCI paradigm that allows hands-free, touchless interaction.

The system pipeline:
```
Webcam → Frame Capture → MediaPipe Hand Tracking →
Landmark Analysis → Gesture Classification →
Music Control Action → Visual Feedback
```

Gesture classification uses rule-based landmark geometry:
- Finger extension: tip.y < pip.y (tip is higher than second joint)
- Direction: vector from MCP (knuckle) to tip landmark