"""Command-line interface for running the local browser client."""

import argparse
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from local.client import LocalBrowserClient


async def main():
    parser = argparse.ArgumentParser(
        description="Run browser automation task with cloud agents"
    )
    parser.add_argument(
        "--url",
        required=True,
        help="Starting URL (e.g., http://localhost:3000 or https://example.com)",
    )
    parser.add_argument(
        "--task",
        required=True,
        help='Task description (e.g., "search for the cheapest product")',
    )
    parser.add_argument(
        "--server",
        default="http://localhost:8000",
        help="Cloud server URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=50,
        help="Maximum number of steps (default: 50)",
    )
    
    args = parser.parse_args()
    
    # Initialize client
    client = LocalBrowserClient(
        server_url=args.server,
        headless=args.headless,
    )
    
    try:
        # Start browser
        await client.start()
        
        # Run task
        await client.run_task(
            url=args.url,
            task=args.task,
            max_steps=args.max_steps,
        )
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
