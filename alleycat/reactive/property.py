from __future__ import annotations

from typing import TypeVar, Generic, Callable, Optional, Any, cast

import rx
from returns.functions import identity, compose
from returns.maybe import Maybe, Nothing
from rx import Observable
from rx.subject import BehaviorSubject

from . import ReactiveValue

T = TypeVar("T")


class ReactiveProperty(Generic[T], ReactiveValue[T]):

    def __init__(
            self,
            init_value: Maybe[T] = Nothing,
            read_only=False,
            post_modifier: Callable[[Observable], Observable] = identity) -> None:

        super().__init__(read_only=read_only)

        self.init_value = init_value
        self.post_modifier = post_modifier

    def bind(self, modifier: Callable[[Observable], Observable]) -> ReactiveProperty:
        if modifier is None:
            raise ValueError("Argument 'modifier' is required.")
        return ReactiveProperty(self.init_value, self.read_only, compose(self.post_modifier, modifier))

    class PropertyData(ReactiveValue.Data[T]):

        def __init__(self, name: str, init_value: Maybe[T], post_modifier: Callable[[Observable], Observable]):
            assert name is not None
            assert init_value is not None

            self._property: Optional[BehaviorSubject] = None

            obs: Observable

            if init_value != Nothing:
                self._property = BehaviorSubject(init_value.unwrap())

                obs = self._property
            else:
                obs = rx.empty()

            super().__init__(name, obs, post_modifier)

        # Must override to appease Mypy... I hate Python.
        @property
        def value(self) -> T:
            return super().value

        @value.setter
        def value(self, value: T):
            self._check_disposed()

            if self.initialized:
                assert self._property is not None

                self._property.on_next(value)
            else:
                self._property = BehaviorSubject(value)

                self.observable = self._property

        def dispose(self) -> None:
            assert self._property is not None

            self._check_disposed()
            self._property.on_completed()

            super().dispose()

    def _create_data(self, obj: Any) -> PropertyData:
        assert obj is not None
        assert self.name is not None

        return self.PropertyData(self.name, self.init_value, self.post_modifier)

    def _get_data(self, obj: Any) -> PropertyData:
        assert obj is not None

        return cast(ReactiveProperty.PropertyData, super()._get_data(obj))

    def _set_value(self, obj: Any, data: ReactiveValue.Data, value: Any) -> None:
        assert obj is not None
        assert isinstance(data, ReactiveProperty.PropertyData)

        data.value = value
