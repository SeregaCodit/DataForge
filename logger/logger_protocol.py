import logging
from typing import Protocol, runtime_checkable

@runtime_checkable
class LoggerProtocol(Protocol):
    logger: logging.Logger