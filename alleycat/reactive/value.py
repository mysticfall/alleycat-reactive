from __future__ import annotations

from abc import ABC, abstractmethod
from functools import partial
from typing import TypeVar, Generic, Callable, Optional, Union, Any, Mapping, Tuple

from returns.context import RequiresContext
from returns.functions import raise_exception, identity
from returns.maybe import Maybe
from returns.result import safe, Success
from rx import Observable
from rx import operators as ops
from rx.core.typing import Disposable
from rx.subject import BehaviorSubject

from alleycat.reactive import utils

T = TypeVar("T")
U = TypeVar("U")

DATA_KEY = "_rv_data"

META_KEY_PREFIX = "_rv_meta_"

Modifier = Callable[[Observable], Observable]


class ReactiveValue(Generic[T], ABC):
    __slots__ = ()

    def __init__(self, read_only=False) -> None:
        self._name: Optional[str] = None
        self._read_only = read_only

        data: RequiresContext[Any, ReactiveValue.Data[T]] = RequiresContext(lambda obj: self._get_data(obj))

        # Declare separately to prevent an object allocation with every value/observable reference.
        self._context = data.map(lambda c: c.observable)
        self._value_context = data.map(lambda c: c.value)

    @property
    def name(self) -> Optional[str]:
        return self._name

    @property
    def read_only(self) -> bool:
        return self._read_only

    @property
    def context(self) -> RequiresContext[Observable, Any]:
        return self._context

    @property
    def value_context(self) -> RequiresContext[T, Any]:
        return self._value_context

    def observable(self, obj: Any) -> Observable:
        if obj is None:
            raise ValueError("Cannot observe a None object.")

        return self.context(obj)

    def map(self, modifier: Callable[[Any, T], Any]) -> ReactiveValue:
        return self.pipe(lambda o: (ops.map(lambda v: modifier(o, v)),))

    @abstractmethod
    def pipe(self, modifiers: Callable[[Any], Tuple[Modifier, ...]]) -> ReactiveValue:
        pass

    @staticmethod
    def _check_hooks(cls: type, name: str) -> None:
        key = META_KEY_PREFIX + cls.__qualname__

        if not hasattr(cls, key):
            setattr(cls, key, {"values": []})

        metadata = getattr(cls, key)
        values = metadata["values"]

        if name not in values:
            values.append(name)

        if "init" not in metadata:
            metadata["init"] = getattr(cls, "__init__")

            def init_hook(instance, *args, **kwargs):
                metadata["init"](instance, *args, **kwargs)

                concrete_type = type(instance)

                for value in metadata["values"]:
                    getattr(concrete_type, value).context(instance)

            setattr(cls, "__init__", init_hook)

        if "del" not in metadata:
            try:
                metadata["del"] = getattr(cls, "__del__")
            except AttributeError:
                def noop(_: Any):
                    pass

                metadata["del"] = noop

            def del_hook(instance):
                data: Mapping[str, ReactiveValue.Data] = getattr(instance, DATA_KEY, [])

                for d in filter(lambda v: not v.disposed, data.values()):
                    d.dispose()

                metadata["del"](instance)

            setattr(cls, "__del__", del_hook)

    def __set_name__(self, cls, name):
        self._name = name

        ReactiveValue._check_hooks(cls, name)

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

        def __init__(self,
                     name: Optional[str],
                     observable: Observable,
                     modifier: Callable[[Observable], Observable] = identity):
            assert observable is not None

            self.name = Maybe.from_value(name)

            self._value: Optional[U] = None

            self._initialized = False
            self._disposed = False
            self._subject = BehaviorSubject(observable)
            self._observable = modifier(self._subject.pipe(ops.switch_latest())) \
                .pipe(ops.share(), ops.replay(buffer_size=1))

            def update(value):
                if not self.initialized:
                    self._initialized = True

                self._value = value  # We don't use Some(value) here to avoid excessive object allocations.

            self._cancel_update = self.observable.subscribe(update, raise_exception)
            self._connection = self._observable.connect()  # type:ignore

        def label(self) -> str:
            return self.name.value_or("(anonymous)")

        def _check_disposed(self) -> None:
            if self.disposed:
                raise AttributeError(f"Property '{self.label()}' has been disposed.")

        @property
        def initialized(self) -> bool:
            return self._initialized

        @property
        def value(self) -> U:
            if not self.initialized:
                # FIXME: This is a bad design but also something unavoidable if we want to call 'observe' on
                #  an uninitialized value.
                def observed_from_frame(depth: int) -> bool:
                    return utils.get_current_frame(depth).map(utils.is_invoked_from_observe).value_or(False)

                observed = observed_from_frame(7) or observed_from_frame(8)

                if observed:
                    return None  # type:ignore
                else:
                    raise AttributeError(f"Property '{self.label()}' is not initialized yet.")

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
            self._connection.dispose()

            self._disposed = True

    @abstractmethod
    def _create_data(self, obj: Any) -> Data[T]:
        pass

    def _get_data(self, obj: Any) -> Data[T]:
        assert obj is not None

        if self.name is None:
            return self._create_data(obj)

        def initialize(container: Any, key: str, default: Callable[[], Any], _: Exception):
            value = default()

            if type(container) == dict:
                container[key] = value
            else:
                setattr(container, key, value)

            return Success(value)

        init_container = partial(initialize, obj, DATA_KEY, lambda: {})
        new_instance = partial(self._create_data, obj)

        def init_data(v: Any):
            return partial(initialize, v, self.name, new_instance)

        return safe(getattr)(obj, DATA_KEY) \
            .rescue(init_container) \
            .bind(lambda v: safe(lambda: v[self.name])().rescue(init_data(v))) \
            .fix(raise_exception) \
            .unwrap()

    @abstractmethod
    def _set_value(self, obj: Any, data: Data[T], value: Any) -> None:
        pass
