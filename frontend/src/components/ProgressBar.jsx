import './ProgressBar.css'

const STEPS = [
    { key: 'downloading', label: 'Téléchargement audio', icon: '⬇️' },
    { key: 'transcribing', label: 'Transcription musicale', icon: '🎵' },
    { key: 'generating', label: 'Génération partition', icon: '📄' },
]

const STEP_ORDER = ['queued', 'downloading', 'downloaded', 'transcribing', 'transcribed', 'generating', 'complete']

function ProgressBar({ status }) {
    const currentStep = status?.step || 'queued'
    const progress = status?.progress || 0
    const title = status?.title || ''
    const currentStepIndex = STEP_ORDER.indexOf(currentStep)

    const getStepState = (stepKey) => {
        const stepIndex = STEP_ORDER.indexOf(stepKey)
        if (currentStepIndex > stepIndex + 1) return 'done'
        if (stepKey === 'downloading' && ['downloading', 'downloaded'].includes(currentStep)) return 'active'
        if (stepKey === 'transcribing' && ['transcribing', 'transcribed'].includes(currentStep)) return 'active'
        if (stepKey === 'generating' && ['generating', 'complete'].includes(currentStep)) return 'active'
        if (currentStepIndex > stepIndex) return 'done'
        return 'pending'
    }

    return (
        <div className="progress-wrapper glass-card">
            <div className="progress-header">
                <div className="progress-spinner"></div>
                <div>
                    <h2>Traitement en cours...</h2>
                    {title && <p className="progress-title">{title}</p>}
                </div>
            </div>

            {/* Main progress bar */}
            <div className="progress-bar-track">
                <div
                    className="progress-bar-fill"
                    style={{ width: `${progress}%` }}
                ></div>
            </div>
            <p className="progress-percent">{progress}%</p>

            {/* Steps */}
            <div className="progress-steps">
                {STEPS.map((step, index) => {
                    const state = getStepState(step.key)
                    return (
                        <div key={step.key} className={`progress-step ${state}`}>
                            <div className="step-indicator">
                                {state === 'done' ? (
                                    <span className="step-check">✓</span>
                                ) : state === 'active' ? (
                                    <div className="step-spinner-mini"></div>
                                ) : (
                                    <span className="step-number">{index + 1}</span>
                                )}
                            </div>
                            <div className="step-info">
                                <span className="step-icon">{step.icon}</span>
                                <span className="step-label">{step.label}</span>
                            </div>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}

export default ProgressBar
