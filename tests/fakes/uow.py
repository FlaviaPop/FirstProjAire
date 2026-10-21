class FakeUnitOfWork:
    """`UnitOfWork` fake that counts enters, commits and rollbacks; never swallows errors."""

    def __init__(self) -> None:
        self.entered = self.committed = self.rolled_back = 0

    def __enter__(self):
        self.entered += 1
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self.committed += 1
        else:
            self.rolled_back += 1
        return False
