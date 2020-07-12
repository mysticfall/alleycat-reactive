from typing import TypeVar

from rx.core.typing import Disposable

from alleycat.reactive import extend, ReactiveProperty, PreModifier, PostModifier, dispose

T = TypeVar("T")


class ReactiveObject(Disposable):

    @classmethod
    def extend(
            cls,
            name: str,
            pre_modifier: PreModifier = None,
            post_modifier: PostModifier = None) -> ReactiveProperty[T]:
        return extend(cls, name, pre_modifier, post_modifier)

    def dispose(self) -> None:
        dispose(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.dispose()
