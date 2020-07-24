from typing import TypeVar

from rx import Observable
from rx.core.typing import Disposable

from alleycat.reactive import observe, dispose, from_value

T = TypeVar("T")


class ReactiveObject(Disposable):
    disposed = from_value(False)

    def observe(self, name: str) -> Observable:
        return observe(self, name)

    def dispose(self) -> None:
        self.disposed = True

        dispose(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.dispose()
