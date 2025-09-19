import { Link, useLocation } from 'react-router-dom'
import { Activity, UserPlus, Mic, Clock, PlayCircle } from 'lucide-react'

const Navigation = () => {
  const location = useLocation()

  const navItems = [
    { path: '/', name: 'Dashboard', icon: Activity },
    { path: '/intake', name: 'Patient Intake', icon: UserPlus },
    { path: '/voice-intake', name: 'Voice Intake', icon: Mic },
    { path: '/queue', name: 'Queue Monitor', icon: Clock },
    { path: '/demo', name: 'Demo Scenarios', icon: PlayCircle },
  ]

  return (
    <nav className="bg-white shadow-lg border-b border-gray-200">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center py-4">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-red-600 rounded-full flex items-center justify-center">
              <span className="text-white font-bold text-sm">🚨</span>
            </div>
            <h1 className="text-xl font-bold text-gray-800">Emergency Triage System</h1>
          </div>

          <div className="flex space-x-1">
            {navItems.map(({ path, name, icon: Icon }) => {
              const isActive = location.pathname === path
              return (
                <Link
                  key={path}
                  to={path}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-red-100 text-red-700 border border-red-200'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-800'
                  }`}
                >
                  <Icon size={18} />
                  <span className="font-medium">{name}</span>
                </Link>
              )
            })}
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navigation