from types import FrameType
from typing import TypeVar, Optional, Callable, Any, Sequence

import rx
from mypy_extensions import VarArg
from returns.context import RequiresContext
from returns.maybe import Maybe, Nothing
from rx import Observable

from . import ReactiveValue
from . import utils
from .property import ReactiveProperty
from .value import DATA_KEY
from .view import ReactiveView

T = TypeVar("T")


def new_property(read_only=False) -> ReactiveProperty:
    return ReactiveProperty(Nothing, read_only)


def new_view(read_only=False) -> ReactiveView:
    return ReactiveView(RequiresContext(lambda _: rx.empty()), read_only)


def from_value(value: Optional[T], read_only=False) -> ReactiveProperty[T]:
    return ReactiveProperty(Maybe.from_value(value), read_only)


def from_observable(value: Optional[Observable] = None, read_only=False) -> ReactiveView:
    init_value: RequiresContext[Observable, Any] = \
        RequiresContext(lambda _: Maybe.from_value(value).value_or(rx.empty()))

    return ReactiveView(init_value, read_only)


def from_instance(value: Callable[[Any], Observable], read_only=False) -> ReactiveView:
    return ReactiveView(RequiresContext(value), read_only)


def combine(*values: ReactiveValue) -> Callable[[Callable[[VarArg(Observable)], Observable]], ReactiveView]:
    if len(values) == 0:
        raise ValueError("At least one argument is required.")

    def process(modifier: Callable[[VarArg(Observable)], Observable]):
        if modifier is None:
            raise ValueError("Argument 'modifier' is required.")

        init_value = RequiresContext.from_iterable([v.context for v in values]).map(lambda v: modifier(*v))

        return ReactiveView(init_value)

    return process


def combine_latest(*values: ReactiveValue) -> Callable[[Callable[[Observable], Observable]], ReactiveView]:
    return _combine_with(values, rx.combine_latest)


def merge(*values: ReactiveValue) -> ReactiveView:
    return combine(*values)(rx.merge)


# noinspection PyShadowingBuiltins
def zip(*values: ReactiveValue) -> Callable[[Callable[[Observable], Observable]], ReactiveView]:
    return _combine_with(values, rx.zip)


def _combine_with(values: Sequence[ReactiveValue], combinator: Callable[[VarArg(Observable)], Observable]) -> \
        Callable[[Callable[[Observable], Observable]], ReactiveView]:
    if values is None:
        raise ValueError("Argument 'values' is required.")

    def process(modifier: Callable[[Observable], Observable]):
        init_value = RequiresContext.from_iterable([v.context for v in values]).map(
            lambda v: combinator(*v)).map(modifier)

        return ReactiveView(init_value)

    return process


def observe(obj, name: Optional[str] = None) -> Observable:
    def infer_name(extractor: Callable[[FrameType], Maybe[T]], depth: int) -> Callable[[], T]:
        def process():
            value = utils.get_current_frame(depth + 1).bind(extractor).value_or(None)

            if value is None:
                raise ValueError(
                    "Argument 'name' is required when the platform does not provide bytecode instructions.")

            return value

        return process

    (target, key) = Maybe \
        .from_value(name) \
        .map(lambda n: (obj, n)) \
        .or_else_call(infer_name(utils.get_property_reference, 3))

    prop: ReactiveValue = getattr(type(target), key)

    if not isinstance(prop, ReactiveValue):
        raise AttributeError(f"Unknown property name: '{key}'.")

    return prop.observable(target)


def dispose(obj) -> None:
    if obj is None:
        raise ValueError("Cannot dispose a None object.")

    properties = getattr(obj, DATA_KEY, {}).values()

    for p in properties:
        p.dispose()
