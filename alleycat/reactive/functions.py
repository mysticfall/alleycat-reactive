from typing import TypeVar

from rx import Observable

from . import PreModifier, PostModifier
from .property import ReactiveProperty

T = TypeVar("T")


def observe(obj, name: str) -> Observable:
    if obj is None or not hasattr(obj, ReactiveProperty.KEY):
        raise AttributeError(f"Unknown property name: '{name}'.")

    return getattr(obj, ReactiveProperty.KEY)[name].observable


def extend(cls, name: str, pre_modifier: PreModifier = None, post_modifier: PostModifier = None) -> ReactiveProperty[T]:
    parent: ReactiveProperty = getattr(cls, name)

    return ReactiveProperty(
        read_only=parent.read_only, parent=parent, pre_modifier=pre_modifier, post_modifier=post_modifier)


def dispose(obj):
    properties = getattr(obj, ReactiveProperty.KEY, {}).values()

    for data in properties:
        data.dispose()
