class AppError(Exception):
    status_code = 500
    code = "APP_ERROR"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

    def to_dict(self) -> dict:
        return {
            "error": self.message,
            "code": self.code,
        }