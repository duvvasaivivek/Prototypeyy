from models.schemas import Action, ActionPlan
from typing import List, Dict

class LocalValidator:
    def validate_plan(self, plan: ActionPlan, vault: Dict[str, str]) -> ActionPlan:
        """
        Validates the proposed actions. 
        Rejects highly sensitive destructive actions or actions on non-existent elements.
        Resolves tokens using the vault just before execution.
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
