"""
Real-time listening service.
Streams note events over WebSocket for synchronized partition playback.
"""
import time


class RealtimeSession:
    """Manages a real-time listening session."""

    def __init__(self, note_events: list, audio_duration: float):
        """
        Args:
            note_events: List of note dicts with 'start', 'end', 'pitch', 'name'.
            audio_duration: Total audio duration in seconds.
        """
        self.note_events = sorted(note_events, key=lambda n: n['start'])
        self.audio_duration = audio_duration
        self.current_index = 0
        self.is_playing = False
        self.start_time = 0
        self.pause_offset = 0

    def start(self):
        """Start or resume playback."""
        self.is_playing = True
        self.start_time = time.time() - self.pause_offset

    def pause(self):
        """Pause playback."""
        if self.is_playing:
            self.pause_offset = time.time() - self.start_time
            self.is_playing = False

    def seek(self, position: float):
        """Seek to a specific position in seconds."""
        self.pause_offset = position
        if self.is_playing:
            self.start_time = time.time() - position
        # Reset index to find the right note
        self.current_index = 0
        for i, note in enumerate(self.note_events):
            if note['start'] > position:
                break
            self.current_index = i

    def get_current_position(self) -> float:
        """Get the current playback position in seconds."""
        if self.is_playing:
            return time.time() - self.start_time
        return self.pause_offset

    def get_active_notes(self) -> list:
        """Get notes that are currently active at the current position."""
        pos = self.get_current_position()
        active = []
        for note in self.note_events:
            if note['start'] <= pos <= note['end']:
                active.append(note)
            elif note['start'] > pos:
                break
        return active

    def get_upcoming_notes(self, window: float = 2.0) -> list:
        """Get notes coming up in the next `window` seconds."""
        pos = self.get_current_position()
        upcoming = []
        for note in self.note_events:
            if pos < note['start'] <= pos + window:
                upcoming.append(note)
            elif note['start'] > pos + window:
                break
        return upcoming

    def to_state(self) -> dict:
        """Serialize the session state for WebSocket."""
        pos = self.get_current_position()
        return {
            'position': round(pos, 3),
            'is_playing': self.is_playing,
            'active_notes': self.get_active_notes(),
            'upcoming_notes': self.get_upcoming_notes(),
            'progress': round(pos / self.audio_duration, 4) if self.audio_duration > 0 else 0,
        }
