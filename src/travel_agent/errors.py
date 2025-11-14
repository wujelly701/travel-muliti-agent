"""Domain errors and warning utilities.
Ref: §5 错误与日志规范
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class DomainError(Exception):
    code: str
    message: str
    detail: Optional[str] = None

    def __str__(self) -> str:  # minimal representation
        return f"{self.code}: {self.message}{' - ' + self.detail if self.detail else ''}"  
