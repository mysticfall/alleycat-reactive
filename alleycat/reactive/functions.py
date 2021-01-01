from types import FrameType
from typing import Any, Callable, Optional, Sequence, Tuple, TypeVar

import rx
from returns.context import RequiresContext
from returns.iterables import Fold
from returns.maybe import Maybe, Nothing
from rx import Observable

from . import ReactiveValue, utils
from .property import ReactiveProperty
from .value import DATA_KEY
from .view import ReactiveView

T = TypeVar("T")


def new_property(read_only=False) -> ReactiveProperty:
    return ReactiveProperty(Nothing, read_only)


def new_view(read_only=True) -> ReactiveView:
    return ReactiveView(RequiresContext(lambda _: rx.empty()), read_only)


def from_value(value: Optional[T], read_only=False) -> ReactiveProperty[T]:
    return ReactiveProperty(Maybe.from_optional(value), read_only)


def from_observable(value: Optional[Observable] = None, read_only=True) -> ReactiveView:
    init_value: RequiresContext[Observable, Any] = \
        RequiresContext(lambda _: Maybe.from_optional(value).value_or(rx.empty()))

    return ReactiveView(init_value, read_only)


def from_instance(value: Callable[[Any], Observable], read_only=True) -> ReactiveView:
    return ReactiveView(RequiresContext(value), read_only)


def combine(*values: ReactiveValue) -> Callable[[Callable[[Tuple[Observable, ...]], Observable]], ReactiveView]:
    if len(values) == 0:
        raise ValueError("At least one argument is required.")

    def process(modifier: Callable[[Tuple[Observable, ...]], Observable]):
        if modifier is None:
            raise ValueError("Argument 'modifier' is required.")

        # noinspection PyTypeChecker
        init_value = Fold.collect([v.context for v in values], RequiresContext.from_value(())) \
            .map(lambda v: modifier(*v))  # type:ignore

        return ReactiveView(init_value)

    return process


def combine_latest(*values: ReactiveValue) -> Callable[[Callable[[Observable], Observable]], ReactiveView]:
    # noinspection PyTypeChecker
    return _combine_with(values, rx.combine_latest)  # type:ignore


def merge(*values: ReactiveValue) -> ReactiveView:
    # noinspection PyTypeChecker
    return combine(*values)(rx.merge)  # type:ignore


# noinspection PyShadowingBuiltins
def zip(*values: ReactiveValue) -> Callable[[Callable[[Observable], Observable]], ReactiveView]:
    # noinspection PyTypeChecker
    return _combine_with(values, rx.zip)  # type:ignore


def _combine_with(values: Sequence[ReactiveValue], combinator: Callable[[Tuple[Observable, ...]], Observable]):
    if values is None:
        raise ValueError("Argument 'values' is required.")

    def process(modifier: Callable[[Observable], Observable]):
        # noinspection PyTypeChecker
        init_value = Fold.collect([v.context for v in values], RequiresContext.from_value(())) \
            .map(lambda v: combinator(*v)).map(modifier)  # type:ignore

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
        .from_optional(name) \
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
