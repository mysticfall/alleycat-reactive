from typing import Callable, TypeVar, Any

from rx import Observable

T = TypeVar("T")

PreModifier = Callable[[Any, T], T]
PostModifier = Callable[[Any, Observable], Observable]

# Import order should not be changed to avoid a circular dependency.
from .value import ReactiveValue as ReactiveValue
from .property import ReactiveProperty as ReactiveProperty
from .functions import dispose as dispose, from_property as from_property, from_value as from_value, observe as observe
from .object import ReactiveObject as ReactiveObject
