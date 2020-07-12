import inspect
from typing import TypeVar

from returns.maybe import Maybe
from rx import Observable

from . import PreModifier, PostModifier
from . import dis
from .property import ReactiveProperty

T = TypeVar("T")


def observe(obj, name: str = None) -> Observable:
    (target, key) = Maybe \
        .from_value(name) \
        .map(lambda n: (obj, n)) \
        .value_or(dis.get_property_reference(inspect.currentframe().f_back).unwrap())

    if not hasattr(target, ReactiveProperty.KEY):
        raise AttributeError(f"Unknown property name: '{key}'.")

    return getattr(target, ReactiveProperty.KEY)[key].observable


def extend(
        obj,
        name: str = None,
        pre_modifier: PreModifier = None,
        post_modifier: PostModifier = None) -> ReactiveProperty[T]:
    (target, key) = Maybe \
        .from_value(name) \
        .map(lambda n: (obj, n)) \
        .value_or(dis.get_object_to_extend(inspect.currentframe().f_back).unwrap())

    parent: ReactiveProperty = getattr(target, key)

    return ReactiveProperty(
        read_only=parent.read_only, parent=parent, pre_modifier=pre_modifier, post_modifier=post_modifier)


def dispose(obj):
    properties = getattr(obj, ReactiveProperty.KEY, {}).values()

    for data in properties:
        data.dispose()
