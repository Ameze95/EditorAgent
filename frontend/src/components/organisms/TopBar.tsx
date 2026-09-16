import { useRef, useState } from 'react'
import { Eyebrow } from '../atoms/Eyebrow'

type ExportFormat = 'davinci' | 'premiere' | 'dataset-json' | 'dataset-csv'
type TopBarProps = { onRefresh: () => void; onBack: () => void; onExport: (format: ExportFormat) => void; onCalibration: () => void; onLearning: () => void }

const SECRET_CLICKS_REQUIRED = 5
const SECRET_CLICKS_TIMEOUT_MS = 1500

export function TopBar({ onRefresh, onBack, onExport, onCalibration, onLearning }: TopBarProps) {
  const [open, setOpen] = useState(false)
  const secretClicksRef = useRef(0)
  const secretClicksTimerRef = useRef<number | undefined>(undefined)

  const handleLogoClick = () => {
    secretClicksRef.current += 1
    window.clearTimeout(secretClicksTimerRef.current)
    if (secretClicksRef.current >= SECRET_CLICKS_REQUIRED) {
      secretClicksRef.current = 0
      onCalibration()
      return
    }
    secretClicksTimerRef.current = window.setTimeout(() => { secretClicksRef.current = 0 }, SECRET_CLICKS_TIMEOUT_MS)
  }

  return <header className="topbar"><div className="brand-lockup"><button className="back-button" type="button" onClick={onBack} aria-label="Volver a proyectos">←</button><span className="brand-mark" onClick={handleLogoClick} role="button" tabIndex={-1}>EA</span><div><Eyebrow>LOCAL REVIEW DESK</Eyebrow><h1>EditorAgent</h1></div></div><div className="topbar-meta"><span className="live-dot" /> Solo lectura de originales <button className="quiet-button" type="button" onClick={onRefresh}>Actualizar</button><button className="quiet-button" type="button" onClick={onLearning}>Aprendizaje</button><div className="export-menu"><button className="export-button" type="button" onClick={() => setOpen((value) => !value)} aria-expanded={open}>Exportar ▾</button>{open && <div className="export-options"><button type="button" onClick={() => { setOpen(false); onExport('davinci') }}>DaVinci Resolve · FCPXML</button><button type="button" onClick={() => { setOpen(false); onExport('premiere') }}>Premiere Pro · EDL</button><button type="button" onClick={() => { setOpen(false); onExport('dataset-json') }}>Dataset de conocimiento · JSON</button><button type="button" onClick={() => { setOpen(false); onExport('dataset-csv') }}>Dataset de conocimiento · CSV</button></div>}</div></div></header>
}
