"""
FastAPI Async API for BroomBot Agent System

This API provides REST endpoints to interact with the BroomBot multi-agent system
for motorcycle product, service, and booking assistance.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio
import uuid
from contextlib import asynccontextmanager

from .agent import BroomBotAgent


# ============================================================================
# Pydantic Models (Request/Response Schemas)
# ============================================================================

class ChatRequest(BaseModel):
    """Request model for chat interactions"""
    message: str = Field(..., description="User message to the agent")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    model: Optional[str] = Field("gemini-2.5-pro", description="Model to use for the agent")


class ChatResponse(BaseModel):
    """Response model for chat interactions"""
    session_id: str = Field(..., description="Session ID for this conversation")
    response: str = Field(..., description="Agent's response")
    agent_name: Optional[str] = Field(None, description="Name of the agent that responded")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SessionInfo(BaseModel):
    """Session information model"""
    session_id: str
    created_at: datetime
    last_active: datetime
    message_count: int


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    agents_loaded: bool
    active_sessions: int


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Session Management
# ============================================================================

class SessionManager:
    """Manages conversation sessions and agent instances"""

    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.agents: Dict[str, BroomBotAgent] = {}

    def create_session(self, model: str = "gemini-2.5-pro") -> str:
        """Create a new session and return session ID"""
        session_id = str(uuid.uuid4())

        # Create agent instance for this session
        agent = BroomBotAgent(model=model)

        self.sessions[session_id] = {
            "created_at": datetime.utcnow(),
            "last_active": datetime.utcnow(),
            "message_count": 0,
            "model": model
        }

        self.agents[session_id] = agent

        return session_id

    def get_agent(self, session_id: str) -> Optional[BroomBotAgent]:
        """Get agent instance for a session"""
        return self.agents.get(session_id)

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        return self.sessions.get(session_id)

    def update_session_activity(self, session_id: str):
        """Update session's last active timestamp"""
        if session_id in self.sessions:
            self.sessions[session_id]["last_active"] = datetime.utcnow()
            self.sessions[session_id]["message_count"] += 1

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and cleanup resources"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            if session_id in self.agents:
                del self.agents[session_id]
            return True
        return False

    def get_all_sessions(self) -> List[SessionInfo]:
        """Get all active sessions"""
        return [
            SessionInfo(
                session_id=sid,
                created_at=info["created_at"],
                last_active=info["last_active"],
                message_count=info["message_count"]
            )
            for sid, info in self.sessions.items()
        ]

    async def cleanup_inactive_sessions(self, max_inactive_minutes: int = 30):
        """Cleanup sessions inactive for more than specified minutes"""
        now = datetime.utcnow()
        inactive_sessions = []

        for session_id, info in self.sessions.items():
            inactive_time = (now - info["last_active"]).total_seconds() / 60
            if inactive_time > max_inactive_minutes:
                inactive_sessions.append(session_id)

        for session_id in inactive_sessions:
            self.delete_session(session_id)

        return len(inactive_sessions)


# ============================================================================
# FastAPI Application Setup
# ============================================================================

# Global session manager
session_manager = SessionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("🚀 BroomBot API starting up...")

    # Start background task for session cleanup
    async def periodic_cleanup():
        while True:
            await asyncio.sleep(300)  # Run every 5 minutes
            cleaned = await session_manager.cleanup_inactive_sessions()
            if cleaned > 0:
                print(f"🧹 Cleaned up {cleaned} inactive sessions")

    cleanup_task = asyncio.create_task(periodic_cleanup())

    yield

    # Shutdown
    print("🛑 BroomBot API shutting down...")
    cleanup_task.cancel()


# Create FastAPI app
app = FastAPI(
    title="BroomBot API",
    description="REST API for BroomBot Multi-Agent System - Motorcycle Product, Service, and Booking Assistant",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to BroomBot API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        agents_loaded=True,
        active_sessions=len(session_manager.sessions)
    )


@app.post("/sessions", tags=["Sessions"])
async def create_session(model: str = "gemini-2.5-pro") -> Dict[str, str]:
    """
    Create a new conversation session

    Returns:
        dict: Contains session_id for future requests
    """
    try:
        session_id = session_manager.create_session(model=model)
        return {
            "session_id": session_id,
            "message": "Session created successfully",
            "model": model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@app.get("/sessions", response_model=List[SessionInfo], tags=["Sessions"])
async def list_sessions():
    """List all active sessions"""
    return session_manager.get_all_sessions()


@app.get("/sessions/{session_id}", tags=["Sessions"])
async def get_session(session_id: str):
    """Get information about a specific session"""
    info = session_manager.get_session_info(session_id)
    if not info:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_id,
        **info
    }


@app.delete("/sessions/{session_id}", tags=["Sessions"])
async def delete_session(session_id: str):
    """Delete a session"""
    success = session_manager.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"message": "Session deleted successfully"}


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Send a message to the BroomBot agent

    Args:
        request: ChatRequest containing message and optional session_id

    Returns:
        ChatResponse with agent's reply
    """
    try:
        # Create session if not provided
        session_id = request.session_id
        if not session_id:
            session_id = session_manager.create_session(model=request.model)

        # Get agent for this session
        agent = session_manager.get_agent(session_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Session not found. Please create a new session.")

        # Update session activity
        session_manager.update_session_activity(session_id)

        # Get root agent and process message asynchronously
        root_agent = agent.get_root_agent()

        # Run agent interaction in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: root_agent.run(request.message)
        )

        # Extract response text (adjust based on actual agent response structure)
        # The agent.run() method returns a response object, we need to extract the text
        response_text = str(response) if response else "No response from agent"

        return ChatResponse(
            session_id=session_id,
            response=response_text,
            agent_name=root_agent.name,
            timestamp=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing message: {str(e)}"
        )


@app.post("/chat/stream", tags=["Chat"])
async def chat_stream(request: ChatRequest):
    """
    Stream chat responses (for future implementation with streaming support)

    Note: This is a placeholder for streaming functionality
    """
    raise HTTPException(
        status_code=501,
        detail="Streaming not yet implemented. Use /chat endpoint for now."
    )


# ============================================================================
# Specialized Endpoints (Optional - Direct Agent Access)
# ============================================================================

@app.post("/agents/product/query", tags=["Specialized Agents"])
async def query_product_agent(session_id: str, query: str):
    """
    Directly query the Product Agent

    Args:
        session_id: Active session ID
        query: Product-related query
    """
    agent = session_manager.get_agent(session_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: agent.product_agent.run(query)
        )

        return {
            "agent": "product_agent",
            "response": str(response),
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/service/query", tags=["Specialized Agents"])
async def query_service_agent(session_id: str, query: str):
    """
    Directly query the Service Agent

    Args:
        session_id: Active session ID
        query: Service-related query
    """
    agent = session_manager.get_agent(session_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: agent.service_agent.run(query)
        )

        return {
            "agent": "service_agent",
            "response": str(response),
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/booking/query", tags=["Specialized Agents"])
async def query_booking_agent(session_id: str, query: str):
    """
    Directly query the Booking Management Agent

    Args:
        session_id: Active session ID
        query: Booking-related query
    """
    agent = session_manager.get_agent(session_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: agent.booking_agent.run(query)
        )

        return {
            "agent": "booking_agent",
            "response": str(response),
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/lead-analysis/query", tags=["Specialized Agents"])
async def query_lead_analysis_agent(session_id: str, query: str):
    """
    Directly query the Lead Analysis Agent

    Args:
        session_id: Active session ID
        query: Lead analysis query
    """
    agent = session_manager.get_agent(session_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: agent.lead_analysis_agent.run(query)
        )

        return {
            "agent": "lead_analysis_agent",
            "response": str(response),
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return ErrorResponse(
        error="Internal Server Error",
        detail=str(exc),
        timestamp=datetime.utcnow()
    )


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("🤖 Starting BroomBot API Server...")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")

    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
