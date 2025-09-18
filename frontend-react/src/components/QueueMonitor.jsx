import { useState, useEffect } from 'react'
import { RefreshCw, Clock, User } from 'lucide-react'
import { triageAPI } from '../services/api'

const QueueMonitor = () => {
  const [queueData, setQueueData] = useState([])
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(new Date())

  // Mock data for demonstration
  const mockQueueData = [
    { id: 1, patient_id: 'P1001', esi_level: 1, severity: 'Resuscitation', complaint: 'Chest pain', wait_time: 0, status: '🏥 In Treatment' },
    { id: 2, patient_id: 'P1002', esi_level: 1, severity: 'Resuscitation', complaint: 'Breathing difficulty', wait_time: 2, status: '⏳ Waiting' },
    { id: 3, patient_id: 'P1003', esi_level: 2, severity: 'Emergent', complaint: 'Severe headache', wait_time: 5, status: '⏳ Waiting' },
    { id: 4, patient_id: 'P1004', esi_level: 2, severity: 'Emergent', complaint: 'Abdominal pain', wait_time: 8, status: '⏳ Waiting' },
    { id: 5, patient_id: 'P1005', esi_level: 3, severity: 'Urgent', complaint: 'Fracture', wait_time: 15, status: '⏳ Waiting' },
    { id: 6, patient_id: 'P1006', esi_level: 3, severity: 'Urgent', complaint: 'Laceration', wait_time: 22, status: '⏳ Waiting' },
    { id: 7, patient_id: 'P1007', esi_level: 3, severity: 'Urgent', complaint: 'Fever', wait_time: 28, status: '⏳ Waiting' },
    { id: 8, patient_id: 'P1008', esi_level: 4, severity: 'Less Urgent', complaint: 'Sprained ankle', wait_time: 35, status: '⏳ Waiting' },
    { id: 9, patient_id: 'P1009', esi_level: 4, severity: 'Less Urgent', complaint: 'Sore throat', wait_time: 42, status: '⏳ Waiting' },
    { id: 10, patient_id: 'P1010', esi_level: 5, severity: 'Non-Urgent', complaint: 'Minor rash', wait_time: 85, status: '⏳ Waiting' },
  ]

  useEffect(() => {
    setQueueData(mockQueueData)
  }, [])

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        // Simulate queue updates
        setQueueData(prev => prev.map(patient => ({
          ...patient,
          wait_time: patient.wait_time + 1
        })))
        setLastUpdated(new Date())
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
    try {
      const response = await triageAPI.getQueue()
      setQueueData(response.data)
    } catch (error) {
      console.log('Using mock data - API not available')
    }
    setLastUpdated(new Date())
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
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <RefreshCw size={16} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md p-4">
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
            Total patients waiting: {queueData.filter(p => p.status.includes('Waiting')).length}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 font-semibold text-gray-800">#</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-800">Patient ID</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-800">ESI Level</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-800">Severity</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-800">Chief Complaint</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-800">Wait Time</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-800">Status</th>
              </tr>
            </thead>
            <tbody>
              {queueData.map((patient, index) => (
                <tr
                  key={patient.id}
                  className={`border-b border-gray-100 hover:bg-gray-50 ${getRowClass(patient.esi_level)}`}
                >
                  <td className="py-4 px-4 font-medium">#{index + 1}</td>
                  <td className="py-4 px-4 font-medium">{patient.patient_id}</td>
                  <td className="py-4 px-4">
                    <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getESIColor(patient.esi_level)}`}>
                      {patient.esi_level}
                    </span>
                  </td>
                  <td className="py-4 px-4 font-medium">{patient.severity}</td>
                  <td className="py-4 px-4">{patient.complaint}</td>
                  <td className="py-4 px-4">
                    <div className="flex items-center space-x-1">
                      <Clock size={16} className="text-gray-500" />
                      <span className={`font-medium ${patient.wait_time > 60 ? 'text-red-600' : 'text-gray-800'}`}>
                        {patient.wait_time} min
                      </span>
                    </div>
                  </td>
                  <td className="py-4 px-4">{patient.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Queue Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Critical Patients</h3>
          <div className="text-3xl font-bold text-red-600">
            {queueData.filter(p => p.esi_level <= 2).length}
          </div>
          <p className="text-gray-600 text-sm">ESI Levels 1-2</p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Average Wait Time</h3>
          <div className="text-3xl font-bold text-blue-600">
            {Math.round(queueData.reduce((acc, p) => acc + p.wait_time, 0) / queueData.length)} min
          </div>
          <p className="text-gray-600 text-sm">All patients</p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Longest Wait</h3>
          <div className="text-3xl font-bold text-orange-600">
            {Math.max(...queueData.map(p => p.wait_time))} min
          </div>
          <p className="text-gray-600 text-sm">Single patient</p>
        </div>
      </div>

      {/* ESI Level Legend */}
      <div className="bg-white rounded-lg shadow-md p-6">
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