import { useState } from 'react'
import './YouTubeInput.css'

function YouTubeInput({ value, onChange }) {
    const [isFocused, setIsFocused] = useState(false)

    const isValidUrl = (url) => {
        const pattern = /^(https?:\/\/)?(www\.)?(youtube\.com\/(watch\?v=|shorts\/)|youtu\.be\/)/
        return pattern.test(url)
    }

    const extractThumbnail = (url) => {
        const match = url.match(/(?:youtube\.com\/(?:watch\?v=|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/)
        return match ? `https://img.youtube.com/vi/${match[1]}/mqdefault.jpg` : null
    }

    const thumbnail = value && isValidUrl(value) ? extractThumbnail(value) : null

    return (
        <div className="youtube-input-wrapper glass-card">
            <div className="youtube-input-header">
                <span className="section-icon">🔗</span>
                <h2>Lien YouTube</h2>
            </div>

            <div className={`youtube-input-field ${isFocused ? 'focused' : ''} ${thumbnail ? 'has-preview' : ''}`}>
                <div className="input-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M22.54 6.42a2.78 2.78 0 0 0-1.94-2C18.88 4 12 4 12 4s-6.88 0-8.6.46a2.78 2.78 0 0 0-1.94 2A29 29 0 0 0 1 11.75a29 29 0 0 0 .46 5.33A2.78 2.78 0 0 0 3.4 19.13C5.12 19.56 12 19.56 12 19.56s6.88 0 8.6-.46a2.78 2.78 0 0 0 1.94-2 29 29 0 0 0 .46-5.25 29 29 0 0 0-.46-5.33z" />
                        <polygon points="9.75 15.02 15.5 11.75 9.75 8.48 9.75 15.02" fill="currentColor" />
                    </svg>
                </div>
                <input
                    type="url"
                    className="input-field yt-input"
                    placeholder="https://www.youtube.com/watch?v=..."
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    onFocus={() => setIsFocused(true)}
                    onBlur={() => setIsFocused(false)}
                />
                {value && (
                    <button className="input-clear" onClick={() => onChange('')} title="Effacer">
                        ✕
                    </button>
                )}
            </div>

            {/* Thumbnail preview */}
            {thumbnail && (
                <div className="youtube-preview fade-in-up">
                    <img src={thumbnail} alt="Video thumbnail" />
                    <div className="preview-badge">
                        <span className="badge-dot"></span>
                        Vidéo détectée
                    </div>
                </div>
            )}

            {value && !isValidUrl(value) && (
                <p className="input-hint error">Ce lien ne semble pas être un lien YouTube valide</p>
            )}
        </div>
    )
}

export default YouTubeInput
