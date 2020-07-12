from typing import Callable, TypeVar

from rx import Observable

T = TypeVar("T")

PreModifier = Callable[[any, T], T]
PostModifier = Callable[[any, Observable], Observable]

# Import order should not be changed to avoid a circular dependency.
from .property import ReactiveProperty
from .functions import dispose, extend, observe
from .object import ReactiveObject
