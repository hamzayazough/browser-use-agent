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
        self._element_cache = {}  # Cache elements by index for clicking
        
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
        
        # Create new page
        page = await self.browser.new_page()
        
        # Navigate to initial URL if provided
        if url:
            print(f"🚀 Navigating to: {url}")
            try:
                await page.goto(url)
                await asyncio.sleep(4)  # Wait for page load and JS rendering
                current_url = await page.get_url()
                title = await page.get_title()
                
                # Check if page is empty or connection refused
                if title == "Empty Tab" or not title:
                    print(f"⚠️  Warning: Page appears empty (title: '{title}')")
                    print(f"   Make sure a web server is running at {url}")
                    print(f"   Try using a real website like https://example.com instead")
                else:
                    print(f"✓ Page loaded: {current_url} - Title: {title}")
            except Exception as e:
                print(f"❌ Failed to load page: {e}")
                print(f"   Make sure a web server is running at {url}")
                raise
        
        for step in range(max_steps):
            self.step_number = step + 1
            print(f"\n{'='*60}")
            print(f"Step {self.step_number}/{max_steps}")
            print('='*60)
            
            # 1. Capture current browser state
            print("📸 Capturing browser state...")
            state = await self._capture_state(page)
            
            # Debug output
            print(f"   Title: {state.title}")
            print(f"   DOM elements: {len(state.dom_elements)}")
            
            # Check if we're stuck on empty pages (but give the agent a chance to navigate)
            if state.title == "Empty Tab" and not state.dom_elements:
                print(f"⚠️  Warning: Page is empty with no interactive elements")
                print(f"   Current URL: {state.url}")
            
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
                
                # Generate UX report
                await self._generate_report(task)
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
            # Generate report even if max steps reached
            await self._generate_report(task)
    
    async def _generate_report(self, task: str):
        """Request and save UX analysis report from server."""
        try:
            print(f"\n📊 Generating UX Analysis Report...")
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.server_url}/report",
                    json={"task": task}
                )
                response.raise_for_status()
                
                result = response.json()
                if result.get("success"):
                    print(f"✓ {result.get('message')}")
                else:
                    print(f"⚠️  {result.get('message')}")
        except Exception as e:
            print(f"⚠️  Could not generate report: {e}")
            
    async def _capture_state(self, page) -> BrowserState:
        """Capture current browser state."""
        # Wait a moment for any dynamic content
        await asyncio.sleep(1.0)
        
        # Get current URL and title directly from the page
        current_url = await page.get_url()
        title = await page.get_title()
        
        # Clear element cache for new state
        self._element_cache = {}
        
        # Get interactive elements using CSS selectors (proper Actor API)
        dom_elements = []
        try:
            # Get all common interactive elements
            selectors = [
                'a',  # links
                'button',  # buttons
                'input',  # inputs
                'select',  # dropdowns
                '[onclick]',  # clickable elements
                '[role="button"]',  # ARIA buttons
                'textarea',  # text areas
            ]
            
            for selector in selectors:
                elements = await page.get_elements_by_css_selector(selector)
                for idx, element in enumerate(elements):
                    try:
                        # Get element info
                        info = await element.get_basic_info()
                        text = await element.evaluate('() => this.innerText || this.textContent || ""')
                        
                        # Create a unique index
                        element_index = len(dom_elements)
                        
                        # Cache the actual Element object for later use
                        self._element_cache[element_index] = element
                        
                        dom_elements.append({
                            "index": element_index,
                            "tag": info.get('nodeName', '').lower(),
                            "text": text[:100] if text else "",
                            "attributes": info.get('attributes', {}),
                            "xpath": "",  # Not available via Actor API
                            "_backend_node_id": info.get('backendNodeId'),  # Store for later use
                        })
                    except Exception as e:
                        # Skip elements that fail to process
                        continue
            
            print(f"   DEBUG - Extracted {len(dom_elements)} interactive elements")
            
        except Exception as e:
            print(f"   DEBUG - Error extracting elements: {e}")
        
        # Take screenshot
        screenshot_b64 = ""
        try:
            screenshot_b64 = await page.screenshot(format='png')
        except Exception as e:
            print(f"   DEBUG - Error taking screenshot: {e}")
        
        return BrowserState(
            url=current_url,
            title=title,
            html="",  # Not needed when we have DOM elements
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
            # Get element from cache
            if action.index not in self._element_cache:
                raise ValueError(f"Element at index {action.index} not found in cache")
            element = self._element_cache[action.index]
            await element.click()
            await asyncio.sleep(0.5)
            
        elif action.type == "input":
            if action.index is None or action.text is None:
                raise ValueError("Input action requires index and text")
            # Get element from cache
            if action.index not in self._element_cache:
                raise ValueError(f"Element at index {action.index} not found in cache")
            element = self._element_cache[action.index]
            await element.fill(action.text)
            await asyncio.sleep(0.3)
            
        elif action.type == "navigate":
            if action.url is None:
                raise ValueError("Navigate action requires url")
            await page.goto(action.url)
            await asyncio.sleep(3)  # Extra wait for JS frameworks like Next.js
            
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
