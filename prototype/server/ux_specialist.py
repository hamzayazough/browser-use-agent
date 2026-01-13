"""UX Specialist Agent - Analyzes pages and provides feedback."""

import json
from datetime import datetime
from typing import Optional

from browser_use.llm.messages import SystemMessage, UserMessage

from shared.models import BrowserState, UXFeedback


class UXSpecialist:
    """Agent specialized in UX analysis and recommendations."""
    
    def __init__(self, llm):
        """
        Initialize UX Specialist.
        
        Args:
            llm: Language model instance (e.g., ChatBrowserUse, ChatOpenAI)
        """
        self.llm = llm
        self.feedback_history: list[UXFeedback] = []
        
        self.system_prompt = """You are a UX Specialist AI agent. Your role is to:

1. Analyze web pages from a user experience perspective
2. Identify UX issues and positive aspects
3. Provide actionable recommendations for navigation
4. Help the Navigation Agent make informed decisions

For each page, analyze:
- Layout and visual hierarchy
- Element visibility and accessibility
- User flow and navigation patterns
- Content relevance to the task
- Potential obstacles or confusing elements

Return your analysis in JSON format:
{
    "issues": ["list of UX issues found"],
    "positive_aspects": ["list of good UX elements"],
    "recommendation": "clear recommendation for next action",
    "confidence": 0.0-1.0,
    "priority": "low|medium|high"
}"""
    
    async def analyze_page(
        self,
        state: BrowserState,
        task: str,
        step_number: int = 0
    ) -> UXFeedback:
        """
        Analyze the current page and provide UX feedback.
        
        Args:
            state: Current browser state
            task: User's task
            step_number: Current step number
            
        Returns:
            UXFeedback with analysis and recommendations
        """
        # Build analysis prompt
        prompt = self._build_analysis_prompt(state, task, step_number)
        
        # Get LLM analysis with proper message format
        messages = [
            SystemMessage(content=self.system_prompt),
            UserMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        # Parse response
        try:
            analysis = self._parse_response(response.completion)
        except Exception as e:
            print(f"Warning: Failed to parse UX analysis: {e}")
            analysis = {
                "issues": ["Failed to analyze page"],
                "positive_aspects": [],
                "recommendation": "Continue with caution",
                "confidence": 0.3,
                "priority": "medium"
            }
        
        # Create feedback object
        feedback = UXFeedback(
            url=state.url,
            timestamp=datetime.now().isoformat(),
            issues=analysis.get("issues", []),
            positive_aspects=analysis.get("positive_aspects", []),
            recommendation=analysis.get("recommendation", "No recommendation"),
            confidence=analysis.get("confidence", 0.5),
            priority=analysis.get("priority", "medium")
        )
        
        # Store in history
        self.feedback_history.append(feedback)
        
        return feedback
    
    def _build_analysis_prompt(
        self,
        state: BrowserState,
        task: str,
        step_number: int
    ) -> str:
        """Build the analysis prompt for the LLM."""
        
        # Summarize DOM elements
        dom_summary = self._summarize_dom(state.dom_elements)
        
        # Get recent history context
        history_context = ""
        if len(self.feedback_history) > 0:
            recent = self.feedback_history[-3:]  # Last 3 pages
            history_context = "\n\nRecent page history:\n"
            for i, feedback in enumerate(recent, 1):
                history_context += f"{i}. {feedback.url} - {feedback.recommendation}\n"
        
        prompt = f"""Analyze this web page for the following task:

TASK: {task}
STEP: {step_number}
CURRENT URL: {state.url}
PAGE TITLE: {state.title}

AVAILABLE ELEMENTS:
{dom_summary}

{history_context}

Please analyze the page and provide:
1. UX issues that might hinder task completion
2. Positive UX aspects that help with the task
3. Clear recommendation for what the Navigation Agent should do next
4. Your confidence level (0.0-1.0)
5. Priority level for this recommendation

Return ONLY valid JSON matching this format:
{{
    "issues": ["issue1", "issue2"],
    "positive_aspects": ["aspect1", "aspect2"],
    "recommendation": "clear next step recommendation",
    "confidence": 0.85,
    "priority": "high"
}}"""
        
        return prompt
    
    def _summarize_dom(self, dom_elements: list[dict], max_elements: int = 20) -> str:
        """Summarize DOM elements for the prompt."""
        if not dom_elements:
            return "No interactive elements found."
        
        summary_lines = []
        for i, elem in enumerate(dom_elements[:max_elements]):
            text = elem.get('text', '')[:50]
            tag = elem.get('tag', 'unknown')
            index = elem.get('index', i)
            
            summary_lines.append(f"  [{index}] <{tag}> {text}")
        
        if len(dom_elements) > max_elements:
            summary_lines.append(f"  ... and {len(dom_elements) - max_elements} more elements")
        
        return "\n".join(summary_lines)
    
    def _parse_response(self, content: str) -> dict:
        """Parse LLM response to extract JSON."""
        # Try to find JSON in the response
        content = content.strip()
        
        # If response is wrapped in markdown code blocks
        if content.startswith("```"):
            # Extract content between code blocks
            lines = content.split("\n")
            json_lines = []
            in_code = False
            for line in lines:
                if line.startswith("```"):
                    in_code = not in_code
                elif in_code:
                    json_lines.append(line)
            content = "\n".join(json_lines)
        
        # Parse JSON
        return json.loads(content)
    
    def get_feedback_summary(self) -> dict:
        """Get summary of all feedback collected."""
        return {
            "total_pages_analyzed": len(self.feedback_history),
            "average_confidence": sum(f.confidence for f in self.feedback_history) / len(self.feedback_history) if self.feedback_history else 0,
            "urls_visited": [f.url for f in self.feedback_history],
        }
