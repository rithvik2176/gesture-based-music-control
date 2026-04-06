import sys
import os
import cv2
import mediapipe as mp
import pygame
import time
import argparse
from pathlib import Path

from gesturedetector import GestureDetector
from musicplayer import MusicPlayer
from overlay import draw_overlay


# CONFIG
CAMERA_INDEX = 0
WINDOW_NAME = "Gesture Music Controller"
FRAME_W, FRAME_H = 960, 540
COOLDOWN_SEC = 0.8


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", help="MP3 file or folder path")
    args = parser.parse_args()

    tracks = []
    if args.path:
        p = Path(args.path)
        if p.is_file():
            tracks = [str(p)]
        elif p.is_dir():
            tracks = [str(f) for f in p.iterdir() if f.suffix in [".mp3", ".wav", ".ogg"]]

    # INIT
    pygame.init()
    pygame.mixer.init()

    player = MusicPlayer(tracks)
    detector = GestureDetector()

    if tracks:
        player.load(0)
        print("[✓] Tracks loaded:", len(tracks))
    else:
        print("[!] No tracks loaded")

    # CAMERA
    cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        print("[ERROR] Camera not working. Trying other index...")

        cap = cv2.VideoCapture(1)
        if not cap.isOpened():
            print("[FATAL] No camera found.")
            sys.exit(1)

    print("[✓] Camera started")
    print("[DEBUG] Running... Press Q to quit")

    last_trigger = 0
    last_gesture = None
    gesture_label = "Show your hand..."

    while True:
        ret, frame = cap.read()

        if not ret:
            print("[ERROR] Frame not received")
            break

        frame = cv2.flip(frame, 1)

        # DETECTION
        gesture, landmarks, handedness = detector.detect(frame)

        if gesture:
            print("[DEBUG] Detected:", gesture)

        now = time.time()
        if gesture and gesture != last_gesture and (now - last_trigger) > COOLDOWN_SEC:
            last_trigger = now
            last_gesture = gesture
            gesture_label = execute_gesture(gesture, player)
            print("[ACTION]", gesture_label)

        elif not gesture:
            last_gesture = None
            gesture_label = "Detecting..."

        # UPDATE PLAYER
        player.update()

        # DRAW
        frame = draw_overlay(frame, gesture_label, player, landmarks, handedness)

        cv2.imshow(WINDOW_NAME, frame)

        key = cv2.waitKey(1) & 0xFF
        if key in [ord('q'), 27]:
            break

    cap.release()
    cv2.destroyAllWindows()
    pygame.quit()

    print("[✓] Closed cleanly")


def execute_gesture(gesture, player):
    if gesture == "open_palm":
        player.toggle_play()
        return "PLAY/PAUSE"

    elif gesture == "index_up":
        player.set_volume(player.volume + 0.1)
        return "VOLUME UP"

    elif gesture == "index_down":
        player.set_volume(player.volume - 0.1)
        return "VOLUME DOWN"

    elif gesture == "point_right":
        player.next_track()
        return "NEXT"

    elif gesture == "point_left":
        player.prev_track()
        return "PREVIOUS"

    elif gesture == "fist":
        player.toggle_mute()
        return "MUTE"

    return gesture


if __name__ == "__main__":
    main()