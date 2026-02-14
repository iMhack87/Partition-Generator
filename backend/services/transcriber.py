"""
Audio-to-MIDI transcription service using basic-pitch (Spotify).
"""
import os
from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH
import pretty_midi
import numpy as np

# Instrument MIDI program mapping
INSTRUMENT_PROGRAMS = {
    'piano': 0,       # Acoustic Grand Piano
    'guitare': 25,    # Acoustic Guitar (steel)
    'basse': 33,      # Electric Bass (finger)
    'violon': 40,     # Violin
    'flute': 73,      # Flute
    'voix': 52,       # Choir Aahs
    'saxophone': 65,  # Alto Sax
    'trompette': 56,  # Trumpet
}

# Pitch ranges per instrument (MIDI note numbers)
INSTRUMENT_RANGES = {
    'piano': (21, 108),
    'guitare': (40, 88),
    'basse': (28, 60),
    'violon': (55, 103),
    'flute': (60, 96),
    'voix': (48, 84),
    'saxophone': (49, 80),
    'trompette': (55, 82),
}


def transcribe_audio(audio_path: str, instrument: str, output_dir: str) -> dict:
    """
    Transcribe an audio file to MIDI using basic-pitch.

    Args:
        audio_path: Path to the WAV audio file.
        instrument: Instrument name (e.g. 'piano', 'guitare').
        output_dir: Directory to save the MIDI file.

    Returns:
        dict with keys: 'midi_path', 'note_events'
    """
    os.makedirs(output_dir, exist_ok=True)
    instrument = instrument.lower()

    # Run basic-pitch inference
    model_output, midi_data, note_events = predict(audio_path)

    # Filter notes by instrument range
    pitch_range = INSTRUMENT_RANGES.get(instrument, (0, 127))
    filtered_midi = pretty_midi.PrettyMIDI()

    program = INSTRUMENT_PROGRAMS.get(instrument, 0)
    inst = pretty_midi.Instrument(program=program, name=instrument.capitalize())

    for midi_instrument in midi_data.instruments:
        for note in midi_instrument.notes:
            if pitch_range[0] <= note.pitch <= pitch_range[1]:
                inst.notes.append(
                    pretty_midi.Note(
                        velocity=note.velocity,
                        pitch=note.pitch,
                        start=note.start,
                        end=note.end,
                    )
                )

    filtered_midi.instruments.append(inst)

    # Save MIDI
    basename = os.path.splitext(os.path.basename(audio_path))[0]
    midi_path = os.path.join(output_dir, f"{basename}_{instrument}.mid")
    filtered_midi.write(midi_path)

    # Build note events list for frontend
    note_events_list = []
    for note in inst.notes:
        note_events_list.append({
            'start': float(round(note.start, 3)),
            'end': float(round(note.end, 3)),
            'pitch': int(note.pitch),
            'velocity': int(note.velocity),
            'name': str(pretty_midi.note_number_to_name(note.pitch)),
        })

    note_events_list.sort(key=lambda n: n['start'])

    return {
        'midi_path': midi_path,
        'note_events': note_events_list,
        'note_count': len(note_events_list),
    }
