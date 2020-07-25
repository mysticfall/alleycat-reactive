from collections import deque
from functools import reduce, partial
from typing import TypeVar, Generic, Callable, Optional, Deque, Any, cast

from returns.maybe import Maybe, Nothing
from rx import Observable
from rx import operators as ops
from rx.subject import BehaviorSubject

from . import PreModifier, PostModifier, ReactiveValue

T = TypeVar("T")


class ReactiveProperty(Generic[T], ReactiveValue[T]):
    pre_modifiers: Deque[PreModifier]

    post_modifiers: Deque[PostModifier]

    def __init__(self,
                 init_value: Maybe[T] = Nothing,
                 read_only=False,
                 pre_modifiers: Optional[Deque[PreModifier]] = None,
                 post_modifiers: Optional[Deque[PostModifier]] = None) -> None:

        super().__init__()

        self.init_value = init_value
        self.read_only = read_only

        self.pre_modifiers = deque() if pre_modifiers is None else pre_modifiers
        self.post_modifiers = deque() if post_modifiers is None else post_modifiers

    class PropertyData(ReactiveValue.Data[T]):

        def __init__(self,
                     name: str,
                     init_value: Maybe[T],
                     pre_modifier: Callable[[T], T],
                     post_modifier: Callable[[Observable], Observable]):
            value = init_value.map(pre_modifier)

            self._subject = BehaviorSubject(value.value_or(None))
            self._modifier = pre_modifier

            obs = post_modifier(self._subject)

            if init_value == Nothing:
                obs = obs.pipe(ops.skip(1))

            super().__init__(name, obs, value)

        # Must override to appease Mypy... I hate Python.
        @property
        def value(self) -> T:
            return super().value

        @value.setter
        def value(self, value: T):
            self._check_disposed()
            self._subject.on_next(self._modifier(value))

        def dispose(self) -> None:
            self._check_disposed()
            self._subject.on_completed()

            super().dispose()

    def _create_data(self, obj: Any) -> PropertyData:
        assert self.name is not None

        def compose(f, g):
            return lambda x, y: g(x, f(x, y))

        def identity(_, x):
            return x

        # FIXME Annotating the following method will crash PyCharm's type checker (See PY-43455).
        # The signature should be 'def build_chain(chain: Deque[Callable[[Any, U], U]]) -> Callable[[U], U]'.
        def build_chain(chain):
            return partial(reduce(compose, chain, identity), obj)

        pre_chain = build_chain(self.pre_modifiers)  # type: ignore
        post_chain = build_chain(self.post_modifiers)  # type: ignore

        # noinspection PyTypeChecker
        return self.PropertyData(self.name, self.init_value, pre_chain, post_chain)

    def _get_data(self, obj: Any) -> PropertyData:
        return cast(ReactiveProperty.PropertyData, super()._get_data(obj))

    def __set__(self, obj: Any, value: T) -> None:
        if obj is None:
            raise AttributeError("Cannot modify property of a None object.")

        if self.read_only and self.init_value is not None:
            raise AttributeError("Cannot modify a read-only property.")

        self._get_data(obj).value = value
