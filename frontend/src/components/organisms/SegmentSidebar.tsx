import { Eyebrow } from '../atoms/Eyebrow'
import { SegmentRow } from '../molecules/SegmentRow'
import type { Clip, Segment } from '../../types/review'

type SegmentSidebarProps = { clips: Clip[]; segments: Segment[]; selectedId: string | null; onSelect: (id: string) => void }

export function SegmentSidebar({ clips, segments, selectedId, onSelect }: SegmentSidebarProps) {
  const groups = clips
    .map((clip) => ({ clip, items: segments.filter((segment) => segment.clip_id === clip.id) }))
    .filter((group) => group.items.length > 0)

  return <aside className="sidebar panel"><div className="panel-heading"><div><Eyebrow>INVENTARIO</Eyebrow><h2>Clips y selects</h2></div><span className="count-badge">{segments.length}</span></div><div className="filter-row"><button className="filter active" type="button">Todos {segments.length}</button><button className="filter" type="button">Aprobados</button></div><div className="segment-list">
    {groups.map(({ clip, items }) => <div className="clip-group" key={clip.id}>
      <div className="clip-group-header"><span className="clip-group-name">{clip.relative_path}</span><span className="clip-group-count">{items.length} select{items.length === 1 ? '' : 's'}</span></div>
      {items.map((segment, index) => <SegmentRow key={segment.id} segment={segment} index={index} selected={segment.id === selectedId} onSelect={() => onSelect(segment.id)} />)}
    </div>)}
    {!segments.length && <div className="list-empty">No hay candidatos persistidos para este proyecto.</div>}
  </div></aside>
}
