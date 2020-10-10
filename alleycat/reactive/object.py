from typing import TypeVar

from returns.functions import identity
from rx import Observable
from rx import operators as ops
from rx.core.typing import Disposable

from alleycat.reactive import functions as rv

T = TypeVar("T")


class ReactiveObject(Disposable):
    disposed = rv.from_value(False)

    def __init__(self):
        super().__init__()

        self.on_dispose = rv.observe(self, "disposed").pipe(ops.filter(identity), ops.map(lambda _: None))

    def observe(self, name: str) -> Observable:
        if self.disposed:
            raise RuntimeError("Cannot observe a disposed object.")

        return rv.observe(self, name).pipe(ops.take_until(self.on_dispose))

    def dispose(self) -> None:
        if self.disposed:
            raise RuntimeError("The object has already been disposed.")

        self.disposed = True

        rv.dispose(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.disposed:
            self.dispose()
