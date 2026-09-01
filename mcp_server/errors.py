"""Best-effort error categorization for generation failures.

The Google Gen AI SDK does not (as of this writing) expose a single
structured exception hierarchy for every Vertex AI failure mode, so this is
a keyword-based classifier over the exception's string representation. It
is intentionally conservative: an unrecognized error becomes "unknown"
rather than being mis-categorized, and callers must still show the raw
message alongside the category.
"""
from __future__ import annotations

from dataclasses import dataclass


class ErrorCategory:
    AUTHENTICATION = "authentication"
    PERMISSION = "permission"
    QUOTA = "quota_exceeded"
    BILLING = "billing"
    CONTENT_FILTERED = "content_filtered"
    MODEL_UNAVAILABLE = "model_unavailable"
    TIMEOUT = "timeout"
    INVALID_REQUEST = "invalid_request"
    RATE_LIMITED = "rate_limited"
    UNKNOWN = "unknown"


_KEYWORD_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (ErrorCategory.AUTHENTICATION, ("application default credentials", "could not find default credentials", "unauthenticated", "401")),
    (ErrorCategory.PERMISSION, ("permission_denied", "permission denied", "iam", "403 forbidden", "403")),
    (ErrorCategory.QUOTA, ("quota", "resource_exhausted", "resource exhausted")),
    (ErrorCategory.RATE_LIMITED, ("rate limit", "429", "too many requests")),
    (ErrorCategory.BILLING, ("billing", "payment required", "402")),
    (ErrorCategory.CONTENT_FILTERED, ("safety", "filtered", "blocked", "responsible ai", "policy violation")),
    (ErrorCategory.MODEL_UNAVAILABLE, ("not found", "404", "not supported in this region", "unavailable", "503")),
    (ErrorCategory.TIMEOUT, ("timeout", "timed out", "deadline exceeded")),
    (ErrorCategory.INVALID_REQUEST, ("invalid_argument", "invalid argument", "400 bad request")),
)


@dataclass(frozen=True)
class ClassifiedError:
    category: str
    message: str


def classify_error(exc: BaseException) -> ClassifiedError:
    message = str(exc)

    # Exception type is a more reliable signal than message text when
    # available — e.g. GoogleVertexProvider's video-polling timeout raises a
    # plain TimeoutError with a Japanese message, which no English keyword
    # rule below would match.
    if isinstance(exc, TimeoutError):
        return ClassifiedError(category=ErrorCategory.TIMEOUT, message=message)

    text = message.lower()
    for category, keywords in _KEYWORD_RULES:
        if any(keyword in text for keyword in keywords):
            return ClassifiedError(category=category, message=message)
    return ClassifiedError(category=ErrorCategory.UNKNOWN, message=message)
