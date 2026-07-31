from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ToolRequest:
    parameters: dict[str, Any] = field(default_factory=dict)