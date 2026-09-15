import type { HumanLabel } from '../../lib/api/client'

type KnowledgeLabelControlsProps = {
  label: HumanLabel | null
  onSave: (patch: Pick<HumanLabel, 'utility_label' | 'shot_type' | 'motion_quality' | 'rejection_reason' | 'confidence' | 'note'>) => void
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

const motionOptions = [
  ['smooth', 'Suave'],
  ['intentional_dynamic', 'Dinámica intencional'],
  ['abrupt', 'Brusca'],
  ['vibration', 'Vibración'],
  ['uncertain', 'Incierta'],
] as const

type LabelDraft = Pick<HumanLabel, 'utility_label' | 'shot_type' | 'motion_quality' | 'rejection_reason' | 'confidence' | 'note'>

const emptyLabel: LabelDraft = {
  utility_label: 'uncertain',
  shot_type: null,
  motion_quality: null,
  rejection_reason: null,
  confidence: 'medium',
  note: null,
}

export function KnowledgeLabelControls({ label, onSave }: KnowledgeLabelControlsProps) {
  const current = label ?? { ...emptyLabel }
  const save = (patch: Partial<LabelDraft>) => onSave({ ...current, ...patch })
  return <section className="knowledge-labels">
    <div className="knowledge-label-heading"><span>Conocimiento del sistema</span><small>{label ? 'Guardado' : 'Sin etiquetar'}</small></div>
    <div className="knowledge-label-group"><small>Decisión</small><div>{utilityOptions.map(([value, text]) => <button className={current.utility_label === value ? 'chosen' : ''} type="button" key={value} onClick={() => save({ utility_label: value })}>{text}</button>)}</div></div>
    <div className="knowledge-label-group"><small>Tipo de plano</small><div>{shotOptions.map(([value, text]) => <button className={current.shot_type === value ? 'chosen' : ''} type="button" key={value} onClick={() => save({ shot_type: value })}>{text}</button>)}</div></div>
    <div className="knowledge-label-group"><small>Movimiento</small><div>{motionOptions.map(([value, text]) => <button className={current.motion_quality === value ? 'chosen' : ''} type="button" key={value} onClick={() => save({ motion_quality: value })}>{text}</button>)}</div></div>
  </section>
}
