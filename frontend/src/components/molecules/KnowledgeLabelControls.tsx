import type { HumanLabel } from '../../lib/api/client'

type KnowledgeLabelControlsProps = {
  label: HumanLabel | null
  onSave: (patch: Pick<HumanLabel, 'utility_label' | 'capture_type' | 'motion_intent' | 'shot_type' | 'motion_quality' | 'rejection_reason' | 'technical_issues' | 'confidence' | 'note'>) => void
}

const utilityOptions = [
  ['usable', 'Utilizable'],
  ['unusable', 'No utilizable'],
  ['uncertain', 'Incierta'],
] as const

const shotOptions = [
  ['traveling', 'Traveling'],
  ['orbit', 'Órbita'],
  ['hover', 'Hover'],
  ['reveal', 'Reveal'],
  ['fpv_dynamic', 'FPV dinámico'],
  ['other', 'Otro'],
] as const

const captureOptions = [
  ['drone', 'Dron'],
  ['fpv', 'FPV'],
  ['gimbal', 'Gimbal'],
  ['handheld', 'Mano'],
  ['tripod', 'Trípode'],
  ['action_camera', 'Action cam'],
  ['vehicle', 'Vehículo'],
] as const

const intentOptions = [
  ['static', 'Estático'],
  ['traveling', 'Travelling'],
  ['orbit', 'Órbita'],
  ['reveal', 'Reveal'],
  ['follow', 'Seguimiento'],
  ['dynamic', 'Dinámico'],
] as const

const issueOptions = [
  ['blur', 'Blur'],
  ['exposure', 'Exposición'],
  ['jerk', 'Jerk'],
  ['vibration', 'Vibración'],
  ['takeoff_landing', 'Despegue / aterrizaje'],
  ['redundant', 'Repetida'],
] as const

const motionOptions = [
  ['smooth', 'Suave'],
  ['intentional_dynamic', 'Dinámica intencional'],
  ['abrupt', 'Brusca'],
  ['vibration', 'Vibración'],
  ['uncertain', 'Incierta'],
] as const

type LabelDraft = Pick<HumanLabel, 'utility_label' | 'capture_type' | 'motion_intent' | 'shot_type' | 'motion_quality' | 'rejection_reason' | 'technical_issues' | 'confidence' | 'note'>

const emptyLabel: LabelDraft = {
  utility_label: 'uncertain',
  capture_type: null,
  motion_intent: null,
  shot_type: null,
  motion_quality: null,
  rejection_reason: null,
  technical_issues: [],
  confidence: 'medium',
  note: null,
}

export function KnowledgeLabelControls({ label, onSave }: KnowledgeLabelControlsProps) {
  const current = label ?? { ...emptyLabel }
  const save = (patch: Partial<LabelDraft>) => onSave({ ...current, ...patch })
  const toggleIssue = (issue: string) => save({ technical_issues: current.technical_issues.includes(issue) ? current.technical_issues.filter((item) => item !== issue) : [...current.technical_issues, issue] })
  return <section className="knowledge-labels">
    <div className="knowledge-label-heading"><span>Conocimiento del sistema</span><small>{label ? 'Guardado' : 'Sin etiquetar'}</small></div>
    <div className="knowledge-label-group"><small>Decisión</small><div>{utilityOptions.map(([value, text]) => <button className={current.utility_label === value ? 'chosen' : ''} type="button" key={value} onClick={() => save({ utility_label: value })}>{text}</button>)}</div></div>
    <div className="knowledge-label-group"><small>Captura</small><div>{captureOptions.map(([value, text]) => <button className={current.capture_type === value ? 'chosen' : ''} type="button" key={value} onClick={() => save({ capture_type: value })}>{text}</button>)}</div></div>
    <div className="knowledge-label-group"><small>Intención</small><div>{intentOptions.map(([value, text]) => <button className={current.motion_intent === value ? 'chosen' : ''} type="button" key={value} onClick={() => save({ motion_intent: value })}>{text}</button>)}</div></div>
    <div className="knowledge-label-group"><small>Tipo de plano</small><div>{shotOptions.map(([value, text]) => <button className={current.shot_type === value ? 'chosen' : ''} type="button" key={value} onClick={() => save({ shot_type: value })}>{text}</button>)}</div></div>
    <div className="knowledge-label-group"><small>Movimiento</small><div>{motionOptions.map(([value, text]) => <button className={current.motion_quality === value ? 'chosen' : ''} type="button" key={value} onClick={() => save({ motion_quality: value })}>{text}</button>)}</div></div>
    <div className="knowledge-label-group"><small>Problemas técnicos</small><div>{issueOptions.map(([value, text]) => <button className={current.technical_issues.includes(value) ? 'chosen' : ''} type="button" key={value} onClick={() => toggleIssue(value)}>{text}</button>)}</div></div>
  </section>
}
