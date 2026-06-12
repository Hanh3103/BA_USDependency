from errors.app_error import AppError
"""Custom errors used by the prompt evaluation tool.

These errors keep the evaluation flow readable by separating file loading,
model response parsing, and schema validation failures into distinct cases.
"""


class PromptEvaluationError(AppError):
    """Base error for failures raised while evaluating prompt files."""

    code = "PROMPT_EVALUATION_ERROR"


class PromptJSONParseError(PromptEvaluationError):
    """Raised when the model output cannot be parsed as JSON."""

    code = "PROMPT_JSON_PARSE_ERROR"


class PromptSchemaValidationError(PromptEvaluationError):
    """Raised when parsed JSON does not match the expected schema."""

    code = "PROMPT_SCHEMA_VALIDATION_ERROR"


class PromptLoadError(PromptEvaluationError):
    """Raised when a prompt file cannot be read from disk."""

    code = "PROMPT_LOAD_ERROR"