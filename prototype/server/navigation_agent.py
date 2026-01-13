"""Navigation Agent - Makes decisions on what actions to take."""

import json
from typing import Optional

from browser_use.llm.messages import SystemMessage, UserMessage

from shared.models import Action, BrowserState, UXFeedback


class NavigationAgent:
    """Agent responsible for navigation decisions."""
    
    def __init__(self, llm):
        """
        Initialize Navigation Agent.
        
        Args:
            llm: Language model instance (e.g., ChatBrowserUse, ChatOpenAI)
        """
        self.llm = llm
        self.history: list[dict] = []
        
        self.system_prompt = """You are a Navigation Agent AI specialized in web automation. Your role is to:

1. Receive the current browser state and UX feedback
2. Decide the best action to take to complete the user's task
3. Execute one action at a time, step by step

Available actions:
- click: Click an element by index
- input: Type text into an input field
- navigate: Go to a URL (MUST include full URL with http:// or https://)
- scroll: Scroll up or down
- wait: Wait for a specified time
- extract: Extract information from the page
- done: Complete the task

CRITICAL RULES:
- For navigate action: YOU MUST ALWAYS include the "url" field with complete URL (e.g., "https://www.google.com" or "http://localhost:3000")
- NEVER return a navigate action without the "url" field
- Use the UX Specialist's recommendations to guide your decisions
- Take one action at a time
- Be methodical and thorough
- If stuck, try alternative approaches
- Use 'done' action when task is completed

IMPORTANT: Every navigate action MUST have a "url" field!

Return your decision in JSON format:
{
    "type": "click|input|navigate|scroll|wait|extract|done",
    "index": element_index (for click/input),
    "text": "text to input" (for input),
    "url": "http://localhost:3000 or https://www.example.com" (REQUIRED for navigate - MUST be complete URL with protocol),
    "direction": "up|down" (for scroll),
    "amount": pixels (for scroll),
    "seconds": time (for wait),
    "query": "what to extract" (for extract),
    "reasoning": "why you chose this action"
}

EXAMPLE navigate actions:
{
    "type": "navigate",
    "url": "https://www.google.com",
    "reasoning": "Need to go to Google to search"
}
{
    "type": "navigate",
    "url": "http://localhost:3000",
    "reasoning": "Going to local development server"
}"""
    
    async def decide_action(
        self,
        state: BrowserState,
        task: str,
        ux_feedback: UXFeedback,
        step_number: int = 0
    ) -> Action:
        """
        Decide the next action to take.
        
        Args:
            state: Current browser state
            task: User's task
            ux_feedback: Feedback from UX Specialist
            step_number: Current step number
            
        Returns:
            Action to execute
        """
        # Build decision prompt
        prompt = self._build_decision_prompt(state, task, ux_feedback, step_number)
        
        # Get LLM decision with proper message format
        messages = [
            SystemMessage(content=self.system_prompt),
            UserMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        # Parse action from response
        try:
            action_data = self._parse_response(response.completion)
            action = Action(**action_data)
            
            # Validate navigate action has URL
            if action.type == "navigate" and not action.url:
                print(f"Warning: Navigate action missing URL. Response was: {response.completion}")
                # Default to Google as fallback
                action.url = "https://www.google.com"
                action.reasoning = f"Fallback: {action.reasoning or 'Navigate action was missing URL'}"
                
        except Exception as e:
            print(f"Warning: Failed to parse action: {e}")
            print(f"Response: {response.completion}")
            # Default to wait action if parsing fails
            action = Action(
                type="wait",
                seconds=1.0,
                reasoning="Failed to parse action, waiting to retry"
            )
        
        # Store in history
        self.history.append({
            "step": step_number,
            "url": state.url,
            "action": action.model_dump(),
            "ux_confidence": ux_feedback.confidence
        })
        
        return action
    
    def _build_decision_prompt(
        self,
        state: BrowserState,
        task: str,
        ux_feedback: UXFeedback,
        step_number: int
    ) -> str:
        """Build the decision prompt for the LLM."""
        
        # Summarize DOM elements
        dom_summary = self._summarize_dom(state.dom_elements)
        
        # Get action history
        action_history = ""
        if len(self.history) > 0:
            action_history = "\n\nPrevious actions:\n"
            recent = self.history[-5:]  # Last 5 actions
            for entry in recent:
                action_history += f"Step {entry['step']}: {entry['action']['type']}"
                if entry['action'].get('reasoning'):
                    action_history += f" - {entry['action']['reasoning']}"
                action_history += "\n"
        
        prompt = f"""Make a decision for the next action:

TASK: {task}
STEP: {step_number}
CURRENT URL: {state.url}
PAGE TITLE: {state.title}

UX SPECIALIST FEEDBACK:
Recommendation: {ux_feedback.recommendation}
Confidence: {ux_feedback.confidence}
Priority: {ux_feedback.priority}
Issues: {', '.join(ux_feedback.issues) if ux_feedback.issues else 'None'}
Positive aspects: {', '.join(ux_feedback.positive_aspects) if ux_feedback.positive_aspects else 'None'}

AVAILABLE ELEMENTS:
{dom_summary}

{action_history}

Based on the UX feedback and current state, decide the next action.
Return ONLY valid JSON matching this format:
{{
    "type": "click|input|navigate|scroll|wait|extract|done",
    "index": 0,
    "text": "text to type",
    "url": "https://example.com",
    "direction": "down",
    "amount": 500,
    "seconds": 1.0,
    "query": "what to extract",
    "reasoning": "why you chose this action"
}}

Only include fields relevant to the action type."""
        
        return prompt
    
    def _summarize_dom(self, dom_elements: list[dict], max_elements: int = 30) -> str:
        """Summarize DOM elements for the prompt."""
        if not dom_elements:
            return "No interactive elements found."
        
        summary_lines = []
        for i, elem in enumerate(dom_elements[:max_elements]):
            text = elem.get('text', '')[:60]
            tag = elem.get('tag', 'unknown')
            index = elem.get('index', i)
            
            # Include relevant attributes
            attrs = elem.get('attributes', {})
            attr_str = ""
            if attrs.get('placeholder'):
                attr_str += f" placeholder='{attrs['placeholder'][:30]}'"
            if attrs.get('aria-label'):
                attr_str += f" aria-label='{attrs['aria-label'][:30]}'"
            
            summary_lines.append(f"  [{index}] <{tag}>{attr_str} {text}")
        
        if len(dom_elements) > max_elements:
            summary_lines.append(f"  ... and {len(dom_elements) - max_elements} more elements")
        
        return "\n".join(summary_lines)
    
    def _parse_response(self, content: str) -> dict:
        """Parse LLM response to extract JSON action."""
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
    
    def get_history_summary(self) -> dict:
        """Get summary of navigation history."""
        return {
            "total_steps": len(self.history),
            "actions_taken": [entry['action']['type'] for entry in self.history],
            "urls_visited": list(set(entry['url'] for entry in self.history)),
        }
