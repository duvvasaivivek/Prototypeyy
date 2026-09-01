from models.schemas import Action, ActionPlan
from typing import List, Dict

class LocalValidator:
    """
    The LocalValidator is the final layer of the Zero-Trust boundary.
    It intercepts the AI's ActionPlan before it is sent to the browser.
    """
    def validate_plan(self, plan: ActionPlan, vault: Dict[str, str]) -> ActionPlan:
        """
        1. Validates that the AI-generated actions are inherently safe.
        2. Resolves semantic tokens (e.g. <EMAIL_TOKEN_1>) back into real PII 
           using the local memory vault just-in-time before physical execution.
        """
        validated_actions = []
        for action in plan.actions:
            if action.action == "DELETE_ACCOUNT":
                print("[Validator] BLOCKING unconfirmed DELETE_ACCOUNT action")
                continue
                
            if action.action == "TYPE_SECURE":
                # Ensure the token exists in the vault
                if action.value in vault:
                    # Resolve token to actual value
                    action.value = vault[action.value]
                    print(f"[Validator] Resolved token {action.value[:4]}*** for secure typing")
                else:
                    print(f"[Validator] WARNING: Token {action.value} not found in vault. Proceeding with caution.")
            
            validated_actions.append(action)
            
        return ActionPlan(actions=validated_actions)

validator = LocalValidator()
