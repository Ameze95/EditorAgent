import type { SegmentStatus } from '../../types/review'

type StatusDotProps = { status: SegmentStatus }

export function StatusDot({ status }: StatusDotProps) {
  return <span className={`status-dot ${status}`} aria-label={`Estado: ${status}`} />
}
