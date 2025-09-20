import { useState, useEffect } from 'react'
import { RefreshCw, Clock, User, Play, CheckCircle, UserX } from 'lucide-react'
import { triageAPI } from '../services/api'
import '../Glass.css'

const QueueMonitor = () => {
  const [queueData, setQueueData] = useState([])
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(new Date())
  const [processingActions, setProcessingActions] = useState(new Set())

  useEffect(() => {
    // Load real queue data on component mount
    loadQueueData()
  }, [])

  const loadQueueData = async () => {
    try {
      const response = await triageAPI.getQueue()
      setQueueData(response.data)
      setLastUpdated(new Date())
    } catch (error) {
      console.error('Failed to load queue data:', error)
    }
  }

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        // Refresh with real data from MongoDB
        loadQueueData()
      }, 10000) // Update every 10 seconds

      return () => clearInterval(interval)
    }
  }, [autoRefresh])

  const getESIColor = (level) => {
    const colors = {
      1: 'bg-red-600 text-white',
      2: 'bg-orange-500 text-white',
      3: 'bg-yellow-400 text-black',
      4: 'bg-green-400 text-black',
      5: 'bg-green-500 text-white'
    }
    return colors[level] || 'bg-gray-400 text-white'
  }

  const getRowClass = (level) => {
    const classes = {
      1: 'bg-red-50 border-l-4 border-red-500',
      2: 'bg-orange-50 border-l-4 border-orange-500',
      3: 'bg-yellow-50 border-l-4 border-yellow-500',
      4: 'bg-green-50 border-l-4 border-green-500',
      5: 'bg-green-50 border-l-4 border-green-600'
    }
    return classes[level] || 'bg-white'
  }

  const refreshQueue = async () => {
    await loadQueueData()
  }

  const handleStartTreatment = async (patientId, patientName) => {
    if (processingActions.has(patientId)) return

    setProcessingActions(prev => new Set(prev).add(patientId))
    try {
      await triageAPI.startTreatment(patientId)
      await loadQueueData() // Refresh the queue
      console.log(`Started treatment for ${patientName}`)
    } catch (error) {
      console.error('Failed to start treatment:', error)
      alert('Failed to start treatment. Please try again.')
    } finally {
      setProcessingActions(prev => {
        const newSet = new Set(prev)
        newSet.delete(patientId)
        return newSet
      })
    }
  }

  const handleCompleteTreatment = async (patientId, patientName) => {
    if (processingActions.has(patientId)) return

    setProcessingActions(prev => new Set(prev).add(patientId))
    try {
      await triageAPI.completeTreatment(patientId)
      await loadQueueData() // Refresh the queue
      console.log(`Completed treatment for ${patientName}`)
    } catch (error) {
      console.error('Failed to complete treatment:', error)
      alert('Failed to complete treatment. Please try again.')
    } finally {
      setProcessingActions(prev => {
        const newSet = new Set(prev)
        newSet.delete(patientId)
        return newSet
      })
    }
  }

  const handleDischargePatient = async (patientId, patientName) => {
    if (processingActions.has(patientId)) return

    if (!confirm(`Are you sure you want to discharge ${patientName}?`)) return

    setProcessingActions(prev => new Set(prev).add(patientId))
    try {
      await triageAPI.dischargePatient(patientId)
      await loadQueueData() // Refresh the queue
      console.log(`Discharged ${patientName}`)
    } catch (error) {
      console.error('Failed to discharge patient:', error)
      alert('Failed to discharge patient. Please try again.')
    } finally {
      setProcessingActions(prev => {
        const newSet = new Set(prev)
        newSet.delete(patientId)
        return newSet
      })
    }
  }

  const renderActionButtons = (patient) => {
    const isProcessing = processingActions.has(patient.patient_id)
    const patientName = patient.patient_name || `Patient ${patient.patient_id}`

    return (
      <div className="flex space-x-1">
        {patient.status === 'waiting' && (
          <button
            onClick={() => handleStartTreatment(patient.patient_id, patientName)}
            disabled={isProcessing}
            className="glass-button flex items-center space-x-1 px-2 py-1 text-blue-600 text-xs rounded disabled:opacity-50"
            title="Start Treatment"
          >
            <Play size={12} />
            <span>Start</span>
          </button>
        )}

        {patient.status === 'in_treatment' && (
          <button
            onClick={() => handleCompleteTreatment(patient.patient_id, patientName)}
            disabled={isProcessing}
            className="glass-button flex items-center space-x-1 px-2 py-1 text-green-600 text-xs rounded disabled:opacity-50"
            title="Complete Treatment"
          >
            <CheckCircle size={12} />
            <span>Complete</span>
          </button>
        )}

        {(patient.status === 'waiting' || patient.status === 'in_treatment' || patient.status === 'completed') && (
          <button
            onClick={() => handleDischargePatient(patient.patient_id, patientName)}
            disabled={isProcessing}
            className="glass-button flex items-center space-x-1 px-2 py-1 text-orange-600 text-xs rounded disabled:opacity-50"
            title="Discharge Patient"
          >
            <UserX size={12} />
            <span>Discharge</span>
          </button>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-800">Emergency Department Queue</h1>
        <div className="flex items-center space-x-4">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded"
            />
            <span className="text-sm font-medium">Auto-refresh (every 10 seconds)</span>
          </label>
          <button
            onClick={refreshQueue}
            className="glass-button flex items-center space-x-2 px-4 py-2 text-blue-600 rounded-lg hover:text-blue-700"
          >
            <RefreshCw size={16} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      <div className="glass-card p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium text-gray-600">Live Queue</span>
            </div>
            <span className="text-sm text-gray-500">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </span>
          </div>
          <div className="text-sm text-gray-600">
            Total patients waiting: {queueData.filter(p => p.status === 'waiting').length}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 font-semibold text-gray-800">Position</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-800">Patient Name</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-800">ESI Level</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-800">Chief Complaint</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-800">Priority Score</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-800">Wait Time</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-800">Status</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-800">Actions</th>
              </tr>
            </thead>
            <tbody>
              {queueData.map((patient, index) => (
                <tr
                  key={patient.patient_id}
                  className={`border-b border-gray-100 hover:bg-gray-50 ${getRowClass(patient.esi_level)}`}
                >
                  <td className="py-4 px-4 font-medium">#{patient.queue_position}</td>
                  <td className="py-4 px-4 font-medium">
                    {patient.patient_name || `Patient ${patient.patient_id}`}
                    <br />
                    <span className="text-sm text-gray-500">ID: {patient.patient_id}</span>
                  </td>
                  <td className="py-4 px-4">
                    <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getESIColor(patient.esi_level)}`}>
                      Level {patient.esi_level}
                    </span>
                  </td>
                  <td className="py-4 px-4">{patient.chief_complaint}</td>
                  <td className="py-4 px-4 font-medium">{patient.priority_score.toFixed(1)}</td>
                  <td className="py-4 px-4">
                    <div className="flex items-center space-x-1">
                      <Clock size={16} className="text-gray-500" />
                      <span className={`font-medium ${patient.wait_time_minutes > 60 ? 'text-red-600' : 'text-gray-800'}`}>
                        {patient.wait_time_minutes} min
                      </span>
                    </div>
                  </td>
                  <td className="py-4 px-4">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      patient.status === 'waiting' ? 'bg-yellow-100 text-yellow-800' :
                      patient.status === 'in_treatment' ? 'bg-blue-100 text-blue-800' :
                      patient.status === 'completed' ? 'bg-green-100 text-green-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {patient.status.replace('_', ' ').toUpperCase()}
                    </span>
                  </td>
                  <td className="py-4 px-4">
                    {renderActionButtons(patient)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Queue Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Critical Patients</h3>
          <div className="text-3xl font-bold text-red-600">
            {queueData.filter(p => p.esi_level <= 2).length}
          </div>
          <p className="text-gray-600 text-sm">ESI Levels 1-2</p>
        </div>

        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Average Wait Time</h3>
          <div className="text-3xl font-bold text-blue-600">
            {queueData.length > 0 ? Math.round(queueData.reduce((acc, p) => acc + p.wait_time_minutes, 0) / queueData.length) : 0} min
          </div>
          <p className="text-gray-600 text-sm">All patients</p>
        </div>

        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Longest Wait</h3>
          <div className="text-3xl font-bold text-orange-600">
            {queueData.length > 0 ? Math.max(...queueData.map(p => p.wait_time_minutes)) : 0} min
          </div>
          <p className="text-gray-600 text-sm">Single patient</p>
        </div>
      </div>

      {/* ESI Level Legend */}
      <div className="glass-card p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">ESI Level Guide</h3>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {[
            { level: 1, name: 'Resuscitation', description: 'Immediate life-saving intervention', color: 'bg-red-600' },
            { level: 2, name: 'Emergent', description: 'High risk, time-critical', color: 'bg-orange-500' },
            { level: 3, name: 'Urgent', description: 'Stable but needs timely care', color: 'bg-yellow-400' },
            { level: 4, name: 'Less Urgent', description: 'Stable, can wait', color: 'bg-green-400' },
            { level: 5, name: 'Non-Urgent', description: 'Minor issues', color: 'bg-green-500' }
          ].map((item) => (
            <div key={item.level} className="text-center">
              <div className={`${item.color} text-white rounded-lg p-3 mb-2`}>
                <div className="text-2xl font-bold">{item.level}</div>
                <div className="text-sm font-medium">{item.name}</div>
              </div>
              <p className="text-xs text-gray-600">{item.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default QueueMonitor