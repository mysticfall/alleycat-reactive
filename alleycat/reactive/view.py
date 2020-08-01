from typing import TypeVar, Generic, Any

from returns.context import RequiresContext
from rx import Observable

from . import ReactiveValue

T = TypeVar("T")


class ReactiveView(Generic[T], ReactiveValue[T]):

    def __init__(self, init_value: RequiresContext[Observable, Any], read_only=False) -> None:
        super().__init__(read_only=read_only)

        self.init_value = init_value

    def _create_data(self, obj: Any) -> ReactiveValue.Data:
        assert self.name is not None

        return self.Data(self.name, self.init_value(obj))

    def _get_data(self, obj: Any) -> ReactiveValue.Data:
        return super()._get_data(obj)

    def _set_value(self, obj: Any, data: ReactiveValue.Data, value: Any) -> None:
        assert obj is not None
        assert isinstance(value, Observable)

        data.observable = value
