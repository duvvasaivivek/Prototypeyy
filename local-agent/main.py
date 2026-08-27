from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

app = FastAPI(title="Privacy-Preserving Local Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ElementInfo(BaseModel):
    id: str
    tag: str
    role: Optional[str] = None
    text: Optional[str] = None
    placeholder: Optional[str] = None
    input_type: Optional[str] = None
    attributes: Dict[str, str] = {}
    is_visible: bool = True
    is_enabled: bool = True

class DOMState(BaseModel):
    url: str
    title: str
    elements: List[ElementInfo]

from reasoning.provider import active_provider
from executor.validator import validator
from executor.playwright_executor import executor
from perception.ocr_engine import ocr_engine
import asyncio

class TaskRequest(BaseModel):
    task: str

from privacy.engine import privacy_engine
from fastapi.responses import HTMLResponse

@app.on_event("startup")
async def startup_event():
    # We could start playwright here if we were driving a specific automated session
    # For a general extension backend, we might not start it immediately or we might just use mock execution for the demo
    print("API Started")

import os

@app.get("/")
async def root():
    """
    Returns the dynamic React Dashboard.
    """
    dashboard_path = os.path.join(os.path.dirname(__file__), "templates", "dashboard.html")
    if os.path.exists(dashboard_path):
        with open(dashboard_path, "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    return HTMLResponse(content="Dashboard not found", status_code=404)

@app.get("/api/v1/metrics")
async def get_metrics():
    """
    Returns real-time privacy metrics for the dashboard.
    """
    # Count tokens by semantic type
    token_types = {}
    tokens = []
    
    for token, original_value in privacy_engine.secure_vault.items():
        # Example token: <EMAIL_ADDRESS_TOKEN_1234>
        parts = token.strip("<>").split("_TOKEN_")
        if len(parts) == 2:
            t_type = parts[0]
            token_types[t_type] = token_types.get(t_type, 0) + 1
            tokens.append({
                "token": token,
                "original_value": original_value
            })
            
    # Format for Recharts
    chart_data = [{"name": k, "count": v} for k, v in token_types.items()]
    
    return {
        "status": "online",
        "total_protected": len(privacy_engine.secure_vault),
        "chart_data": chart_data,
        "recent_tokens": tokens[-10:] # Last 10 tokens
    }

@app.post("/api/v1/perceive")
async def perceive_dom(dom_state: DOMState):
    """
    Receives the raw DOM state from the extension.
    Sanitizes it and returns the sanitized context.
    """
    print(f"Received DOM from {dom_state.url} with {len(dom_state.elements)} elements")
    
    # 0. OCR Fallback
    image_data = getattr(dom_state, 'image_data', None)
    if image_data:
        ocr_elements = ocr_engine.extract_elements_from_base64(image_data)
        dom_state.elements.extend(ocr_elements)
        print(f"Merged {len(ocr_elements)} OCR elements into DOM state.")
        
    sanitized_context, vault = privacy_engine.sanitize_dom(dom_state)
    
    # In a real system, we might persist the vault to a secure local DB
    # For now, we'll just log how many tokens we generated
    print(f"Protected {len(vault)} sensitive items.")
    
    return {
        "status": "success", 
        "elements_processed": len(dom_state.elements),
        "sanitized_elements": len(sanitized_context.elements),
        "tokens_generated": len(vault)
    }

@app.post("/api/v1/perceive_and_act")
async def perceive_and_act(dom_state: DOMState, task: str = "Fill the checkout form"):
    """
    Full pipeline: Perceive -> Sanitize -> Reason -> Validate -> Execute
    """
    print(f"[Pipeline] Starting for task: {task}")
    
    # 0. OCR Perception
    image_data = getattr(dom_state, 'image_data', None)
    if image_data:
        ocr_elements = ocr_engine.extract_elements_from_base64(image_data)
        dom_state.elements.extend(ocr_elements)
        print(f"[Pipeline] Added {len(ocr_elements)} OCR elements")
    
    # 1. Sanitize
    sanitized_context, vault = privacy_engine.sanitize_dom(dom_state)
    print(f"[Pipeline] Sanitized {len(sanitized_context.elements)} elements, protected {len(vault)} sensitive values")
    
    # 2. Reason (Remote AI)
    plan = active_provider.generate_plan(sanitized_context, task)
    print(f"[Pipeline] LLM proposed {len(plan.actions)} actions")
    
    # 3. Validate & Resolve Tokens
    safe_plan = validator.validate_plan(plan, vault)
    
    # 3.5 Inject text fallback for OCR elements so the browser can find them
    for action in safe_plan.actions:
        if action.element_id and str(action.element_id).startswith("ocr_el_"):
            # Find the OCR element in the DOM state
            for el in dom_state.elements:
                if el.id == action.element_id:
                    action.value = f"TEXT:{el.text}"
                    break
    
    print(f"[Pipeline] Validation complete. {len(safe_plan.actions)} safe actions ready")
    
    # 4. Execute
    # In a real async environment we might background this or return the plan to the extension
    await executor.execute_plan(safe_plan)
    
    return {
        "status": "success",
        "actions_executed": len(safe_plan.actions),
        "plan": safe_plan.dict()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
