import { useState, useEffect } from 'react'
import { Users, Clock, AlertTriangle, TrendingUp } from 'lucide-react'
import { PieChart, Pie, Cell, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { dashboardAPI } from '../services/api'

const Dashboard = () => {
  const [stats, setStats] = useState({
    total_patients: 87,
    waiting_patients: 32,
    critical_patients: 5,
    average_wait_time: 25,
    beds_available: 12,
    staff_on_duty: 8,
    esi_distribution: {
      level_1: 2,
      level_2: 3,
      level_3: 12,
      level_4: 10,
      level_5: 5
    }
  })

  const [alerts, setAlerts] = useState([
    { id: 1, time: '2 min ago', patient: 'Patient #45', message: 'Critical vitals - ESI Level 1', type: 'critical' },
    { id: 2, time: '5 min ago', patient: 'Patient #38', message: 'Deteriorating condition', type: 'warning' },
    { id: 3, time: '12 min ago', patient: 'Patient #29', message: 'Wait time exceeded', type: 'warning' },
  ])

  useEffect(() => {
    // Fetch dashboard stats
    const fetchStats = async () => {
      try {
        const response = await dashboardAPI.getStats()
        setStats(response.data)
      } catch (error) {
        console.log('Using mock data - API not available')
      }
    }

    fetchStats()
    const interval = setInterval(fetchStats, 10000) // Refresh every 10 seconds

    return () => clearInterval(interval)
  }, [])

  const esiData = [
    { name: 'Level 1 - Resuscitation', value: stats.esi_distribution.level_1, color: '#FF0000' },
    { name: 'Level 2 - Emergent', value: stats.esi_distribution.level_2, color: '#FF6600' },
    { name: 'Level 3 - Urgent', value: stats.esi_distribution.level_3, color: '#FFCC00' },
    { name: 'Level 4 - Less Urgent', value: stats.esi_distribution.level_4, color: '#99CC00' },
    { name: 'Level 5 - Non-Urgent', value: stats.esi_distribution.level_5, color: '#00CC00' },
  ]

  const waitTimeData = [
    { hour: 0, waitTime: 15 }, { hour: 6, waitTime: 20 }, { hour: 12, waitTime: 35 },
    { hour: 14, waitTime: 45 }, { hour: 18, waitTime: 30 }, { hour: 22, waitTime: 18 }
  ]

  const MetricCard = ({ title, value, subtitle, icon: Icon, trend, color = "blue" }) => (
    <div className="metric-card">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-gray-600 text-sm font-medium">{title}</p>
          <p className={`text-3xl font-bold text-${color}-600 mt-1`}>{value}</p>
          {subtitle && <p className="text-gray-500 text-sm mt-1">{subtitle}</p>}
        </div>
        <div className={`p-3 bg-${color}-100 rounded-lg`}>
          <Icon className={`w-6 h-6 text-${color}-600`} />
        </div>
      </div>
      {trend && (
        <div className="mt-3 flex items-center">
          <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
          <span className="text-green-500 text-sm font-medium">{trend}</span>
        </div>
      )}
    </div>
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-800">Emergency Department Dashboard</h1>
        <div className="flex items-center space-x-2 text-green-600">
          <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-sm font-medium">Live Data</span>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Patients"
          value={stats.total_patients}
          subtitle="↑ 5 today"
          icon={Users}
          color="blue"
        />
        <MetricCard
          title="Waiting"
          value={stats.waiting_patients}
          subtitle="↓ 3 last hour"
          icon={Clock}
          color="yellow"
        />
        <MetricCard
          title="Critical (ESI 1-2)"
          value={stats.critical_patients}
          subtitle="↑ 1"
          icon={AlertTriangle}
          color="red"
        />
        <MetricCard
          title="Avg Wait Time"
          value={`${stats.average_wait_time} min`}
          subtitle="↓ 5 min"
          icon={TrendingUp}
          color="green"
        />
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Beds Available"
          value={stats.beds_available}
          icon={Users}
          color="indigo"
        />
        <MetricCard
          title="Staff on Duty"
          value={stats.staff_on_duty}
          icon={Users}
          color="purple"
        />
        <MetricCard
          title="Efficiency Score"
          value="92%"
          subtitle="↑ 3%"
          icon={TrendingUp}
          color="green"
        />
        <MetricCard
          title="Patient Satisfaction"
          value="4.2/5"
          subtitle="↑ 0.1"
          icon={TrendingUp}
          color="blue"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">ESI Level Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={esiData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={120}
                paddingAngle={5}
                dataKey="value"
              >
                {esiData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-4 space-y-2">
            {esiData.map((item, index) => (
              <div key={index} className="flex items-center text-sm">
                <div
                  className="w-3 h-3 rounded-full mr-2"
                  style={{ backgroundColor: item.color }}
                ></div>
                <span className="text-gray-600">{item.name}: {item.value} patients</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Wait Times by Hour</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={waitTimeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="waitTime" stroke="#FF6600" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Alerts */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">⚠️ Recent Alerts</h3>
        <div className="space-y-3">
          {alerts.map((alert) => (
            <div key={alert.id} className={`p-4 rounded-lg border ${
              alert.type === 'critical'
                ? 'bg-red-50 border-red-200'
                : 'bg-yellow-50 border-yellow-200'
            }`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <span className={`text-2xl ${
                    alert.type === 'critical' ? 'text-red-600' : 'text-yellow-600'
                  }`}>
                    {alert.type === 'critical' ? '🔴' : '🟡'}
                  </span>
                  <div>
                    <p className="font-medium text-gray-800">{alert.patient}</p>
                    <p className="text-gray-600 text-sm">{alert.message}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-gray-500 text-sm">{alert.time}</p>
                  <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                    Acknowledge
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default Dashboard