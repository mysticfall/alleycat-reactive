from typing import Callable, TypeVar, Any

from rx import Observable

T = TypeVar("T")

PreModifier = Callable[[Any, T], T]
PostModifier = Callable[[Any, Observable], Observable]

# Import order should not be changed to avoid a circular dependency.
from .value import ReactiveValue as ReactiveValue
from .view import ReactiveView as ReactiveView
from .property import ReactiveProperty as ReactiveProperty
from . import functions
from .object import ReactiveObject as ReactiveObject
