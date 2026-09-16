import { useEffect, useMemo, useRef, useState } from 'react'
import { Eyebrow } from '../components/atoms/Eyebrow'
import {
  reviewApi,
  type AnalysisProfile,
  type AnalysisRun,
  type AnalysisWindow,
  type AnnotationInterval,
  type AnalyzeOverrides,
  type EvaluationMetrics,
} from '../lib/api/client'
import type { Clip } from '../types/review'

type CalibrationPageProps = { onBack: () => void }

const labels = [
  ['usable', 'Utilizable'],
  ['technical_bad', 'Técnica mala'],
  ['intentional_dynamic', 'Dinámica intencional'],
  ['abrupt_motion', 'Movimiento brusco'],
  ['takeoff_landing', 'Despegue / aterrizaje'],
  ['uncertain', 'Incierta'],
] as const

// Mirrors the tunable fields in backend PROFILE_DEFAULTS / AnalyzeOverrides.
const paramFields: Array<[key: keyof AnalyzeOverrides, label: string, step: number]> = [
  ['enter_threshold', 'Umbral de entrada', 0.01],
  ['exit_threshold', 'Umbral de salida', 0.01],
  ['minimum_duration_seconds', 'Duración mínima (s)', 0.1],
  ['critical_jerk_threshold', 'Jerk crítico', 0.01],
  ['critical_hard_turn_ratio', 'Giro brusco crítico', 0.01],
  ['critical_hard_brake_ratio', 'Frenazo crítico', 0.01],
]

const keyFor = (window: AnalysisWindow) => `${window.start_seconds}-${window.end_seconds}`
const time = (seconds: number) => `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(Math.floor(seconds % 60)).padStart(2, '0')}`
const pct = (value: number) => `${Math.round(value * 100)}%`

export function CalibrationPage({ onBack }: CalibrationPageProps) {
  const [clips, setClips] = useState<Clip[]>([])
  const [runs, setRuns] = useState<AnalysisRun[]>([])
  const [runId, setRunId] = useState('')
  const [windows, setWindows] = useState<AnalysisWindow[]>([])
  const [annotations, setAnnotations] = useState<AnnotationInterval[]>([])
  const [intentProfile, setIntentProfile] = useState('cinematic')
  const [message, setMessage] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [selectedWindowKey, setSelectedWindowKey] = useState<string | null>(null)
  const videoRef = useRef<HTMLVideoElement>(null)

  const [profiles, setProfiles] = useState<AnalysisProfile[]>([])
  const [profileName, setProfileName] = useState('')
  const [overrides, setOverrides] = useState<Record<string, number>>({})
  const [reanalyzing, setReanalyzing] = useState(false)
  const [metrics, setMetrics] = useState<EvaluationMetrics | null>(null)
  const [metricsRefreshKey, setMetricsRefreshKey] = useState(0)

  useEffect(() => {
    void reviewApi.listClips().then(setClips).catch(() => setMessage('No se pudieron cargar los clips del proyecto.'))
    void reviewApi.listAnalysisRuns().then((loaded) => {
      setRuns(loaded.filter((run) => run.status === 'completed'))
      setRunId(loaded.find((run) => run.status === 'completed')?.id ?? '')
    }).catch(() => setMessage('No se pudieron cargar los análisis completados.'))
    void reviewApi.listAnalysisProfiles().then((loaded) => {
      setProfiles(loaded)
      if (loaded.length) {
        setProfileName(loaded[0].name)
        setOverrides(loaded[0].parameters)
      }
    }).catch(() => setMessage('No se pudieron cargar los perfiles de análisis.'))
  }, [])

  useEffect(() => {
    if (!runId) return
    void Promise.all([reviewApi.getAnalysisWindows(runId), reviewApi.getAnnotations(runId)]).then(([loadedWindows, document]) => {
      setWindows(loadedWindows)
      setAnnotations(document.intervals)
      setIntentProfile(document.intent_profile)
      setSelectedWindowKey(loadedWindows[0] ? keyFor(loadedWindows[0]) : null)
      setMessage(null)
    }).catch(() => setMessage('No se pudo cargar la calibración de esta ejecución.')).finally(() => setBusy(false))
  }, [runId])

  const selectedRun = runs.find((run) => run.id === runId)
  const selectedClip = clips.find((clip) => clip.id === selectedRun?.clip_id)
  const annotationMap = useMemo(() => new Map(annotations.map((item) => [`${item.start_seconds}-${item.end_seconds}`, item])), [annotations])

  useEffect(() => {
    let cancelled = false
    async function refreshMetrics() {
      if (!runId || !windows.length || overrides.enter_threshold === undefined) {
        if (!cancelled) setMetrics(null)
        return
      }
      try {
        const result = await reviewApi.getAnalysisMetrics(runId, overrides.enter_threshold)
        if (!cancelled) setMetrics(result)
      } catch {
        if (!cancelled) setMetrics(null)
      }
    }
    void refreshMetrics()
    return () => { cancelled = true }
  }, [runId, overrides.enter_threshold, windows.length, metricsRefreshKey])

  const setLabel = (window: AnalysisWindow, label: string) => {
    const current = annotationMap.get(keyFor(window))
    const next: AnnotationInterval = { start_seconds: window.start_seconds, end_seconds: window.end_seconds, label, reason: current?.reason ?? null, confidence: current?.confidence ?? null }
    setAnnotations((items) => [...items.filter((item) => `${item.start_seconds}-${item.end_seconds}` !== keyFor(window)), next])
    setSelectedWindowKey(keyFor(window))
  }

  const selectWindow = (window: AnalysisWindow) => {
    setSelectedWindowKey(keyFor(window))
    if (videoRef.current) {
      videoRef.current.currentTime = window.start_seconds
      void videoRef.current.play().catch(() => undefined)
    }
  }

  const selectRun = (value: string) => {
    setBusy(true)
    setRunId(value)
    // Reflect the profile that actually produced this run, when known.
    const run = runs.find((item) => item.id === value)
    const matching = run ? profiles.find((item) => item.name === run.profile_name) : undefined
    if (matching) {
      setProfileName(matching.name)
      setOverrides(matching.parameters)
    }
  }

  const selectProfile = (name: string) => {
    setProfileName(name)
    const profile = profiles.find((item) => item.name === name)
    if (profile) setOverrides(profile.parameters)
  }

  const updateOverride = (key: string, value: number) => {
    setOverrides((current) => ({ ...current, [key]: value }))
  }

  const save = async () => {
    if (!runId) return
    setBusy(true)
    try {
      await reviewApi.saveAnnotations(runId, { intent_profile: intentProfile, intervals: annotations })
      setMessage('Anotaciones guardadas en el proyecto.')
      setMetricsRefreshKey((value) => value + 1)
    } catch (error) { setMessage(error instanceof Error ? error.message : 'No se pudieron guardar las anotaciones.') } finally { setBusy(false) }
  }

  const reanalyze = async () => {
    if (!selectedRun) return
    setReanalyzing(true)
    setMessage(null)
    const previousRunId = runId
    try {
      const job = await reviewApi.analyzeClip(selectedRun.clip_id, { profile_name: profileName, ...overrides })
      let currentJob = job
      while (!['completed', 'failed', 'cancelled'].includes(currentJob.status)) {
        await new Promise((resolve) => window.setTimeout(resolve, 800))
        currentJob = await reviewApi.getAnalysisJob(job.id)
      }
      if (currentJob.status !== 'completed') {
        setMessage('El reanálisis no se completó correctamente.')
        return
      }
      const updatedRuns = await reviewApi.listAnalysisRuns()
      const completedRuns = updatedRuns.filter((run) => run.status === 'completed')
      const newest = completedRuns
        .filter((run) => run.clip_id === selectedRun.clip_id)
        .sort((first, second) => new Date(second.started_at).getTime() - new Date(first.started_at).getTime())[0]
      setRuns(completedRuns)
      if (!newest) { setMessage('No se encontró la nueva ejecución tras reanalizar.'); return }
      // Window boundaries stay identical across reruns of the same clip (only
      // thresholds change), so previous annotations still line up and can move forward.
      if (previousRunId) {
        try {
          const previousAnnotations = await reviewApi.getAnnotations(previousRunId)
          if (previousAnnotations.intervals.length) await reviewApi.saveAnnotations(newest.id, previousAnnotations)
        } catch { /* carrying over annotations is best-effort */ }
      }
      setRunId(newest.id)
      setMessage(`Reanalizado con ${profileName}.`)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'No se pudo reanalizar el clip.')
    } finally {
      setReanalyzing(false)
    }
  }

  return <main className="calibration-shell">
    <header className="calibration-header"><button className="back-button" type="button" onClick={onBack} aria-label="Volver a revisión">←</button><div><Eyebrow>BACKOFFICE / CALIBRACIÓN</Eyebrow><h1>Etiquetar ventanas reales</h1></div><button className="quiet-button" type="button" onClick={() => void save()} disabled={busy || !runId}>Guardar anotaciones</button></header>
    <section className="calibration-toolbar panel"><label><Eyebrow>EJECUCIÓN</Eyebrow><select value={runId} onChange={(event) => selectRun(event.target.value)}><option value="">Selecciona un análisis</option>{runs.map((run) => <option value={run.id} key={run.id}>{clips.find((clip) => clip.id === run.clip_id)?.relative_path ?? run.clip_id} · {run.profile_name} · {new Date(run.started_at).toLocaleString()}</option>)}</select></label><label><Eyebrow>INTENCIÓN DEL VUELO</Eyebrow><select value={intentProfile} onChange={(event) => setIntentProfile(event.target.value)}><option value="cinematic">Cinemático</option><option value="fpv">FPV</option><option value="static">Estático</option></select></label><div className="calibration-summary"><strong>{windows.length}</strong><span>ventanas · {annotations.filter((item) => item.label !== 'unlabeled').length} etiquetadas</span></div></section>

    <section className="calibration-tuning panel">
      <div className="panel-heading"><div><Eyebrow>PRECISIÓN</Eyebrow><h2>Ajustar perfil y reanalizar</h2></div></div>
      <div className="calibration-tuning-grid">
        <label>Perfil<select value={profileName} onChange={(event) => selectProfile(event.target.value)}>{profiles.map((profile) => <option value={profile.name} key={profile.name}>{profile.name}</option>)}</select></label>
        {paramFields.map(([key, label, step]) => <label key={key}>{label}<input type="number" step={step} value={overrides[key] ?? ''} onChange={(event) => updateOverride(key, Number(event.target.value))} /></label>)}
      </div>
      <div className="calibration-tuning-actions">
        <button type="button" onClick={() => void reanalyze()} disabled={reanalyzing || !selectedRun}>{reanalyzing ? 'Reanalizando…' : 'Reanalizar clip con estos parámetros'}</button>
        <small>Conserva las anotaciones al reanalizar el mismo clip.</small>
      </div>
      {metrics && <div className="calibration-metrics-panel">
        <div className="calibration-metrics-card"><Eyebrow>SCORE ACTUAL</Eyebrow>
          <p><span>Precision</span><strong>{pct(metrics.current.precision)}</strong></p>
          <p><span>Recall</span><strong>{pct(metrics.current.recall)}</strong></p>
          <p><span>Precision@K</span><strong>{pct(metrics.current.precision_at_k)}</strong></p>
          <p><span>IoU temporal</span><strong>{pct(metrics.current.temporal_iou)}</strong></p>
        </div>
        <div className="calibration-metrics-card baseline"><Eyebrow>BASELINE NITIDEZ+EXPOSICIÓN</Eyebrow>
          <p><span>Precision</span><strong>{pct(metrics.baseline_sharpness_exposure.precision)}</strong></p>
          <p><span>Recall</span><strong>{pct(metrics.baseline_sharpness_exposure.recall)}</strong></p>
        </div>
        <small className="calibration-metrics-note">Basado en {metrics.labeled_windows} ventanas etiquetadas · {metrics.usable_seconds.toFixed(1)}s marcados como utilizables.</small>
      </div>}
      {!metrics && <p className="calibration-metrics-empty">Etiqueta al menos una ventana como "Utilizable" y guarda para ver precision/recall aquí.</p>}
    </section>

    {message && <div className="notice">{message}</div>}
    <section className="calibration-workspace">{selectedClip && <section className="calibration-clip panel"><div className="calibration-player"><div className="calibration-player-heading"><div><Eyebrow>CLIP SELECCIONADO</Eyebrow><h2>{selectedClip.relative_path}</h2></div><span>{selectedWindowKey ? 'Ventana seleccionada' : 'Selecciona una ventana'}</span></div><video ref={videoRef} controls preload="metadata" src={`http://127.0.0.1:8765/clips/${selectedClip.id}/media`} /></div></section>}<div className="calibration-list">{windows.map((window, index) => { const annotation = annotationMap.get(keyFor(window)); const label = annotation?.label ?? 'unlabeled'; const selected = selectedWindowKey === keyFor(window); return <article className={`calibration-window ${label} ${selected ? 'selected' : ''}`} key={keyFor(window)} onClick={() => selectWindow(window)}><div className="calibration-window-heading"><span className="segment-index">{String(index + 1).padStart(2, '0')}</span><strong>{time(window.start_seconds)} — {time(window.end_seconds)}</strong><span className="calibration-score">score {Math.round((window.sharpness_norm + window.exposure_norm + window.direction_coherence) / 3 * 100)}</span></div><div className="calibration-metrics"><span>Nitidez {window.sharpness_norm.toFixed(2)}</span><span>Exposición {window.exposure_norm.toFixed(2)}</span><span>Movimiento {window.motion_norm.toFixed(2)}</span><span>Jerk {window.jerk_norm.toFixed(2)}</span><span>Estabilidad {window.stability_norm.toFixed(2)}</span></div><div className="calibration-labels">{labels.map(([value, text]) => <button className={label === value ? 'chosen' : ''} type="button" key={value} onClick={(event) => { event.stopPropagation(); setLabel(window, value) }}>{text}</button>)}</div></article> })}{!windows.length && <div className="empty-state">Selecciona una ejecución completada para empezar a etiquetar.</div>}</div></section>
  </main>
}
