class APIError(Exception):
    status_code: int
