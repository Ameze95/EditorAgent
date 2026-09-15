import type { Clip, Segment } from '../../types/review'
import type { Project } from '../../types/project'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8765'

export type AnalysisJob = {
  id: string
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled'
  total: number
  completed: number
  progress: number
  current_clip_id: string | null
  current_progress: number
  current_phase: string
  current_frames: number
  current_total_frames: number
  errors: Record<string, string>
}

export type AnalysisProfile = {
  name: string
  parameters: Record<string, number>
}

export type AnalysisRun = {
  id: string
  clip_id: string
  profile_name: string
  status: string
  started_at: string
  finished_at: string | null
  windows_path: string | null
}

export type AnalysisWindow = {
  start_seconds: number
  end_seconds: number
  sharpness_norm: number
  exposure_norm: number
  motion_norm: number
  direction_coherence: number
  jerk_norm: number
  tracking_confidence: number
  stability_norm: number
  hard_turn_ratio?: number
  hard_brake_ratio?: number
  reasons: string[]
  penalties: string[]
}

export type AnnotationInterval = {
  start_seconds: number
  end_seconds: number
  label: string
  reason?: string | null
  confidence?: string | null
}

export type HumanLabel = {
  id: string
  clip_id: string
  analysis_run_id: string | null
  segment_id: string | null
  start_seconds: number
  end_seconds: number
  utility_label: string
  shot_type: string | null
  motion_quality: string | null
  rejection_reason: string | null
  confidence: string | null
  note: string | null
  annotator: string
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init)
  if (!response.ok) {
    const detail = await response.json().catch(() => null) as { detail?: string } | null
    throw new Error(detail?.detail ?? `API request failed: ${response.status}`)
  }
  return response.json() as Promise<T>
}

export const reviewApi = {
  listProjects: () => request<Project[]>('/projects'),
  createProject: (name: string, parentPath?: string) => request<Project>('/projects', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, parent_path: parentPath }) }),
  updateProject: (id: string, patch: { name?: string; parent_path?: string }) => request<Project>(`/projects/${id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(patch) }),
  deleteProject: (id: string) => request<{ status: string }>(`/projects/${id}`, { method: 'DELETE' }),
  selectProject: (id: string) => request<Project>(`/active-project/${id}`, { method: 'POST' }),
  exportApproved: () => request<{ path: string; segment_count: number }>('/exports/fcpxml', { method: 'POST' }),
  exportApprovedEdl: () => request<{ path: string; segment_count: number }>('/exports/edl', { method: 'POST' }),
  exportDatasetJson: () => request<{ path: string; segment_count: number }>('/exports/dataset/json', { method: 'POST' }),
  exportDatasetCsv: () => request<{ path: string; segment_count: number }>('/exports/dataset/csv', { method: 'POST' }),
  learningSummary: () => request<{ clips_total: number; clips_with_segments: number; segments_total: number; segments_labeled: number; labels_total: number; uncertain_labels: number; approved_segments: number; rejected_segments: number; coverage_percent: number; utility_labels: Record<string, number>; shot_types: Record<string, number>; motion_quality: Record<string, number> }>('/learning/summary'),
  scanFolder: (folderPath: string) => request<{ media_root_path: string; inspected: number; valid: number; unsupported: number; errored: number; reused_existing_root: boolean }>('/clips/scan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ folder_path: folderPath }) }),
  selectFolderDialog: () => request<{ path: string | null }>('/dialogs/select-folder', { method: 'POST' }),
  analyzeClip: (clipId: string) => request<AnalysisJob>(`/clips/${clipId}/analyze`, { method: 'POST' }),
  analyzeAll: () => request<AnalysisJob>('/analysis/all', { method: 'POST' }),
  getAnalysisJob: (jobId: string) => request<AnalysisJob>(`/analysis/jobs/${jobId}`),
  cancelAnalysisJob: (jobId: string) => request<AnalysisJob>(`/analysis/jobs/${jobId}`, { method: 'DELETE' }),
  listAnalysisProfiles: () => request<AnalysisProfile[]>('/analysis/profiles'),
  listAnalysisRuns: () => request<AnalysisRun[]>('/analysis/runs'),
  getAnalysisWindows: (runId: string) => request<AnalysisWindow[]>(`/analysis/runs/${runId}/windows`),
  getAnnotations: (runId: string) => request<{ intent_profile: string; intervals: AnnotationInterval[] }>(`/evaluation/annotations/${runId}`),
  saveAnnotations: (runId: string, document: { intent_profile: string; intervals: AnnotationInterval[] }) => request<{ intent_profile: string; intervals: AnnotationInterval[] }>(`/evaluation/annotations/${runId}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(document) }),
  listLabels: (clipId?: string) => request<HumanLabel[]>(`/labels${clipId ? `?clip_id=${encodeURIComponent(clipId)}` : ''}`),
  saveLabel: (label: Omit<HumanLabel, 'id' | 'annotator'> & { id?: string; annotator?: string }) => request<HumanLabel>('/labels', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(label) }),
  listClips: () => request<Clip[]>('/clips'),
  listSegments: () => request<Segment[]>('/segments'),
  updateSegment: (id: string, patch: Partial<Pick<Segment, 'status' | 'start_seconds' | 'end_seconds' | 'user_note'>>) =>
    request<Segment>(`/segments/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patch),
    }),
  createManualSegment: (clipId: string, startSeconds: number, endSeconds: number) => request<Segment>('/segments/manual', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ clip_id: clipId, start_seconds: startSeconds, end_seconds: endSeconds }) }),
}
