"""Payment-context domain exceptions."""

from __future__ import annotations


class PaymentDeclinedError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Payment declined: {reason}")
