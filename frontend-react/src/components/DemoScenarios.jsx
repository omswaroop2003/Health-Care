import { useState } from 'react'
import { Play, Users, Heart, TrendingUp, Clock, AlertTriangle } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

const DemoScenarios = () => {
  const [activeDemo, setActiveDemo] = useState(null)
  const [isRunning, setIsRunning] = useState(false)

  const scenarios = [
    {
      id: 'mass-casualty',
      title: 'Mass Casualty Event - Bus Accident',
      description: 'Simulate processing 50 patients from a highway bus accident',
      icon: Users,
      color: 'red',
      metrics: {
        patients: 50,
        timeToProcess: '3.2 minutes',
        timeSaved: '85%',
        critical: 5,
        emergent: 10,
        urgent: 15,
        lessUrgent: 15,
        nonUrgent: 5
      }
    },
    {
      id: 'pediatric-emergency',
      title: 'Pediatric Emergency - Severe Allergic Reaction',
      description: '3-year-old child with anaphylaxis requiring immediate intervention',
      icon: Heart,
      color: 'orange',
      metrics: {
        age: '3 years',
        condition: 'Anaphylaxis',
        esiLevel: 1,
        responseTime: '< 30 seconds',
        teamAlerted: 'Pediatric Emergency',
        interventions: ['Epinephrine', 'Airway management', 'IV access']
      }
    },
    {
      id: 'overcrowded-er',
      title: 'Overcrowded ER - System Optimization',
      description: 'AI optimization during peak hours with 120% capacity',
      icon: TrendingUp,
      color: 'blue',
      metrics: {
        capacity: '120%',
        waitingPatients: 80,
        avgWaitBefore: '95 minutes',
        avgWaitAfter: '57 minutes',
        improvement: '40%',
        fastTracked: 18,
        redirected: 12
      }
    }
  ]

  const runDemo = async (scenarioId) => {
    setActiveDemo(scenarioId)
    setIsRunning(true)

    // Simulate demo running
    await new Promise(resolve => setTimeout(resolve, 2000))
    setIsRunning(false)
  }

  const MassCasualtyDemo = () => {
    const scenario = scenarios[0]
    const triageData = [
      { level: 'Level 1', count: scenario.metrics.critical, color: '#FF0000' },
      { level: 'Level 2', count: scenario.metrics.emergent, color: '#FF6600' },
      { level: 'Level 3', count: scenario.metrics.urgent, color: '#FFCC00' },
      { level: 'Level 4', count: scenario.metrics.lessUrgent, color: '#99CC00' },
      { level: 'Level 5', count: scenario.metrics.nonUrgent, color: '#00CC00' }
    ]

    const resourceData = [
      { resource: 'Trauma Bays', allocated: 5, available: 5 },
      { resource: 'OR Suites', allocated: 3, available: 4 },
      { resource: 'ICU Beds', allocated: 8, available: 10 },
      { resource: 'General Beds', allocated: 20, available: 35 },
      { resource: 'Staff Called', allocated: 15, available: 20 }
    ]

    return (
      <div className="space-y-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-red-800 mb-2">📍 Mass Casualty Event Simulation</h3>
          <p className="text-red-700">Location: Highway 101 - Bus accident with 50 casualties</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h4 className="text-lg font-semibold mb-4">Triage Summary</h4>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={triageData}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="count"
                  label={({ level, count }) => `${level}: ${count}`}
                >
                  {triageData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h4 className="text-lg font-semibold mb-4">System Performance</h4>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span>Total Processing Time:</span>
                <span className="font-bold text-blue-600">{scenario.metrics.timeToProcess}</span>
              </div>
              <div className="flex justify-between">
                <span>Patients per Minute:</span>
                <span className="font-bold text-green-600">15.6</span>
              </div>
              <div className="flex justify-between">
                <span>Time Saved vs Manual:</span>
                <span className="font-bold text-green-600">{scenario.metrics.timeSaved}</span>
              </div>
              <div className="bg-green-100 rounded-lg p-3 mt-4">
                <p className="text-green-800 font-semibold">✅ All 50 patients triaged successfully!</p>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h4 className="text-lg font-semibold mb-4">Resource Allocation</h4>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={resourceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="resource" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="allocated" fill="#3B82F6" name="Allocated" />
              <Bar dataKey="available" fill="#10B981" name="Available" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h4 className="text-lg font-semibold mb-4">Top 5 Critical Patients</h4>
          <div className="space-y-2">
            {['P1001 - trauma - ESI 1 (Resuscitation)', 'P1002 - breathing difficulty - ESI 1 (Resuscitation)',
              'P1008 - trauma - ESI 1 (Resuscitation)', 'P1017 - breathing difficulty - ESI 1 (Resuscitation)',
              'P1021 - laceration - ESI 1 (Resuscitation)'].map((patient, index) => (
              <div key={index} className="flex items-center space-x-2 p-2 bg-red-50 rounded">
                <span className="font-medium">{index + 1}.</span>
                <span>{patient}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  const PediatricEmergencyDemo = () => {
    const scenario = scenarios[1]

    return (
      <div className="space-y-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-red-800 mb-2">🚨 Pediatric Emergency Response</h3>
          <p className="text-red-700">Patient: 3-year-old child with severe anaphylaxis</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow-md p-6 text-center">
            <h4 className="text-lg font-semibold mb-4">Triage Decision</h4>
            <div className="bg-red-600 text-white rounded-lg p-4 mb-4">
              <div className="text-2xl font-bold">ESI LEVEL 1</div>
              <div className="text-sm">IMMEDIATE INTERVENTION</div>
            </div>
            <p className="text-gray-600">Auto-escalated to highest priority</p>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6 text-center">
            <h4 className="text-lg font-semibold mb-4">Response Time</h4>
            <div className="space-y-3">
              <div>
                <div className="text-sm text-gray-600">Detection to Alert</div>
                <div className="text-2xl font-bold text-blue-600">{"< 5 seconds"}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Team Response</div>
                <div className="text-2xl font-bold text-green-600">{"< 30 seconds"}</div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h4 className="text-lg font-semibold mb-4">Actions Initiated</h4>
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <span className="text-green-600">✓</span>
                <span>Pediatric team alerted</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-green-600">✓</span>
                <span>Epinephrine prepared</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-green-600">✓</span>
                <span>Resuscitation bay ready</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-green-600">✓</span>
                <span>Airway team on standby</span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-green-100 border border-green-200 rounded-lg p-4">
          <p className="text-green-800 font-semibold">✅ Patient stabilized - transferred to PICU</p>
        </div>
      </div>
    )
  }

  const OvercrowdedERDemo = () => {
    const scenario = scenarios[2]

    return (
      <div className="space-y-6">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-yellow-800 mb-2">⚠️ ER Optimization During Peak Hours</h3>
          <p className="text-yellow-700">Current Status: 120% capacity - 80 patients waiting</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h4 className="text-lg font-semibold mb-4">Before AI Optimization</h4>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span>Average Wait:</span>
                <span className="font-bold text-red-600">95 minutes</span>
              </div>
              <div className="flex justify-between">
                <span>Critical Patient Wait:</span>
                <span className="font-bold text-red-600">25 minutes</span>
              </div>
              <div className="flex justify-between">
                <span>Patient Flow:</span>
                <span className="font-bold text-red-600">3.2/hour</span>
              </div>
              <div className="flex justify-between">
                <span>Satisfaction:</span>
                <span className="font-bold text-red-600">2.8/5</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h4 className="text-lg font-semibold mb-4">After AI Optimization</h4>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span>Average Wait:</span>
                <span className="font-bold text-green-600">57 minutes ↓40%</span>
              </div>
              <div className="flex justify-between">
                <span>Critical Patient Wait:</span>
                <span className="font-bold text-green-600">8 minutes ↓68%</span>
              </div>
              <div className="flex justify-between">
                <span>Patient Flow:</span>
                <span className="font-bold text-green-600">5.1/hour ↑59%</span>
              </div>
              <div className="flex justify-between">
                <span>Satisfaction:</span>
                <span className="font-bold text-green-600">4.1/5 ↑46%</span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h4 className="text-lg font-semibold mb-4">Optimization Actions</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <span className="text-blue-600">•</span>
                <span>18 patients fast-tracked to urgent care</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-blue-600">•</span>
                <span>12 patients identified for discharge</span>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <span className="text-blue-600">•</span>
                <span>Resource reallocation completed</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-blue-600">•</span>
                <span>Staff assignments optimized</span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-green-100 border border-green-200 rounded-lg p-4">
          <p className="text-green-800 font-semibold">✅ Queue optimized - 18 patients fast-tracked, 12 redirected to urgent care</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-800">Demo Scenarios</h1>
      <p className="text-gray-600">Demonstrate system capabilities with pre-configured scenarios</p>

      {!activeDemo && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {scenarios.map((scenario) => {
            const Icon = scenario.icon
            return (
              <div key={scenario.id} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
                <div className={`w-12 h-12 bg-${scenario.color}-100 rounded-lg flex items-center justify-center mb-4`}>
                  <Icon className={`w-6 h-6 text-${scenario.color}-600`} />
                </div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2">{scenario.title}</h3>
                <p className="text-gray-600 text-sm mb-4">{scenario.description}</p>
                <button
                  onClick={() => runDemo(scenario.id)}
                  disabled={isRunning}
                  className={`w-full flex items-center justify-center space-x-2 px-4 py-2 bg-${scenario.color}-600 text-white rounded-lg hover:bg-${scenario.color}-700 disabled:opacity-50`}
                >
                  <Play size={16} />
                  <span>{isRunning ? 'Running...' : 'Run Scenario'}</span>
                </button>
              </div>
            )
          })}
        </div>
      )}

      {activeDemo && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-800">
              {scenarios.find(s => s.id === activeDemo)?.title}
            </h2>
            <button
              onClick={() => setActiveDemo(null)}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
            >
              Back to Scenarios
            </button>
          </div>

          {activeDemo === 'mass-casualty' && <MassCasualtyDemo />}
          {activeDemo === 'pediatric-emergency' && <PediatricEmergencyDemo />}
          {activeDemo === 'overcrowded-er' && <OvercrowdedERDemo />}
        </div>
      )}
    </div>
  )
}

export default DemoScenarios