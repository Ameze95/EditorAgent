import { useEffect, useState } from 'react'
import { Eyebrow } from '../components/atoms/Eyebrow'
import { reviewApi } from '../lib/api/client'

type LearningSummary = { clips_total: number; clips_with_segments: number; segments_total: number; segments_labeled: number; labels_total: number; uncertain_labels: number; approved_segments: number; rejected_segments: number; coverage_percent: number; utility_labels: Record<string, number>; shot_types: Record<string, number>; motion_quality: Record<string, number> }

export function LearningPage({ onBack }: { onBack: () => void }) {
  const [summary, setSummary] = useState<LearningSummary | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => { void reviewApi.learningSummary().then(setSummary).catch(() => setError('No se pudo cargar el monitor de aprendizaje.')) }, [])
  return <main className="learning-shell"><header className="calibration-header"><button className="back-button" type="button" onClick={onBack} aria-label="Volver a revisión">←</button><div><Eyebrow>BACKOFFICE / APRENDIZAJE</Eyebrow><h1>Monitor de conocimiento</h1></div></header>{error && <div className="notice">{error}</div>}{summary && <><section className="learning-kpis">{[['Clips', summary.clips_total], ['Segmentos', summary.segments_total], ['Etiquetas', summary.labels_total], ['Cobertura', `${summary.coverage_percent}%`], ['Inciertas', summary.uncertain_labels]].map(([label, value]) => <div className="learning-kpi panel" key={String(label)}><Eyebrow>{String(label)}</Eyebrow><strong>{value}</strong></div>)}</section><section className="learning-grid"><div className="learning-card panel"><Eyebrow>UTILIDAD</Eyebrow>{Object.entries(summary.utility_labels).map(([key, value]) => <p key={key}><span>{key}</span><strong>{value}</strong></p>)}</div><div className="learning-card panel"><Eyebrow>TIPOS DE PLANO</Eyebrow>{Object.entries(summary.shot_types).map(([key, value]) => <p key={key}><span>{key}</span><strong>{value}</strong></p>)}</div><div className="learning-card panel"><Eyebrow>MOVIMIENTO</Eyebrow>{Object.entries(summary.motion_quality).map(([key, value]) => <p key={key}><span>{key}</span><strong>{value}</strong></p>)}</div></section></>}</main>
}
