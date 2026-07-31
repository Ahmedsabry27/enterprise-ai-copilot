from abc import ABC, abstractmethod

from app.contracts.results import ToolResult
from app.contracts.tool_models import ToolRequest


class Tool(ABC):
    """
    Base contract for enterprise tools.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    async def execute(
        self,
        request: ToolRequest,
    ) -> ToolResult:
        ...