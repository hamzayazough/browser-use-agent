"""Local browser client that executes actions from the cloud server."""

import asyncio
import base64
import sys
from pathlib import Path
from typing import Optional

import httpx
from browser_use import Browser

# Add parent directory to path to import shared models
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.models import Action, BrowserState, NavigationRequest, NavigationResponse


class LocalBrowserClient:
    """Client that controls local browser and communicates with cloud server."""
    
    def __init__(self, server_url: str, headless: bool = False):
        self.server_url = server_url.rstrip('/')
        self.browser: Optional[Browser] = None
        self.headless = headless
        self.step_number = 0
        
    async def start(self):
        """Initialize the browser."""
        self.browser = Browser(
            headless=self.headless,
            window_size={'width': 1280, 'height': 720},
            highlight_elements=True,
        )
        await self.browser.start()
        print(f"✓ Browser started (headless={self.headless})")
        
    async def stop(self):
        """Close the browser."""
        if self.browser:
            await self.browser.stop()
            print("✓ Browser stopped")
            
    async def run_task(self, url: str, task: str, max_steps: int = 50):
        """
        Run a task by communicating with the cloud server.
        
        Args:
            url: Starting URL
            task: Task description
            max_steps: Maximum number of steps to execute
        """
        if not self.browser:
            raise RuntimeError("Browser not started. Call start() first.")
            
        print(f"\n🎯 Task: {task}")
        print(f"🌐 Starting URL: {url}\n")
        
        # Navigate to initial URL
        page = await self.browser.new_page(url)
        await asyncio.sleep(1)  # Wait for page load
        
        for step in range(max_steps):
            self.step_number = step + 1
            print(f"\n{'='*60}")
            print(f"Step {self.step_number}/{max_steps}")
            print('='*60)
            
            # 1. Capture current browser state
            print("📸 Capturing browser state...")
            state = await self._capture_state(page)
            
            # 2. Send to server and get action
            print("🚀 Sending to server...")
            try:
                response = await self._request_action(task, state)
            except Exception as e:
                print(f"❌ Error communicating with server: {e}")
                break
                
            # 3. Display UX feedback
            print(f"\n💡 UX Feedback:")
            print(f"   Recommendation: {response.ux_feedback.recommendation}")
            print(f"   Confidence: {response.ux_feedback.confidence:.2f}")
            if response.ux_feedback.issues:
                print(f"   Issues: {', '.join(response.ux_feedback.issues)}")
                
            # 4. Display action
            print(f"\n🎬 Action: {response.action.type}")
            if response.action.reasoning:
                print(f"   Reasoning: {response.action.reasoning}")
                
            # 5. Check if done
            if response.action.type == "done":
                print(f"\n✅ Task completed!")
                if response.message:
                    print(f"   {response.message}")
                break
                
            # 6. Execute action
            try:
                await self._execute_action(page, response.action)
                print("✓ Action executed")
            except Exception as e:
                print(f"❌ Error executing action: {e}")
                continue
                
            # Wait between actions
            await asyncio.sleep(0.5)
        else:
            print(f"\n⚠️  Reached maximum steps ({max_steps})")
            
    async def _capture_state(self, page) -> BrowserState:
        """Capture current browser state."""
        # Get DOM elements using Browser-Use's browser state API
        state = await self.browser.get_browser_state_summary()
        
        # Convert selector map to simple element list
        dom_elements = []
        if state.dom_state and state.dom_state.selector_map:
            # Handle both dict and object types
            selector_map = state.dom_state.selector_map
            if isinstance(selector_map, dict):
                items = selector_map.items()
            else:
                items = selector_map.selector_map.items()
            
            for index, element in items:
                # Handle both dict and object element types
                if isinstance(element, dict):
                    dom_elements.append({
                        "index": index,
                        "tag": element.get("tag_name", ""),
                        "text": element.get("text", "")[:100],
                        "attributes": element.get("attributes", {}),
                        "xpath": element.get("xpath", ""),
                    })
                else:
                    # EnhancedDOMTreeNode object
                    text = ""
                    if hasattr(element, 'get_all_children_text'):
                        text = element.get_all_children_text()[:100]
                    elif hasattr(element, 'node_value'):
                        text = element.node_value[:100] if element.node_value else ""
                    
                    dom_elements.append({
                        "index": index,
                        "tag": element.tag_name if hasattr(element, 'tag_name') else element.node_name.lower(),
                        "text": text,
                        "attributes": element.attributes or {},
                        "xpath": element.xpath if hasattr(element, 'xpath') else "",
                    })
        
        # Take screenshot (already available in state)
        screenshot_b64 = state.screenshot or ""
        
        return BrowserState(
            url=state.url,
            title=state.title or "",
            html="",  # We don't need full HTML, using DOM elements instead
            screenshot=screenshot_b64,
            dom_elements=dom_elements,
            viewport={"width": 1280, "height": 720},
        )
        
    async def _request_action(self, task: str, state: BrowserState) -> NavigationResponse:
        """Send state to server and get next action."""
        request = NavigationRequest(
            task=task,
            state=state,
            step_number=self.step_number,
        )
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.server_url}/navigate",
                json=request.model_dump(),
            )
            response.raise_for_status()
            
        return NavigationResponse(**response.json())
        
    async def _execute_action(self, page, action: Action):
        """Execute action on the browser."""
        if action.type == "click":
            if action.index is None:
                raise ValueError("Click action requires index")
            element = await page.get_element_by_index(action.index)
            await element.click()
            await asyncio.sleep(0.5)
            
        elif action.type == "input":
            if action.index is None or action.text is None:
                raise ValueError("Input action requires index and text")
            element = await page.get_element_by_index(action.index)
            await element.fill(action.text)
            await asyncio.sleep(0.3)
            
        elif action.type == "navigate":
            if action.url is None:
                raise ValueError("Navigate action requires url")
            await page.goto(action.url)
            await asyncio.sleep(1)
            
        elif action.type == "scroll":
            direction = action.direction or "down"
            amount = action.amount or 500
            if direction == "down":
                await page.evaluate(f"window.scrollBy(0, {amount})")
            else:
                await page.evaluate(f"window.scrollBy(0, -{amount})")
            await asyncio.sleep(0.3)
            
        elif action.type == "wait":
            seconds = action.seconds or 1.0
            await asyncio.sleep(seconds)
            
        elif action.type == "extract":
            # Extract action doesn't modify page, just note it
            print(f"   Extracting: {action.query}")
            
        elif action.type == "done":
            pass  # Handled in run_task
            
        else:
            raise ValueError(f"Unknown action type: {action.type}")
