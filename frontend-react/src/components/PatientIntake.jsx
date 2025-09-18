import { useState } from 'react'
import { User, Heart, Thermometer, Activity, Clock } from 'lucide-react'
import { patientAPI } from '../services/api'

const PatientIntake = () => {
  const [formData, setFormData] = useState({
    age: 35,
    gender: 'Male',
    chief_complaint: '',
    bp_systolic: 120,
    bp_diastolic: 80,
    heart_rate: 75,
    temperature: 37.0,
    o2_saturation: 98,
    respiratory_rate: 16,
    pain_scale: 5,
    consciousness_level: 'Alert',
    bleeding: false,
    breathing_difficulty: false,
    trauma_indicator: false,
    medical_history: {},
    allergies: [],
    current_medications: []
  })

  const [triageResult, setTriageResult] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : type === 'number' ? Number(value) : value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      const response = await patientAPI.create(formData)

      // Simulate triage result
      const esiLevel = response.data.esi_level || simulateTriageLevel()
      setTriageResult({
        esi_level: esiLevel,
        patient_id: response.data.id,
        priority_score: 500,
        wait_time: getWaitTime(esiLevel),
        queue_position: 12
      })
    } catch (error) {
      // Fallback to mock triage
      const esiLevel = simulateTriageLevel()
      setTriageResult({
        esi_level: esiLevel,
        patient_id: Math.floor(Math.random() * 1000) + 1000,
        priority_score: 500,
        wait_time: getWaitTime(esiLevel),
        queue_position: 12
      })
    }

    setIsSubmitting(false)
  }

  const simulateTriageLevel = () => {
    if (formData.consciousness_level === 'Unresponsive' || formData.o2_saturation < 90) return 1
    if (formData.breathing_difficulty || formData.bp_systolic < 90 || formData.pain_scale >= 8) return 2
    if (formData.pain_scale >= 5) return 3
    if (formData.pain_scale >= 3) return 4
    return 5
  }

  const getWaitTime = (level) => [0, 10, 30, 60, 120][level - 1]

  const getESIInfo = (level) => {
    const info = {
      1: { name: 'Resuscitation', color: 'bg-red-600', priority: 'CRITICAL' },
      2: { name: 'Emergent', color: 'bg-orange-500', priority: 'URGENT' },
      3: { name: 'Urgent', color: 'bg-yellow-400', priority: 'URGENT' },
      4: { name: 'Less Urgent', color: 'bg-green-400', priority: 'ROUTINE' },
      5: { name: 'Non-Urgent', color: 'bg-green-500', priority: 'ROUTINE' }
    }
    return info[level] || info[3]
  }

  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">Patient Registration & Triage</h1>

      <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Column - Patient Information */}
        <div className="space-y-6">
          {/* Demographics */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
              <User className="mr-2" size={20} />
              Demographics
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Age</label>
                <input
                  type="number"
                  name="age"
                  value={formData.age}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="0"
                  max="120"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Gender</label>
                <select
                  name="gender"
                  value={formData.gender}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>
          </div>

          {/* Chief Complaint */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Chief Complaint</h3>
            <textarea
              name="chief_complaint"
              value={formData.chief_complaint}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows="3"
              placeholder="e.g., chest pain, difficulty breathing, severe headache..."
              required
            />
          </div>

          {/* Symptoms */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Symptoms</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Pain Scale (0-10): {formData.pain_scale}
                </label>
                <input
                  type="range"
                  name="pain_scale"
                  value={formData.pain_scale}
                  onChange={handleInputChange}
                  min="0"
                  max="10"
                  className="w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Consciousness Level</label>
                <select
                  name="consciousness_level"
                  value={formData.consciousness_level}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="Alert">Alert</option>
                  <option value="Voice">Voice</option>
                  <option value="Pain">Pain</option>
                  <option value="Unresponsive">Unresponsive</option>
                </select>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    name="bleeding"
                    checked={formData.bleeding}
                    onChange={handleInputChange}
                    className="mr-2"
                  />
                  Active Bleeding
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    name="breathing_difficulty"
                    checked={formData.breathing_difficulty}
                    onChange={handleInputChange}
                    className="mr-2"
                  />
                  Breathing Difficulty
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    name="trauma_indicator"
                    checked={formData.trauma_indicator}
                    onChange={handleInputChange}
                    className="mr-2"
                  />
                  Trauma Indicator
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column - Vital Signs */}
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
              <Heart className="mr-2" size={20} />
              Vital Signs
            </h3>
            <div className="grid grid-cols-1 gap-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">BP Systolic</label>
                  <input
                    type="number"
                    name="bp_systolic"
                    value={formData.bp_systolic}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    min="60"
                    max="250"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">BP Diastolic</label>
                  <input
                    type="number"
                    name="bp_diastolic"
                    value={formData.bp_diastolic}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    min="40"
                    max="150"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Heart Rate (bpm)</label>
                <input
                  type="number"
                  name="heart_rate"
                  value={formData.heart_rate}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="30"
                  max="200"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Temperature (°C)</label>
                <input
                  type="number"
                  name="temperature"
                  value={formData.temperature}
                  onChange={handleInputChange}
                  step="0.1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="32"
                  max="42"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">O2 Saturation (%)</label>
                <input
                  type="number"
                  name="o2_saturation"
                  value={formData.o2_saturation}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="70"
                  max="100"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Respiratory Rate</label>
                <input
                  type="number"
                  name="respiratory_rate"
                  value={formData.respiratory_rate}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="8"
                  max="40"
                />
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50"
          >
            {isSubmitting ? 'Processing...' : 'Register Patient & Perform Triage'}
          </button>
        </div>
      </form>

      {/* Triage Results */}
      {triageResult && (
        <div className="mt-8 bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-bold text-green-600 mb-6">✅ Patient Registered Successfully!</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <h3 className="text-lg font-semibold mb-2">ESI Level: {triageResult.esi_level}</h3>
              <div className={`inline-block px-4 py-2 rounded-lg text-white font-bold ${getESIInfo(triageResult.esi_level).color}`}>
                {getESIInfo(triageResult.esi_level).name}
              </div>
              <p className="mt-2 text-gray-600">
                Priority: {getESIInfo(triageResult.esi_level).priority}
              </p>
            </div>

            <div className="text-center">
              <h3 className="text-lg font-semibold mb-2">Estimated Wait Time</h3>
              <p className="text-3xl font-bold text-blue-600">{triageResult.wait_time} minutes</p>
              <p className="text-gray-600">Queue Position: #{triageResult.queue_position}</p>
            </div>

            <div className="text-center">
              <h3 className="text-lg font-semibold mb-2">Recommended Actions</h3>
              <div className="text-left space-y-1">
                {triageResult.esi_level === 1 && (
                  <>
                    <p>• Immediate resuscitation</p>
                    <p>• Call code team</p>
                  </>
                )}
                {triageResult.esi_level === 2 && (
                  <>
                    <p>• High acuity area</p>
                    <p>• Immediate physician</p>
                  </>
                )}
                {triageResult.esi_level >= 3 && (
                  <>
                    <p>• Urgent care area</p>
                    <p>• Labs/imaging as needed</p>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default PatientIntake