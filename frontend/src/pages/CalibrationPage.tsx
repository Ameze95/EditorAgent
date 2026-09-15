import { useEffect, useMemo, useRef, useState } from 'react'
import { Eyebrow } from '../components/atoms/Eyebrow'
import { reviewApi, type AnalysisRun, type AnalysisWindow, type AnnotationInterval } from '../lib/api/client'
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

const keyFor = (window: AnalysisWindow) => `${window.start_seconds}-${window.end_seconds}`
const time = (seconds: number) => `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(Math.floor(seconds % 60)).padStart(2, '0')}`

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

  useEffect(() => {
    void reviewApi.listClips().then(setClips).catch(() => setMessage('No se pudieron cargar los clips del proyecto.'))
    void reviewApi.listAnalysisRuns().then((loaded) => {
      setRuns(loaded.filter((run) => run.status === 'completed'))
      setRunId(loaded.find((run) => run.status === 'completed')?.id ?? '')
    }).catch(() => setMessage('No se pudieron cargar los análisis completados.'))
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
  }

  const save = async () => {
    if (!runId) return
    setBusy(true)
    try {
      await reviewApi.saveAnnotations(runId, { intent_profile: intentProfile, intervals: annotations })
      setMessage('Anotaciones guardadas en el proyecto.')
    } catch (error) { setMessage(error instanceof Error ? error.message : 'No se pudieron guardar las anotaciones.') } finally { setBusy(false) }
  }

  return <main className="calibration-shell">
    <header className="calibration-header"><button className="back-button" type="button" onClick={onBack} aria-label="Volver a revisión">←</button><div><Eyebrow>BACKOFFICE / CALIBRACIÓN</Eyebrow><h1>Etiquetar ventanas reales</h1></div><button className="quiet-button" type="button" onClick={() => void save()} disabled={busy || !runId}>Guardar anotaciones</button></header>
    <section className="calibration-toolbar panel"><label><Eyebrow>EJECUCIÓN</Eyebrow><select value={runId} onChange={(event) => selectRun(event.target.value)}><option value="">Selecciona un análisis</option>{runs.map((run) => <option value={run.id} key={run.id}>{clips.find((clip) => clip.id === run.clip_id)?.relative_path ?? run.clip_id} · {run.profile_name} · {new Date(run.started_at).toLocaleString()}</option>)}</select></label><label><Eyebrow>INTENCIÓN DEL VUELO</Eyebrow><select value={intentProfile} onChange={(event) => setIntentProfile(event.target.value)}><option value="cinematic">Cinemático</option><option value="fpv">FPV</option><option value="static">Estático</option></select></label><div className="calibration-summary"><strong>{windows.length}</strong><span>ventanas · {annotations.filter((item) => item.label !== 'unlabeled').length} etiquetadas</span></div></section>
    {message && <div className="notice">{message}</div>}
    <section className="calibration-workspace">{selectedClip && <section className="calibration-clip panel"><div className="calibration-player"><div className="calibration-player-heading"><div><Eyebrow>CLIP SELECCIONADO</Eyebrow><h2>{selectedClip.relative_path}</h2></div><span>{selectedWindowKey ? 'Ventana seleccionada' : 'Selecciona una ventana'}</span></div><video ref={videoRef} controls preload="metadata" src={`http://127.0.0.1:8765/clips/${selectedClip.id}/media`} /></div></section>}<div className="calibration-list">{windows.map((window, index) => { const annotation = annotationMap.get(keyFor(window)); const label = annotation?.label ?? 'unlabeled'; const selected = selectedWindowKey === keyFor(window); return <article className={`calibration-window ${label} ${selected ? 'selected' : ''}`} key={keyFor(window)} onClick={() => selectWindow(window)}><div className="calibration-window-heading"><span className="segment-index">{String(index + 1).padStart(2, '0')}</span><strong>{time(window.start_seconds)} — {time(window.end_seconds)}</strong><span className="calibration-score">score {Math.round((window.sharpness_norm + window.exposure_norm + window.direction_coherence) / 3 * 100)}</span></div><div className="calibration-metrics"><span>Nitidez {window.sharpness_norm.toFixed(2)}</span><span>Exposición {window.exposure_norm.toFixed(2)}</span><span>Movimiento {window.motion_norm.toFixed(2)}</span><span>Jerk {window.jerk_norm.toFixed(2)}</span><span>Estabilidad {window.stability_norm.toFixed(2)}</span></div><div className="calibration-labels">{labels.map(([value, text]) => <button className={label === value ? 'chosen' : ''} type="button" key={value} onClick={(event) => { event.stopPropagation(); setLabel(window, value) }}>{text}</button>)}</div></article> })}{!windows.length && <div className="empty-state">Selecciona una ejecución completada para empezar a etiquetar.</div>}</div></section>
  </main>
}
