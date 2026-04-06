"""
gesture_detector.py
───────────────────
Uses MediaPipe Hands to detect hand landmarks and classify gestures.

Classified gestures:
  open_palm    - All 4 fingers extended upward
  fist         - All 4 fingers curled down
  index_up     - Only index finger up, pointing upward
  index_down   - Only index finger up, pointing downward
  point_right  - Only index finger extended, pointing right
  point_left   - Only index finger extended, pointing left
"""

import cv2
import mediapipe as mp
import math


class GestureDetector:
    # Finger tip and pip (second joint) landmark indices
    FINGER_TIPS = [8, 12, 16, 20]   # index, middle, ring, pinky
    FINGER_PIPS = [6, 10, 14, 18]

    def __init__(self, max_hands=1, detection_conf=0.75, tracking_conf=0.65):
        self.mp_hands   = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_styles  = mp.solutions.drawing_styles

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=detection_conf,
            min_tracking_confidence=tracking_conf,
        )

    def detect(self, frame_bgr):
        """
        Run detection on a BGR frame (already flipped by caller).
        Returns:
            gesture    (str | None)
            landmarks  (list of normalized landmarks | None)
            handedness (str | None) — 'Left' or 'Right'
        """
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = self.hands.process(rgb)

        if not results.multi_hand_landmarks:
            return None, None, None

        lm_list    = results.multi_hand_landmarks[0].landmark
        handedness = results.multi_handedness[0].classification[0].label  # 'Left'/'Right'

        gesture = self._classify(lm_list)
        return gesture, lm_list, handedness

    # ── Private ───────────────────────────────────────────

    def _classify(self, lm):
        fingers_up = self._fingers_up(lm)
        count      = sum(fingers_up)           # 0 = fist, 4 = open palm

        # Open palm — all 4 non-thumb fingers extended
        if count == 4:
            return "open_palm"

        # Fist — all fingers curled
        if count == 0:
            return "fist"

        # Only index finger extended
        if fingers_up == [True, False, False, False]:
            return self._index_direction(lm)

        return None

    def _fingers_up(self, lm):
        """Return [bool x4] — True if each finger (index→pinky) is extended."""
        result = []
        for tip, pip in zip(self.FINGER_TIPS, self.FINGER_PIPS):
            result.append(lm[tip].y < lm[pip].y)   # tip higher (smaller y) than pip
        return result

    def _index_direction(self, lm):
        """Determine direction the index finger is pointing."""
        tip = lm[8]
        mcp = lm[5]   # knuckle base

        dx = tip.x - mcp.x   # positive = right in mirrored frame
        dy = tip.y - mcp.y   # positive = down

        adx = abs(dx)
        ady = abs(dy)

        # Need a minimum movement to avoid noise
        magnitude = math.hypot(dx, dy)
        if magnitude < 0.05:
            return None

        if adx > ady * 0.8:          # Mostly horizontal
            return "point_right" if dx > 0 else "point_left"
        else:                         # Mostly vertical
            return "index_up" if dy < 0 else "index_down"