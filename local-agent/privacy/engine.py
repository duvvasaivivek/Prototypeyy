from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from typing import Dict, Any, Tuple
import re
import uuid

# Initialize Presidio
analyzer = AnalyzerEngine()

# Hackathon: Presidio ignores fake credit cards because they fail the Luhn algorithm check.
# We add a dumb regex recognizer to force it to detect our fake test data!
cc_pattern = Pattern(name="fake_cc", regex=r"\b(?:\d{4}[-\s]?){3}\d{4}\b", score=0.9)
cc_recognizer = PatternRecognizer(supported_entity="CREDIT_CARD", patterns=[cc_pattern])
analyzer.registry.add_recognizer(cc_recognizer)

email_pattern = Pattern(name="fake_email", regex=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", score=0.9)
email_recognizer = PatternRecognizer(supported_entity="EMAIL_ADDRESS", patterns=[email_pattern])
analyzer.registry.add_recognizer(email_recognizer)

# --- SIH 2026 KILLER FEATURES: Indian PII & API Keys ---
# Aadhaar Card: 12 digits, often formatted as 4-4-4
aadhaar_pattern = Pattern(name="aadhaar", regex=r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", score=0.95)
aadhaar_recognizer = PatternRecognizer(supported_entity="AADHAAR_NUMBER", patterns=[aadhaar_pattern])
analyzer.registry.add_recognizer(aadhaar_recognizer)

# PAN Card: 5 letters, 4 numbers, 1 letter (e.g. ABCDE1234F)
pan_pattern = Pattern(name="pan_card", regex=r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b", score=0.95)
pan_recognizer = PatternRecognizer(supported_entity="PAN_CARD", patterns=[pan_pattern])
analyzer.registry.add_recognizer(pan_recognizer)

# API Keys / Crypto Wallets (Generic high-entropy alphanumeric strings > 30 chars)
api_key_pattern = Pattern(name="api_key", regex=r"\b[A-Za-z0-9-_]{32,}\b", score=0.8)
api_key_recognizer = PatternRecognizer(supported_entity="API_KEY", patterns=[api_key_pattern])
analyzer.registry.add_recognizer(api_key_recognizer)

anonymizer = AnonymizerEngine()

class PrivacyEngine:
    def __init__(self):
        # In-memory mapping of tokens to actual values
        self.secure_vault: Dict[str, str] = {}
        
    def add_to_vault(self, original_text: str, entity_type: str) -> str:
        # Create a unique token like <EMAIL_TOKEN_1234>
        token = f"<{entity_type}_TOKEN_{uuid.uuid4().hex[:8].upper()}>"
        self.secure_vault[token] = original_text
        return token

    def sanitize_text(self, text: str) -> str:
        if not text:
            return text
            
        # 1. Run Presidio NLP analyzer with high confidence threshold
        # Removed "LOCATION" to stop flagging country/language dropdowns as PII
        results = analyzer.analyze(
            text=text, 
            entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "PERSON", "AADHAAR_NUMBER", "PAN_CARD", "API_KEY"], 
            language='en',
            score_threshold=0.85  # Only flag if it's VERY confident it's PII
        )
        
        if not results:
            return text
            
        # 2. Setup anonymization operators using our vault
        operators = {}
        for entity_type in ["EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "PERSON", "LOCATION"]:
            # We want to replace each with a custom vault token.
            # Presidio's default replace just puts <EMAIL_ADDRESS>. 
            # We will handle the tokenization manually for tighter integration.
            pass
            
        # Manual replacement to capture tokens
        # Sort results by start index in reverse to not mess up offsets
        sanitized_text = text
        for result in sorted(results, key=lambda x: x.start, reverse=True):
            original_value = text[result.start:result.end]
            token = self.add_to_vault(original_value, result.entity_type)
            sanitized_text = sanitized_text[:result.start] + token + sanitized_text[result.end:]
            
        return sanitized_text

    def sanitize_dom(self, dom_state: Any) -> Tuple[Any, Dict[str, str]]:
        """
        Takes a DOMState, returns a SanitizedContext and the token vault.
        """
        from models.schemas import SanitizedContext, SanitizedElement
        
        sanitized_elements = []
        for el in dom_state.elements:
            # We need to sanitize text and placeholders
            sanitized_text = self.sanitize_text(el.text) if el.text else None
            sanitized_placeholder = self.sanitize_text(el.placeholder) if el.placeholder else None
            
            sanitized_el = SanitizedElement(
                id=el.id,
                tag=el.tag,
                role=el.role,
                text=sanitized_text,
                placeholder=sanitized_placeholder,
                input_type=el.input_type,
                attributes=el.attributes,
                is_visible=el.is_visible,
                is_enabled=el.is_enabled,
                original_value=el.text if el.text != sanitized_text else None
            )
            sanitized_elements.append(sanitized_el)
            
        sanitized_context = SanitizedContext(
            url=dom_state.url, # In a full system, you might sanitize query params
            title=dom_state.title,
            elements=sanitized_elements
        )
        
        return sanitized_context, self.secure_vault

# Singleton instance
privacy_engine = PrivacyEngine()
