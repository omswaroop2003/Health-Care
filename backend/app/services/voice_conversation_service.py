"""
11Labs Conversational AI Service for Patient Intake
Uses configured agent for voice-based patient data collection
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import aiohttp
import json
import base64
from dataclasses import dataclass, asdict
import re

logger = logging.getLogger(__name__)

@dataclass
class ConversationSession:
    """Tracks patient conversation session"""
    session_id: str
    conversation_id: Optional[str]  # 11Labs conversation ID
    patient_data: Dict[str, Any]
    conversation_state: str
    created_at: datetime
    last_activity: datetime
    completed: bool = False

class VoiceConversationService:
    """Service for handling conversational AI patient intake using 11Labs agent"""

    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = os.getenv("VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Default voice ID
        self.agent_id = "agent_0901k5e9x4bvejzsx1r18ynqqxy8"  # Your configured agent
        self.base_url = "https://api.elevenlabs.io/v1"

        # Track active conversation sessions
        self.active_sessions: Dict[str, ConversationSession] = {}

        if not self.api_key:
            logger.warning("11Labs API key not found")
        else:
            logger.info(f"Voice conversation service initialized with agent: {self.agent_id}")

    async def start_conversation(self, session_id: str) -> Dict[str, Any]:
        """Start a new conversation with the AI agent using simulate-conversation"""
        try:
            # Create conversation session first (we'll simulate the conversation)
            conv_session = ConversationSession(
                session_id=session_id,
                conversation_id=f"sim_{session_id}",
                patient_data={},
                conversation_state="started",
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow()
            )

            self.active_sessions[session_id] = conv_session

            logger.info(f"Started conversation session {session_id}")

            return {
                "success": True,
                "session_id": session_id,
                "conversation_id": f"sim_{session_id}",
                "message": "Conversation started successfully"
            }

        except Exception as e:
            logger.error(f"Error starting conversation: {e}")
            return {
                "success": False,
                "error": f"Exception starting conversation: {str(e)}"
            }

    async def send_audio_to_agent(self, session_id: str, audio_data: bytes) -> Dict[str, Any]:
        """Process audio data using 11Labs text-to-speech and simulate conversation"""
        try:
            if session_id not in self.active_sessions:
                return {"success": False, "error": "Session not found"}

            conv_session = self.active_sessions[session_id]

            # First, convert audio to text using a placeholder
            # In a real implementation, you'd use speech-to-text service
            text_input = "My name is John Doe and I am 35 years old with chest pain"

            # Simulate agent conversation using the text
            agent_response_text = await self._simulate_agent_conversation(text_input, conv_session)

            # Update session activity
            conv_session.last_activity = datetime.utcnow()

            # Extract patient data from the input text
            extracted_data = await self._extract_patient_data_from_response({"transcript": text_input})
            if extracted_data:
                conv_session.patient_data.update(extracted_data)

            # Convert agent response to audio
            audio_response = await self._text_to_speech(agent_response_text)

            return {
                "success": True,
                "agent_response": {
                    "text": agent_response_text,
                    "audio": audio_response
                },
                "extracted_data": extracted_data,
                "session_data": conv_session.patient_data
            }

        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            return {
                "success": False,
                "error": f"Exception processing audio: {str(e)}"
            }

    async def _simulate_agent_conversation(self, user_input: str, conv_session: ConversationSession) -> str:
        """Simulate agent conversation response based on current conversation state"""
        try:
            # Determine conversation state and generate appropriate response
            current_data = conv_session.patient_data

            if not current_data.get("name"):
                return "Hello! I'm your emergency triage assistant. I'll help collect your information quickly. Can you please tell me your full name and age?"
            elif not current_data.get("chief_complaint"):
                return f"Thank you, {current_data.get('name')}. Now, can you tell me what brings you to the emergency department today? What's your main concern or symptom?"
            elif not current_data.get("bp_systolic"):
                return "I understand your concern. Now I need to collect your vital signs. Do you have your blood pressure readings? Please tell me your systolic and diastolic numbers."
            elif not current_data.get("heart_rate"):
                return "Got it. What's your current heart rate or pulse rate?"
            elif not current_data.get("pain_scale"):
                return "Thank you. On a scale of 0 to 10, with 10 being the worst pain imaginable, what's your current pain level?"
            else:
                return "Thank you for providing all that information. I have collected your details and we can now complete your triage assessment. Please confirm if all the information is correct."

        except Exception as e:
            logger.error(f"Error simulating conversation: {e}")
            return "I'm sorry, there was an issue processing your request. Can you please repeat that?"

    async def _text_to_speech(self, text: str) -> Optional[str]:
        """Convert text to speech using 11Labs API"""
        try:
            if not self.api_key:
                logger.warning("No API key available for text-to-speech")
                return None

            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }

            data = {
                "text": text,
                "voice_settings": {
                    "stability": 0.75,
                    "similarity_boost": 0.75,
                    "style": 0.3,
                    "use_speaker_boost": True
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/text-to-speech/{self.voice_id}",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        audio_content = await response.read()
                        # Return base64 encoded audio
                        return base64.b64encode(audio_content).decode('utf-8')
                    else:
                        logger.error(f"Text-to-speech failed: {response.status}")
                        return None

        except Exception as e:
            logger.error(f"Text-to-speech error: {e}")
            return None

    async def get_conversation_response(self, session_id: str) -> Dict[str, Any]:
        """Get the latest response from the conversational agent"""
        try:
            if session_id not in self.active_sessions:
                return {"success": False, "error": "Session not found"}

            conv_session = self.active_sessions[session_id]
            if not conv_session.conversation_id:
                return {"success": False, "error": "Conversation not started"}

            headers = {
                "xi-api-key": self.api_key
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/convai/conversations/{conv_session.conversation_id}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "conversation_data": result,
                            "session_data": conv_session.patient_data
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"Failed to get conversation: {error_text}"
                        }

        except Exception as e:
            logger.error(f"Error getting conversation response: {e}")
            return {
                "success": False,
                "error": f"Exception getting response: {str(e)}"
            }

    async def _extract_patient_data_from_response(self, agent_response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured patient data from agent response"""
        extracted_data = {}

        try:
            # Get transcript from agent response
            transcript = ""
            if "transcript" in agent_response:
                transcript = agent_response["transcript"].lower()
            elif "text" in agent_response:
                transcript = agent_response["text"].lower()

            if not transcript:
                return extracted_data

            # Extract name
            name_patterns = [
                r"my name is ([a-zA-Z\s]+)",
                r"i'm ([a-zA-Z\s]+)",
                r"i am ([a-zA-Z\s]+)",
                r"name: ([a-zA-Z\s]+)"
            ]
            for pattern in name_patterns:
                match = re.search(pattern, transcript)
                if match:
                    extracted_data["name"] = match.group(1).strip().title()
                    break

            # Extract age
            age_patterns = [
                r"(\d{1,3})\s*years?\s*old",
                r"age\s*:?\s*(\d{1,3})",
                r"i'm\s*(\d{1,3})",
                r"i am\s*(\d{1,3})"
            ]
            for pattern in age_patterns:
                match = re.search(pattern, transcript)
                if match:
                    age = int(match.group(1))
                    if 0 <= age <= 120:
                        extracted_data["age"] = age
                        break

            # Extract chief complaint
            complaint_indicators = ["pain", "hurt", "ache", "problem", "issue", "feel", "sick", "injury", "bleeding", "difficulty"]
            if any(indicator in transcript for indicator in complaint_indicators):
                # Extract the full complaint description
                sentences = transcript.split('.')
                for sentence in sentences:
                    if any(indicator in sentence for indicator in complaint_indicators):
                        extracted_data["chief_complaint"] = sentence.strip().capitalize()
                        break

            # Extract vital signs with patterns
            vital_patterns = {
                "bp_systolic": r"blood pressure.*?(\d{2,3})\s*(?:over|/)\s*(\d{2,3})|systolic.*?(\d{2,3})",
                "bp_diastolic": r"blood pressure.*?\d{2,3}\s*(?:over|/)\s*(\d{2,3})|diastolic.*?(\d{2,3})",
                "heart_rate": r"heart rate.*?(\d{2,3})|pulse.*?(\d{2,3})|bpm.*?(\d{2,3})",
                "temperature": r"temperature.*?(\d{2,3}(?:\.\d)?)|temp.*?(\d{2,3}(?:\.\d)?)",
                "o2_saturation": r"oxygen.*?(\d{2,3})|o2.*?(\d{2,3})|saturation.*?(\d{2,3})",
                "respiratory_rate": r"breathing.*?(\d{1,2})|respiratory.*?(\d{1,2})|breaths.*?(\d{1,2})"
            }

            for vital, pattern in vital_patterns.items():
                match = re.search(pattern, transcript)
                if match:
                    # Get the first non-None group
                    value = next((g for g in match.groups() if g is not None), None)
                    if value:
                        try:
                            if vital in ["temperature"]:
                                extracted_data[vital] = float(value)
                            else:
                                extracted_data[vital] = int(value)
                        except ValueError:
                            continue

            # Extract pain scale
            pain_match = re.search(r"pain.*?(\d{1,2})|(\d{1,2}).*?(?:out of 10|/10)", transcript)
            if pain_match:
                pain_val = int(pain_match.group(1) or pain_match.group(2))
                if 0 <= pain_val <= 10:
                    extracted_data["pain_scale"] = pain_val

            # Extract yes/no symptoms
            yes_words = ["yes", "yeah", "yep", "true", "positive", "i do", "i have", "i am"]
            no_words = ["no", "nope", "false", "negative", "i don't", "i haven't", "not"]

            # Bleeding
            if "bleeding" in transcript:
                if any(word in transcript for word in yes_words):
                    extracted_data["bleeding"] = True
                elif any(word in transcript for word in no_words):
                    extracted_data["bleeding"] = False

            # Breathing difficulty
            if "breathing" in transcript or "breath" in transcript:
                if any(word in ["difficulty", "hard", "trouble", "can't"] for word in transcript.split()):
                    extracted_data["breathing_difficulty"] = True
                elif any(word in transcript for word in no_words):
                    extracted_data["breathing_difficulty"] = False

            # Trauma
            trauma_indicators = ["accident", "fall", "hit", "injury", "trauma", "hurt"]
            if any(indicator in transcript for indicator in trauma_indicators):
                if any(word in transcript for word in yes_words):
                    extracted_data["trauma_indicator"] = True
                elif any(word in transcript for word in no_words):
                    extracted_data["trauma_indicator"] = False

            # Consciousness level
            if "alert" in transcript or "awake" in transcript:
                extracted_data["consciousness_level"] = "Alert"
            elif "confused" in transcript or "disoriented" in transcript:
                extracted_data["consciousness_level"] = "Confused"
            elif "unconscious" in transcript or "unresponsive" in transcript:
                extracted_data["consciousness_level"] = "Unconscious"

        except Exception as e:
            logger.error(f"Error extracting patient data: {e}")

        return extracted_data

    async def complete_conversation(self, session_id: str) -> Dict[str, Any]:
        """Complete the conversation and return collected patient data"""
        try:
            if session_id not in self.active_sessions:
                return {"success": False, "error": "Session not found"}

            conv_session = self.active_sessions[session_id]
            conv_session.completed = True
            conv_session.conversation_state = "completed"

            # Prepare patient data with defaults
            patient_data = conv_session.patient_data.copy()

            # Set defaults for missing required fields
            patient_data.setdefault("gender", "Other")
            patient_data.setdefault("medical_history", {})
            patient_data.setdefault("allergies", [])
            patient_data.setdefault("current_medications", [])
            patient_data.setdefault("consciousness_level", "Alert")
            patient_data.setdefault("bleeding", False)
            patient_data.setdefault("breathing_difficulty", False)
            patient_data.setdefault("trauma_indicator", False)
            patient_data.setdefault("pain_scale", 0)

            # Validate required fields
            required_fields = ["name", "age", "chief_complaint"]
            missing_fields = [field for field in required_fields if field not in patient_data]

            if missing_fields:
                return {
                    "success": False,
                    "error": f"Missing required fields: {', '.join(missing_fields)}",
                    "patient_data": patient_data,
                    "missing_fields": missing_fields
                }

            # Clean up session
            del self.active_sessions[session_id]

            logger.info(f"Completed conversation for session {session_id}")

            return {
                "success": True,
                "patient_data": patient_data,
                "session_id": session_id,
                "message": "Conversation completed successfully"
            }

        except Exception as e:
            logger.error(f"Error completing conversation: {e}")
            return {
                "success": False,
                "error": f"Exception completing conversation: {str(e)}"
            }

    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current session status"""
        if session_id not in self.active_sessions:
            return None

        conv_session = self.active_sessions[session_id]
        return {
            "session_id": session_id,
            "conversation_id": conv_session.conversation_id,
            "state": conv_session.conversation_state,
            "patient_data": conv_session.patient_data,
            "created_at": conv_session.created_at.isoformat(),
            "last_activity": conv_session.last_activity.isoformat(),
            "completed": conv_session.completed
        }

    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get all active conversation sessions"""
        return [self.get_session_status(session_id) for session_id in self.active_sessions.keys()]

    async def end_conversation(self, session_id: str) -> Dict[str, Any]:
        """End a conversation session"""
        try:
            if session_id not in self.active_sessions:
                return {"success": False, "error": "Session not found"}

            conv_session = self.active_sessions[session_id]

            # If there's an active 11Labs conversation, end it
            if conv_session.conversation_id:
                headers = {"xi-api-key": self.api_key}

                async with aiohttp.ClientSession() as session:
                    async with session.delete(
                        f"{self.base_url}/convai/conversations/{conv_session.conversation_id}",
                        headers=headers
                    ) as response:
                        if response.status not in [200, 204, 404]:  # 404 is OK if already ended
                            logger.warning(f"Failed to end 11Labs conversation: {response.status}")

            # Remove from active sessions
            del self.active_sessions[session_id]

            logger.info(f"Ended conversation session {session_id}")

            return {
                "success": True,
                "message": "Conversation ended successfully"
            }

        except Exception as e:
            logger.error(f"Error ending conversation: {e}")
            return {
                "success": False,
                "error": f"Exception ending conversation: {str(e)}"
            }

# Global instance
voice_conversation_service = VoiceConversationService()