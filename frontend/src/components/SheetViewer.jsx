import { useState, useEffect } from 'react'
import './SheetViewer.css'

const API_URL = 'http://localhost:5001/api'

function SheetViewer({ jobId, title }) {
    const [pdfUrl, setPdfUrl] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        if (jobId) {
            setPdfUrl(`${API_URL}/download/${jobId}`)
            setLoading(false)
        }
    }, [jobId])

    const handleDownload = () => {
        const link = document.createElement('a')
        link.href = pdfUrl
        link.download = `partition_${jobId}.pdf`
        link.click()
    }

    return (
        <div className="sheet-viewer glass-card">
            <div className="sheet-header">
                <div className="sheet-header-left">
                    <span className="section-icon">📄</span>
                    <div>
                        <h2>Partition générée</h2>
                        {title && <p className="sheet-title">{title}</p>}
                    </div>
                </div>
                <div className="sheet-actions">
                    <button className="btn btn-primary btn-sm" onClick={handleDownload}>
                        ⬇️ Télécharger PDF
                    </button>
                </div>
            </div>

            <div className="sheet-content">
                {loading ? (
                    <div className="sheet-loading">
                        <div className="progress-spinner"></div>
                        <p>Chargement de la partition...</p>
                    </div>
                ) : (
                    <div className="pdf-embed-wrapper">
                        <object
                            data={pdfUrl}
                            type="application/pdf"
                            className="pdf-embed"
                        >
                            <div className="pdf-fallback">
                                <p>Impossible d'afficher le PDF dans le navigateur.</p>
                                <button className="btn btn-secondary" onClick={handleDownload}>
                                    Télécharger le PDF
                                </button>
                            </div>
                        </object>
                    </div>
                )}
            </div>
        </div>
    )
}

export default SheetViewer
