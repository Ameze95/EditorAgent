import { useEffect, useRef, useState } from 'react'
import { Eyebrow } from '../atoms/Eyebrow'
import type { Clip, Segment } from '../../types/review'

const time = (seconds: number) => `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(Math.floor(seconds % 60)).padStart(2, '0')}`

type ReviewViewerProps = {
  clip?: Clip
  segment: Segment | null
  segments: Segment[]
  onSetIn: (seconds: number) => void
  onSetOut: (seconds: number) => void
  onCreateSegment: (startSeconds: number, endSeconds: number) => void
  onMoveClip: (offset: number) => void
  onMoveSegment: (offset: number) => void
  onSelectSegment: (id: string) => void
}

export function ReviewViewer({ clip, segment, segments, onSetIn, onSetOut, onCreateSegment, onMoveClip, onMoveSegment, onSelectSegment }: ReviewViewerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const timelineRef = useRef<HTMLDivElement>(null)
  const [mediaError, setMediaError] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const duration = clip?.duration_seconds || 1
  const segmentStart = segment?.start_seconds

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setMediaError(false)
      setCurrentTime(segmentStart ?? 0)
      if (videoRef.current && segmentStart !== undefined) videoRef.current.currentTime = segmentStart
    }, 0)
    return () => window.clearTimeout(timer)
  }, [clip?.id, segment?.id, segmentStart])

  const seekFromPointer = (clientX: number) => {
    if (!videoRef.current || !timelineRef.current) return
    const bounds = timelineRef.current.getBoundingClientRect()
    const ratio = Math.max(0, Math.min(1, (clientX - bounds.left) / bounds.width))
    videoRef.current.currentTime = ratio * duration
    setCurrentTime(videoRef.current.currentTime)
  }

  const createFromPosition = () => {
    const end = Math.min(duration, currentTime + Math.min(4, duration - currentTime))
    if (end > currentTime + 0.01) onCreateSegment(currentTime, end)
  }

  const currentPercent = Math.max(0, Math.min(100, currentTime / duration * 100))

  return <section className="viewer panel">
    <div className="viewer-header"><div><Eyebrow>REVIEW / 01</Eyebrow><h2>{clip?.relative_path ?? 'Selecciona un clip'}</h2></div><span className="source-chip">{clip ? `${clip.width} × ${clip.height} · ${clip.fps_num}/{clip.fps_den} fps` : 'Sin clip'}</span></div>
    <div className="video-stage">
      {clip ? <>{!mediaError && <video ref={videoRef} key={clip.id} className="review-video" src={`http://127.0.0.1:8765/clips/${clip.id}/media`} controls preload="metadata" onTimeUpdate={(event) => setCurrentTime(event.currentTarget.currentTime)} onError={() => setMediaError(true)} />}{mediaError && <div className="stage-message"><strong>El navegador no puede reproducir este HEVC directamente.</strong><small>Generaremos un proxy compatible en el siguiente paso.</small></div>}</> : <div className="stage-message"><strong>Selecciona un clip para empezar.</strong></div>}
      <span className="timecode">{time(currentTime)}{segment ? ` · segmento ${time(segment.start_seconds)} — ${time(segment.end_seconds)}` : ''}</span>
    </div>
    <div className="timeline" ref={timelineRef} onClick={(event) => seekFromPointer(event.clientX)} role="slider" aria-label="Posición del vídeo" aria-valuemin={0} aria-valuemax={duration} aria-valuenow={currentTime} tabIndex={0}>
      <div className="timeline-track">{segments.map((item, index) => <button className={`timeline-segment segment-color-${index % 6} ${item.id === segment?.id ? 'selected' : ''}`} key={item.id} type="button" title={`${time(item.start_seconds)} - ${time(item.end_seconds)}`} style={{ left: `${item.start_seconds / duration * 100}%`, width: `${item.duration_seconds / duration * 100}%` }} onClick={(event) => { event.stopPropagation(); onSelectSegment(item.id); if (videoRef.current) videoRef.current.currentTime = item.start_seconds; setCurrentTime(item.start_seconds) }} aria-label={`Seleccionar segmento ${index + 1}`} />)}<span className="timeline-playhead" style={{ left: `${currentPercent}%` }} /></div>
      <div className="timeline-labels"><span>00:00</span><span>{time(duration)}</span></div>
    </div>
    <div className="viewer-actions">
      <button type="button" onClick={() => onMoveClip(-1)} disabled={!clip}>Clip anterior</button>
      <button type="button" onClick={() => onMoveClip(1)} disabled={!clip}>Clip siguiente</button>
      <button type="button" onClick={() => onMoveSegment(-1)} disabled={!segment}>Segmento anterior</button>
      <button type="button" onClick={() => onMoveSegment(1)} disabled={!segment}>Segmento siguiente</button>
      <button type="button" onClick={() => onSetIn(currentTime)} disabled={!clip || !segment}>Marcar IN</button>
      <button type="button" onClick={() => onSetOut(currentTime)} disabled={!clip || !segment}>Marcar OUT</button>
      <button className="create-segment-button" type="button" onClick={createFromPosition} disabled={!clip}>Crear segmento desde aquí</button>
    </div>
  </section>
}
