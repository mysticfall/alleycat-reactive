import inspect
from types import FrameType
from typing import TypeVar, Optional

from returns.maybe import Maybe
from rx import Observable

from . import PreModifier, PostModifier
from . import utils
from .property import ReactiveProperty

T = TypeVar("T")


def observe(obj, name: Optional[str] = None) -> Observable:
    (target, key) = Maybe \
        .from_value(name) \
        .map(lambda n: (obj, n)) \
        .value_or(utils.get_property_reference(inspect.currentframe().f_back).unwrap())

    if not hasattr(target, ReactiveProperty.KEY):
        raise AttributeError(f"Unknown property name: '{key}'.")

    return getattr(target, ReactiveProperty.KEY)[key].observable


def extend(
        obj,
        name: Optional[str] = None,
        pre_modifier: Optional[PreModifier] = None,
        post_modifier: Optional[PostModifier] = None) -> ReactiveProperty[T]:
    (target, key) = Maybe \
        .from_value(name) \
        .map(lambda n: (obj, n)) \
        .value_or(utils.get_object_to_extend(inspect.currentframe().f_back).unwrap())

    parent: ReactiveProperty = getattr(target, key)

    return ReactiveProperty(
        read_only=parent.read_only, parent=parent, pre_modifier=pre_modifier, post_modifier=post_modifier)


def dispose(obj) -> None:
    properties = getattr(obj, ReactiveProperty.KEY, {}).values()

    for data in properties:
        data.dispose()
