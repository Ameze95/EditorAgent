import type { FormEvent } from 'react'
import { useEffect, useState } from 'react'
import { Eyebrow } from '../components/atoms/Eyebrow'
import { reviewApi } from '../lib/api/client'
import type { Project } from '../types/project'

type ProjectsPageProps = { onOpen: () => void }

type EditState = { id: string; name: string; parentPath: string }

export function ProjectsPage({ onOpen }: ProjectsPageProps) {
  const [projects, setProjects] = useState<Project[]>([])
  const [name, setName] = useState('')
  const [parentPath, setParentPath] = useState('')
  const [editing, setEditing] = useState<EditState | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const load = async () => {
    try { setProjects(await reviewApi.listProjects()); setError(null) } catch { setError('No se pudo cargar la lista de proyectos.') }
  }
  useEffect(() => { const timer = window.setTimeout(() => void load(), 0); return () => window.clearTimeout(timer) }, [])

  const chooseFolder = async (setter: (path: string) => void) => {
    try {
      const result = await reviewApi.selectFolderDialog()
      if (result.path) setter(result.path)
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'No se pudo abrir el selector de carpetas.') }
  }

  const create = async (event: FormEvent) => {
    event.preventDefault()
    if (!name.trim()) return
    setBusy(true)
    try { await reviewApi.createProject(name.trim(), parentPath.trim() || undefined); setName(''); setParentPath(''); await load() } catch (reason) { setError(reason instanceof Error ? reason.message : 'No se pudo crear el proyecto.') } finally { setBusy(false) }
  }

  const saveEdit = async () => {
    if (!editing) return
    const moving = editing.parentPath.trim() !== ''
    if (moving && !window.confirm('Mover el proyecto cambiará la ubicación de sus artefactos. Los vídeos originales no se moverán. ¿Continuar?')) return
    setBusy(true)
    try { await reviewApi.updateProject(editing.id, { name: editing.name.trim(), ...(moving ? { parent_path: editing.parentPath.trim() } : {}) }); setEditing(null); await load() } catch (reason) { setError(reason instanceof Error ? reason.message : 'No se pudo editar el proyecto.') } finally { setBusy(false) }
  }

  const remove = async (project: Project) => {
    if (!window.confirm(`Se eliminará la carpeta de artefactos de “${project.name}”. Los originales y las carpetas de medios no se tocarán. ¿Continuar?`)) return
    setBusy(true)
    try { await reviewApi.deleteProject(project.id); await load() } catch (reason) { setError(reason instanceof Error ? reason.message : 'No se pudo eliminar el proyecto.') } finally { setBusy(false) }
  }

  const open = async (project: Project) => {
    setBusy(true)
    try { await reviewApi.selectProject(project.id); onOpen() } catch { setError('No se pudo abrir el proyecto.') } finally { setBusy(false) }
  }

  return <main className="projects-shell"><header className="projects-header"><div className="brand-lockup"><span className="brand-mark">EA</span><div><Eyebrow>PROJECT DESK</Eyebrow><h1>EditorAgent</h1></div></div><span className="live-dot" /></header><section className="projects-content"><div><Eyebrow>WORKSPACE LOCAL</Eyebrow><h2>Tus proyectos</h2><p className="projects-lead">Los artefactos se guardan fuera del código del producto. Los medios originales siempre permanecen en modo sólo lectura.</p></div>{error && <div className="notice">{error}</div>}<form className="create-project create-project-expanded" onSubmit={(event) => void create(event)}><input value={name} onChange={(event) => setName(event.target.value)} placeholder="Nombre del nuevo proyecto" aria-label="Nombre del nuevo proyecto" /><div className="project-path-control"><input value={parentPath} onChange={(event) => setParentPath(event.target.value)} placeholder="Carpeta contenedora (por defecto: projects)" aria-label="Carpeta contenedora del proyecto" /><button type="button" onClick={() => void chooseFolder(setParentPath)}>Elegir carpeta</button></div><button type="submit" disabled={busy}>Crear proyecto</button></form><div className="project-list">{projects.map((project) => editing?.id === project.id ? <div className="project-edit panel" key={project.id}><input value={editing.name} onChange={(event) => setEditing({ ...editing, name: event.target.value })} aria-label="Nombre del proyecto" /><input value={editing.parentPath} onChange={(event) => setEditing({ ...editing, parentPath: event.target.value })} placeholder="Nueva carpeta contenedora (vacío = no mover)" aria-label="Nueva carpeta contenedora" /><div><button type="button" onClick={() => void chooseFolder((path) => setEditing({ ...editing, parentPath: path }))}>Elegir carpeta</button><button type="button" onClick={() => void saveEdit()} disabled={busy}>Guardar</button><button type="button" onClick={() => setEditing(null)}>Cancelar</button></div></div> : <div className={`project-card ${project.active ? 'active' : ''}`} key={project.id}><button className="project-open-area" type="button" onClick={() => void open(project)}><span className="project-icon">{project.name.slice(0, 1).toUpperCase()}</span><span><strong>{project.name}</strong><small>{project.root_path}</small></span><span className="project-open">{project.active ? 'Activo' : 'Abrir'} →</span></button><div className="project-actions"><button type="button" onClick={() => setEditing({ id: project.id, name: project.name, parentPath: '' })}>Editar</button><button type="button" onClick={() => void remove(project)}>Eliminar</button></div></div>)}{!projects.length && <p className="list-empty">Aún no hay proyectos en este workspace.</p>}</div></section></main>
}
