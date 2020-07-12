from typing import TypeVar

from rx.core.typing import Disposable, Observable

import alleycat
from alleycat.reactive import observe, extend, ReactiveProperty, PreModifier, PostModifier

T = TypeVar("T")


class ReactiveObject(Disposable):

    @classmethod
    def extend(
            cls,
            name: str,
            pre_modifier: PreModifier = None,
            post_modifier: PostModifier = None) -> ReactiveProperty[T]:
        return extend(cls, name, pre_modifier, post_modifier)

    def observe(self, name: str) -> Observable:
        return observe(self, name)

    def dispose(self) -> None:
        alleycat.reactive.dispose(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.dispose()
