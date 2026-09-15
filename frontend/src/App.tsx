import { useState } from 'react'
import { ReviewPage } from './pages/ReviewPage'
import { ProjectsPage } from './pages/ProjectsPage'
import { CalibrationPage } from './pages/CalibrationPage'
import { LearningPage } from './pages/LearningPage'
import './styles/review.css'

function App() {
  const [view, setView] = useState<'projects' | 'review' | 'calibration' | 'learning'>('projects')
  if (view === 'projects') return <ProjectsPage onOpen={() => setView('review')} />
  if (view === 'calibration') return <CalibrationPage onBack={() => setView('review')} />
  if (view === 'learning') return <LearningPage onBack={() => setView('review')} />
  return <ReviewPage onBack={() => setView('projects')} onCalibration={() => setView('calibration')} onLearning={() => setView('learning')} />
}

export default App
