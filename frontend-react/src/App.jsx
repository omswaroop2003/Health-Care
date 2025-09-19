import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Navigation from './components/Navigation'
import Dashboard from './components/Dashboard'
import PatientIntake from './components/PatientIntake'
import VoicePatientIntake from './components/VoicePatientIntake'
import QueueMonitor from './components/QueueMonitor'
import DemoScenarios from './components/DemoScenarios'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/intake" element={<PatientIntake />} />
            <Route path="/voice-intake" element={<VoicePatientIntake />} />
            <Route path="/queue" element={<QueueMonitor />} />
            <Route path="/demo" element={<DemoScenarios />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
