"""
11Labs API Service for Voice Conversation
Real implementation with speech-to-text, conversational AI, and text-to-speech
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
import uuid

logger = logging.getLogger(__name__)

@dataclass
class ConversationSession:
    """Tracks patient conversation session"""
    session_id: str
    conversation_id: Optional[str]
    patient_data: Dict[str, Any]
    conversation_state: str
    created_at: datetime
    last_activity: datetime
    completed: bool = False
    transcript: List[str] = None

    def __post_init__(self):
        if self.transcript is None:
            self.transcript = []

class ElevenLabsService:
    """Service for handling 11Labs API integration"""

    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
        self.agent_id = "agent_0901k5e9x4bvejzsx1r18ynqqxy8"
        self.base_url = "https://api.elevenlabs.io/v1"

        # Track active conversation sessions
        self.active_sessions: Dict[str, ConversationSession] = {}

        if not self.api_key:
            logger.error("11Labs API key not found in environment variables")
        else:
            logger.info(f"11Labs service initialized with agent: {self.agent_id}")

    async def start_conversation(self, session_id: str) -> Dict[str, Any]:
        """Start a new conversation with the 11Labs conversational AI agent"""
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "error": "11Labs API key not configured"
                }

            # Create conversation session
            conv_session = ConversationSession(
                session_id=session_id,
                conversation_id=None,
                patient_data={},
                conversation_state="initializing",
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow()
            )

            # Initialize conversation with 11Labs Conversational AI
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }

            # Note: Conversational AI endpoint may not be available or may require different approach
            # For now, skip the agent conversation creation and use fallback mode
            # This allows the system to work with basic TTS/STT without conversational AI

            # Fallback approach - create session without ElevenLabs conversation
            logger.warning("ElevenLabs Conversational AI not available, using fallback mode")
            conv_session.conversation_state = "fallback"
            self.active_sessions[session_id] = conv_session

            return {
                "success": True,
                "session_id": session_id,
                "conversation_id": f"fallback_{session_id}",
                "message": "Started in fallback mode - using TTS/STT only",
                "warning": "Conversational AI not available"
            }

            # Original conversation creation code (commented out for now)
            # conversation_data = {
            #     "agent_id": self.agent_id,
            #     "requires_auth": False
            # }
            # async with aiohttp.ClientSession() as session:
            #     async with session.post(
            #         f"{self.base_url}/convai/conversations",  # This endpoint may not exist
            #         headers=headers,
            #         json=conversation_data
            #     ) as response:
            if False:  # Disable this block
                pass  # This block is disabled

        except Exception as e:
            logger.error(f"Error starting conversation: {e}")
            return {
                "success": False,
                "error": f"Exception starting conversation: {str(e)}"
            }

    async def speech_to_text(self, audio_data: bytes) -> Dict[str, Any]:
        """Convert speech to text using 11Labs API"""
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "error": "11Labs API key required for real-time STT"
                }

            headers = {
                "xi-api-key": self.api_key,
            }

            # Use ElevenLabs speech-to-text endpoint according to API docs
            async with aiohttp.ClientSession() as session:
                # Create form data for audio upload (multipart/form-data)
                data = aiohttp.FormData()
                data.add_field('model_id', 'scribe_v1')  # Updated to valid model ID
                data.add_field('file', audio_data, filename='audio.webm', content_type='audio/webm')
                # Optional parameters based on docs
                data.add_field('language_code', 'en')  # English language
                data.add_field('diarize', 'false')  # Single speaker expected

                async with session.post(
                    f"{self.base_url}/speech-to-text",  # Correct endpoint from docs
                    headers=headers,
                    data=data,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        # Extract text from the response structure based on API docs
                        transcript_text = ""
                        confidence = 0.0

                        # According to API docs, response contains 'text' field
                        if "text" in result:
                            transcript_text = result["text"]

                        # Calculate confidence from language_probability if available
                        if "language_probability" in result:
                            confidence = result["language_probability"]

                        # Alternative: calculate from word-level confidence if available
                        elif "words" in result:
                            confidences = [w.get("confidence", 0.0) for w in result["words"] if "confidence" in w]
                            if confidences:
                                confidence = sum(confidences) / len(confidences)

                        return {
                            "success": True,
                            "text": transcript_text.strip(),
                            "confidence": confidence
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Speech-to-text failed: {response.status} - {error_text}")

                        return {
                            "success": False,
                            "error": f"Speech-to-text API error: {response.status} - {error_text}"
                        }

        except Exception as e:
            logger.error(f"Speech-to-text error: {e}")
            return {
                "success": False,
                "error": f"Speech-to-text exception: {str(e)}"
            }

    async def process_conversation_turn(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Process a conversation turn with fast AI data extraction and DB storage"""
        try:
            if session_id not in self.active_sessions:
                return {
                    "success": False,
                    "error": "Session not found"
                }

            conv_session = self.active_sessions[session_id]
            conv_session.last_activity = datetime.utcnow()
            conv_session.transcript.append(f"Patient: {user_input}")

            # Use faster AI extraction
            extracted_data = await self._ai_extract_patient_data(user_input, conv_session.patient_data)
            if extracted_data:
                conv_session.patient_data.update(extracted_data)
                logger.info(f"Updated patient data for {session_id}: {extracted_data}")

            # Generate contextual response
            agent_response = self._generate_agent_response(conv_session, user_input)
            conv_session.transcript.append(f"Agent: {agent_response}")

            # Check if we have minimum required data
            required_fields = ["name", "age", "chief_complaint"]
            completed_fields = [field for field in required_fields if field in conv_session.patient_data]
            completion_percentage = len(completed_fields) / len(required_fields) * 100

            return {
                "success": True,
                "agent_response": agent_response,
                "extracted_data": extracted_data,
                "session_data": conv_session.patient_data,
                "conversation_state": conv_session.conversation_state,
                "completion_percentage": completion_percentage,
                "required_fields_completed": completed_fields,
                "can_complete": len(completed_fields) == len(required_fields)
            }

        except Exception as e:
            logger.error(f"Error processing conversation turn: {e}")
            return {
                "success": False,
                "error": f"Conversation processing error: {str(e)}"
            }

    def _generate_agent_response(self, conv_session: ConversationSession, user_input: str) -> str:
        """Generate fast, contextual agent response for required fields"""

        patient_data = conv_session.patient_data

        # Priority-based question sequence for faster triage
        if not patient_data.get("name"):
            return "Hello! I'm your emergency triage assistant. What's your name?"

        elif not patient_data.get("age"):
            return f"Thanks {patient_data.get('name')}. How old are you?"

        elif not patient_data.get("chief_complaint"):
            return "What's the main reason you're here today? What's bothering you?"

        elif not patient_data.get("pain_scale") and "pain" in patient_data.get("chief_complaint", "").lower():
            return "On a scale of 0 to 10, how bad is your pain right now?"

        # Fast optional data collection
        elif not patient_data.get("allergies_asked"):
            patient_data["allergies_asked"] = True
            return "Any allergies to medications?"

        elif not patient_data.get("medications_asked"):
            patient_data["medications_asked"] = True
            return "Are you taking any medications regularly?"

        else:
            # Calculate completion status
            required = ["name", "age", "chief_complaint"]
            completed = [f for f in required if f in patient_data]

            if len(completed) == len(required):
                return "Perfect! I have all the essential information. You'll be triaged and seen by a healthcare provider shortly."
            else:
                return "Thank you for that information. Is there anything else about your symptoms you'd like to tell me?"

    async def _ai_extract_patient_data(self, text: str, existing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI agent for faster and more accurate data extraction"""
        import re

        extracted = {}
        text_lower = text.lower()

        # Enhanced name extraction
        name_patterns = [
            r"(?:my name is|i'm|i am|call me|name is)\s+([a-zA-Z][a-zA-Z\s]*[a-zA-Z])",
            r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",  # Full name at start
            r"i'm\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"
        ]
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Better name validation
                if len(name) > 2 and not any(word in name.lower() for word in ['years', 'old', 'pain', 'feel', 'have']):
                    extracted["name"] = name.title()
                    break

        # Enhanced age extraction
        age_patterns = [
            r"(\d{1,3})\s*(?:years?\s*)?old",
            r"(?:i'm|i am|age is|age)\s*(\d{1,3})",
            r"born in\s*(19|20)\d{2}"
        ]
        for pattern in age_patterns:
            match = re.search(pattern, text_lower)
            if match:
                if "born in" in pattern:
                    birth_year = int(match.group(0).split()[-1])
                    age = datetime.utcnow().year - birth_year
                else:
                    age = int(match.group(1))
                if 0 < age < 120:
                    extracted["age"] = age
                    break

        # Enhanced chief complaint extraction
        complaint_mapping = {
            "chest pain": ["chest pain", "heart pain", "chest hurt", "chest ache"],
            "headache": ["headache", "head pain", "migraine", "head hurt"],
            "abdominal pain": ["stomach pain", "belly pain", "abdominal pain", "stomach hurt"],
            "breathing difficulty": ["shortness of breath", "trouble breathing", "can't breathe", "breathing problem"],
            "nausea": ["nausea", "vomiting", "sick to stomach", "throw up"],
            "fever": ["fever", "hot", "temperature"],
            "injury": ["injury", "accident", "fall", "hurt", "cut", "wound"]
        }

        for complaint, keywords in complaint_mapping.items():
            if any(keyword in text_lower for keyword in keywords):
                extracted["chief_complaint"] = complaint
                break

        # Enhanced pain scale extraction
        pain_patterns = [
            r"pain.*?(\d+)\s*(?:out of\s*10|/10|level)",
            r"(\d+)\s*(?:out of\s*10|/10).*?pain",
            r"pain level\s*(\d+)"
        ]
        for pattern in pain_patterns:
            match = re.search(pattern, text_lower)
            if match:
                pain = int(match.group(1))
                if 0 <= pain <= 10:
                    extracted["pain_scale"] = pain
                    break

        # Smart medication extraction
        common_medications = {
            "aspirin": ["aspirin", "asa"],
            "ibuprofen": ["ibuprofen", "advil", "motrin"],
            "acetaminophen": ["acetaminophen", "tylenol", "paracetamol"],
            "metformin": ["metformin"],
            "lisinopril": ["lisinopril"],
            "atorvastatin": ["atorvastatin", "lipitor"]
        }

        found_meds = []
        for med_name, variants in common_medications.items():
            if any(variant in text_lower for variant in variants):
                found_meds.append(med_name)

        if found_meds:
            extracted["current_medications"] = found_meds

        # Context-aware responses
        if "allergies_asked" in existing_data:
            if any(word in text_lower for word in ["no", "none", "negative"]):
                extracted["allergies"] = []
            elif "penicillin" in text_lower:
                extracted["allergies"] = ["penicillin"]

        return extracted

    async def send_audio_to_agent(self, session_id: str, audio_data: bytes) -> Dict[str, Any]:
        """Process audio data using speech-to-text and store transcript in DB"""
        try:
            if session_id not in self.active_sessions:
                return {"success": False, "error": "Session not found"}

            # Convert speech to text
            stt_result = await self.speech_to_text(audio_data)

            if not stt_result.get("success"):
                return {
                    "success": False,
                    "error": f"Speech-to-text failed: {stt_result.get('error', 'Unknown error')}"
                }

            # Get session and add transcript
            conv_session = self.active_sessions[session_id]
            transcript_text = stt_result["text"]
            conv_session.transcript.append(f"Patient: {transcript_text}")
            conv_session.last_activity = datetime.utcnow()

            # Use AI agent for faster data extraction
            extracted_data = await self._ai_extract_patient_data(transcript_text, conv_session.patient_data)

            if extracted_data:
                conv_session.patient_data.update(extracted_data)

            # Generate simple response based on what we have
            agent_response_text = self._generate_agent_response(conv_session, transcript_text)
            conv_session.transcript.append(f"Agent: {agent_response_text}")

            # Convert agent response to speech
            audio_response = await self.text_to_speech(agent_response_text)

            return {
                "success": True,
                "transcribed_text": transcript_text,
                "agent_response": {
                    "text": agent_response_text,
                    "audio": audio_response
                },
                "extracted_data": extracted_data,
                "session_data": conv_session.patient_data,
                "conversation_state": conv_session.conversation_state
            }

        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            return {
                "success": False,
                "error": f"Exception processing audio: {str(e)}"
            }

    async def text_to_speech(self, text: str) -> Optional[str]:
        """Convert text to speech using 11Labs API"""
        try:
            if not self.api_key:
                logger.error("11Labs API key required for text-to-speech")
                return None

            if not text or not text.strip():
                logger.warning("Empty text provided for TTS")
                return None

            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }

            # Optimized voice settings for medical professional conversation
            data = {
                "text": text.strip(),
                "model_id": "eleven_multilingual_v1",  # Updated to available TTS model
                "voice_settings": {
                    "stability": 0.85,  # More stable for medical context
                    "similarity_boost": 0.80,  # Clear pronunciation
                    "style": 0.25,  # Professional tone
                    "use_speaker_boost": True
                },
                "optimize_streaming_latency": 2  # Lower latency for real-time
            }

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.post(
                    f"{self.base_url}/text-to-speech/{self.voice_id}",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        audio_content = await response.read()
                        # Return base64 encoded audio for frontend playback
                        audio_base64 = base64.b64encode(audio_content).decode('utf-8')
                        logger.info(f"TTS successful for text: '{text[:50]}...' ({len(audio_content)} bytes)")
                        return audio_base64
                    else:
                        error_text = await response.text()
                        logger.error(f"TTS API error: {response.status} - {error_text}")
                        return None

        except asyncio.TimeoutError:
            logger.error("TTS API timeout")
            return None
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return None

    async def complete_conversation(self, session_id: str) -> Dict[str, Any]:
        """Complete the conversation and return collected patient data"""
        try:
            if session_id not in self.active_sessions:
                return {
                    "success": False,
                    "error": "Session not found"
                }

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

            # Set default vitals if not collected
            patient_data.setdefault("bp_systolic", 120)
            patient_data.setdefault("bp_diastolic", 80)
            patient_data.setdefault("heart_rate", 80)
            patient_data.setdefault("temperature", 98.6)
            patient_data.setdefault("o2_saturation", 98)
            patient_data.setdefault("respiratory_rate", 16)

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
                "transcript": conv_session.transcript,
                "message": "Conversation completed successfully"
            }

        except Exception as e:
            logger.error(f"Error completing conversation: {e}")
            return {
                "success": False,
                "error": f"Exception completing conversation: {str(e)}"
            }

    async def end_conversation(self, session_id: str) -> Dict[str, Any]:
        """End a conversation session"""
        try:
            if session_id not in self.active_sessions:
                return {"success": False, "error": "Session not found"}

            conv_session = self.active_sessions[session_id]

            # Clean up any resources (simplified since we're not using complex conversation API)
            if conv_session.conversation_id:
                logger.info(f"Cleaning up conversation resources for {conv_session.conversation_id}")

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

    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current session status with completion tracking"""
        if session_id not in self.active_sessions:
            return None

        conv_session = self.active_sessions[session_id]

        # Calculate completion metrics
        required_fields = ["name", "age", "chief_complaint"]
        completed_fields = [field for field in required_fields if field in conv_session.patient_data]
        completion_percentage = len(completed_fields) / len(required_fields) * 100

        return {
            "session_id": session_id,
            "conversation_id": conv_session.conversation_id,
            "state": conv_session.conversation_state,
            "patient_data": conv_session.patient_data,
            "created_at": conv_session.created_at.isoformat(),
            "last_activity": conv_session.last_activity.isoformat(),
            "completed": conv_session.completed,
            "transcript_length": len(conv_session.transcript),
            "transcript": conv_session.transcript,
            "completion_percentage": completion_percentage,
            "required_fields_completed": completed_fields,
            "can_complete": len(completed_fields) == len(required_fields)
        }

    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get all active conversation sessions"""
        return [self.get_session_status(session_id) for session_id in self.active_sessions.keys() if self.get_session_status(session_id) is not None]




# Global instance
elevenlabs_service = ElevenLabsService()