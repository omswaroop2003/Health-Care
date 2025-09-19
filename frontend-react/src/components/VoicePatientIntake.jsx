import { useState, useEffect, useRef } from 'react'
import { Mic, MicOff, Phone, PhoneOff, Volume2, User, Clock, CheckCircle, AlertCircle } from 'lucide-react'

const VoicePatientIntake = () => {
  const [isRecording, setIsRecording] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const [conversationState, setConversationState] = useState('disconnected')
  const [collectedData, setCollectedData] = useState({})
  const [isProcessing, setIsProcessing] = useState(false)
  const [agentResponse, setAgentResponse] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const [completedPatient, setCompletedPatient] = useState(null)
  const [isPlaying, setIsPlaying] = useState(false)

  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])
  const wsRef = useRef(null)

  const API_BASE = 'http://localhost:8000/api/v1/voice-conversation'

  useEffect(() => {
    return () => {
      // Cleanup on unmount
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop()
      }
    }
  }, [])

  const startVoiceConversation = async () => {
    try {
      setErrorMessage('')
      setIsProcessing(true)

      // Start conversation session
      const response = await fetch(`${API_BASE}/conversations/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error(`Failed to start conversation: ${response.statusText}`)
      }

      const result = await response.json()
      setSessionId(result.session_id)
      setConversationState('connected')
      setIsConnected(true)

      // Initialize WebSocket connection
      initializeWebSocket(result.session_id)

    } catch (error) {
      console.error('Failed to start voice conversation:', error)
      setErrorMessage(`Failed to start conversation: ${error.message}`)
    } finally {
      setIsProcessing(false)
    }
  }

  const initializeWebSocket = (sessionId) => {
    const wsUrl = `ws://localhost:8000/api/v1/voice-conversation/conversations/${sessionId}/ws`
    wsRef.current = new WebSocket(wsUrl)

    wsRef.current.onopen = () => {
      console.log('WebSocket connected')
      setConversationState('ready')

      // Start the conversation with the agent
      wsRef.current.send(JSON.stringify({
        type: 'start_conversation'
      }))
    }

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data)
      handleWebSocketMessage(data)
    }

    wsRef.current.onclose = () => {
      console.log('WebSocket disconnected')
      setIsConnected(false)
      setConversationState('disconnected')
    }

    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error)
      setErrorMessage('Connection error occurred')
    }
  }

  const handleWebSocketMessage = (data) => {
    console.log('WebSocket message:', data)

    switch (data.type) {
      case 'conversation_started':
        if (data.success) {
          setConversationState('active')
          setAgentResponse('Hello! I\'m your triage assistant. Let\'s collect your information.')
        } else {
          setErrorMessage('Failed to start conversation with agent')
        }
        break

      case 'audio_processed':
        if (data.success) {
          setCollectedData(prev => ({ ...prev, ...data.data.extracted_data }))
          if (data.data.agent_response) {
            setAgentResponse(data.data.agent_response.text || 'Processing your response...')
          }
        } else {
          setErrorMessage('Failed to process audio')
        }
        break

      case 'conversation_completed':
        if (data.success) {
          setCompletedPatient(data.patient_data)
          setConversationState('completed')
        } else {
          setErrorMessage('Failed to complete conversation')
        }
        break

      case 'status_update':
        if (data.data) {
          setCollectedData(data.data.patient_data || {})
        }
        break

      case 'error':
        setErrorMessage(data.message)
        break

      default:
        console.log('Unknown message type:', data.type)
    }
  }

  const startRecording = async () => {
    try {
      if (!isConnected) {
        setErrorMessage('Please start the conversation first')
        return
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        }
      })

      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })

      audioChunksRef.current = []

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm;codecs=opus' })
        sendAudioToAgent(audioBlob)

        // Stop all tracks to free up the microphone
        stream.getTracks().forEach(track => track.stop())
      }

      mediaRecorderRef.current.start()
      setIsRecording(true)

    } catch (error) {
      console.error('Failed to start recording:', error)
      setErrorMessage('Failed to access microphone. Please check permissions.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      setIsProcessing(true)
    }
  }

  const sendAudioToAgent = async (audioBlob) => {
    try {
      // Convert blob to base64 for WebSocket transmission
      const arrayBuffer = await audioBlob.arrayBuffer()
      const base64Audio = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)))

      wsRef.current.send(JSON.stringify({
        type: 'audio_data',
        audio: base64Audio
      }))

    } catch (error) {
      console.error('Failed to send audio:', error)
      setErrorMessage('Failed to send audio data')
    } finally {
      setIsProcessing(false)
    }
  }

  const simulateTextInput = async (text) => {
    try {
      if (!sessionId) return

      const response = await fetch(`${API_BASE}/conversations/${sessionId}/simulate-audio`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text })
      })

      if (response.ok) {
        const result = await response.json()
        setCollectedData(prev => ({ ...prev, ...result.extracted_data }))
        setAgentResponse('Data received and processed')
      }
    } catch (error) {
      console.error('Failed to simulate text input:', error)
    }
  }

  const completeConversation = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'complete_conversation'
      }))
    }
  }

  const endConversation = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'end_conversation'
      }))
    }

    setIsConnected(false)
    setSessionId(null)
    setConversationState('disconnected')
    setCollectedData({})
    setAgentResponse('')
    setCompletedPatient(null)
  }

  const getDataCompleteness = () => {
    const requiredFields = ['name', 'age', 'chief_complaint']
    const recommendedFields = ['bp_systolic', 'bp_diastolic', 'heart_rate', 'temperature', 'o2_saturation', 'pain_scale']

    const completed = requiredFields.filter(field => collectedData[field]).length
    const recommended = recommendedFields.filter(field => collectedData[field]).length

    return {
      required: `${completed}/${requiredFields.length}`,
      recommended: `${recommended}/${recommendedFields.length}`,
      canComplete: completed === requiredFields.length
    }
  }

  const renderCollectedData = () => {
    if (Object.keys(collectedData).length === 0) return null

    return (
      <div className="bg-blue-50 rounded-lg p-4">
        <h4 className="font-semibold text-blue-800 mb-3">Collected Information</h4>
        <div className="grid grid-cols-2 gap-2 text-sm">
          {Object.entries(collectedData).map(([key, value]) => (
            <div key={key} className="flex justify-between">
              <span className="text-gray-600 capitalize">{key.replace('_', ' ')}:</span>
              <span className="font-medium">{typeof value === 'boolean' ? (value ? 'Yes' : 'No') : value}</span>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (completedPatient) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <div className="flex items-center mb-4">
            <CheckCircle className="w-8 h-8 text-green-600 mr-3" />
            <h2 className="text-2xl font-bold text-green-800">Patient Registered Successfully!</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white rounded-lg p-4">
              <h3 className="font-semibold text-gray-800 mb-2">Patient Details</h3>
              <p><strong>Name:</strong> {completedPatient.name}</p>
              <p><strong>ID:</strong> {completedPatient.id}</p>
              <p><strong>Queue Position:</strong> #{completedPatient.queue_position}</p>
            </div>

            <div className="bg-white rounded-lg p-4">
              <h3 className="font-semibold text-gray-800 mb-2">Triage Assessment</h3>
              <p><strong>ESI Level:</strong> {completedPatient.esi_level}</p>
              <p><strong>Priority Score:</strong> {completedPatient.priority_score}</p>
              <p><strong>AI Confidence:</strong> {Math.round((completedPatient.ai_confidence || 0) * 100)}%</p>
            </div>

            <div className="bg-white rounded-lg p-4">
              <h3 className="font-semibold text-gray-800 mb-2">Next Steps</h3>
              <p className="text-sm text-gray-600">
                Patient has been added to the emergency queue and will be called when ready.
              </p>
            </div>
          </div>

          <button
            onClick={() => {
              setCompletedPatient(null)
              endConversation()
            }}
            className="mt-4 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
          >
            Start New Conversation
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">Voice Patient Intake</h1>


      {/* Connection Status */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="font-medium">
              Status: {conversationState.charAt(0).toUpperCase() + conversationState.slice(1)}
            </span>
          </div>

          {!isConnected ? (
            <button
              onClick={startVoiceConversation}
              disabled={isProcessing}
              className="flex items-center space-x-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              <Phone className="w-4 h-4" />
              <span>{isProcessing ? 'Connecting...' : 'Start Voice Conversation'}</span>
            </button>
          ) : (
            <button
              onClick={endConversation}
              className="flex items-center space-x-2 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
            >
              <PhoneOff className="w-4 h-4" />
              <span>End Conversation</span>
            </button>
          )}
        </div>
      </div>

      {/* Error Display */}
      {errorMessage && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-center">
          <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
          <span className="text-red-700">{errorMessage}</span>
          <button
            onClick={() => setErrorMessage('')}
            className="ml-auto text-red-600 hover:text-red-800"
          >
            ×
          </button>
        </div>
      )}

      {/* Voice Controls */}
      {isConnected && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex flex-col items-center space-y-4">
            <div className="text-center">
              <h3 className="text-lg font-semibold mb-2">Voice Recording</h3>
              <p className="text-gray-600">
                {isRecording ? 'Speaking... Release to send' : 'Hold to record your voice'}
              </p>
            </div>

            <button
              onMouseDown={startRecording}
              onMouseUp={stopRecording}
              onTouchStart={startRecording}
              onTouchEnd={stopRecording}
              disabled={!isConnected || isProcessing}
              className={`w-20 h-20 rounded-full flex items-center justify-center text-white text-2xl transition-all duration-200 ${
                isRecording
                  ? 'bg-red-600 scale-110 shadow-lg'
                  : 'bg-blue-600 hover:bg-blue-700 shadow-md'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {isRecording ? <MicOff /> : <Mic />}
            </button>

            {isProcessing && (
              <div className="flex items-center space-x-2 text-blue-600">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <span>Processing audio...</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Agent Response */}
      {agentResponse && isConnected && (
        <div className="bg-gray-50 rounded-lg p-4 mb-6">
          <div className="flex items-center space-x-2 mb-2">
            <Volume2 className="w-5 h-5 text-blue-600" />
            <span className="font-medium text-gray-800">Assistant:</span>
          </div>
          <p className="text-gray-700">{agentResponse}</p>
        </div>
      )}

      {/* Data Collection Progress */}
      {isConnected && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-4">Collection Progress</h3>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-sm">
                  <span>Required Fields</span>
                  <span>{getDataCompleteness().required}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-600 h-2 rounded-full"
                    style={{ width: `${(parseInt(getDataCompleteness().required.split('/')[0]) / parseInt(getDataCompleteness().required.split('/')[1])) * 100}%` }}
                  ></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-sm">
                  <span>Recommended Fields</span>
                  <span>{getDataCompleteness().recommended}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: `${(parseInt(getDataCompleteness().recommended.split('/')[0]) / parseInt(getDataCompleteness().recommended.split('/')[1])) * 100}%` }}
                  ></div>
                </div>
              </div>

              {getDataCompleteness().canComplete && (
                <button
                  onClick={completeConversation}
                  className="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 flex items-center justify-center space-x-2"
                >
                  <CheckCircle className="w-4 h-4" />
                  <span>Complete Registration</span>
                </button>
              )}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            {renderCollectedData()}
          </div>
        </div>
      )}

      {/* Testing Panel */}
      {isConnected && process.env.NODE_ENV === 'development' && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h4 className="font-semibold text-yellow-800 mb-2">Testing Mode</h4>
          <div className="space-y-2">
            <button
              onClick={() => simulateTextInput('My name is John Doe and I am 35 years old')}
              className="mr-2 text-sm bg-yellow-600 text-white px-3 py-1 rounded"
            >
              Simulate Name & Age
            </button>
            <button
              onClick={() => simulateTextInput('I have severe chest pain, level 8 out of 10')}
              className="mr-2 text-sm bg-yellow-600 text-white px-3 py-1 rounded"
            >
              Simulate Complaint
            </button>
            <button
              onClick={() => simulateTextInput('Blood pressure 140 over 90, heart rate 95')}
              className="text-sm bg-yellow-600 text-white px-3 py-1 rounded"
            >
              Simulate Vitals
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default VoicePatientIntake