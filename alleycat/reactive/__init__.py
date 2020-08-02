from typing import Callable, TypeVar, Any

from rx import Observable

T = TypeVar("T")

PreModifier = Callable[[Any, T], T]
PostModifier = Callable[[Any, Observable], Observable]

# Import order should not be changed to avoid a circular dependency.
from .value import ReactiveValue as ReactiveValue
from .view import ReactiveView as ReactiveView
from .property import ReactiveProperty as ReactiveProperty
from .functions import dispose as dispose, from_property as from_property, from_value as from_value, \
    from_observable as from_observable, combine as combine, combine_latest as combine_latest, observe as observe, \
    map_value as map_value
from .object import ReactiveObject as ReactiveObject
