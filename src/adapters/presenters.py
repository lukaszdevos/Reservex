"""Presenter functions: use-case response → HTTP-ready dict.

Layer: adapters
"""

from use_cases.response_objects import UseCaseResponse


def present_reserve_response(uc_response: UseCaseResponse) -> dict[str, object]:
    result: dict[str, object] = {
        "success": uc_response.success,
        "message": uc_response.message,
    }
    if uc_response.data is not None:
        result["data"] = uc_response.data
    return result
