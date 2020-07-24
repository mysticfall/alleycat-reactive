from abc import ABC, abstractmethod
from functools import partial
from typing import TypeVar, Generic, Callable, Optional, Union, Any

from returns.functions import raise_exception
from returns.maybe import Maybe, Nothing
from returns.result import safe, Success
from rx import Observable
from rx.core.typing import Disposable

T = TypeVar("T")
U = TypeVar("U")


class ReactiveValue(Generic[T], ABC):
    KEY = "_rx_value"

    def __init__(self, name: str):
        if name is None:
            raise ValueError("Name is a required argument.")

        self.name = name

    def __get__(self, obj: Any, obj_type: Optional[type] = None) -> Union[T, "ReactiveValue[T]"]:
        if obj is None:
            return self

        return self._get_data(obj).value

    def observable(self, obj: Any) -> Observable:
        if obj is None:
            raise ValueError("Cannot observe a None object.")

        return self._get_data(obj).observable

    class Data(Generic[U], Disposable, ABC):

        observable: Observable

        def __init__(self, observable: Observable, init_value: Maybe[U] = Nothing):
            assert observable is not None

            self.observable = observable
            self.lazy = init_value == Nothing
            self.initialized = not self.lazy

            self._value = init_value.value_or(None)

            def update(value):
                if not self.initialized:
                    self.initialized = True

                self._value = value  # We don't use Some(value) here to avoid excessive object allocations.

            self._cancel_update = self.observable.subscribe(update, lambda x: print(x))

        @property
        def value(self) -> U:
            if not self.initialized:
                raise AttributeError("The value is not initialized yet.")

            return self._value

        def dispose(self) -> None:
            self._cancel_update.dispose()

    @abstractmethod
    def _create_data(self, obj: Any) -> Data[T]:
        pass

    def _get_data(self, obj: Any) -> Data[T]:
        assert obj is not None

        def initialize(container: Any, key: str, default: Callable[[], Any], _: Exception):
            value = default()

            if type(container) == dict:
                container[key] = value
            else:
                setattr(container, key, value)

            return Success(value)

        init_container = partial(initialize, obj, self.KEY, lambda: {})
        new_instance = partial(self._create_data, obj)

        def init_data(v: Any):
            return partial(initialize, v, self.name, new_instance)

        return safe(getattr)(obj, self.KEY) \
            .rescue(init_container) \
            .bind(lambda v: safe(lambda: v[self.name])().rescue(init_data(v))) \
            .fix(raise_exception) \
            .unwrap()
