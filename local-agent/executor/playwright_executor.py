from playwright.async_api import async_playwright, Page
from models.schemas import ActionPlan
import asyncio

class PlaywrightExecutor:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        
    async def start(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        print("[Executor] Started Playwright Browser")
        
    async def stop(self):
        if self.browser:
            await self.browser.close()
            
    async def execute_plan(self, plan: ActionPlan):
        if not self.page:
            print("[Executor] Browser not started. Mocking execution.")
            for action in plan.actions:
                print(f"[Executor Mock] Executing {action.action} on {action.element_id} with value {action.value}")
            return
            
        for action in plan.actions:
            print(f"[Executor] Executing {action.action} on {action.element_id}")
            try:
                # We expect elements to have a 'data-agent-id' attribute which we injected during perception
                selector = f"[data-agent-id='{action.element_id}']"
                
                if action.action == "CLICK":
                    await self.page.click(selector, timeout=5000)
                elif action.action in ["TYPE", "TYPE_SECURE"]:
                    await self.page.fill(selector, action.value, timeout=5000)
                elif action.action == "WAIT":
                    await self.page.wait_for_timeout(2000)
                
                # Small wait between actions to make it observable
                await self.page.wait_for_timeout(500)
            except Exception as e:
                print(f"[Executor] Failed to execute {action.action} on {action.element_id}: {e}")

executor = PlaywrightExecutor()
