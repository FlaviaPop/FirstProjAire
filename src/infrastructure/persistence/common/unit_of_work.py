"""Django implementation of the `UnitOfWork` port: one DB transaction per use case."""

from typing import Self

from django.db import transaction


class DjangoUnitOfWork:
    """Wraps `transaction.atomic()`; commits on clean exit, rolls back if an exception escapes."""

    def __enter__(self) -> Self:
        self._atomic = transaction.atomic()
        self._atomic.__enter__()
        return self

    def __exit__(self, *exc_info: object) -> None:
        # Never suppresses the exception: atomic rolls back, then it propagates to the caller.
        self._atomic.__exit__(*exc_info)  # type: ignore[arg-type]
