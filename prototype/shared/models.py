"""Shared data models between client and server."""

from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


class BrowserState(BaseModel):
    """Current state of the browser."""
    
    url: str
    title: str
    html: str
    screenshot: str  # base64 encoded
    dom_elements: list[dict[str, Any]]
    viewport: dict[str, int]


class Action(BaseModel):
    """Action to be executed by the browser."""
    
    type: Literal["click", "input", "navigate", "scroll", "wait", "done", "extract"]
    index: Optional[int] = None
    text: Optional[str] = None
    url: Optional[str] = None
    query: Optional[str] = None
    direction: Optional[Literal["up", "down"]] = None
    amount: Optional[int] = None
    seconds: Optional[float] = None
    reasoning: Optional[str] = None


class UXFeedback(BaseModel):
    """UX analysis feedback."""
    
    url: str
    timestamp: str
    issues: list[str] = Field(default_factory=list)
    positive_aspects: list[str] = Field(default_factory=list)
    recommendation: str
    confidence: float = Field(ge=0.0, le=1.0)
    priority: Literal["low", "medium", "high"] = "medium"


class NavigationRequest(BaseModel):
    """Request sent from client to server."""
    
    task: str
    state: BrowserState
    step_number: int = 0


class NavigationResponse(BaseModel):
    """Response from server to client."""
    
    action: Action
    ux_feedback: UXFeedback
    message: Optional[str] = None
