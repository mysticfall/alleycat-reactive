from typing import TypeVar

from rx import Observable
from rx.core.typing import Disposable

from alleycat.reactive import functions as rv

T = TypeVar("T")


class ReactiveObject(Disposable):
    disposed = rv.from_value(False)

    def observe(self, name: str) -> Observable:
        if self.disposed:
            raise RuntimeError("Cannot observe a disposed object.")

        return rv.observe(self, name)

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
