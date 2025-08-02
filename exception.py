from fastapi import HTTPException, status


class NotFoundException(HTTPException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_200_OK, detail=detail)


class BadRequestException(HTTPException):
    def __init__(self, detail: str = "Invalid input provided"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


# Unauthorized access
class UnauthorizedException(HTTPException):
    def __init__(self, detail: str = "Not authorized to perform this action"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


# Unauthorized access
class FailedToCreateEmployee(HTTPException):
    def __init__(self, detail: str = "Failed to create new employee"):
        super().__init__(status_code=status.HTTP_200_OK, detail=detail)


class DatabaseException(HTTPException):
    def __init__(self, detail: str = "failed to perform database operation"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
