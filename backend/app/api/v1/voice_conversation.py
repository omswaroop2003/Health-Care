"""
Voice Conversation API Endpoints for Patient Intake
Handles conversational AI interactions using 11Labs agent
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from typing import Dict, Any, Optional
import logging
import json
import uuid
from datetime import datetime

from ...services.elevenlabs_service import elevenlabs_service
from ...services.ai_triage_simple import ai_triage_engine
from ...models.mongo_models import Patient, QueueEntry, TriageAssessment, PatientCreate

router = APIRouter()
logger = logging.getLogger(__name__)

# Track active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

@router.post("/conversations/start")
async def start_voice_conversation():
    """Start a new voice conversation session"""
    try:
        session_id = str(uuid.uuid4())
        result = await elevenlabs_service.start_conversation(session_id)

        if result["success"]:
            logger.info(f"Started voice conversation session: {session_id}")
            return {
                "session_id": session_id,
                "conversation_id": result.get("conversation_id"),
                "message": "Voice conversation started successfully",
                "instructions": "You can now send audio to the /conversations/{session_id}/audio endpoint"
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])

    except Exception as e:
        logger.error(f"Failed to start voice conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start conversation: {str(e)}")

@router.post("/conversations/{session_id}/audio")
async def send_audio_to_conversation(
    session_id: str,
    audio_file: UploadFile = File(...)
):
    """Send audio data to the conversational agent"""
    try:
        # Read audio data
        audio_data = await audio_file.read()

        # Convert speech to text
        stt_result = await elevenlabs_service.speech_to_text(audio_data)

        if not stt_result["success"]:
            raise HTTPException(status_code=500, detail=stt_result.get("error", "Speech-to-text failed"))

        # Process conversation turn with the transcribed text
        result = await elevenlabs_service.process_conversation_turn(session_id, stt_result["text"])

        if result["success"]:
            return {
                "session_id": session_id,
                "agent_response": result.get("agent_response"),
                "extracted_data": result.get("extracted_data", {}),
                "session_data": result.get("session_data", {}),
                "message": "Audio processed successfully"
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except Exception as e:
        logger.error(f"Failed to process audio for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process audio: {str(e)}")

@router.get("/conversations/{session_id}/status")
async def get_conversation_status(session_id: str):
    """Get current conversation status and collected data"""
    try:
        status = elevenlabs_service.get_session_status(session_id)

        if status:
            return status
        else:
            raise HTTPException(status_code=404, detail="Conversation session not found")

    except Exception as e:
        logger.error(f"Failed to get conversation status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@router.get("/conversations/{session_id}/response")
async def get_conversation_response(session_id: str):
    """Get latest response from the conversational agent"""
    try:
        result = await elevenlabs_service.get_conversation_response(session_id)

        if result["success"]:
            return {
                "session_id": session_id,
                "conversation_data": result.get("conversation_data"),
                "session_data": result.get("session_data", {}),
                "message": "Response retrieved successfully"
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except Exception as e:
        logger.error(f"Failed to get conversation response: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get response: {str(e)}")

@router.post("/conversations/{session_id}/complete")
async def complete_voice_conversation(session_id: str):
    """Complete conversation and create patient record with AI triage"""
    try:
        # Get completed conversation data
        result = await elevenlabs_service.complete_conversation(session_id)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        patient_data = result["patient_data"]

        # Create patient record with AI triage - replicating the logic from patients_mongo.py
        try:
            # Prepare AI input data
            ai_input_data = {
                "age": patient_data.get("age", 50),
                "gender": patient_data.get("gender", "Other"),
                "chief_complaint": patient_data.get("chief_complaint", ""),
                "bp_systolic": patient_data.get("bp_systolic", 120),
                "bp_diastolic": patient_data.get("bp_diastolic", 80),
                "heart_rate": patient_data.get("heart_rate", 80),
                "temperature": patient_data.get("temperature", 98.6),
                "o2_saturation": patient_data.get("o2_saturation", 98),
                "respiratory_rate": patient_data.get("respiratory_rate", 16),
                "pain_scale": patient_data.get("pain_scale", 0),
                "consciousness_level": patient_data.get("consciousness_level", "Alert"),
                "bleeding": patient_data.get("bleeding", False),
                "breathing_difficulty": patient_data.get("breathing_difficulty", False),
                "trauma_indicator": patient_data.get("trauma_indicator", False),
                "chronic_conditions": patient_data.get("medical_history", {}),
                "allergies": patient_data.get("allergies", []),
                "medications_count": len(patient_data.get("current_medications", [])),
                "previous_admissions": 0
            }

            # Get AI triage assessment
            esi_level, confidence, reasons = ai_triage_engine.predict_esi_level(ai_input_data)
            priority_score = ai_triage_engine.calculate_priority_score(
                esi_level, 0, patient_data.get("age", 50), patient_data.get("pain_scale", 0)
            )

            # Create patient record
            patient = Patient(
                name=patient_data["name"],
                age=patient_data["age"],
                gender=patient_data.get("gender", "Other"),
                chief_complaint=patient_data["chief_complaint"],
                vitals=ai_input_data,
                medical_history=patient_data.get("medical_history", {}),
                allergies=patient_data.get("allergies", []),
                current_medications=patient_data.get("current_medications", []),
                consciousness_level=patient_data.get("consciousness_level", "Alert"),
                bleeding=patient_data.get("bleeding", False),
                breathing_difficulty=patient_data.get("breathing_difficulty", False),
                trauma_indicator=patient_data.get("trauma_indicator", False),
                esi_level=esi_level,
                priority_score=priority_score,
                ai_confidence=confidence,
                ai_reasoning=reasons,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            await patient.save()

            # Create triage assessment record
            assessment = TriageAssessment(
                patient_id=str(patient.id),
                esi_level=esi_level,
                confidence_score=confidence,
                reasoning=reasons,
                features_analyzed=ai_input_data,
                assessor_type="voice_ai_triage"
            )
            await assessment.save()

            # Add to queue
            queue_entry = QueueEntry(
                patient_id=str(patient.id),
                esi_level=esi_level,
                priority_score=priority_score,
                entered_queue=datetime.utcnow(),
                estimated_treatment_time=30
            )
            await queue_entry.save()

            # Calculate queue position
            higher_priority_count = await QueueEntry.find(
                QueueEntry.priority_score > priority_score,
                QueueEntry.status == "waiting"
            ).count()
            queue_position = higher_priority_count + 1

            return {
                "session_id": session_id,
                "patient_id": str(patient.id),
                "patient_name": patient.name,
                "esi_level": esi_level,
                "priority_score": priority_score,
                "ai_confidence": confidence,
                "queue_position": queue_position,
                "collected_data": patient_data,
                "message": "Voice conversation completed and patient registered successfully"
            }

        except Exception as e:
            logger.error(f"Failed to create patient record: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create patient record: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to complete voice conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to complete conversation: {str(e)}")

@router.delete("/conversations/{session_id}")
async def end_voice_conversation(session_id: str):
    """End a voice conversation session"""
    try:
        result = await elevenlabs_service.end_conversation(session_id)

        if result["success"]:
            return {
                "session_id": session_id,
                "message": "Conversation ended successfully"
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except Exception as e:
        logger.error(f"Failed to end conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to end conversation: {str(e)}")

@router.get("/conversations")
async def get_active_conversations():
    """Get all active conversation sessions"""
    try:
        sessions = elevenlabs_service.get_active_sessions()
        return {
            "active_sessions": sessions,
            "total_count": len(sessions)
        }

    except Exception as e:
        logger.error(f"Failed to get active conversations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversations: {str(e)}")

# WebSocket endpoint for real-time voice communication
@router.websocket("/conversations/{session_id}/ws")
async def voice_conversation_websocket(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time voice conversation"""
    await websocket.accept()
    active_connections[session_id] = websocket

    try:
        logger.info(f"WebSocket connection established for session: {session_id}")

        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "session_id": session_id,
            "message": "WebSocket connection established"
        })

        while True:
            # Wait for messages from client
            message = await websocket.receive_json()

            if message.get("type") == "start_conversation":
                # Start conversation with agent
                result = await elevenlabs_service.start_conversation(session_id)
                await websocket.send_json({
                    "type": "conversation_started",
                    "success": result["success"],
                    "data": result
                })

            elif message.get("type") == "audio_data":
                # Handle base64 encoded audio data
                try:
                    import base64
                    audio_data = base64.b64decode(message.get("audio", ""))
                    result = await elevenlabs_service.send_audio_to_agent(session_id, audio_data)

                    await websocket.send_json({
                        "type": "audio_processed",
                        "success": result["success"],
                        "data": result
                    })
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Failed to process audio: {str(e)}"
                    })

            elif message.get("type") == "get_status":
                # Get current conversation status
                status = elevenlabs_service.get_session_status(session_id)
                await websocket.send_json({
                    "type": "status_update",
                    "data": status
                })

            elif message.get("type") == "complete_conversation":
                # Complete the conversation
                result = await elevenlabs_service.complete_conversation(session_id)
                if result["success"]:
                    # Create patient record using the same logic as the REST endpoint
                    try:
                        patient_data = result["patient_data"]

                        # Prepare AI input data
                        ai_input_data = {
                            "age": patient_data.get("age", 50),
                            "gender": patient_data.get("gender", "Other"),
                            "chief_complaint": patient_data.get("chief_complaint", ""),
                            "bp_systolic": patient_data.get("bp_systolic", 120),
                            "bp_diastolic": patient_data.get("bp_diastolic", 80),
                            "heart_rate": patient_data.get("heart_rate", 80),
                            "temperature": patient_data.get("temperature", 98.6),
                            "o2_saturation": patient_data.get("o2_saturation", 98),
                            "respiratory_rate": patient_data.get("respiratory_rate", 16),
                            "pain_scale": patient_data.get("pain_scale", 0),
                            "consciousness_level": patient_data.get("consciousness_level", "Alert"),
                            "bleeding": patient_data.get("bleeding", False),
                            "breathing_difficulty": patient_data.get("breathing_difficulty", False),
                            "trauma_indicator": patient_data.get("trauma_indicator", False),
                            "chronic_conditions": patient_data.get("medical_history", {}),
                            "allergies": patient_data.get("allergies", []),
                            "medications_count": len(patient_data.get("current_medications", [])),
                            "previous_admissions": 0
                        }

                        # Get AI triage assessment
                        esi_level, confidence, reasons = ai_triage_engine.predict_esi_level(ai_input_data)
                        priority_score = ai_triage_engine.calculate_priority_score(
                            esi_level, 0, patient_data.get("age", 50), patient_data.get("pain_scale", 0)
                        )

                        # Create patient record
                        patient = Patient(
                            name=patient_data["name"],
                            age=patient_data["age"],
                            gender=patient_data.get("gender", "Other"),
                            chief_complaint=patient_data["chief_complaint"],
                            vitals=ai_input_data,
                            medical_history=patient_data.get("medical_history", {}),
                            allergies=patient_data.get("allergies", []),
                            current_medications=patient_data.get("current_medications", []),
                            consciousness_level=patient_data.get("consciousness_level", "Alert"),
                            bleeding=patient_data.get("bleeding", False),
                            breathing_difficulty=patient_data.get("breathing_difficulty", False),
                            trauma_indicator=patient_data.get("trauma_indicator", False),
                            esi_level=esi_level,
                            priority_score=priority_score,
                            ai_confidence=confidence,
                            ai_reasoning=reasons,
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )

                        await patient.save()

                        # Add to queue
                        queue_entry = QueueEntry(
                            patient_id=str(patient.id),
                            esi_level=esi_level,
                            priority_score=priority_score,
                            entered_queue=datetime.utcnow(),
                            estimated_treatment_time=30
                        )
                        await queue_entry.save()

                        # Calculate queue position
                        higher_priority_count = await QueueEntry.find(
                            QueueEntry.priority_score > priority_score,
                            QueueEntry.status == "waiting"
                        ).count()
                        queue_position = higher_priority_count + 1

                        await websocket.send_json({
                            "type": "conversation_completed",
                            "success": True,
                            "patient_data": {
                                "id": str(patient.id),
                                "name": patient.name,
                                "esi_level": esi_level,
                                "priority_score": priority_score,
                                "ai_confidence": confidence,
                                "queue_position": queue_position
                            }
                        })
                    except Exception as e:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Failed to create patient record: {str(e)}"
                        })
                else:
                    await websocket.send_json({
                        "type": "conversation_completed",
                        "success": False,
                        "error": result["error"]
                    })

            elif message.get("type") == "end_conversation":
                # End the conversation
                result = await elevenlabs_service.end_conversation(session_id)
                await websocket.send_json({
                    "type": "conversation_ended",
                    "success": result["success"],
                    "data": result
                })
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"WebSocket error: {str(e)}"
            })
        except:
            pass
    finally:
        # Clean up
        if session_id in active_connections:
            del active_connections[session_id]

        # End conversation if still active
        try:
            await elevenlabs_service.end_conversation(session_id)
        except:
            pass

@router.post("/conversations/{session_id}/simulate-audio")
async def simulate_audio_input(session_id: str, text_input: Dict[str, str]):
    """Simulate audio input with text for testing purposes"""
    try:
        # This is for testing - simulate what would be extracted from audio
        text = text_input.get("text", "")

        # Get session status
        status = elevenlabs_service.get_session_status(session_id)
        if not status:
            raise HTTPException(status_code=404, detail="Session not found")

        # Manually extract data from text (simulation)
        service = elevenlabs_service
        if session_id in service.active_sessions:
            conv_session = service.active_sessions[session_id]

            # Extract data using the same method
            extracted_data = await service._extract_patient_data_from_response({"transcript": text})

            # Update session data
            conv_session.patient_data.update(extracted_data)
            conv_session.last_activity = datetime.utcnow()

            return {
                "session_id": session_id,
                "extracted_data": extracted_data,
                "session_data": conv_session.patient_data,
                "message": "Text input processed successfully (simulation)"
            }
        else:
            raise HTTPException(status_code=404, detail="Session not found")

    except Exception as e:
        logger.error(f"Failed to simulate audio input: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process text: {str(e)}")



