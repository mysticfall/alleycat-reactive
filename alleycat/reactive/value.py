from __future__ import annotations

from abc import ABC, abstractmethod
from functools import partial
from typing import TypeVar, Generic, Callable, Optional, Union, Any

from returns.context import RequiresContext
from returns.functions import raise_exception, identity
from returns.maybe import Maybe
from returns.result import safe, Success
from rx import Observable
from rx import operators as ops
from rx.core.typing import Disposable
from rx.subject import BehaviorSubject

T = TypeVar("T")
U = TypeVar("U")


class ReactiveValue(Generic[T], ABC):
    KEY = "_rx_value"

    context: RequiresContext[Any, Observable]

    value_context: RequiresContext[Any, T]

    __slots__ = ()

    def __init__(self, read_only=False, parent: Optional[ReactiveValue] = None) -> None:
        self._name: Optional[str] = None
        self.read_only = read_only
        self.parent = Maybe.from_value(parent)

        data: RequiresContext[Any, ReactiveValue.Data[T]] = RequiresContext(lambda obj: self._get_data(obj))

        # Declare separately to prevent an object allocation with every value/observable reference.
        self.context = data.map(lambda c: c.observable)
        self.value_context = data.map(lambda c: c.value)

    @property
    def name(self) -> Optional[str]:
        return self._name if self._name is not None else self.parent.map(lambda p: p.name).value_or(None)

    def observable(self, obj: Any) -> Observable:
        if obj is None:
            raise ValueError("Cannot observe a None object.")

        return self.context(obj)

    def map(self, modifier: Callable[[T], Any]) -> ReactiveValue:
        return self.bind(lambda o: o.pipe(ops.map(modifier)))

    @abstractmethod
    def bind(self, modifier: Callable[[Observable], Observable]) -> ReactiveValue:
        pass

    def __set_name__(self, obj, name):
        self._name = name

    def __get__(self, obj: Any, obj_type: Optional[type] = None) -> Union[T, ReactiveValue[T]]:
        if obj is None:
            return self

        return self.value_context(obj)

    def __set__(self, obj: Any, value: Any) -> None:
        if obj is None:
            raise AttributeError("Cannot modify property of a None object.")

        data = self._get_data(obj)

        assert data is not None

        if self.read_only and data.initialized:
            raise AttributeError("Cannot modify a read-only property.")

        self._set_value(obj, data, value)

    class Data(Generic[U], Disposable):

        def __init__(self, name: str, observable: Observable, modifier: Callable[[Observable], Observable] = identity):
            assert str is not None
            assert observable is not None

            self.name = name

            self._value: Optional[U] = None

            self._initialized = False
            self._disposed = False
            self._subject = BehaviorSubject(observable)
            self._observable = modifier(self._subject.pipe(ops.switch_latest()))

            def update(value):
                if not self.initialized:
                    self._initialized = True

                self._value = value  # We don't use Some(value) here to avoid excessive object allocations.

            self._cancel_update = self.observable.subscribe(update, raise_exception)

        def _check_disposed(self) -> None:
            if self.disposed:
                raise AttributeError(f"Property '{self.name}' has been disposed.")

        @property
        def initialized(self) -> bool:
            return self._initialized

        @property
        def value(self) -> U:
            if not self.initialized:
                raise AttributeError(f"Property '{self.name}' is not initialized yet.")

            assert self._value is not None  # Again, to appease the wrath of the Mypyan god.

            return self._value

        @property
        def observable(self) -> Observable:
            self._check_disposed()

            return self._observable

        @observable.setter
        def observable(self, value: Observable) -> None:
            assert value is not None

            self._check_disposed()
            self._subject.on_next(value)

        @property
        def disposed(self) -> bool:
            return self._disposed

        def dispose(self) -> None:
            self._check_disposed()
            self._cancel_update.dispose()

            self._disposed = True

    @abstractmethod
    def _create_data(self, obj: Any) -> Data[T]:
        pass

    def _get_data(self, obj: Any) -> Data[T]:
        assert obj is not None

        if self.name is None:
            raise AttributeError("The class must be instantiated as a property of a class.")

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

    @abstractmethod
    def _set_value(self, obj: Any, data: Data[T], value: Any) -> None:
        pass
