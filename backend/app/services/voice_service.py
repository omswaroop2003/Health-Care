"""
AI Voice Agent Service using 11Labs API
Provides voice announcements and alerts for emergency triage system
"""

import os
import asyncio
import logging
from typing import Optional, Dict, List
from datetime import datetime
import aiohttp
import json
from io import BytesIO
import base64

logger = logging.getLogger(__name__)

class VoiceAlertService:
    """AI Voice Agent for Emergency Triage Announcements"""

    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.api_url = "https://api.elevenlabs.io/v1"
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Default voice

        # Voice settings for medical announcements
        self.voice_settings = {
            "stability": 0.5,
            "similarity_boost": 0.5,
            "style": 0.0,
            "use_speaker_boost": True
        }

        # Track announcement history
        self.announcement_history: List[Dict] = []
        self.enabled = bool(self.api_key)

        if not self.enabled:
            logger.warning("11Labs API key not found. Voice alerts disabled.")
        else:
            logger.info("Voice Alert Service initialized with 11Labs API")

    async def _generate_speech(self, text: str, voice_settings: Optional[Dict] = None) -> Optional[bytes]:
        """Generate speech audio using 11Labs API"""
        if not self.enabled:
            logger.warning("Voice service disabled - no API key")
            return None

        try:
            settings = voice_settings or self.voice_settings

            payload = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": settings
            }

            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/text-to-speech/{self.voice_id}",
                    json=payload,
                    headers=headers,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        audio_data = await response.read()
                        logger.info(f"Generated speech for: {text[:50]}...")
                        return audio_data
                    else:
                        error_text = await response.text()
                        logger.error(f"11Labs API error {response.status}: {error_text}")
                        return None

        except Exception as e:
            logger.error(f"Failed to generate speech: {e}")
            return None

    def _log_announcement(self, announcement_type: str, message: str, patient_id: Optional[int] = None):
        """Log announcement for audit trail"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": announcement_type,
            "message": message,
            "patient_id": patient_id
        }

        self.announcement_history.append(log_entry)

        # Keep only last 100 announcements
        if len(self.announcement_history) > 100:
            self.announcement_history = self.announcement_history[-100:]

    async def announce_critical_patient(self, patient_id: int, esi_level: int, chief_complaint: str) -> bool:
        """Announce critical patient requiring immediate attention"""

        # Create appropriate urgency message based on ESI level
        urgency_messages = {
            1: "EMERGENCY ALERT: Code Blue activation required",
            2: "CRITICAL ALERT: Immediate physician attention needed",
            3: "URGENT: Patient requires prompt medical evaluation"
        }

        urgency = urgency_messages.get(esi_level, "Patient alert")

        message = (
            f"{urgency}. "
            f"Patient {patient_id} presenting with {chief_complaint}. "
            f"Emergency Severity Index Level {esi_level}. "
            f"Staff to bed assignment immediately."
        )

        # Use more urgent voice settings for critical patients
        critical_voice_settings = {
            "stability": 0.3,  # More variation for urgency
            "similarity_boost": 0.7,
            "style": 0.2,  # More expressive
            "use_speaker_boost": True
        }

        audio_data = await self._generate_speech(message, critical_voice_settings)

        if audio_data:
            self._log_announcement("critical_patient", message, patient_id)
            # In a real implementation, you would play this audio through hospital PA system
            logger.info(f"VOICE ALERT: {message}")
            return True

        return False

    async def announce_queue_status(self, waiting_count: int, critical_count: int) -> bool:
        """Announce current queue status"""

        message = (
            f"Queue status update: {waiting_count} patients currently waiting. "
        )

        if critical_count > 0:
            message += f"{critical_count} critical patients require immediate attention. "

        if waiting_count > 20:
            message += "Emergency department at high capacity. Consider overflow protocols."
        elif waiting_count > 10:
            message += "Emergency department experiencing moderate volume."
        else:
            message += "Emergency department operating at normal capacity."

        audio_data = await self._generate_speech(message)

        if audio_data:
            self._log_announcement("queue_status", message)
            logger.info(f"VOICE ANNOUNCEMENT: {message}")
            return True

        return False

    async def announce_mass_casualty_event(self, patient_count: int, event_description: str) -> bool:
        """Announce mass casualty event activation"""

        message = (
            f"MASS CASUALTY INCIDENT ACTIVATION. "
            f"{patient_count} patients incoming from {event_description}. "
            f"All available staff report to emergency department. "
            f"Activate disaster protocols immediately. "
            f"Repeat: Mass casualty incident in progress."
        )

        # Use very urgent voice settings for mass casualty
        emergency_voice_settings = {
            "stability": 0.2,
            "similarity_boost": 0.8,
            "style": 0.4,
            "use_speaker_boost": True
        }

        audio_data = await self._generate_speech(message, emergency_voice_settings)

        if audio_data:
            self._log_announcement("mass_casualty", message)
            logger.critical(f"MASS CASUALTY ALERT: {message}")
            return True

        return False

    async def announce_patient_update(self, patient_id: int, old_esi: int, new_esi: int, reason: str) -> bool:
        """Announce patient condition change"""

        if new_esi < old_esi:
            # Patient condition worsened
            message = (
                f"Patient condition alert: Patient {patient_id} condition has deteriorated. "
                f"ESI level changed from {old_esi} to {new_esi}. "
                f"Reason: {reason}. Immediate reassessment required."
            )
        else:
            # Patient condition improved
            message = (
                f"Patient update: Patient {patient_id} condition stable. "
                f"ESI level updated from {old_esi} to {new_esi}."
            )

        audio_data = await self._generate_speech(message)

        if audio_data:
            self._log_announcement("patient_update", message, patient_id)
            logger.info(f"PATIENT UPDATE: {message}")
            return True

        return False

    async def announce_staff_alert(self, message: str, urgency: str = "normal") -> bool:
        """General staff announcement"""

        prefix_messages = {
            "high": "URGENT STAFF ALERT: ",
            "critical": "EMERGENCY STAFF ALERT: ",
            "normal": "Staff notification: "
        }

        full_message = prefix_messages.get(urgency, "Staff notification: ") + message

        # Adjust voice settings based on urgency
        voice_settings = self.voice_settings.copy()
        if urgency in ["high", "critical"]:
            voice_settings["stability"] = 0.3
            voice_settings["style"] = 0.2

        audio_data = await self._generate_speech(full_message, voice_settings)

        if audio_data:
            self._log_announcement("staff_alert", full_message)
            logger.info(f"STAFF ALERT: {full_message}")
            return True

        return False

    def get_available_voices(self) -> List[Dict]:
        """Get list of available voices from 11Labs"""
        # This would make an API call to get available voices
        # For now, return some common medical-appropriate voices
        return [
            {
                "voice_id": "21m00Tcm4TlvDq8ikWAM",
                "name": "Rachel - Professional Female",
                "description": "Clear, professional female voice suitable for medical announcements"
            },
            {
                "voice_id": "AZnzlk1XvdvUeBnXmlld",
                "name": "Domi - Confident Female",
                "description": "Confident female voice with good clarity"
            },
            {
                "voice_id": "EXAVITQu4vr4xnSDxMaL",
                "name": "Bella - Warm Female",
                "description": "Warm, reassuring female voice"
            }
        ]

    def get_announcement_history(self, limit: int = 20) -> List[Dict]:
        """Get recent announcement history"""
        return self.announcement_history[-limit:]

    async def test_voice_service(self) -> Dict:
        """Test the voice service functionality"""
        if not self.enabled:
            return {
                "status": "disabled",
                "message": "11Labs API key not configured"
            }

        test_message = "Voice alert system test. Emergency triage system operational."

        try:
            audio_data = await self._generate_speech(test_message)

            if audio_data:
                return {
                    "status": "success",
                    "message": "Voice service operational",
                    "audio_length": len(audio_data),
                    "test_message": test_message
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to generate speech"
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Voice service error: {str(e)}"
            }

    def set_voice_settings(self, stability: float, similarity_boost: float, style: float = 0.0):
        """Update voice settings for announcements"""
        self.voice_settings.update({
            "stability": max(0.0, min(1.0, stability)),
            "similarity_boost": max(0.0, min(1.0, similarity_boost)),
            "style": max(0.0, min(1.0, style)),
            "use_speaker_boost": True
        })

        logger.info(f"Voice settings updated: {self.voice_settings}")

# Global voice service instance
voice_service = VoiceAlertService()