import { useState, useRef } from 'react';
import './UploadForm.css';

const ROLES = ['Data Analyst', 'Web Developer', 'AI Engineer', 'Cloud Engineer'];

export default function UploadForm({ onResult, onError }) {
  const [file, setFile] = useState(null);
  const [role, setRole] = useState(ROLES[0]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef(null);

  /* ── File handling ── */
  function handleFileChange(e) {
    const selected = e.target.files?.[0];
    if (selected) {
      setFile(selected);
      setError('');
    }
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) {
      setFile(dropped);
      setError('');
    }
  }

  function removeFile() {
    setFile(null);
    if (inputRef.current) inputRef.current.value = '';
  }

  /* ── Submit ── */
  async function handleSubmit(e) {
    e.preventDefault();
    if (!file) {
      setError('Please upload a resume first.');
      return;
    }

    setLoading(true);
    setError('');

    const formData = new FormData();
    formData.append('resume', file);
    formData.append('role', role);

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || `Server error (${res.status})`);
      }

      onResult(data);
    } catch (err) {
      const msg =
        err.name === 'TypeError'
          ? 'Cannot reach the server. Is the backend running?'
          : err.message;
      setError(msg);
      onError?.(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      {/* Drop zone */}
      <div
        className={`upload-form__dropzone${dragOver ? ' upload-form__dropzone--drag-over' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        aria-label="Upload resume file"
        id="dropzone"
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx"
          onChange={handleFileChange}
          className="upload-form__file-input"
          tabIndex={-1}
          id="file-input"
        />

        <div className="upload-form__dropzone-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
        </div>

        <p className="upload-form__dropzone-label">
          <strong>Click to upload</strong> or drag &amp; drop
        </p>
        <p className="upload-form__dropzone-hint">PDF or DOCX · max 5 MB</p>
      </div>

      {/* File pill */}
      {file && (
        <div className="upload-form__file-pill">
          <span>{file.name}</span>
          <button
            type="button"
            className="upload-form__file-remove"
            onClick={(e) => { e.stopPropagation(); removeFile(); }}
            aria-label="Remove file"
            id="remove-file-btn"
          >
            ×
          </button>
        </div>
      )}

      {/* Role selector */}
      <div className="upload-form__role-group">
        <label htmlFor="role-select" className="upload-form__role-label">
          Target Role
        </label>
        <select
          id="role-select"
          className="upload-form__role-select"
          value={role}
          onChange={(e) => setRole(e.target.value)}
        >
          {ROLES.map((r) => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>
      </div>

      {/* Submit */}
      <button
        type="submit"
        className="upload-form__submit"
        disabled={loading}
        id="analyze-btn"
      >
        {loading ? (
          <>
            <span className="upload-form__spinner" />
            Analyzing…
          </>
        ) : (
          'Analyze Resume'
        )}
      </button>

      {/* Error */}
      {error && (
        <div className="upload-form__error" role="alert" id="upload-error">
          {error}
        </div>
      )}
    </form>
  );
}
