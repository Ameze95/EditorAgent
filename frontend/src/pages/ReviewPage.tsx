import { ClipInventory } from '../components/organisms/ClipInventory'
import { SegmentList } from '../components/organisms/SegmentList'
import { ReviewInspector } from '../components/organisms/ReviewInspector'
import { ReviewViewer } from '../components/organisms/ReviewViewer'
import { TopBar } from '../components/organisms/TopBar'
import { ClipImportPanel } from '../components/organisms/ClipImportPanel'
import { useReviewData } from '../hooks/useReviewData'
import { reviewApi } from '../lib/api/client'
import { useEffect } from 'react'

const MAX_SHUTTLE_SPEED = 8

export function ReviewPage({ onBack, onCalibration, onLearning }: { onBack: () => void; onCalibration: () => void; onLearning: () => void }) {
  const review = useReviewData()
  const { moveClip, moveSegment, selected, updateSegment, saveLabel } = review
  const exportApproved = async (format: 'davinci' | 'premiere' | 'dataset-json' | 'dataset-csv') => {
    try {
      const result = format === 'davinci'
        ? await reviewApi.exportApproved()
        : format === 'premiere'
          ? await reviewApi.exportApprovedEdl()
          : format === 'dataset-json'
            ? await reviewApi.exportDatasetJson()
            : await reviewApi.exportDatasetCsv()
      const formatLabel = format === 'davinci' ? 'FCPXML' : format === 'premiere' ? 'EDL' : format.toUpperCase()
      window.alert(`${formatLabel} creado con ${result.segment_count} segmentos:\n${result.path}`)
    } catch (error) {
      window.alert(error instanceof Error ? error.message : 'No se pudo exportar.')
    }
  }
  const markIn = (seconds: number) => {
    if (!selected) return
    const end = Math.max(seconds + 0.01, selected.end_seconds)
    void updateSegment({ start_seconds: Math.min(seconds, end - 0.01), end_seconds: end, status: 'manual' })
  }
  const markOut = (seconds: number) => {
    if (!selected) return
    const start = Math.min(seconds - 0.01, selected.start_seconds)
    void updateSegment({ start_seconds: Math.max(0, start), end_seconds: Math.max(seconds, start + 0.01), status: 'manual' })
  }
  useEffect(() => {
    const getVideo = () => document.querySelector<HTMLVideoElement>('.review-video')
    const currentVideoTime = () => getVideo()?.currentTime ?? 0

    // Shuttle speed: positive = forward multiplier, negative = simulated reverse
    // multiplier (native <video> playbackRate can't go negative), 0 = stopped.
    let shuttleSpeed = 0
    let reverseIntervalId: number | undefined

    const stopReverse = () => {
      if (reverseIntervalId !== undefined) {
        window.clearInterval(reverseIntervalId)
        reverseIntervalId = undefined
      }
    }
    const startReverse = (video: HTMLVideoElement, speed: number) => {
      stopReverse()
      const stepMs = 50
      reverseIntervalId = window.setInterval(() => {
        const next = video.currentTime - (speed * stepMs) / 1000
        if (next <= 0) {
          video.currentTime = 0
          stopReverse()
          shuttleSpeed = 0
          return
        }
        video.currentTime = next
      }, stepMs)
    }
    const shuttleForward = () => {
      const video = getVideo()
      if (!video) return
      stopReverse()
      shuttleSpeed = shuttleSpeed > 0 ? Math.min(MAX_SHUTTLE_SPEED, shuttleSpeed * 2) : 1
      video.playbackRate = shuttleSpeed
      void video.play()
    }
    const shuttleBackward = () => {
      const video = getVideo()
      if (!video) return
      video.pause()
      shuttleSpeed = shuttleSpeed < 0 ? Math.max(-MAX_SHUTTLE_SPEED, shuttleSpeed * 2) : -1
      startReverse(video, Math.abs(shuttleSpeed))
    }
    const shuttleStop = () => {
      stopReverse()
      shuttleSpeed = 0
      const video = getVideo()
      if (video) {
        video.pause()
        video.playbackRate = 1
      }
    }

    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)) return
      // Claim every player shortcut before the browser's own scroll/activate defaults run.
      if (event.code === 'Space') {
        event.preventDefault()
        const video = getVideo()
        if (video) {
          if (video.paused) void video.play()
          else video.pause()
        }
      }
      else if (event.key.toLowerCase() === 'l') { event.preventDefault(); shuttleForward() }
      else if (event.key.toLowerCase() === 'j') { event.preventDefault(); shuttleBackward() }
      else if (event.key.toLowerCase() === 'k') { event.preventDefault(); shuttleStop() }
      else if (event.altKey && event.key.toLowerCase() === 'n') { event.preventDefault(); moveClip(1) }
      else if (event.altKey && event.key.toLowerCase() === 'p') { event.preventDefault(); moveClip(-1) }
      else if (event.key.toLowerCase() === 'n') { event.preventDefault(); moveSegment(1) }
      else if (event.key.toLowerCase() === 'p') { event.preventDefault(); moveSegment(-1) }
      else if (event.key.toLowerCase() === 'i' && selected) {
        event.preventDefault()
        const end = Math.max(currentVideoTime() + 0.01, selected.end_seconds)
        void updateSegment({ start_seconds: Math.min(currentVideoTime(), end - 0.01), end_seconds: end, status: 'manual' })
      }
      else if (event.key.toLowerCase() === 'o' && selected) {
        event.preventDefault()
        const start = Math.min(currentVideoTime() - 0.01, selected.start_seconds)
        void updateSegment({ start_seconds: Math.max(0, start), end_seconds: Math.max(currentVideoTime(), start + 0.01), status: 'manual' })
      }
      else if (event.key.toLowerCase() === 'a' && selected) { event.preventDefault(); void updateSegment({ status: 'approved' }) }
      else if (event.key.toLowerCase() === 'r' && selected) { event.preventDefault(); void updateSegment({ status: 'rejected' }) }
      else if (event.key === '1' && selected) { event.preventDefault(); void saveLabel({ utility_label: 'usable', shot_type: null, motion_quality: null, rejection_reason: null, confidence: 'high', note: null }) }
      else if (event.key === '2' && selected) { event.preventDefault(); void saveLabel({ utility_label: 'unusable', shot_type: null, motion_quality: 'abrupt', rejection_reason: 'other', confidence: 'high', note: null }) }
      else if (event.key === '3' && selected) { event.preventDefault(); void saveLabel({ utility_label: 'uncertain', shot_type: null, motion_quality: null, rejection_reason: null, confidence: 'low', note: null }) }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => {
      window.removeEventListener('keydown', onKeyDown)
      stopReverse()
    }
  }, [moveClip, moveSegment, selected, saveLabel, updateSegment])
  return <main className="workspace-shell"><TopBar onBack={onBack} onCalibration={onCalibration} onLearning={onLearning} onExport={(format) => void exportApproved(format)} onRefresh={() => void review.reload()} />{review.error && <div className="notice">{review.error}</div>}<ClipImportPanel onImported={() => void review.reload()} />{review.loading ? <div className="empty-state">Cargando revisión...</div> : <><ClipInventory analysisJob={review.analysisJob} clips={review.clips} selectedClipId={review.selectedClipId} onSelect={review.selectClip} onAnalyze={(clipId) => void review.startAnalysis(clipId)} onAnalyzeAll={() => void review.startAnalysisAll()} onCancel={() => void review.cancelAnalysis()} /><section className="review-grid"><div className="review-main"><ReviewViewer clip={review.selectedClip} segment={review.selected} segments={review.segments} onSetIn={markIn} onSetOut={markOut} onCreateSegment={(start, end) => void review.createManualSegment(start, end)} onMoveClip={review.moveClip} onMoveSegment={review.moveSegment} onSelectSegment={review.setSelectedId} /><SegmentList segments={review.segments} selectedId={review.selectedId} onSelect={review.setSelectedId} /></div><ReviewInspector segment={review.selected} label={review.selectedLabel} saving={review.saving} onUpdate={(patch) => void review.updateSegment(patch)} onLabel={(patch) => void review.saveLabel(patch)} onMoveSegment={review.moveSegment} onDraft={(patch) => review.setSegments((items) => items.map((item) => item.id === review.selected?.id ? { ...item, ...patch } : item))} /></section></>}</main>
}
