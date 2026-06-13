import logging

def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger with the specified name.

    This provides a consistent way to get logger instances throughout the application.
    The actual logging configuration is done in main.py when the application starts.

    Args:
        name: Usually the module name (use __name__)

    Returns:
        A configured logger instance
    """
    return logging.getLogger(name)
