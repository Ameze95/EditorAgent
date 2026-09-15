import type { Segment } from '../../types/review'

const time = (seconds: number) => `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(Math.floor(seconds % 60)).padStart(2, '0')}`

type SegmentRowProps = { segment: Segment; index: number; selected: boolean; onSelect: () => void }

export function SegmentRow({ segment, index, selected, onSelect }: SegmentRowProps) {
  return <button className={`segment-row segment-color-${index % 6} ${selected ? 'selected' : ''}`} type="button" onClick={onSelect}>
    <span className="segment-color-marker" aria-hidden="true" /><span className="segment-index">{String(index + 1).padStart(2, '0')}</span>
    <span className="segment-copy"><strong>{time(segment.start_seconds)} - {time(segment.end_seconds)}</strong><small>{segment.duration_seconds.toFixed(1)}s · {segment.status}</small></span>
    <span className="score-pill">{Math.round(segment.technical_score * 100)}</span>
  </button>
}
