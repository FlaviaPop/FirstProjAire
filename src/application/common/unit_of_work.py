"""Transaction boundary port: each use case runs inside exactly one unit of work."""

from typing import Protocol, Self


class UnitOfWork(Protocol):
    """Context manager that commits on clean exit and rolls back when an exception escapes."""

    def __enter__(self) -> Self: ...

    def __exit__(self, *exc_info: object) -> bool | None: ...
