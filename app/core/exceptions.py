# Raised when a requested resource does not exist (HTTP 404).
class NotFoundError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


# Raised when a request conflicts with current state (HTTP 409).
# Examples: duplicate service name, invalid status transition,
# deleting a service that still has active incidents.
class ConflictError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


# Raised when a required external dependency is unavailable (HTTP 503).
# Currently used to surface SQLAlchemy connection failures.
class ServiceUnavailableError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)
