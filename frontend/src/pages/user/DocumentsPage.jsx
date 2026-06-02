import { useState, useEffect } from 'react'
import { Badge, StarPicker, Alert, ProgressBar, SectionHeader } from '../../components/UI'
import { documents, feedback as feedbackApi } from '../../api'

async function downloadWithToken(url, filename) {
  const token = localStorage.getItem('authToken')
  try {
    const res = await fetch(url, { headers: { Authorization: `Token ${token}` } })
    if (!res.ok) throw new Error(`Server returned ${res.status}`)
    const blob = await res.blob()
    const blobUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = blobUrl
    a.download = filename
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(blobUrl)
  } catch (err) {
    alert(`Download failed: ${err.message}`)
  }
}

async function openHtmlWithToken(url) {
  const token = localStorage.getItem('authToken')
  try {
    const res = await fetch(url, { headers: { Authorization: `Token ${token}` } })
    if (!res.ok) throw new Error(`Server returned ${res.status}`)
    const html = await res.text()
    const blob = new Blob([html], { type: 'text/html' })
    window.open(URL.createObjectURL(blob), '_blank')
  } catch (err) {
    alert(`Export failed: ${err.message}`)
  }
}

function DocumentDetail({ doc, onBack }) {
  const [rating, setRating] = useState(0)
  const [fbText, setFbText] = useState('')
  const [fbDone, setFbDone] = useState(false)
  const [fbError, setFbError] = useState('')
  const [regen, setRegen] = useState('default')
  const [regenMsg, setRegenMsg] = useState('')
  const [downloading, setDownloading] = useState(false)

  const handleDownload = async () => {
    setDownloading(true)
    await downloadWithToken(`/api/v1/documents/${doc.id}/download/`, `document_${doc.id}.pdf`)
    setDownloading(false)
  }

  const handleRegenerate = async () => {
    try {
      await documents.regenerate(doc.id, regen)
      setRegenMsg(`Re-generated with "${regen}" style. Download to see updated PDF.`)
    } catch (err) { setRegenMsg(`Error: ${err.message}`) }
  }

  const handleFeedback = async () => {
    try {
      await feedbackApi.submit(doc.id, rating, fbText)
      setFbDone(true)
    } catch (err) { setFbError(err.message) }
  }

  return (
    <div style={{ maxWidth: 660 }}>
      <button className="btn btn-ghost btn-sm" style={{ marginBottom: 20 }} onClick={onBack}>
        ← Back to documents
      </button>
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 20 }}>
          <div>
            <h2 style={{ fontFamily: "'Playfair Display', serif", fontSize: 22, fontWeight: 500, marginBottom: 4 }}>
              {doc.title || `Document #${doc.id}`}
            </h2>
            <div style={{ fontSize: 12.5, color: 'var(--ink-muted)' }}>
              {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : ''} · {doc.style_template} template · {doc.page_count || '—'} pages
            </div>
          </div>
          <Badge status={doc.status} />
        </div>

        {doc.status === 'completed' && (
          <>
            <div className="pdf-preview" style={{ marginBottom: 20 }}>
              <div className="pdf-preview-icon">📄</div>
              <div>PDF Ready</div>
              <div style={{ fontSize: 11, color: 'var(--ink-muted)' }}>{doc.page_count} pages · {doc.style_template} style</div>
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 20 }}>
              <button className="btn btn-amber" onClick={handleDownload} disabled={downloading}>
                {downloading ? 'Downloading…' : '⬇ Download PDF'}
              </button>
              <button className="btn btn-ghost" onClick={() => openHtmlWithToken(`/api/v1/documents/${doc.id}/export/html/`)}>
                ⊙ Export HTML
              </button>
            </div>
            <div style={{ display: 'flex', gap: 8, marginBottom: 4, alignItems: 'center' }}>
              <select className="form-input" style={{ flex: 1 }} value={regen} onChange={e => setRegen(e.target.value)}>
                <option value="default">Default style</option>
                <option value="academic">Academic style</option>
                <option value="notion">Notion-style</option>
                <option value="minimal">Minimal style</option>
              </select>
              <button className="btn btn-ghost" onClick={handleRegenerate}>↺ Re-generate</button>
            </div>
            {regenMsg && <div style={{ fontSize: 12.5, color: 'var(--sage)', marginBottom: 16 }}>{regenMsg}</div>}
            <div className="divider" />
            <div className="section-title" style={{ marginBottom: 14 }}>Leave feedback</div>
            {fbDone ? <Alert type="success">Feedback submitted. Thank you!</Alert> : (
              <>
                {fbError && <Alert type="error">{fbError}</Alert>}
                <StarPicker value={rating} onChange={setRating} />
                <textarea className="form-input" style={{ marginTop: 12, marginBottom: 12 }} placeholder="Share your thoughts on the output quality…" value={fbText} onChange={e => setFbText(e.target.value)} />
                <button className="btn btn-primary btn-sm" disabled={!fbText || !rating} onClick={handleFeedback}>Submit feedback</button>
              </>
            )}
            {doc.raw_ocr_text && (
              <details style={{ marginTop: 20 }}>
                <summary style={{ fontSize: 12.5, color: 'var(--ink-muted)', cursor: 'pointer' }}>View raw OCR text</summary>
                <pre style={{ marginTop: 10, padding: '12px 14px', background: 'var(--paper)', borderRadius: 8, fontSize: 12, lineHeight: 1.7, whiteSpace: 'pre-wrap', color: 'var(--ink-light)', maxHeight: 300, overflowY: 'auto' }}>
                  {doc.raw_ocr_text}
                </pre>
              </details>
            )}
          </>
        )}
        {doc.status === 'processing' && (
          <Alert type="info"><strong>Processing in progress.</strong> OCR Engine 3 is analysing your document. Refresh in a moment.<ProgressBar value={60} /></Alert>
        )}
        {doc.status === 'pending' && (
          <Alert type="info"><strong>Queued.</strong> Waiting for the Celery worker. Make sure Terminal 2 (celery worker) is running.<ProgressBar value={10} /></Alert>
        )}
        {doc.status === 'failed' && (
          <>
            <Alert type="error"><strong>Processing failed.</strong> {doc.error_message || 'An unexpected error occurred.'}</Alert>
            <button className="btn btn-amber btn-sm" onClick={async () => {
              const { ocr } = await import('../../api')
              try { await ocr.trigger(doc.id); alert('OCR re-triggered successfully.') }
              catch (err) { alert(`Could not re-trigger: ${err.message}`) }
            }}>↺ Re-trigger OCR</button>
          </>
        )}
      </div>
    </div>
  )
}

export default function DocumentsPage() {
  const [docs, setDocs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    documents.list()
      .then(data => setDocs(Array.isArray(data) ? data : data.results ?? []))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (selected) return <DocumentDetail doc={selected} onBack={() => setSelected(null)} />
  if (loading) return <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--ink-muted)' }}>Loading documents…</div>
  if (error) return <Alert type="error">Failed to load documents: {error}</Alert>
  if (!docs.length) return (
    <div className="empty-state">
      <div className="empty-state-icon">📂</div>
      <h3>No documents yet</h3>
      <p>Upload a handwritten note to get started.</p>
    </div>
  )

  return (
    <div>
      <SectionHeader title="My Documents" meta={`${docs.length} total`} />
      <div className="doc-grid">
        {docs.map(doc => (
          <div key={doc.id} className="doc-card" onClick={() => setSelected(doc)}>
            <div className="doc-thumb">📝<span className="doc-style-chip">{doc.style_template}</span></div>
            <div className="doc-body">
              <div className="doc-name">{doc.title || `Document #${doc.id}`}</div>
              <div className="doc-meta-row">
                <span className="doc-date">{doc.created_at ? new Date(doc.created_at).toLocaleDateString() : ''}</span>
                <Badge status={doc.status} />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
