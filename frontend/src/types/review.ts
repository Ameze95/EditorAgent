export type Clip = {
  id: string
  relative_path: string
  duration_seconds: number | null
  width: number | null
  height: number | null
  fps_num: number | null
  fps_den: number | null
  ingest_status?: string
  analysis_status?: 'not_started' | 'running' | 'completed' | 'failed'
  segment_count?: number
}

export type SegmentStatus = 'suggested' | 'approved' | 'rejected' | 'manual'

export type Segment = {
  id: string
  clip_id: string
  start_seconds: number
  end_seconds: number
  duration_seconds: number
  technical_score: number
  reasons: string[]
  penalties: string[]
  status: SegmentStatus
  user_note: string | null
}
