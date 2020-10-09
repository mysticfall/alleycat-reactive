from __future__ import annotations

from typing import TypeVar, Generic, Any, Callable, Tuple

from returns.context import RequiresContext
from rx import Observable
from rx import operators as ops

from . import ReactiveValue
from .value import Modifier

T = TypeVar("T")


class ReactiveView(Generic[T], ReactiveValue[T]):

    def __init__(self, init_value: RequiresContext[Observable, Any], read_only=True) -> None:
        super().__init__(read_only)

        self._init_value = init_value

    def pipe(self, modifiers: Callable[[Any], Tuple[Modifier, ...]]) -> ReactiveView:
        return ReactiveView(self.context.map(lambda o: o.pipe(*(modifiers(o)))), self.read_only)

    def with_instance(self) -> ReactiveView[Tuple[Any, T]]:
        context: RequiresContext[Observable, Any] = \
            RequiresContext(lambda i: self.context(i).pipe(ops.map(lambda v: (i, v))))

        return ReactiveView(context, self.read_only)

    def _create_data(self, obj: Any) -> ReactiveValue.Data:
        assert obj is not None

        return self.Data(self.name, self._init_value(obj))

    def _get_data(self, obj: Any) -> ReactiveValue.Data:
        return super()._get_data(obj)

    def _set_value(self, obj: Any, data: ReactiveValue.Data, value: Any) -> None:
        assert obj is not None
        assert isinstance(value, Observable)

        data.observable = value
