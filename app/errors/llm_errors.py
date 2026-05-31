from errors.app_error import AppError


class LLMConnectionError(AppError):
    status_code = 503
    code = "LLM_CONNECTION_ERROR"