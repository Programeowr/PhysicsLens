import { useState, useRef, useCallback } from 'react';
import './App.css';
import { parseTextProblem, parseImageProblem, generateDiagram, type ParsedData } from './api';

const EXAMPLES = [
  'A 5 kg block slides down a 30° inclined plane with coefficient of friction 0.2.',
  'A 10 kg box is pushed with 50 N force on a rough horizontal surface. μ = 0.3.',
  'Two masses of 3 kg and 5 kg are connected by a string over a frictionless pulley.',
  'A 60 kg person stands on a scale in an elevator accelerating upward at 2 m/s².',
];

type InputMode = 'text' | 'image';
type AppState = 'idle' | 'loading' | 'ready' | 'error';

function App() {
  const [mode, setMode] = useState<InputMode>('text');
  const [problem, setProblem] = useState('');
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [appState, setAppState] = useState<AppState>('idle');
  const [svgContent, setSvgContent] = useState<string | null>(null);
  const [parsedData, setParsedData] = useState<ParsedData | null>(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [showJson, setShowJson] = useState(false);
  const [dragover, setDragover] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // ── Image handling ──────────────────────────
  const handleImageSelect = useCallback((file: File) => {
    setImageFile(file);
    const reader = new FileReader();
    reader.onload = (e) => setImagePreview(e.target?.result as string);
    reader.readAsDataURL(file);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragover(false);
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      handleImageSelect(file);
    }
  }, [handleImageSelect]);

  const clearImage = () => {
    setImageFile(null);
    setImagePreview(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // ── Parse & Generate ────────────────────────
  const handleParse = async () => {
    setAppState('loading');
    setErrorMsg('');
    setSvgContent(null);
    setParsedData(null);

    try {
      let response;
      if (mode === 'text') {
        if (!problem.trim()) return;
        response = await parseTextProblem(problem);
      } else {
        if (!imageFile) return;
        response = await parseImageProblem(imageFile);
      }

      setParsedData(response.data);

      // Generate diagram
      const svg = await generateDiagram(response.data);
      setSvgContent(svg);
      setAppState('ready');
    } catch (err: unknown) {
      setAppState('error');
      setErrorMsg(err instanceof Error ? err.message : 'Something went wrong');
    }
  };

  const canParse = mode === 'text' ? problem.trim().length > 10 : !!imageFile;

  // ── Export ──────────────────────────────────
  const exportSVG = () => {
    if (!svgContent) return;
    const blob = new Blob([svgContent], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'physics_fbd.svg';
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportPNG = () => {
    if (!svgContent) return;
    const svgEl = document.querySelector('.diagram-svg-container svg') as SVGSVGElement;
    if (!svgEl) return;

    const canvas = document.createElement('canvas');
    const rect = svgEl.getBoundingClientRect();
    canvas.width = rect.width * 2;
    canvas.height = rect.height * 2;
    const ctx = canvas.getContext('2d')!;
    ctx.scale(2, 2);

    const img = new Image();
    const svgBlob = new Blob([svgContent], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(svgBlob);
    img.onload = () => {
      ctx.drawImage(img, 0, 0, rect.width, rect.height);
      URL.revokeObjectURL(url);
      const a = document.createElement('a');
      a.href = canvas.toDataURL('image/png');
      a.download = 'physics_fbd.png';
      a.click();
    };
    img.src = url;
  };

  // ── Render ─────────────────────────────────
  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-brand">
          <span className="header-logo">🔭</span>
          <div>
            <div className="header-title">PhysicsLens</div>
            <div className="header-subtitle">AI-Powered Free Body Diagrams</div>
          </div>
        </div>
        <span className="header-badge">AMD Slingshot</span>
      </header>

      {/* Main Content */}
      <div className="main-content">
        {/* Left Panel — Input */}
        <div className="input-panel">
          <div className="panel-label">Input Method</div>

          {/* Tabs */}
          <div className="input-tabs">
            <button className={`input-tab ${mode === 'text' ? 'active' : ''}`} onClick={() => setMode('text')}>
              ✏️ Text
            </button>
            <button className={`input-tab ${mode === 'image' ? 'active' : ''}`} onClick={() => setMode('image')}>
              📸 Image
            </button>
          </div>

          {/* Text input */}
          {mode === 'text' && (
            <>
              <textarea
                className="text-input-area"
                placeholder="Type or paste a physics problem here...&#10;&#10;Example: A 5 kg block slides down a 30° inclined plane with coefficient of friction 0.2."
                value={problem}
                onChange={(e) => setProblem(e.target.value)}
              />
              <div className="examples-section">
                <div className="panel-label">Try an example</div>
                <div className="examples-list">
                  {EXAMPLES.map((ex, i) => (
                    <button key={i} className="example-chip" onClick={() => setProblem(ex)}>
                      {ex}
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* Image upload */}
          {mode === 'image' && (
            <>
              {!imagePreview ? (
                <div
                  className={`upload-zone ${dragover ? 'dragover' : ''}`}
                  onClick={() => fileInputRef.current?.click()}
                  onDragOver={(e) => { e.preventDefault(); setDragover(true); }}
                  onDragLeave={() => setDragover(false)}
                  onDrop={handleDrop}
                >
                  <div className="upload-icon">📤</div>
                  <div className="upload-text">
                    <strong>Click to upload</strong> or drag & drop
                  </div>
                  <div className="upload-hint">Supports JPEG, PNG, WebP • Max 10MB</div>
                </div>
              ) : (
                <div className="upload-preview">
                  <img src={imagePreview} alt="Uploaded question" />
                  <button className="upload-preview-remove" onClick={clearImage}>✕</button>
                </div>
              )}
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                style={{ display: 'none' }}
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) handleImageSelect(file);
                }}
              />
            </>
          )}

          {/* Parse button */}
          <button className="parse-button" onClick={handleParse} disabled={!canParse || appState === 'loading'}>
            {appState === 'loading' ? (
              <>
                <span className="spinner" />
                Analyzing...
              </>
            ) : (
              <>🔍 Generate Free Body Diagram</>
            )}
          </button>

          {/* Parsed data toggle */}
          {parsedData && (
            <div className="parsed-section">
              <button className="parsed-toggle" onClick={() => setShowJson(!showJson)}>
                {showJson ? '▼' : '▶'} Parsed Physics Data
              </button>
              {showJson && (
                <pre className="parsed-json">{JSON.stringify(parsedData, null, 2)}</pre>
              )}
            </div>
          )}
        </div>

        {/* Right Panel — Diagram */}
        <div className="diagram-panel">
          {/* Toolbar */}
          <div className="diagram-toolbar">
            <div className="diagram-toolbar-left">
              <div className="diagram-status">
                <span className={`status-dot ${appState === 'ready' ? 'ready' : appState === 'loading' ? 'loading' : appState === 'error' ? 'error' : ''}`} />
                {appState === 'idle' && 'Waiting for input'}
                {appState === 'loading' && 'Generating diagram...'}
                {appState === 'ready' && 'Diagram ready'}
                {appState === 'error' && 'Error occurred'}
              </div>
            </div>
            {svgContent && (
              <div className="diagram-toolbar-right">
                <button className="toolbar-btn" onClick={exportSVG}>⬇ SVG</button>
                <button className="toolbar-btn" onClick={exportPNG}>⬇ PNG</button>
              </div>
            )}
          </div>

          {/* Diagram area */}
          <div className="diagram-viewer">
            {appState === 'error' && (
              <div className="error-banner">
                <span className="error-banner-icon">⚠️</span>
                <div>{errorMsg}</div>
              </div>
            )}

            {!svgContent && appState !== 'error' && (
              <div className="diagram-empty">
                <div className="diagram-empty-icon">📐</div>
                <h3>No diagram yet</h3>
                <p>Enter a physics problem on the left, then click "Generate" to see the free body diagram here.</p>
              </div>
            )}

            {svgContent && (
              <div className="diagram-svg-container" dangerouslySetInnerHTML={{ __html: svgContent }} />
            )}
          </div>

          {/* Force Legend */}
          {svgContent && (
            <div className="force-legend">
              <span className="legend-title">Forces</span>
              <span className="legend-item"><span className="legend-dot" style={{ background: 'var(--force-gravity)' }} /> Gravity</span>
              <span className="legend-item"><span className="legend-dot" style={{ background: 'var(--force-normal)' }} /> Normal</span>
              <span className="legend-item"><span className="legend-dot" style={{ background: 'var(--force-friction)' }} /> Friction</span>
              <span className="legend-item"><span className="legend-dot" style={{ background: 'var(--force-applied)' }} /> Applied</span>
              <span className="legend-item"><span className="legend-dot" style={{ background: 'var(--force-tension)' }} /> Tension</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
