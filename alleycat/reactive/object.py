from typing import TypeVar, Optional

from rx import Observable
from rx.core.typing import Disposable

from alleycat.reactive import observe, extend, ReactiveProperty, PreModifier, PostModifier, dispose

T = TypeVar("T")


class ReactiveObject(Disposable):

    @classmethod
    def extend(
            cls,
            name: str,
            pre_modifier: Optional[PreModifier] = None,
            post_modifier: Optional[PostModifier] = None) -> ReactiveProperty[T]:
        return extend(cls, name, pre_modifier, post_modifier)

    def observe(self, name: str) -> Observable:
        return observe(self, name)

    def dispose(self) -> None:
        dispose(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.dispose()
