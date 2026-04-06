"""
overlay.py
──────────
Draws the HUD overlay on the OpenCV frame:
  - Hand skeleton (landmarks + connections)
  - Gesture label banner
  - Player info panel (track name, progress bar, volume)
  - Gesture reference guide
"""

import cv2
import mediapipe as mp
import numpy as np
import math

mp_drawing = mp.solutions.drawing_utils
mp_hands   = mp.solutions.hands

# ── Colour palette (BGR) ──────────────────────────────────
C_ACCENT  = (0, 255, 220)     # cyan-ish
C_ACCENT2 = (120, 60, 255)    # purple
C_WHITE   = (240, 240, 240)
C_BLACK   = (0, 0, 0)
C_DARK    = (20, 20, 30)
C_GREEN   = (80, 220, 100)
C_YELLOW  = (50, 200, 255)
C_RED     = (80, 80, 255)
C_MUTED   = (100, 100, 120)

FONT      = cv2.FONT_HERSHEY_DUPLEX
FONT_MONO = cv2.FONT_HERSHEY_PLAIN


# ── Main entry ────────────────────────────────────────────

def draw_overlay(frame, gesture_label, player, landmarks, handedness):
    h, w = frame.shape[:2]

    # 1. Hand skeleton
    if landmarks:
        _draw_hand(frame, landmarks, w, h)

    # 2. Gesture banner (bottom centre)
    _draw_gesture_banner(frame, gesture_label, w, h)

    # 3. Player panel (top-left)
    _draw_player_panel(frame, player, w, h)

    # 4. Gesture guide (right side, small)
    _draw_gesture_guide(frame, w, h)

    # 5. Handedness label near wrist
    if landmarks and handedness:
        wx = int(landmarks[0].x * w)
        wy = int(landmarks[0].y * h)
        cv2.putText(frame, handedness, (wx - 20, wy + 22),
                    FONT_MONO, 1.1, C_ACCENT, 1, cv2.LINE_AA)

    return frame


# ── Sections ──────────────────────────────────────────────

def _draw_hand(frame, lm_list, w, h):
    """Draw coloured landmark dots and connection lines."""
    connections = mp_hands.HAND_CONNECTIONS

    # Draw connections first (behind dots)
    for conn in connections:
        a, b = conn
        x1, y1 = int(lm_list[a].x * w), int(lm_list[a].y * h)
        x2, y2 = int(lm_list[b].x * w), int(lm_list[b].y * h)
        cv2.line(frame, (x1, y1), (x2, y2), C_ACCENT, 2, cv2.LINE_AA)

    # Draw landmark circles
    TIPS = {4, 8, 12, 16, 20}
    for i, pt in enumerate(lm_list):
        cx, cy = int(pt.x * w), int(pt.y * h)
        color = C_ACCENT2 if i in TIPS else C_WHITE
        radius = 7 if i in TIPS else 4
        cv2.circle(frame, (cx, cy), radius, color, -1, cv2.LINE_AA)
        cv2.circle(frame, (cx, cy), radius, C_BLACK, 1, cv2.LINE_AA)


def _draw_gesture_banner(frame, label, w, h):
    """Translucent banner at the bottom of the frame."""
    banner_h = 52
    y0 = h - banner_h

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, y0), (w, h), C_DARK, -1)
    cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)

    # Accent line at top of banner
    cv2.line(frame, (0, y0), (w, y0), C_ACCENT, 2)

    text = label.upper()
    (tw, th), _ = cv2.getTextSize(text, FONT, 0.9, 2)
    tx = (w - tw) // 2
    ty = y0 + (banner_h + th) // 2

    # Shadow
    cv2.putText(frame, text, (tx + 2, ty + 2), FONT, 0.9, C_BLACK, 2, cv2.LINE_AA)
    cv2.putText(frame, text, (tx, ty), FONT, 0.9, C_ACCENT, 2, cv2.LINE_AA)


def _draw_player_panel(frame, player, w, h):
    """Player info box in the top-left corner."""
    pw, ph = 320, 110
    margin = 12

    overlay = frame.copy()
    cv2.rectangle(overlay, (margin, margin), (margin + pw, margin + ph), C_DARK, -1)
    cv2.addWeighted(overlay, 0.72, frame, 0.28, 0, frame)
    cv2.rectangle(frame, (margin, margin), (margin + pw, margin + ph), C_ACCENT, 1)

    x0, y0 = margin + 10, margin + 10

    # Track name (truncated)
    name = player.track_name
    if len(name) > 30:
        name = name[:28] + "…"
    cv2.putText(frame, name, (x0, y0 + 14), FONT, 0.48, C_WHITE, 1, cv2.LINE_AA)

    # Track index
    if player.tracks:
        idx_str = f"Track {player.track_idx + 1} / {len(player.tracks)}"
        cv2.putText(frame, idx_str, (x0, y0 + 30), FONT_MONO, 0.85, C_MUTED, 1, cv2.LINE_AA)

    # Progress bar
    bar_x, bar_y = x0, y0 + 44
    bar_w, bar_h = pw - 20, 8
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (50, 50, 60), -1)
    filled = int(bar_w * player.progress)
    if filled > 0:
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + filled, bar_y + bar_h), C_ACCENT, -1)
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), C_MUTED, 1)

    # Time stamps
    elapsed_str  = player.fmt_time(player.elapsed)
    duration_str = player.fmt_time(player.duration)
    cv2.putText(frame, elapsed_str,  (bar_x, bar_y + 22),         FONT_MONO, 0.85, C_MUTED, 1, cv2.LINE_AA)
    cv2.putText(frame, duration_str, (bar_x + bar_w - 30, bar_y + 22), FONT_MONO, 0.85, C_MUTED, 1, cv2.LINE_AA)

    # Volume bar
    vol_x, vol_y = x0, y0 + 80
    vol_w = pw - 20
    cv2.putText(frame, "VOL", (vol_x, vol_y + 8), FONT_MONO, 0.85, C_MUTED, 1, cv2.LINE_AA)
    vb_x = vol_x + 32
    cv2.rectangle(frame, (vb_x, vol_y), (vb_x + vol_w - 32, vol_y + 7), (50, 50, 60), -1)
    vol_fill = int((vol_w - 32) * player.volume)
    col = C_RED if player.muted else C_YELLOW
    if vol_fill > 0:
        cv2.rectangle(frame, (vb_x, vol_y), (vb_x + vol_fill, vol_y + 7), col, -1)

    status = "⏸ PAUSED" if not player.playing else "▶ PLAYING"
    if player.muted:
        status = "🔇 MUTED"
    cv2.putText(frame, status, (vol_x + vol_w - 50, vol_y + 8),
                FONT_MONO, 0.85, C_GREEN if player.playing else C_MUTED, 1, cv2.LINE_AA)


def _draw_gesture_guide(frame, w, h):
    """Small gesture cheat sheet in top-right."""
    guide = [
        ("✋ Palm",   "Play/Pause"),
        ("☝ Up",     "Vol Up"),
        ("↓ Down",   "Vol Down"),
        ("→ Right",  "Next/+10s"),
        ("← Left",   "Prev/-10s"),
        ("✊ Fist",   "Mute"),
    ]

    gw, gh = 190, len(guide) * 18 + 14
    margin = 12
    x0 = w - gw - margin

    overlay = frame.copy()
    cv2.rectangle(overlay, (x0, margin), (x0 + gw, margin + gh), C_DARK, -1)
    cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)
    cv2.rectangle(frame, (x0, margin), (x0 + gw, margin + gh), C_ACCENT, 1)

    cv2.putText(frame, "GESTURES", (x0 + 6, margin + 12),
                FONT_MONO, 0.9, C_ACCENT, 1, cv2.LINE_AA)

    for i, (gesture, action) in enumerate(guide):
        y = margin + 24 + i * 18
        cv2.putText(frame, gesture, (x0 + 6, y),   FONT_MONO, 0.82, C_WHITE, 1, cv2.LINE_AA)
        cv2.putText(frame, action,  (x0 + 90, y),  FONT_MONO, 0.82, C_MUTED, 1, cv2.LINE_AA)