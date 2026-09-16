import { Eyebrow } from '../atoms/Eyebrow'
import { StatusDot } from '../atoms/StatusDot'
import { KnowledgeLabelControls } from '../molecules/KnowledgeLabelControls'
import type { HumanLabel } from '../../lib/api/client'
import type { Segment } from '../../types/review'

type ReviewInspectorProps = {
  segment: Segment | null
  label: HumanLabel | null
  saving: boolean
  onUpdate: (patch: Partial<Pick<Segment, 'status' | 'start_seconds' | 'end_seconds' | 'user_note'>>) => void
  onLabel: (patch: Pick<HumanLabel, 'utility_label' | 'capture_type' | 'motion_intent' | 'shot_type' | 'motion_quality' | 'rejection_reason' | 'technical_issues' | 'confidence' | 'note'>) => void
  onDraft: (patch: Partial<Segment>) => void
  onMoveSegment: (offset: number) => void
}

export function ReviewInspector({ segment, label, saving, onUpdate, onLabel, onDraft, onMoveSegment }: ReviewInspectorProps) {
  if (!segment) {
    return <aside className="inspector panel">
      <div className="panel-heading"><div><Eyebrow>INSPECTOR</Eyebrow><h2>Decisión humana</h2></div></div>
      <div className="inspector-empty">Selecciona un candidato para revisar sus señales.</div>
    </aside>
  }

  return <aside className="inspector panel" key={segment.id}>
    <div className="panel-heading"><div><Eyebrow>INSPECTOR</Eyebrow><h2>Decisión humana</h2></div><StatusDot status={segment.status} /></div>
    <div className="segment-nav-actions">
      <button type="button" onClick={() => onMoveSegment(-1)}>← Segmento anterior</button>
      <button type="button" onClick={() => onMoveSegment(1)}>Segmento siguiente →</button>
    </div>
    <div className="decision-actions">
      <button className={segment.status === 'approved' ? 'chosen approve' : 'approve'} type="button" onClick={() => onUpdate({ status: 'approved' })}>✓ Aprobar</button>
      <button className={segment.status === 'rejected' ? 'chosen reject' : 'reject'} type="button" onClick={() => onUpdate({ status: 'rejected' })}>× Rechazar</button>
    </div>
    <KnowledgeLabelControls label={label} onSave={onLabel} />
    <div className="range-fields">
      <label>IN<input type="number" step="0.01" value={segment.start_seconds} onChange={(event) => onDraft({ start_seconds: Number(event.target.value) })} onBlur={() => onUpdate({ start_seconds: segment.start_seconds, end_seconds: segment.end_seconds, status: 'manual' })} /></label>
      <label>OUT<input type="number" step="0.01" value={segment.end_seconds} onChange={(event) => onDraft({ end_seconds: Number(event.target.value) })} onBlur={() => onUpdate({ start_seconds: segment.start_seconds, end_seconds: segment.end_seconds, status: 'manual' })} /></label>
    </div>
    <div className="metric-card"><span>Technical score</span><strong>{Math.round(segment.technical_score * 100)}<small>/100</small></strong><div className="score-bar"><span style={{ width: `${segment.technical_score * 100}%` }} /></div></div>
    <div className="reason-section"><h3>Señales a favor</h3>{segment.reasons.map((reason) => <p className="reason positive" key={reason}>+ {reason}</p>)}</div>
    <div className="reason-section"><h3>Penalizaciones</h3>{segment.penalties.slice(0, 4).map((penalty) => <p className="reason negative" key={penalty}>− {penalty}</p>)}</div>
    <label className="note-field">Nota de revisión<textarea key={segment.id} placeholder="Añade contexto editorial..." defaultValue={segment.user_note ?? ''} onBlur={(event) => onUpdate({ user_note: event.target.value })} /></label>
    {saving && <small className="save-state">Guardando...</small>}
  </aside>
}
