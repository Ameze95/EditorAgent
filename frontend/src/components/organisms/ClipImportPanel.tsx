import { useState } from 'react'
import { reviewApi } from '../../lib/api/client'

type ClipImportPanelProps = { onImported: () => void }

export function ClipImportPanel({ onImported }: ClipImportPanelProps) {
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState<string | null>(null)

  const browseAndImport = async () => {
    setBusy(true)
    setMessage(null)
    try {
      const { path } = await reviewApi.selectFolderDialog()
      if (!path) { setBusy(false); return }
      const result = await reviewApi.scanFolder(path)
      setMessage(`${result.valid} válidos · ${result.unsupported} no soportados · ${result.errored} con error (de ${result.inspected})`)
      onImported()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'No se pudo escanear esa carpeta.')
    } finally {
      setBusy(false)
    }
  }

  return <div className="clip-import">
    <button type="button" onClick={() => void browseAndImport()} disabled={busy}>{busy ? 'Escaneando…' : '+ Añadir clips…'}</button>
    {message && <span className="clip-import-message">{message}</span>}
  </div>
}

