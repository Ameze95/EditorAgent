import { Eyebrow } from '../atoms/Eyebrow'
import { SegmentRow } from '../molecules/SegmentRow'
import type { Segment } from '../../types/review'

type SegmentListProps = {
  segments: Segment[]
  selectedId: string | null
  onSelect: (id: string) => void
}

export function SegmentList({ segments, selectedId, onSelect }: SegmentListProps) {
  return <section className="segment-panel panel">
    <div className="panel-heading"><div><Eyebrow>RESULTADO</Eyebrow><h2>Cortes seleccionados</h2></div><span className="count-badge">{segments.length}</span></div>
    <div className="segment-list">
      {segments.map((segment, index) => <SegmentRow key={segment.id} segment={segment} index={index} selected={segment.id === selectedId} onSelect={() => onSelect(segment.id)} />)}
      {!segments.length && <div className="list-empty">Este clip todavía no tiene segmentos analizados.</div>}
    </div>
  </section>
}
