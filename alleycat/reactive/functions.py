from types import FrameType
from typing import TypeVar, Optional, Deque, Callable, Any, Sequence

import rx
from mypy_extensions import VarArg
from returns.context import RequiresContext
from returns.maybe import Maybe
from rx import Observable

from . import PreModifier, PostModifier, ReactiveValue
from . import utils
from .property import ReactiveProperty
from .view import ReactiveView

T = TypeVar("T")


def from_value(value: Optional[T] = None, read_only=False) -> ReactiveProperty[T]:
    return ReactiveProperty(Maybe.from_value(value), read_only)


def from_observable(value: Optional[Observable] = None, read_only=False) -> ReactiveView:
    init_value: RequiresContext[Observable, Any] = \
        RequiresContext(lambda _: Maybe.from_value(value).value_or(rx.empty()))

    return ReactiveView(init_value, read_only)


def map_value(value: ReactiveValue[T]) -> Callable[[Callable[[Observable], Observable]], ReactiveView]:
    if value is None:
        raise ValueError("Argument 'value' is required.")

    def process(modifier: Callable[[Observable], Observable]):
        if modifier is None:
            raise ValueError("Argument 'modifier' is required.")

        return ReactiveView(value.context.map(modifier))

    return process


def combine(*values: ReactiveValue) -> Callable[[Callable[[Sequence[Observable]], Observable]], ReactiveView]:
    if len(values) == 0:
        raise ValueError("At least one argument is required.")

    def process(modifier: Callable[[Sequence[Observable]], Observable]):
        if modifier is None:
            raise ValueError("Argument 'modifier' is required.")

        init_value = RequiresContext.from_iterable([v.context for v in values]).map(modifier)

        return ReactiveView(init_value)

    return process


def combine_latest(*values: ReactiveValue) -> Callable[[Callable[[Observable], Observable]], ReactiveView]:
    return _combine_with(values, rx.combine_latest)


def zip_values(*values: ReactiveValue) -> Callable[[Callable[[Observable], Observable]], ReactiveView]:
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


def from_property(
        parent: ReactiveProperty[T],
        pre_modifier: Optional[PreModifier] = None,
        post_modifier: Optional[PostModifier] = None) -> ReactiveProperty[T]:
    if parent is None:
        raise ValueError("Argument 'parent' is required.")
    elif parent.read_only and pre_modifier is not None:
        raise ValueError("Pre-modifier is not applicable to a read-only property.")

    pre_modifiers: Optional[Deque[PreModifier]] = None
    post_modifiers: Optional[Deque[PostModifier]] = None

    if pre_modifier is not None:
        pre_modifiers = parent.pre_modifiers.copy()
        pre_modifiers.appendleft(pre_modifier)

    if post_modifier is not None:
        post_modifiers = parent.post_modifiers.copy()
        post_modifiers.appendleft(post_modifier)

    return ReactiveProperty(
        parent.init_value, parent.read_only, pre_modifiers=pre_modifiers, post_modifiers=post_modifiers)


def observe(obj, name: Optional[str] = None) -> Observable:
    if obj is None:
        raise ValueError("Cannot observe a None object.")

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

    properties = getattr(obj, ReactiveProperty.KEY, {}).values()

    for p in properties:
        p.dispose()
