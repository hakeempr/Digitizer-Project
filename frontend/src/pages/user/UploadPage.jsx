import { useState, useRef } from 'react'
import { Alert, ProgressBar } from '../../components/UI'

const STYLES = [
  { value: 'default',  label: 'Default — Clean general purpose' },
  { value: 'academic', label: 'Academic — Times Roman, double-spaced' },
  { value: 'notion',   label: 'Notion-style — Modern sans-serif' },
  { value: 'minimal',  label: 'Minimal — Compact monospace' },
]

export default function UploadPage({ setPage }) {
  const [drag,      setDrag]      = useState(false)
  const [file,      setFile]      = useState(null)
  const [title,     setTitle]     = useState('')
  const [style,     setStyle]     = useState('default')
  const [uploading, setUploading] = useState(false)
  const [progress,  setProgress]  = useState(0)
  const [stage,     setStage]     = useState('')   // current pipeline stage text
  const [result,    setResult]    = useState(null) // { status, document_id, message }
  const [error,     setError]     = useState('')
  const inputRef = useRef()

  const pickFile = f => {
    if (!f) return
    const ext = f.name.split('.').pop().toLowerCase()
    if (!['jpg','jpeg','png','pdf','tif','tiff','bmp'].includes(ext)) {
      setError(`File type .${ext} is not supported.`); return
    }
    if (f.size > 10 * 1024 * 1024) {
      setError('File exceeds the 10 MB limit.'); return
    }
    setError('')
    setFile(f)

    // Auto-fill title from filename — but skip UUID/hash filenames
    // Django storage renames files to random hashes like "a3f8b2c1..."
    const nameWithoutExt = f.name.replace(/\.[^.]+$/, '')
    const isUUID = /^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$/i.test(nameWithoutExt)
    const isHexHash = nameWithoutExt.length >= 20 && /^[0-9a-f]+$/i.test(nameWithoutExt.replace(/[-_]/g,''))
    if (!isUUID && !isHexHash) {
      const cleanName = nameWithoutExt
        .replace(/[_-]/g, ' ')
        .replace(/\b\w/g, c => c.toUpperCase())
      setTitle(cleanName)
    } else {
      setTitle('') // let user enter a proper title
    }
  }

  const handleUpload = async () => {
    if (!file || !title.trim()) return

    setUploading(true)
    setError('')
    setResult(null)
    setProgress(5)
    setStage('Uploading file…')

    // Animate progress while waiting for server
    const stages = [
      { pct: 15, msg: 'Uploading file…' },
      { pct: 30, msg: 'Pre-processing image (OpenCV)…' },
      { pct: 50, msg: 'Running OCR Engine 3…' },
      { pct: 75, msg: 'Analysing document layout…' },
      { pct: 88, msg: 'Generating PDF…' },
    ]
    let stageIdx = 0
    const iv = setInterval(() => {
      if (stageIdx < stages.length) {
        setProgress(stages[stageIdx].pct)
        setStage(stages[stageIdx].msg)
        stageIdx++
      }
    }, 3000)

    try {
      const token = localStorage.getItem('authToken')

      // Build FormData — must match Django field names exactly
      const formData = new FormData()
      formData.append('uploaded_file', file)       // matches model field name
      formData.append('title', title.trim())
      formData.append('style_template', style)

      const res = await fetch('/api/v1/customer/documents/', {
        method: 'POST',
        headers: { Authorization: `Token ${token}` },
        // Do NOT set Content-Type — browser sets it automatically with boundary
        body: formData,
      })

      clearInterval(iv)

      const data = await res.json()

      if (!res.ok) {
        const msg = typeof data === 'object'
          ? Object.entries(data).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join(' | ')
          : String(data)
        throw new Error(msg)
      }

      setProgress(100)
      setStage('Done!')
      setResult(data)

    } catch (err) {
      clearInterval(iv)
      setError(err.message || 'Upload failed. Check Django terminal for details.')
    } finally {
      setUploading(false)
    }
  }

  const reset = () => {
    setFile(null); setResult(null)
    setProgress(0); setTitle('')
    setError(''); setStage('')
  }

  // ── Success screen ─────────────────────────────────────
  if (result) {
    const isComplete  = result.status === 'completed'
    const isFailed    = result.status === 'failed'
    const isProcessing= result.status === 'processing' || result.status === 'pending'

    return (
      <div style={{ maxWidth: 520 }}>
        <div className="card" style={{ textAlign: 'center', padding: '44px 32px' }}>
          <div style={{ fontSize: 52, marginBottom: 16 }}>
            {isComplete ? '🎉' : isFailed ? '❌' : '⏳'}
          </div>
          <div className="section-title" style={{ marginBottom: 10 }}>
            {isComplete  ? 'PDF Generated Successfully!'    : ''}
            {isFailed    ? 'Processing Failed'               : ''}
            {isProcessing? 'Upload Successful — Processing…' : ''}
          </div>

          {isComplete && (
            <Alert type="success">
              Your document has been processed and a PDF has been generated.
              Go to <strong>My Documents</strong> to download it.
            </Alert>
          )}

          {isFailed && (
            <Alert type="error">
              {result.message}<br/><br/>
              Most likely cause: <strong>OCR_SPACE_API_KEY</strong> is missing from your <code>.env</code> file.
              Check the Django terminal for the exact error.
            </Alert>
          )}

          {isProcessing && (
            <Alert type="info">
              Your file is queued for processing by the Celery worker.
              Make sure Terminal 2 (celery worker) is running.
              Check <strong>My Documents</strong> in a moment.
            </Alert>
          )}

          <div style={{ display: 'flex', gap: 10, justifyContent: 'center', marginTop: 20 }}>
            {isComplete && (
              <button className="btn btn-amber" onClick={() => setPage && setPage('documents')}>
                View My Documents →
              </button>
            )}
            <button className="btn btn-ghost" onClick={reset}>Upload another</button>
          </div>
        </div>
      </div>
    )
  }

  // ── Upload form ────────────────────────────────────────
  return (
    <div style={{ maxWidth: 580 }}>

      {/* Drop zone */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div
          className={`upload-zone ${drag ? 'drag-over' : ''}`}
          onDragOver={e => { e.preventDefault(); setDrag(true) }}
          onDragLeave={() => setDrag(false)}
          onDrop={e => { e.preventDefault(); setDrag(false); pickFile(e.dataTransfer.files[0]) }}
          onClick={() => !uploading && inputRef.current.click()}
          style={{ cursor: uploading ? 'not-allowed' : 'pointer' }}
        >
          <input
            ref={inputRef} type="file"
            accept=".jpg,.jpeg,.png,.pdf,.tif,.tiff,.bmp"
            hidden
            onChange={e => pickFile(e.target.files[0])}
          />
          {file ? (
            <>
              <div className="upload-zone-icon">📄</div>
              <div className="upload-zone-title">{file.name}</div>
              <div className="upload-zone-sub">{(file.size / 1024).toFixed(0)} KB · Click to change</div>
            </>
          ) : (
            <>
              <div className="upload-zone-icon">📷</div>
              <div className="upload-zone-title">Drop your handwritten notes here</div>
              <div className="upload-zone-sub">JPG, PNG, PDF, TIFF, BMP · Max 10 MB</div>
            </>
          )}
        </div>
        {error && <Alert type="error" style={{ marginTop: 12 }}>{error}</Alert>}
      </div>

      {/* Settings + upload button */}
      {file && (
        <div className="card">
          <div className="section-title" style={{ marginBottom: 18 }}>Document settings</div>

          <div className="form-group">
            <label className="form-label">Document title</label>
            <input
              className="form-input"
              placeholder="e.g. Biology Chapter 5 Notes"
              value={title}
              onChange={e => setTitle(e.target.value)}
              disabled={uploading}
            />
            <div style={{ fontSize: 11.5, color: 'var(--ink-muted)', marginTop: 4 }}>
              This title will appear on your document card and inside the PDF.
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Output style template</label>
            <select
              className="form-input"
              value={style}
              onChange={e => setStyle(e.target.value)}
              disabled={uploading}
            >
              {STYLES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
            </select>
          </div>

          {/* Processing progress */}
          {uploading && (
            <div style={{ marginBottom: 18 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12.5, color: 'var(--ink-muted)', marginBottom: 6 }}>
                <span style={{ fontStyle: 'italic' }}>{stage}</span>
                <span>{progress}%</span>
              </div>
              <ProgressBar value={progress} />
              <div style={{ fontSize: 11.5, color: 'var(--ink-muted)', marginTop: 6 }}>
                This may take 10–30 seconds while OCR processes your image.
              </div>
            </div>
          )}

          <div className="info-block" style={{ marginBottom: 18 }}>
            <strong>What happens after upload:</strong><br/>
            OpenCV pre-processes your image → OCR.space Engine 3 reads the handwriting
            → Layout analysis detects headings and paragraphs → PDF is generated with your chosen style.
          </div>

          <button
            className="btn btn-amber btn-full"
            onClick={handleUpload}
            disabled={uploading || !title.trim()}
          >
            {uploading ? stage || 'Processing…' : '↑  Upload & Generate PDF'}
          </button>
        </div>
      )}
    </div>
  )
}
