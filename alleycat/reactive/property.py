from __future__ import annotations

from typing import TypeVar, Generic, Callable, Optional, Any, cast

import rx
from returns.functions import identity
from returns.maybe import Maybe, Nothing
from returns.pipeline import pipe as pipe_
from rx import Observable
from rx.subject import BehaviorSubject

from . import ReactiveValue, ReactiveView

T = TypeVar("T")


class ReactiveProperty(Generic[T], ReactiveValue[T]):

    def __init__(
            self,
            init_value: Maybe[T] = Nothing,
            read_only=False,
            modifier: Callable[[Observable], Observable] = identity,
            validator: Callable[[T, Any], T] = lambda v, _: v) -> None:

        super().__init__(read_only)

        self._init_value = init_value
        self._modifier = modifier
        self._validator = validator

    @property
    def init_value(self) -> Maybe[T]:
        return self._init_value

    @property
    def validator(self) -> Callable[[T, Any], T]:
        return self._validator

    @property
    def modifier(self) -> Callable[[Observable], Observable]:
        return self._modifier

    def as_view(self) -> ReactiveView[T]:
        return ReactiveView(self.context, self.read_only)

    def pipe(self, *modifiers: Callable[[Observable], Observable]) -> ReactiveProperty:
        stack = [self.modifier] + list(modifiers)

        return ReactiveProperty(self.init_value, self.read_only, pipe_(*stack), self.validator)  # type:ignore

    def validate(self, validator: Callable[[T, Any], T]) -> ReactiveProperty[T]:
        if validator is None:
            raise ValueError("Argument 'modifier' is required.")

        def validate(v: T, obj: Any) -> T:
            return validator(self.validator(v, obj), obj)

        return ReactiveProperty(self.init_value, self.read_only, self.modifier, validate)

    class PropertyData(ReactiveValue.Data[T]):

        def __init__(
                self,
                name: str,
                init_value: Maybe[T],
                modifier: Callable[[Observable], Observable],
                validator: Callable[[T], T]):

            assert name is not None
            assert init_value is not None
            assert modifier is not None
            assert validator is not None

            self._validator = validator
            self._property: Optional[BehaviorSubject] = None

            obs: Observable

            if init_value != Nothing:
                self._property = BehaviorSubject(init_value.map(validator).unwrap())

                obs = self._property
            else:
                obs = rx.empty()

            super().__init__(name, obs, modifier)

        # Must override to appease Mypy... I hate Python.
        @property
        def value(self) -> T:
            return super().value

        @value.setter
        def value(self, value: T):
            self._check_disposed()

            if self.initialized:
                assert self._property is not None

                self._property.on_next(self.validator(value))
            else:
                self._property = BehaviorSubject(self.validator(value))

                self.observable = self._property

        @property
        def validator(self) -> Callable[[T], T]:
            return self._validator

        def dispose(self) -> None:
            assert self._property is not None

            self._check_disposed()
            self._property.on_completed()

            super().dispose()

    def _create_data(self, obj: Any) -> PropertyData:
        assert obj is not None
        assert self.name is not None

        def validate(v: T) -> T:
            return self.validator(v, obj)

        return self.PropertyData(self.name, self.init_value, self.modifier, validate)

    def _get_data(self, obj: Any) -> PropertyData:
        assert obj is not None

        return cast(ReactiveProperty.PropertyData, super()._get_data(obj))

    def _set_value(self, obj: Any, data: ReactiveValue.Data, value: Any) -> None:
        assert obj is not None
        assert isinstance(data, ReactiveProperty.PropertyData)

        data.value = value
