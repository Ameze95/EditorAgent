import { useCallback, useEffect, useMemo, useState } from 'react'
import { reviewApi, type AnalysisJob, type HumanLabel } from '../lib/api/client'
import type { Clip, Segment } from '../types/review'

export function useReviewData() {
  const [clips, setClips] = useState<Clip[]>([])
  const [segments, setSegments] = useState<Segment[]>([])
  const [selectedClipId, setSelectedClipId] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [analysisJob, setAnalysisJob] = useState<AnalysisJob | null>(null)
  const [labels, setLabels] = useState<HumanLabel[]>([])

  const reload = useCallback(async () => {
    setLoading(true)
    try {
      const [loadedClips, loadedSegments, loadedLabels] = await Promise.all([reviewApi.listClips(), reviewApi.listSegments(), reviewApi.listLabels()])
      setClips(loadedClips)
      setSegments(loadedSegments)
      setLabels(loadedLabels)
      setSelectedClipId((current) => current ?? loadedClips[0]?.id ?? null)
      setSelectedId((current) => current ?? loadedSegments[0]?.id ?? null)
      setError(null)
    } catch {
      setError('No se pudo conectar con la API local. Arranca el stack desde scripts/start-dev.ps1.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => void reload(), 0)
    return () => window.clearTimeout(timer)
  }, [reload])

  useEffect(() => {
    if (!analysisJob || ['completed', 'failed', 'cancelled'].includes(analysisJob.status)) return
    const timer = window.setInterval(() => {
      void reviewApi.getAnalysisJob(analysisJob.id).then((job) => {
        setAnalysisJob(job)
        if (['completed', 'failed', 'cancelled'].includes(job.status)) void reload()
      }).catch(() => setError('No se pudo consultar el progreso del análisis.'))
    }, 1000)
    return () => window.clearInterval(timer)
  }, [analysisJob, reload])

  const selectedClip = clips.find((item) => item.id === selectedClipId)
  const clipSegments = useMemo(
    () => segments
      .filter((item) => item.clip_id === selectedClipId)
      .sort((first, second) => first.start_seconds - second.start_seconds),
    [segments, selectedClipId],
  )
  const selected = useMemo(
    () => clipSegments.find((item) => item.id === selectedId) ?? clipSegments[0] ?? null,
    [clipSegments, selectedId],
  )
  const selectedLabel = useMemo(
    () => labels.find((label) => label.segment_id === selected?.id) ?? null,
    [labels, selected],
  )

  const selectClip = useCallback((clipId: string) => {
    setSelectedClipId(clipId)
    setSelectedId((current) => {
      const currentSegment = segments.find((item) => item.id === current)
      return currentSegment?.clip_id === clipId
        ? current
        : segments.find((item) => item.clip_id === clipId)?.id ?? null
    })
  }, [segments])

  const moveClip = useCallback((offset: number) => {
    if (!selectedClipId || !clips.length) return
    const currentIndex = clips.findIndex((clip) => clip.id === selectedClipId)
    const nextIndex = Math.max(0, Math.min(clips.length - 1, currentIndex + offset))
    if (nextIndex !== currentIndex) selectClip(clips[nextIndex].id)
  }, [clips, selectedClipId, selectClip])

  const moveSegment = useCallback((offset: number) => {
    if (!clipSegments.length) return
    const currentIndex = clipSegments.findIndex((item) => item.id === selectedId)
    const nextIndex = Math.max(0, Math.min(clipSegments.length - 1, currentIndex + offset))
    setSelectedId(clipSegments[nextIndex].id)
  }, [clipSegments, selectedId])

  const updateSegment = async (patch: Partial<Pick<Segment, 'status' | 'start_seconds' | 'end_seconds' | 'user_note'>>) => {
    if (!selected) return
    setSaving(true)
    try {
      const updated = await reviewApi.updateSegment(selected.id, patch)
      setSegments((items) => items.map((item) => item.id === updated.id ? updated : item))
      setError(null)
    } catch {
      setError('No se pudo guardar la revisión.')
    } finally { setSaving(false) }
  }

  const createManualSegment = async (startSeconds: number, endSeconds: number) => {
    if (!selectedClipId) return
    const requestedDuration = endSeconds - startSeconds
    const clipDuration = selectedClip?.duration_seconds ?? endSeconds
    const ordered = [...clipSegments].sort((first, second) => first.start_seconds - second.start_seconds)
    let candidateStart = Math.max(0, startSeconds)
    for (const existing of ordered) {
      if (candidateStart + requestedDuration <= existing.start_seconds) break
      if (candidateStart < existing.end_seconds) candidateStart = existing.end_seconds
    }
    const candidateEnd = Math.min(clipDuration, candidateStart + requestedDuration)
    if (candidateEnd <= candidateStart) {
      setError('No queda espacio libre para crear otro segmento en este clip.')
      return
    }
    try {
      const created = await reviewApi.createManualSegment(selectedClipId, candidateStart, candidateEnd)
      setSegments((items) => [...items, created])
      setSelectedId(created.id)
      setError(null)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No se pudo crear el segmento manual.')
    }
  }

  const startAnalysis = async (clipId: string) => {
    try {
      setAnalysisJob(await reviewApi.analyzeClip(clipId))
      setError(null)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No se pudo iniciar el análisis.')
    }
  }

  const startAnalysisAll = async () => {
    try {
      setAnalysisJob(await reviewApi.analyzeAll())
      setError(null)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No se pudo iniciar el análisis.')
    }
  }

  const cancelAnalysis = async () => {
    if (!analysisJob) return
    setAnalysisJob(await reviewApi.cancelAnalysisJob(analysisJob.id))
  }

  const saveLabel = async (patch: Pick<HumanLabel, 'utility_label' | 'shot_type' | 'motion_quality' | 'rejection_reason' | 'confidence' | 'note'>) => {
    if (!selected || !selectedClip) return
    try {
      const saved = await reviewApi.saveLabel({
        ...patch,
        id: selectedLabel?.id,
        clip_id: selected.clip_id,
        segment_id: selected.id,
        analysis_run_id: null,
        start_seconds: selected.start_seconds,
        end_seconds: selected.end_seconds,
      })
      setLabels((items) => [...items.filter((item) => item.id !== saved.id && item.segment_id !== saved.segment_id), saved])
      setError(null)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No se pudo guardar la etiqueta.')
    }
  }

  return { clips, segments: clipSegments, selected, selectedClip, selectedClipId, selectClip, moveClip, selectedId, setSelectedId, moveSegment, selectedLabel, loading, error, saving, reload, updateSegment, createManualSegment, setSegments, analysisJob, startAnalysis, startAnalysisAll, cancelAnalysis, saveLabel }
}
