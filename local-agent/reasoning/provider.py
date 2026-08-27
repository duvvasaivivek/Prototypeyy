from abc import ABC, abstractmethod
from typing import Dict, Any, List
import json
from models.schemas import SanitizedContext, ActionPlan, Action

class ReasoningProvider(ABC):
    @abstractmethod
    def generate_plan(self, context: SanitizedContext, task: str) -> ActionPlan:
        pass

class MockReasoningProvider(ReasoningProvider):
    """
    A mock provider for testing without an API key.
    Always returns a static action plan based on the task.
    """
    def generate_plan(self, context: SanitizedContext, task: str) -> ActionPlan:
        print(f"[Mock LLM] Analyzing sanitized context for task: {task}")
        print(f"[Mock LLM] Received {len(context.elements)} sanitized elements")
        
        actions = []
        if "checkout" in task.lower() or "fill" in task.lower():
            # Try to find input fields in the sanitized context
            for el in context.elements:
                if el.input_type in ['text', 'email', 'tel', 'number'] or el.tag == 'input':
                    # Use the actual token that the privacy engine put in 'text' or 'placeholder'
                    token_to_use = el.text if el.text and "TOKEN" in el.text else f"<MOCK_TOKEN_{el.id}>"
                    actions.append(Action(
                        action="TYPE_SECURE",
                        element_id=el.id,
                        value=token_to_use,
                        reason=f"Fill {el.placeholder or el.attributes.get('name', 'input')}"
                    ))
                elif el.tag == 'button' or el.role == 'button' or (el.tag == 'input' and el.input_type == 'submit'):
                    actions.append(Action(
                        action="CLICK",
                        element_id=el.id,
                        reason="Submit the form"
                    ))
        
        if not actions:
            # Fallback action
            actions.append(Action(
                action="WAIT",
                reason="Nothing obvious to do, waiting for context to change."
            ))
            
        return ActionPlan(actions=actions)

import os
from google import genai
from google.genai import types

class GeminiReasoningProvider(ReasoningProvider):
    """
    A real LLM provider using Gemini to generate structured actions
    from the sanitized context.
    """
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def generate_plan(self, context: SanitizedContext, task: str) -> ActionPlan:
        if not self.client:
            print("[Gemini] ERROR: GEMINI_API_KEY not found in environment.")
            return ActionPlan(actions=[Action(action="WAIT", reason="API Key missing")])
            
        print(f"[Gemini] Asking Gemini 2.5 Flash to plan for: {task}")
        
        # Convert the sanitized Pydantic model to a clean JSON string for the prompt
        context_json = context.json()
        
        prompt = f"""
        You are a privacy-preserving browser automation agent.
        Your goal is to execute the user's task: "{task}"
        
        You have been provided with a SANITIZED UI Graph representing the current web page.
        Sensitive values (PII) have already been replaced with TOKENS (e.g. <EMAIL_TOKEN_123>).
        You must use these exact TOKENS when generating TYPE_SECURE actions.
        
        UI Graph:
        {context_json}
        
        Allowed Actions: CLICK, TYPE_SECURE, SCROLL, WAIT, NAVIGATE
        
        Return a structured JSON ActionPlan.
        """
        
        try:
            response = self.client.models.generate_content(
                model='gemini-3.6-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ActionPlan,
                ),
            )
            
            if response.text:
                plan = ActionPlan.parse_raw(response.text)
                return plan
            return ActionPlan(actions=[Action(action="WAIT", reason="Empty response from LLM")])
        except Exception as e:
            print(f"[Reasoning] Gemini API Error: {e}")
            print("[Reasoning] Falling back to safe mock plan due to API error.")
            return ActionPlan(actions=[Action(action="WAIT", reason=f"API Error: {str(e)[:50]}")])

# You can swap this with an OpenAI or Gemini implementation
# Automatically use Gemini if API key is present and valid, otherwise Mock
api_key = os.getenv("GEMINI_API_KEY")
if api_key and "your_api_key_here" not in api_key and "your_real_key_here" not in api_key:
    print("[Reasoning] Using Real Gemini Provider")
    active_provider: ReasoningProvider = GeminiReasoningProvider()
else:
    print("[Reasoning] Using Mock Provider (No valid API Key detected)")
    active_provider: ReasoningProvider = MockReasoningProvider()
