import { useState, useEffect, useRef } from 'react'
import './RealtimeListener.css'

const API_URL = 'http://localhost:5001/api'

function RealtimeListener({ jobId, socket }) {
    const [notes, setNotes] = useState([])
    const [duration, setDuration] = useState(0)
    const [isPlaying, setIsPlaying] = useState(false)
    const [currentTime, setCurrentTime] = useState(0)
    const [activeNotes, setActiveNotes] = useState([])
    const [playbackRate, setPlaybackRate] = useState(1)
    const audioRef = useRef(null)
    const animFrameRef = useRef(null)
    const notesContainerRef = useRef(null)

    // Fetch notes on mount
    useEffect(() => {
        fetch(`${API_URL}/notes/${jobId}`)
            .then((res) => res.json())
            .then((data) => {
                setNotes(data.notes || [])
                setDuration(data.duration || 0)
            })
            .catch(console.error)
    }, [jobId])

    // Animation loop for syncing notes
    useEffect(() => {
        const updateActiveNotes = () => {
            if (audioRef.current && isPlaying) {
                const time = audioRef.current.currentTime
                setCurrentTime(time)

                const active = notes.filter(
                    (note) => note.start <= time && note.end >= time
                )
                setActiveNotes(active)

                // Sync with backend via WebSocket
                socket.emit('realtime_sync', {
                    position: time,
                    playing: true,
                })
            }
            animFrameRef.current = requestAnimationFrame(updateActiveNotes)
        }

        if (isPlaying) {
            animFrameRef.current = requestAnimationFrame(updateActiveNotes)
        }

        return () => {
            if (animFrameRef.current) {
                cancelAnimationFrame(animFrameRef.current)
            }
        }
    }, [isPlaying, notes, socket])

    // Auto-scroll to active notes
    useEffect(() => {
        if (activeNotes.length > 0 && notesContainerRef.current) {
            const activeEl = notesContainerRef.current.querySelector('.note-item.active')
            if (activeEl) {
                activeEl.scrollIntoView({ behavior: 'smooth', block: 'center' })
            }
        }
    }, [activeNotes])

    const togglePlay = () => {
        if (!audioRef.current) return

        if (isPlaying) {
            audioRef.current.pause()
            setIsPlaying(false)
            socket.emit('realtime_pause')
        } else {
            audioRef.current.play()
            setIsPlaying(true)
            socket.emit('realtime_start', { job_id: jobId })
        }
    }

    const handleSeek = (e) => {
        const time = parseFloat(e.target.value)
        if (audioRef.current) {
            audioRef.current.currentTime = time
            setCurrentTime(time)
        }
    }

    const handleRateChange = (rate) => {
        setPlaybackRate(rate)
        if (audioRef.current) {
            audioRef.current.playbackRate = rate
        }
    }

    const formatTime = (seconds) => {
        const m = Math.floor(seconds / 60)
        const s = Math.floor(seconds % 60)
        return `${m}:${s.toString().padStart(2, '0')}`
    }

    const isNoteActive = (note) => {
        return activeNotes.some(
            (a) => a.start === note.start && a.pitch === note.pitch
        )
    }

    const isNotePast = (note) => {
        return note.end < currentTime
    }

    return (
        <div className="realtime-listener glass-card">
            <div className="realtime-header">
                <span className="section-icon">🎧</span>
                <h2>Écoute en temps réel</h2>
            </div>

            {/* Audio player */}
            <audio
                ref={audioRef}
                src={`${API_URL}/audio/${jobId}`}
                preload="auto"
                onEnded={() => setIsPlaying(false)}
            />

            <div className="audio-controls">
                <button
                    className={`play-btn ${isPlaying ? 'playing' : ''}`}
                    onClick={togglePlay}
                >
                    {isPlaying ? (
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                            <rect x="6" y="4" width="4" height="16" rx="1" />
                            <rect x="14" y="4" width="4" height="16" rx="1" />
                        </svg>
                    ) : (
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                            <polygon points="5,3 19,12 5,21" />
                        </svg>
                    )}
                </button>

                <span className="time-display">{formatTime(currentTime)}</span>

                <input
                    type="range"
                    className="seek-slider"
                    min="0"
                    max={duration || 100}
                    step="0.1"
                    value={currentTime}
                    onChange={handleSeek}
                />

                <span className="time-display">{formatTime(duration)}</span>

                {/* Playback speed */}
                <div className="speed-controls">
                    {[0.5, 0.75, 1, 1.25, 1.5].map((rate) => (
                        <button
                            key={rate}
                            className={`speed-btn ${playbackRate === rate ? 'active' : ''}`}
                            onClick={() => handleRateChange(rate)}
                        >
                            {rate}x
                        </button>
                    ))}
                </div>
            </div>

            {/* Notes timeline */}
            <div className="notes-timeline" ref={notesContainerRef}>
                <div className="notes-header-row">
                    <span className="notes-col-time">Temps</span>
                    <span className="notes-col-note">Note</span>
                    <span className="notes-col-dur">Durée</span>
                </div>
                <div className="notes-list">
                    {notes.slice(0, 200).map((note, i) => (
                        <div
                            key={i}
                            className={`note-item ${isNoteActive(note) ? 'active' : ''} ${isNotePast(note) ? 'past' : ''}`}
                        >
                            <span className="note-time">{formatTime(note.start)}</span>
                            <span className="note-name">{note.name}</span>
                            <span className="note-duration">
                                {Math.round((note.end - note.start) * 1000)}ms
                            </span>
                        </div>
                    ))}
                    {notes.length > 200 && (
                        <p className="notes-truncated">
                            + {notes.length - 200} notes supplémentaires
                        </p>
                    )}
                </div>
            </div>
        </div>
    )
}

export default RealtimeListener
