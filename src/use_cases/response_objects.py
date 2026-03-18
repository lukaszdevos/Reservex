"""Use-case response DTOs.

Layer: use_cases
Imports: stdlib only
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class UseCaseResponse:
    success: bool
    message: str
    data: dict[str, object] | None = field(default=None)
