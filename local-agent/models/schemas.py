from pydantic import BaseModel
from typing import List, Dict, Optional, Any

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
    # Bounding box: [x, y, width, height] for precise visual mapping
    bbox: Optional[List[int]] = None

class DOMState(BaseModel):
    url: str
    title: str
    elements: List[ElementInfo]
    # Optional base64 encoded image for OCR fallback
    image_data: Optional[str] = None

class SanitizedElement(ElementInfo):
    semantic_type: Optional[str] = None
    original_value: Optional[str] = None  # Internal use only

class SanitizedContext(BaseModel):
    url: str
    title: str
    elements: List[SanitizedElement]
    
class Action(BaseModel):
    action: str
    element_id: Optional[str] = None
    value: Optional[str] = None
    
class ActionPlan(BaseModel):
    actions: List[Action]
