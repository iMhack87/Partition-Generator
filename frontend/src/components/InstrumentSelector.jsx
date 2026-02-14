import './InstrumentSelector.css'

const INSTRUMENTS = [
    { id: 'piano', name: 'Piano', icon: '🎹' },
    { id: 'guitare', name: 'Guitare', icon: '🎸' },
    { id: 'basse', name: 'Basse', icon: '🎸' },
    { id: 'violon', name: 'Violon', icon: '🎻' },
    { id: 'flute', name: 'Flûte', icon: '🪈' },
    { id: 'voix', name: 'Voix', icon: '🎤' },
    { id: 'saxophone', name: 'Saxophone', icon: '🎷' },
    { id: 'trompette', name: 'Trompette', icon: '🎺' },
]

function InstrumentSelector({ value, onChange }) {
    return (
        <div className="instrument-selector glass-card">
            <div className="instrument-header">
                <span className="section-icon">🎼</span>
                <h2>Instrument</h2>
            </div>

            <div className="instrument-grid">
                {INSTRUMENTS.map((inst) => (
                    <button
                        key={inst.id}
                        className={`instrument-card ${value === inst.id ? 'active' : ''}`}
                        onClick={() => onChange(inst.id)}
                    >
                        <span className="instrument-icon">{inst.icon}</span>
                        <span className="instrument-name">{inst.name}</span>
                        {value === inst.id && <span className="instrument-check">✓</span>}
                    </button>
                ))}
            </div>
        </div>
    )
}

export default InstrumentSelector
