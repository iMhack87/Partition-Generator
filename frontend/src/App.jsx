import { useState, useEffect, useCallback } from 'react'
import './App.css'
import YouTubeInput from './components/YouTubeInput'
import InstrumentSelector from './components/InstrumentSelector'
import ProgressBar from './components/ProgressBar'
import SheetViewer from './components/SheetViewer'
import RealtimeListener from './components/RealtimeListener'
import { io } from 'socket.io-client'

const API_URL = 'http://localhost:5001/api'
const socket = io('http://localhost:5001', { autoConnect: false })

function App() {
  const [step, setStep] = useState('input') // input | processing | result
  const [youtubeUrl, setYoutubeUrl] = useState('')
  const [instrument, setInstrument] = useState('piano')
  const [jobId, setJobId] = useState(null)
  const [jobStatus, setJobStatus] = useState(null)
  const [error, setError] = useState(null)

  // Connect socket on mount
  useEffect(() => {
    socket.connect()

    socket.on('job_update', (data) => {
      if (data.id === jobId || !jobId) {
        setJobStatus(data)
        if (data.status === 'complete') {
          setStep('result')
        }
        if (data.status === 'error') {
          setError(data.error)
        }
      }
    })

    return () => {
      socket.off('job_update')
      socket.disconnect()
    }
  }, [jobId])

  const handleGenerate = useCallback(async () => {
    setError(null)
    setStep('processing')

    try {
      const res = await fetch(`${API_URL}/transcribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: youtubeUrl, instrument }),
      })

      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData.error || 'Erreur lors de la requête')
      }

      const data = await res.json()
      setJobId(data.job_id)
    } catch (err) {
      setError(err.message)
      setStep('input')
    }
  }, [youtubeUrl, instrument])

  const handleReset = () => {
    setStep('input')
    setYoutubeUrl('')
    setInstrument('piano')
    setJobId(null)
    setJobStatus(null)
    setError(null)
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="container">
          <div className="logo" onClick={handleReset}>
            <span className="logo-icon">🎵</span>
            <h1>Partition Generator</h1>
          </div>
          <p className="subtitle">Générez des partitions à partir de vidéos YouTube</p>
        </div>
      </header>

      {/* Main */}
      <main className="app-main">
        <div className="container">

          {/* Error display */}
          {error && (
            <div className="error-banner fade-in-up">
              <span className="error-icon">⚠️</span>
              <p>{error}</p>
              <button className="error-close" onClick={() => setError(null)}>✕</button>
            </div>
          )}

          {/* Step: Input */}
          {step === 'input' && (
            <div className="input-section fade-in-up">
              <YouTubeInput value={youtubeUrl} onChange={setYoutubeUrl} />
              <InstrumentSelector value={instrument} onChange={setInstrument} />
              <div className="generate-section">
                <button
                  className="btn btn-primary btn-generate"
                  onClick={handleGenerate}
                  disabled={!youtubeUrl.trim()}
                >
                  <span className="btn-icon">✨</span>
                  Générer la partition
                </button>
              </div>
            </div>
          )}

          {/* Step: Processing */}
          {step === 'processing' && (
            <div className="processing-section fade-in-up">
              <ProgressBar status={jobStatus} />
            </div>
          )}

          {/* Step: Result */}
          {step === 'result' && jobId && (
            <div className="result-section fade-in-up">
              <SheetViewer jobId={jobId} title={jobStatus?.title} />
              <RealtimeListener jobId={jobId} socket={socket} />
              <div className="result-actions">
                <button className="btn btn-secondary" onClick={handleReset}>
                  ← Nouvelle partition
                </button>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <div className="container">
          <p>Partition Generator — Propulsé par basic-pitch & LilyPond</p>
        </div>
      </footer>
    </div>
  )
}

export default App
