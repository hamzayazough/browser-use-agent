"""FastAPI server that coordinates Navigation and UX Specialist agents."""

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.models import NavigationRequest, NavigationResponse
from server.navigation_agent import NavigationAgent
from server.ux_specialist import UXSpecialist
from server.feedback_storage import FeedbackStorage

# Import LLM - you can change this to your preferred LLM
try:
    from browser_use import ChatBrowserUse
    LLM_CLASS = ChatBrowserUse
except ImportError:
    from langchain_openai import ChatOpenAI
    LLM_CLASS = ChatOpenAI


# Initialize FastAPI app
app = FastAPI(
    title="Browser Agent Server",
    description="Cloud server for Navigation and UX Specialist agents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instances
navigation_agent: NavigationAgent = None
ux_specialist: UXSpecialist = None
feedback_storage: FeedbackStorage = None


@app.on_event("startup")
async def startup_event():
    """Initialize agents on server startup."""
    global navigation_agent, ux_specialist, feedback_storage
    
    print("🚀 Initializing agents...")
    
    # Initialize LLMs (you can use different models for each agent)
    nav_llm = LLM_CLASS(temperature=0.1)
    ux_llm = LLM_CLASS(temperature=0.3)
    
    # Initialize agents
    navigation_agent = NavigationAgent(llm=nav_llm)
    ux_specialist = UXSpecialist(llm=ux_llm)
    feedback_storage = FeedbackStorage()
    
    print("✅ Agents initialized")
    print(f"   - Navigation Agent: {type(nav_llm).__name__}")
    print(f"   - UX Specialist: {type(ux_llm).__name__}")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "service": "Browser Agent Server",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "agents": {
            "navigation": navigation_agent is not None,
            "ux_specialist": ux_specialist is not None,
        },
        "stats": {
            "navigation_steps": len(navigation_agent.history) if navigation_agent else 0,
            "ux_analyses": len(ux_specialist.feedback_history) if ux_specialist else 0,
        }
    }


@app.post("/navigate", response_model=NavigationResponse)
async def navigate(request: NavigationRequest):
    """
    Main endpoint: receives browser state and returns next action.
    
    Flow:
    1. UX Specialist analyzes the page
    2. Feedback is stored
    3. Navigation Agent decides next action
    4. Response is returned to client
    """
    if not navigation_agent or not ux_specialist:
        raise HTTPException(status_code=500, detail="Agents not initialized")
    
    try:
        print(f"\n{'='*60}")
        print(f"📥 Request - Step {request.step_number}")
        print(f"   URL: {request.state.url}")
        print(f"   Task: {request.task}")
        
        # 1. UX Specialist analyzes the page
        print("   🎨 UX Specialist analyzing...")
        ux_feedback = await ux_specialist.analyze_page(
            state=request.state,
            task=request.task,
            step_number=request.step_number
        )
        
        # 2. Store feedback
        feedback_storage.store(ux_feedback)
        print(f"   ✓ UX Analysis: {ux_feedback.recommendation[:60]}...")
        
        # 3. Navigation Agent decides action
        print("   🧭 Navigation Agent deciding...")
        action = await navigation_agent.decide_action(
            state=request.state,
            task=request.task,
            ux_feedback=ux_feedback,
            step_number=request.step_number
        )
        print(f"   ✓ Action: {action.type}")
        
        # 4. Build response
        response = NavigationResponse(
            action=action,
            ux_feedback=ux_feedback,
            message=f"Step {request.step_number} completed"
        )
        
        print("   📤 Response sent")
        return response
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """Get statistics about the current session."""
    if not navigation_agent or not ux_specialist:
        raise HTTPException(status_code=500, detail="Agents not initialized")
    
    return {
        "navigation": navigation_agent.get_history_summary(),
        "ux": ux_specialist.get_feedback_summary(),
        "feedback": feedback_storage.get_summary(),
    }


@app.get("/feedback")
async def get_feedback():
    """Get all stored UX feedback."""
    if not feedback_storage:
        raise HTTPException(status_code=500, detail="Storage not initialized")
    
    return {
        "feedback": [f.model_dump() for f in feedback_storage.get_all()]
    }


@app.post("/reset")
async def reset():
    """Reset all agents and clear history."""
    global navigation_agent, ux_specialist, feedback_storage
    
    if navigation_agent:
        navigation_agent.history.clear()
    if ux_specialist:
        ux_specialist.feedback_history.clear()
    if feedback_storage:
        feedback_storage.clear()
    
    return {"status": "reset", "message": "All agents cleared"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
