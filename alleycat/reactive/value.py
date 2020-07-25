from abc import ABC, abstractmethod
from functools import partial
from typing import TypeVar, Generic, Callable, Optional, Union, Any

import rx
from returns.functions import raise_exception
from returns.maybe import Maybe, Nothing
from returns.result import safe, Success
from rx import Observable
from rx import operators as ops
from rx.core.typing import Disposable
from rx.subject import BehaviorSubject

T = TypeVar("T")
U = TypeVar("U")


class ReactiveValue(Generic[T], ABC):
    KEY = "_rx_value"

    __slots__ = ()

    def __init__(self) -> None:
        self._name: Optional[str] = None

    @property
    def name(self) -> Optional[str]:
        return self._name

    def observable(self, obj: Any) -> Observable:
        if obj is None:
            raise ValueError("Cannot observe a None object.")

        return self._get_data(obj).observable

    def __set_name__(self, obj, name):
        self._name = name

    def __get__(self, obj: Any, obj_type: Optional[type] = None) -> Union[T, "ReactiveValue[T]"]:
        if obj is None:
            return self

        return self._get_data(obj).value

    class Data(Generic[U], Disposable, ABC):

        def __init__(self, name: str, observable: Maybe[Observable]):
            assert str is not None
            assert observable is not None

            self.name = name

            self._value: Optional[U] = None

            self._initialized = observable != Nothing
            self._disposed = False

            if observable is Nothing:
                self._subject = BehaviorSubject(rx.empty())
                self._observable = self._subject.pipe(ops.switch_latest())
            else:
                self._observable = observable.unwrap()

            def update(value):
                if not self.initialized:
                    self._initialized = True

                self._value = value  # We don't use Some(value) here to avoid excessive object allocations.

            self._cancel_update = self.observable.subscribe(update, lambda x: print(x))

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
        def observable(self, value: Observable):
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

        if self._name is None:
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
