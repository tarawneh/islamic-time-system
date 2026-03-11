# Version 0.6.3
# Build 2026-03-10 14:58:29 UTC
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class VisibilityResult:
    criterion_name: str
    raw_value: Optional[float]
    category: str
    explanation: str
    metadata: Optional[Dict[str, Any]] = None
