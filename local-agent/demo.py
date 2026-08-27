import asyncio
import sys

# Fix Windows Event Loop issue with Playwright
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from dotenv import load_dotenv
load_dotenv()

import cv2
import numpy as np
import base64
from models.schemas import DOMState, ElementInfo
from privacy.engine import privacy_engine
from reasoning.provider import active_provider
from executor.validator import validator
from executor.playwright_executor import executor
from perception.ocr_engine import ocr_engine

def generate_mock_image() -> str:
    # Create a simple white image
    img = np.ones((200, 500, 3), dtype=np.uint8) * 255
    # Write some sensitive text on it
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, 'Card: 4532 1234 5678 9012', (10, 50), font, 1, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.putText(img, 'Email: secret@gmail.com', (10, 100), font, 1, (0, 0, 0), 2, cv2.LINE_AA)
    
    # Encode to base64
    _, buffer = cv2.imencode('.png', img)
    base64_str = base64.b64encode(buffer).decode('utf-8')
    return base64_str

async def run_demo():
    print("=== SIH 2026 Privacy-Preserving Agent Demo ===")
    
    # 1. Mock DOM State with Image Data
    mock_dom = DOMState(
        url="https://shop.example.com/checkout",
        title="Checkout Page",
        elements=[
            ElementInfo(id="name_field", tag="input", input_type="text", placeholder="Full Name", text="John Doe"),
            ElementInfo(id="submit_btn", tag="button", role="button", text="Pay Now")
        ],
        image_data=generate_mock_image()
    )
    
    print("\n[1] Raw DOM State Received from Extension:")
    for el in mock_dom.elements:
        print(f"  - {el.id}: {el.text or el.placeholder}")
    print("  - [Image Data Included]")
        
    # 1.5 OCR Perception
    if mock_dom.image_data:
        print("\n[1.5] Extracting non-DOM text via Lightweight OCR...")
        ocr_elements = ocr_engine.extract_elements_from_base64(mock_dom.image_data)
        mock_dom.elements.extend(ocr_elements)
        for el in ocr_elements:
            print(f"  - Extracted: {el.text}")
            
    # 2. Local Privacy Engine
    print("\n[2] Passing through Local Privacy Firewall...")
    sanitized_context, vault = privacy_engine.sanitize_dom(mock_dom)
    
    print(f"  -> Generated {len(vault)} Secure Tokens")
    for token, value in vault.items():
        print(f"     {token} => {value}")
        
    print("\n[3] Sanitized Context (This is what the Remote AI sees):")
    for el in sanitized_context.elements:
        print(f"  - {el.id}: {el.text or el.placeholder}")
        
    # 3. Remote AI Reasoning
    print("\n[4] Remote AI Generating Action Plan...")
    plan = active_provider.generate_plan(sanitized_context, task="Complete the checkout form")
    
    for action in plan.actions:
        print(f"  -> {action.action} on {action.element_id} (Value: {action.value})")
        
    # 4. Local Validator
    print("\n[5] Local Action Validator processing plan...")
    safe_plan = validator.validate_plan(plan, vault)
    
    # 5. Local Execution
    print("\n[6] Local Execution (Playwright):")
    
    # Create a mock HTML file for playwright to interact with
    html_content = """
    <html><body>
        <input data-agent-id="name_field" type="text" placeholder="Full Name" />
        <input data-agent-id="email_field" type="email" placeholder="Email Address" />
        <input data-agent-id="cc_field" type="text" placeholder="Credit Card" />
        <button data-agent-id="submit_btn">Pay Now</button>
    </body></html>
    """
    import os
    with open("test.html", "w") as f:
        f.write(html_content)
        
    await executor.start()
    test_file_url = f"file:///{os.path.abspath('test.html').replace(chr(92), '/')}"
    await executor.page.goto(test_file_url)
    
    await executor.execute_plan(safe_plan)
    await executor.stop()
    
    print("\n=== Demo Complete ===")
    
if __name__ == "__main__":
    asyncio.run(run_demo())
