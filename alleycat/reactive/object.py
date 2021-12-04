from typing import TypeVar

from returns.functions import identity
from rx import Observable, operators as ops
from rx.core.typing import Disposable

from alleycat.reactive import functions as rv

T = TypeVar("T")


class ReactiveObject(Disposable):
    disposed = rv.from_value(False)

    @property
    def on_dispose(self) -> Observable:
        return rv.observe(self, "disposed").pipe(ops.filter(identity), ops.map(lambda _: None))

    def observe(self, name: str) -> Observable:
        try:
            if self.disposed:
                raise RuntimeError("Cannot observe a disposed object.")
        except AttributeError:
            pass

        return rv.observe(self, name).pipe(ops.take_until(self.on_dispose))

    def dispose(self) -> None:
        if not self.disposed:
            self.disposed = True

            rv.dispose(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.disposed:
            self.dispose()
