import { useState } from 'react'
import { Eyebrow } from '../atoms/Eyebrow'
import type { AnalysisJob } from '../../lib/api/client'
import type { Clip } from '../../types/review'

type ClipInventoryProps = {
  clips: Clip[]
  selectedClipId: string | null
  analysisJob: AnalysisJob | null
  onSelect: (clipId: string) => void
  onAnalyze: (clipId: string) => void
  onAnalyzeAll: () => void
  onCancel: () => void
}

const statusLabel: Record<string, string> = {
  not_started: 'Sin analizar',
  running: 'Analizando',
  completed: 'Analizado',
  failed: 'Error',
}

export function ClipInventory({ clips, selectedClipId, analysisJob, onSelect, onAnalyze, onAnalyzeAll, onCancel }: ClipInventoryProps) {
  const [expanded, setExpanded] = useState(true)
  const active = analysisJob && ['queued', 'running'].includes(analysisJob.status)
  return <section className={`clip-inventory panel ${expanded ? 'expanded' : 'collapsed'}`}>
    <header className="clip-inventory-header">
      <button className="collapse-button" type="button" onClick={() => setExpanded((value) => !value)} aria-expanded={expanded}>
        <span className="collapse-chevron">{expanded ? '▾' : '▸'}</span>
        <span><Eyebrow>PROYECTO</Eyebrow><strong>Clips</strong></span>
        <span className="count-badge">{clips.length}</span>
      </button>
      <div className="clip-inventory-actions">
        {active ? <button className="quiet-button" type="button" onClick={onCancel}>Cancelar · {analysisJob.progress}%</button> : <button className="analyze-all-button" type="button" onClick={onAnalyzeAll} disabled={!clips.length}>Analizar todos</button>}
      </div>
    </header>
    {active && <div className="analysis-progress" role="status"><span style={{ width: `${analysisJob.progress}%` }} /><small>{analysisJob.completed}/{analysisJob.total} clips · {analysisJob.current_progress}% clip actual · {analysisJob.progress}% total · {analysisJob.current_phase === 'sampling' ? 'muestreando frames' : 'finalizando'}</small></div>}
    {expanded && <div className="clip-inventory-list">
      {clips.map((clip) => {
        const status = clip.id === analysisJob?.current_clip_id ? 'running' : clip.analysis_status ?? (clip.segment_count ? 'completed' : 'not_started')
        const canAnalyze = !active && status !== 'running'
        return <div className={`clip-inventory-row ${clip.id === selectedClipId ? 'selected' : ''}`} key={clip.id}>
          <button className="clip-select-button" type="button" onClick={() => onSelect(clip.id)}>
            <span className="clip-status-dot" data-status={status} />
            <span className="clip-inventory-copy"><strong>{clip.relative_path}</strong><small>{statusLabel[status] ?? status} · {clip.segment_count ?? 0} segmentos</small></span>
          </button>
          <button className="clip-analyze-button" type="button" onClick={() => onAnalyze(clip.id)} disabled={!canAnalyze} aria-label={`Analizar ${clip.relative_path}`}>{status === 'completed' ? 'Reanalizar' : 'Analizar'}</button>
        </div>
      })}
      {!clips.length && <div className="list-empty">Todavía no hay clips en este proyecto.</div>}
    </div>}
  </section>
}
