import inspect
from typing import TypeVar

from rx import Observable

from . import PreModifier, PostModifier
from . import dis
from .property import ReactiveProperty

T = TypeVar("T")


def observe(obj, name: str = None) -> Observable:
    if name is None:
        (target, key) = dis.get_property_reference(inspect.currentframe().f_back)
    else:
        (target, key) = (obj, name)

    if target is None or not hasattr(target, ReactiveProperty.KEY):
        raise AttributeError(f"Unknown property name: '{key}'.")

    return getattr(target, ReactiveProperty.KEY)[key].observable


def extend(cls, name: str, pre_modifier: PreModifier = None, post_modifier: PostModifier = None) -> ReactiveProperty[T]:
    parent: ReactiveProperty = getattr(cls, name)

    return ReactiveProperty(
        read_only=parent.read_only, parent=parent, pre_modifier=pre_modifier, post_modifier=post_modifier)


def dispose(obj):
    properties = getattr(obj, ReactiveProperty.KEY, {}).values()

    for data in properties:
        data.dispose()
