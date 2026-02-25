class NotFoundError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class ConflictError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class ServiceUnavailableError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)
