from collections import deque
from functools import reduce, partial
from typing import TypeVar, Generic, Callable, Optional, Deque, Any, cast

import rx
from returns.maybe import Maybe, Nothing
from rx import Observable
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

        super().__init__(read_only=read_only)

        self.init_value = init_value

        self.pre_modifiers = deque() if pre_modifiers is None else pre_modifiers
        self.post_modifiers = deque() if post_modifiers is None else post_modifiers

    class PropertyData(ReactiveValue.Data[T]):

        def __init__(self,
                     name: str,
                     init_value: Maybe[T],
                     pre_modifier: Callable[[T], T],
                     post_modifier: Callable[[Observable], Observable]):
            assert name is not None
            assert init_value is not None
            assert pre_modifier is not None
            assert post_modifier is not None

            self._property: Optional[BehaviorSubject] = None

            self._pre_modifier = pre_modifier
            self._post_modifier = post_modifier

            init_value.map(pre_modifier).map(lambda v: BehaviorSubject(v))

            obs: Observable

            if init_value != Nothing:
                self._property = BehaviorSubject(self._pre_modifier(init_value.unwrap()))

                obs = self._post_modifier(self._property)
            else:
                obs = rx.empty()

            super().__init__(name, obs)

        # Must override to appease Mypy... I hate Python.
        @property
        def value(self) -> T:
            return super().value

        @value.setter
        def value(self, value: T):
            self._check_disposed()

            if self.initialized:
                assert self._property is not None

                self._property.on_next(self._pre_modifier(value))
            else:
                self._property = BehaviorSubject(self._pre_modifier(value))

                self.observable = self._post_modifier(self._property)

        def dispose(self) -> None:
            assert self._property is not None

            self._check_disposed()
            self._property.on_completed()

            super().dispose()

    def _create_data(self, obj: Any) -> PropertyData:
        assert obj is not None
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
        assert obj is not None

        return cast(ReactiveProperty.PropertyData, super()._get_data(obj))

    def _set_value(self, obj: Any, data: ReactiveValue.Data, value: Any) -> None:
        assert obj is not None
        assert isinstance(data, ReactiveProperty.PropertyData)

        data.value = value
