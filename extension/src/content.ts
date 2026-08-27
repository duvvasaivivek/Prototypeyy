// Content script for Privacy Gateway Agent
// Injected into all web pages

function extractDOM() {
  const elements: any[] = [];
  
  // Basic DOM extraction logic (Phase 1)
  // We'll target inputs, buttons, links, and common ARIA roles used by React apps like Instagram
  const query = 'input, button, a, select, textarea, [role="button"], [role="link"], [role="menuitem"], [role="listitem"], [tabindex="0"]';
  const nodes = document.querySelectorAll(query);
  
  nodes.forEach((node, index) => {
    const el = node as HTMLElement;
    const rect = el.getBoundingClientRect();
    
    // Only capture visible elements roughly
    if (rect.width === 0 || rect.height === 0 || el.style.visibility === 'hidden' || el.style.display === 'none') {
      return;
    }
    
    // Assign a unique temporary ID if it doesn't have one, just for tracking in our graph
    const elementId = el.id || `agent_el_${index}`;
    if (!el.id) {
        el.setAttribute('data-agent-id', elementId);
    }
    
    const elementInfo = {
      id: elementId,
      tag: el.tagName.toLowerCase(),
      role: el.getAttribute('role') || '',
      text: el.innerText || el.textContent || '',
      placeholder: el.getAttribute('placeholder') || '',
      input_type: el.getAttribute('type') || '',
      attributes: {
        name: el.getAttribute('name') || '',
        'aria-label': el.getAttribute('aria-label') || ''
      },
      is_visible: true,
      is_enabled: !(el as any).disabled
    };
    
    elements.push(elementInfo);
  });
  
  return {
    url: window.location.href,
    title: document.title,
    elements: elements
  };
}

// Allow popup or background to trigger extraction
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "EXTRACT_DOM") {
    const domState = extractDOM();
    sendResponse({ domState });
  } else if (request.action === "EXECUTE_PLAN") {
    // Actually execute the LLM's plan natively in the browser tab!
    console.log("Executing LLM Plan:", request.plan);
    const actions = request.plan.actions || [];
    
    actions.forEach((action: any, index: number) => {
      setTimeout(() => {
        const selector = action.element_id ? 
          `#${action.element_id}, [data-agent-id='${action.element_id}']` : null;
          
        let el: HTMLElement | null = null;
        if (selector) {
            el = document.querySelector(selector) as HTMLElement | null;
        }
        
        // Fallback: If it's an OCR element or missing, try to find it by TEXT injection
        if (!el && action.value && action.value.startsWith("TEXT:")) {
            const searchStr = action.value.replace("TEXT:", "").toLowerCase().trim();
            const allElements = document.querySelectorAll('div, span, a, button, p, h1, h2, h3, h4, h5, li');
            for (let i = 0; i < allElements.length; i++) {
                const node = allElements[i] as HTMLElement;
                // Only click leaf-ish nodes that contain the exact text
                if (node.children.length === 0 && node.textContent && node.textContent.toLowerCase().includes(searchStr)) {
                    el = node;
                    console.log("Found OCR element via TEXT fallback:", searchStr);
                    break;
                }
            }
        }
        
        if (!el) {
          console.warn(`Element not found for action ${action.action}:`, action.element_id);
          return;
        }

        console.log(`Executing ${action.action} on`, el);
        
        if (action.action === "CLICK") {
          el.dispatchEvent(new MouseEvent('mouseover', { bubbles: true, cancelable: true, view: window }));
          el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true, view: window }));
          el.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true, view: window }));
          el.click();
        } else if (action.action === "TYPE" || action.action === "TYPE_SECURE") {
          if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement) {
            el.value = action.value || "";
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
          }
        }
      }, index * 800); // 800ms delay between actions to simulate human speed
    });
    
    sendResponse({ success: true });
  }
});

// Optionally, we can observe mutations or just extract on load.
// For now, let's expose it to the window for debugging.
(window as any).extractPrivacyAgentDOM = extractDOM;
