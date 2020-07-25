from typing import TypeVar, Optional, Deque

from returns.maybe import Maybe, Some
from rx import Observable

from . import PreModifier, PostModifier, ReactiveValue
from . import utils
from .property import ReactiveProperty

T = TypeVar("T")


def from_value(value: T, name: Optional[str] = None, read_only=False) -> ReactiveProperty[T]:
    prop_name = Maybe.from_value(name).or_else_call(utils.infer_or_require_name(utils.get_assigned_name, 3))

    return ReactiveProperty(prop_name, Some(value), read_only)


def from_property(
        parent: ReactiveProperty[T],
        pre_modifier: Optional[PreModifier] = None,
        post_modifier: Optional[PostModifier] = None) -> ReactiveProperty[T]:
    if parent is None:
        raise ValueError("Argument parent is required.")
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
        parent.name, parent.init_value, parent.read_only, pre_modifiers=pre_modifiers, post_modifiers=post_modifiers)


def observe(obj, name: Optional[str] = None) -> Observable:
    if obj is None:
        raise ValueError("Cannot observe a None object.")

    (target, key) = Maybe \
        .from_value(name) \
        .map(lambda n: (obj, n)) \
        .or_else_call(utils.infer_or_require_name(utils.get_property_reference, 3))

    prop: ReactiveValue = getattr(type(target), key)

    if prop is None or not isinstance(prop, ReactiveValue):
        raise AttributeError(f"Unknown property name: '{key}'.")

    return prop.observable(target)


def dispose(obj) -> None:
    if obj is None:
        raise ValueError("Cannot dispose a None object.")

    properties = getattr(obj, ReactiveProperty.KEY, {}).values()

    for p in properties:
        p.dispose()
