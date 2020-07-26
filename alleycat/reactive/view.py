from typing import TypeVar, Generic, Any

from returns.maybe import Maybe, Nothing
from rx import Observable

from . import ReactiveValue

T = TypeVar("T")


class ReactiveView(Generic[T], ReactiveValue[T]):

    def __init__(self, observable: Maybe[Observable] = Nothing, read_only=False) -> None:
        super().__init__(read_only=read_only)

        self.init_observable = observable

    def _create_data(self, obj: Any) -> ReactiveValue.Data:
        assert self.name is not None

        return self.Data(self.name, self.init_observable)

    def _get_data(self, obj: Any) -> ReactiveValue.Data:
        return super()._get_data(obj)

    def _set_value(self, obj: Any, data: ReactiveValue.Data, value: Any) -> None:
        assert obj is not None
        assert isinstance(value, Observable)

        data.observable = value
