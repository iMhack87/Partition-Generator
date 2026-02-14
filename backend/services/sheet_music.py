"""
Sheet music generation service: MIDI → LilyPond → PDF.
"""
import os
import subprocess
import pretty_midi
import math

# Note name mapping for LilyPond
PITCH_TO_LILY = {
    0: 'c', 1: 'cis', 2: 'd', 3: 'dis', 4: 'e', 5: 'f',
    6: 'fis', 7: 'g', 8: 'gis', 9: 'a', 10: 'ais', 11: 'b',
}

# LilyPond clef per instrument
INSTRUMENT_CLEF = {
    'piano': 'treble',
    'guitare': 'treble',
    'basse': 'bass',
    'violon': 'treble',
    'flute': 'treble',
    'voix': 'treble',
    'saxophone': 'treble',
    'trompette': 'treble',
}

# LilyPond instrument name
INSTRUMENT_DISPLAY = {
    'piano': 'Piano',
    'guitare': 'Guitare',
    'basse': 'Basse',
    'violon': 'Violon',
    'flute': 'Flûte',
    'voix': 'Voix',
    'saxophone': 'Saxophone',
    'trompette': 'Trompette',
}


def midi_note_to_lily(pitch: int) -> str:
    """Convert a MIDI note number to LilyPond pitch notation."""
    note_name = PITCH_TO_LILY[pitch % 12]
    octave = (pitch // 12) - 1  # MIDI octave

    # LilyPond: c' = middle C (MIDI 60, octave 4)
    lily_octave = octave - 3
    if lily_octave > 0:
        note_name += "'" * lily_octave
    elif lily_octave < 0:
        note_name += "," * abs(lily_octave)

    return note_name


def duration_to_lily(duration_beats: float) -> str:
    """Convert a duration in beats to LilyPond duration notation."""
    # Quantize to nearest standard duration
    standard_durations = [
        (4.0, '1'),     # whole note
        (3.0, '2.'),    # dotted half
        (2.0, '2'),     # half note
        (1.5, '4.'),    # dotted quarter
        (1.0, '4'),     # quarter note
        (0.75, '8.'),   # dotted eighth
        (0.5, '8'),     # eighth note
        (0.375, '16.'), # dotted sixteenth
        (0.25, '16'),   # sixteenth note
        (0.125, '32'),  # thirty-second
    ]

    best_match = '4'  # default quarter note
    best_diff = float('inf')

    for beats, lily_dur in standard_durations:
        diff = abs(duration_beats - beats)
        if diff < best_diff:
            best_diff = diff
            best_match = lily_dur

    return best_match


def generate_lilypond(midi_path: str, instrument: str, output_dir: str, title: str = "Transcription") -> dict:
    """
    Generate a LilyPond file and PDF from a MIDI file.

    Args:
        midi_path: Path to the MIDI file.
        instrument: Instrument name.
        output_dir: Directory to save output files.
        title: Title for the sheet music.

    Returns:
        dict with keys: 'ly_path', 'pdf_path'
    """
    os.makedirs(output_dir, exist_ok=True)
    instrument = instrument.lower()

    midi_data = pretty_midi.PrettyMIDI(midi_path)

    # Estimate tempo
    tempo_changes = midi_data.get_tempo_changes()
    if len(tempo_changes[1]) > 0:
        tempo = int(round(tempo_changes[1][0]))
    else:
        tempo = 120

    # Get notes from first instrument
    if not midi_data.instruments or not midi_data.instruments[0].notes:
        raise ValueError("No notes found in MIDI file")

    notes = sorted(midi_data.instruments[0].notes, key=lambda n: n.start)

    # Convert notes to LilyPond notation
    lily_notes = []
    beats_per_second = tempo / 60.0

    for i, note in enumerate(notes):
        # Calculate duration in beats
        duration_seconds = note.end - note.start
        duration_beats = duration_seconds * beats_per_second

        # Clamp minimum duration
        if duration_beats < 0.125:
            duration_beats = 0.125

        lily_pitch = midi_note_to_lily(note.pitch)
        lily_dur = duration_to_lily(duration_beats)

        # Add rest if there's a gap between notes
        if i > 0:
            gap = note.start - notes[i - 1].end
            gap_beats = gap * beats_per_second
            if gap_beats >= 0.125:
                rest_dur = duration_to_lily(gap_beats)
                lily_notes.append(f"r{rest_dur}")

        lily_notes.append(f"{lily_pitch}{lily_dur}")

    # Build LilyPond source
    clef = INSTRUMENT_CLEF.get(instrument, 'treble')
    display_name = INSTRUMENT_DISPLAY.get(instrument, instrument.capitalize())

    # Group notes into measures of 4 beats (approx, for readability)
    notes_per_line = 8
    note_lines = []
    for i in range(0, len(lily_notes), notes_per_line):
        chunk = lily_notes[i:i + notes_per_line]
        note_lines.append("    " + " ".join(chunk))

    notes_block = "\n".join(note_lines)

    ly_content = f'''\\version "2.24.0"

\\header {{
  title = "{title}"
  subtitle = "{display_name}"
  tagline = "Généré par Partition Generator"
}}

\\paper {{
  #(set-paper-size "a4")
}}

\\score {{
  \\new Staff {{
    \\clef {clef}
    \\tempo 4 = {tempo}
    \\time 4/4
{notes_block}
  }}
  \\layout {{ }}
  \\midi {{ }}
}}
'''

    basename = os.path.splitext(os.path.basename(midi_path))[0]
    ly_path = os.path.join(output_dir, f"{basename}.ly")
    pdf_path = os.path.join(output_dir, f"{basename}.pdf")

    # Write .ly file
    with open(ly_path, 'w') as f:
        f.write(ly_content)

    # Compile with LilyPond
    try:
        result = subprocess.run(
            ['lilypond', '-o', os.path.join(output_dir, basename), ly_path],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            print(f"LilyPond warning/error: {result.stderr}")
    except FileNotFoundError:
        raise RuntimeError(
            "LilyPond is not installed. Install it with: brew install lilypond"
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("LilyPond compilation timed out.")

    return {
        'ly_path': ly_path,
        'pdf_path': pdf_path,
    }
