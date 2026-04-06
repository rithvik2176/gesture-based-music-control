"""
music_player.py
───────────────
Wraps pygame.mixer to provide track management, volume, seek, and state.
"""

import os
import time
import pygame


class MusicPlayer:
    def __init__(self, tracks: list):
        self.tracks    = tracks        # list of file paths
        self.track_idx = 0
        self.playing   = False
        self.muted     = False
        self.volume    = 0.7
        self._pre_mute_vol = 0.7

        # Elapsed tracking (pygame doesn't expose position for mp3 easily)
        self._start_time   = 0.0
        self._elapsed_base = 0.0      # seconds accumulated before pause
        self._duration     = 0.0

        pygame.mixer.music.set_volume(self.volume)

    # ── Public API ────────────────────────────────────────

    def load(self, idx: int):
        if not self.tracks:
            return
        self.track_idx = idx % len(self.tracks)
        path = self.tracks[self.track_idx]
        try:
            pygame.mixer.music.load(path)
            self._duration     = self._get_duration(path)
            self._elapsed_base = 0.0
            self._start_time   = 0.0
            self.playing       = False
            print(f"[Player] Loaded: {os.path.basename(path)}")
        except Exception as e:
            print(f"[Player] Error loading {path}: {e}")

    def play(self):
        if not self.tracks:
            return
        pygame.mixer.music.play()
        self._start_time = time.time()
        self.playing = True

    def pause(self):
        pygame.mixer.music.pause()
        self._elapsed_base += time.time() - self._start_time
        self.playing = False

    def toggle_play(self):
        if not self.tracks:
            print("[Player] No tracks loaded")
            return
        if self.playing:
            self.pause()
        else:
            if self._elapsed_base > 0:
                pygame.mixer.music.unpause()
                self._start_time = time.time()
                self.playing = True
            else:
                self.play()

    def next_track(self):
        if not self.tracks:
            return
        self.load((self.track_idx + 1) % len(self.tracks))
        self.play()

    def prev_track(self):
        if not self.tracks:
            return
        # If past 3s, restart current; else go back
        if self.elapsed > 3:
            self.load(self.track_idx)
        else:
            self.load((self.track_idx - 1) % len(self.tracks))
        self.play()

    def seek(self, seconds: float):
        """Seek relative to current position (positive or negative)."""
        if not self.tracks:
            return
        new_pos = max(0.0, min(self._duration or 999, self.elapsed + seconds))
        try:
            pygame.mixer.music.play(start=new_pos)
            self._elapsed_base = new_pos
            self._start_time   = time.time()
            if not self.playing:
                pygame.mixer.music.pause()
        except Exception as e:
            print(f"[Player] Seek error: {e}")

    def set_volume(self, v: float):
        self.volume = max(0.0, min(1.0, v))
        if not self.muted:
            pygame.mixer.music.set_volume(self.volume)
        self._pre_mute_vol = self.volume

    def toggle_mute(self):
        if self.muted:
            self.muted = False
            pygame.mixer.music.set_volume(self._pre_mute_vol)
            self.volume = self._pre_mute_vol
        else:
            self._pre_mute_vol = self.volume
            self.muted  = True
            pygame.mixer.music.set_volume(0.0)

    def update(self):
        """Call once per frame to detect natural track end."""
        if self.playing and not pygame.mixer.music.get_busy():
            # Track finished naturally
            if len(self.tracks) > 1:
                self.next_track()
            else:
                self.playing = False
                self._elapsed_base = 0.0

    # ── Properties ────────────────────────────────────────

    @property
    def elapsed(self) -> float:
        if self.playing:
            return self._elapsed_base + (time.time() - self._start_time)
        return self._elapsed_base

    @property
    def duration(self) -> float:
        return self._duration

    @property
    def track_name(self) -> str:
        if not self.tracks:
            return "No track loaded"
        return os.path.basename(self.tracks[self.track_idx])

    @property
    def progress(self) -> float:
        """0.0 – 1.0"""
        if not self._duration:
            return 0.0
        return min(1.0, self.elapsed / self._duration)

    # ── Helpers ───────────────────────────────────────────

    @staticmethod
    def _get_duration(path: str) -> float:
        """Get audio duration in seconds using pygame Sound (works for most formats)."""
        try:
            sound = pygame.mixer.Sound(path)
            return sound.get_length()
        except Exception:
            return 0.0

    @staticmethod
    def fmt_time(seconds: float) -> str:
        s = int(seconds)
        m, s = divmod(s, 60)
        return f"{m}:{s:02d}"