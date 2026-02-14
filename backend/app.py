"""
Partition Generator — Flask Backend
Main application with REST API and WebSocket support.
"""
import os
import uuid
import json
import threading
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit

from services.youtube import extract_audio
from services.transcriber import transcribe_audio
from services.sheet_music import generate_lilypond
from services.realtime import RealtimeSession

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TMP_DIR = os.path.join(BASE_DIR, 'tmp')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

os.makedirs(TMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'partition-generator-secret'
CORS(app, origins=['http://localhost:5173', 'http://127.0.0.1:5173'])
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='eventlet')

# In-memory job store
jobs = {}
realtime_sessions = {}


# ─── REST API ──────────────────────────────────────────────────

@app.route('/api/instruments', methods=['GET'])
def get_instruments():
    """Return the list of supported instruments."""
    instruments = [
        {'id': 'piano', 'name': 'Piano', 'icon': '🎹'},
        {'id': 'guitare', 'name': 'Guitare', 'icon': '🎸'},
        {'id': 'basse', 'name': 'Basse', 'icon': '🎸'},
        {'id': 'violon', 'name': 'Violon', 'icon': '🎻'},
        {'id': 'flute', 'name': 'Flûte', 'icon': '🪈'},
        {'id': 'voix', 'name': 'Voix', 'icon': '🎤'},
        {'id': 'saxophone', 'name': 'Saxophone', 'icon': '🎷'},
        {'id': 'trompette', 'name': 'Trompette', 'icon': '🎺'},
    ]
    return jsonify(instruments)


@app.route('/api/transcribe', methods=['POST'])
def start_transcription():
    """Start a new transcription job."""
    data = request.get_json()
    youtube_url = data.get('url')
    instrument = data.get('instrument', 'piano')

    if not youtube_url:
        return jsonify({'error': 'URL YouTube requise'}), 400

    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {
        'id': job_id,
        'status': 'pending',
        'step': 'queued',
        'progress': 0,
        'url': youtube_url,
        'instrument': instrument,
        'title': '',
        'error': None,
        'pdf_path': None,
        'audio_path': None,
        'note_events': None,
        'duration': 0,
    }

    # Run pipeline in background thread
    thread = threading.Thread(target=run_pipeline, args=(job_id,))
    thread.daemon = True
    thread.start()

    return jsonify({'job_id': job_id}), 202


def run_pipeline(job_id: str):
    """Run the full transcription pipeline for a job."""
    job = jobs[job_id]
    job_dir = os.path.join(TMP_DIR, job_id)

    try:
        # Step 1: Download audio
        job['status'] = 'processing'
        job['step'] = 'downloading'
        job['progress'] = 10
        socketio.emit('job_update', job, namespace='/')

        audio_result = extract_audio(job['url'], job_dir)
        job['title'] = audio_result['title']
        job['audio_path'] = audio_result['audio_path']
        job['duration'] = audio_result['duration']
        job['progress'] = 30
        job['step'] = 'downloaded'
        socketio.emit('job_update', job, namespace='/')

        # Step 2: Transcribe to MIDI
        job['step'] = 'transcribing'
        job['progress'] = 40
        socketio.emit('job_update', job, namespace='/')

        transcription = transcribe_audio(
            audio_result['audio_path'],
            job['instrument'],
            job_dir,
        )
        job['note_events'] = transcription['note_events']
        job['progress'] = 70
        job['step'] = 'transcribed'
        socketio.emit('job_update', job, namespace='/')

        # Step 3: Generate sheet music
        job['step'] = 'generating'
        job['progress'] = 80
        socketio.emit('job_update', job, namespace='/')

        output_dir = os.path.join(OUTPUT_DIR, job_id)
        sheet = generate_lilypond(
            transcription['midi_path'],
            job['instrument'],
            output_dir,
            title=job['title'],
        )
        job['pdf_path'] = sheet['pdf_path']
        job['progress'] = 100
        job['step'] = 'complete'
        job['status'] = 'complete'
        socketio.emit('job_update', job, namespace='/')

    except Exception as e:
        job['status'] = 'error'
        job['step'] = 'error'
        job['error'] = str(e)
        socketio.emit('job_update', job, namespace='/')


@app.route('/api/status/<job_id>', methods=['GET'])
def get_status(job_id):
    """Get the status of a transcription job."""
    job = jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    # Return safe subset (no file paths)
    return jsonify({
        'id': job['id'],
        'status': job['status'],
        'step': job['step'],
        'progress': job['progress'],
        'title': job['title'],
        'error': job['error'],
        'note_count': len(job['note_events']) if job['note_events'] else 0,
        'duration': job['duration'],
    })


@app.route('/api/download/<job_id>', methods=['GET'])
def download_pdf(job_id):
    """Download the generated PDF."""
    job = jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    if job['status'] != 'complete' or not job.get('pdf_path'):
        return jsonify({'error': 'PDF not ready'}), 400
    if not os.path.exists(job['pdf_path']):
        return jsonify({'error': 'PDF file not found'}), 404

    return send_file(
        job['pdf_path'],
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"partition_{job['instrument']}_{job_id}.pdf",
    )


@app.route('/api/audio/<job_id>', methods=['GET'])
def stream_audio(job_id):
    """Stream the extracted audio file."""
    job = jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    if not job.get('audio_path') or not os.path.exists(job['audio_path']):
        return jsonify({'error': 'Audio not available'}), 404

    return send_file(
        job['audio_path'],
        mimetype='audio/wav',
    )


@app.route('/api/notes/<job_id>', methods=['GET'])
def get_notes(job_id):
    """Get note events for a completed job."""
    job = jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    if not job.get('note_events'):
        return jsonify({'error': 'Notes not available yet'}), 400

    return jsonify({
        'notes': job['note_events'],
        'duration': job['duration'],
        'title': job['title'],
        'instrument': job['instrument'],
    })


# ─── WebSocket Events ─────────────────────────────────────────

@socketio.on('connect')
def handle_connect():
    print('Client connected')


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


@socketio.on('realtime_start')
def handle_realtime_start(data):
    """Start a real-time listening session."""
    job_id = data.get('job_id')
    job = jobs.get(job_id)
    if not job or not job.get('note_events'):
        emit('error', {'message': 'Job not found or not ready'})
        return

    session = RealtimeSession(job['note_events'], job['duration'])
    realtime_sessions[request.sid] = session
    session.start()
    emit('realtime_state', session.to_state())


@socketio.on('realtime_seek')
def handle_realtime_seek(data):
    """Seek to a position in the real-time session."""
    session = realtime_sessions.get(request.sid)
    if session:
        session.seek(data.get('position', 0))
        emit('realtime_state', session.to_state())


@socketio.on('realtime_pause')
def handle_realtime_pause():
    """Pause the real-time session."""
    session = realtime_sessions.get(request.sid)
    if session:
        session.pause()
        emit('realtime_state', session.to_state())


@socketio.on('realtime_resume')
def handle_realtime_resume():
    """Resume the real-time session."""
    session = realtime_sessions.get(request.sid)
    if session:
        session.start()
        emit('realtime_state', session.to_state())


@socketio.on('realtime_sync')
def handle_realtime_sync(data):
    """Sync position from the frontend audio player."""
    session = realtime_sessions.get(request.sid)
    if session:
        position = data.get('position', 0)
        session.seek(position)
        if data.get('playing', False):
            session.start()
        else:
            session.pause()
        emit('realtime_state', session.to_state())


# ─── Main ─────────────────────────────────────────────────────

if __name__ == '__main__':
    print("🎵 Partition Generator Backend")
    print("   Running on http://localhost:5001")
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
