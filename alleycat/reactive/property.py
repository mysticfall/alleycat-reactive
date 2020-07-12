import dis
import inspect
from collections import deque
from functools import reduce, partial
from typing import TypeVar, Generic, Callable

from rx import Observable
from rx.core.typing import Disposable
from rx.subject import BehaviorSubject

from . import PreModifier, PostModifier
from . import dis

T = TypeVar('T')


class ReactiveProperty(Generic[T]):
    KEY = "_ro_property"

    def __init__(self,
                 init_value: T = None,
                 read_only=False,
                 parent=None,
                 pre_modifier: PreModifier = None,
                 post_modifier: PostModifier = None):

        self.init_value = init_value

        if parent is None:
            self.name = dis.get_assigned_name(inspect.currentframe().f_back)
            self.read_only = read_only
            self.pre_mod_chain = deque()
            self.post_mod_chain = deque()
        else:
            self.name = parent.name
            self.read_only = parent.read_only
            self.pre_mod_chain = parent.pre_mod_chain.copy()
            self.post_mod_chain = parent.post_mod_chain.copy()

        if pre_modifier is not None:
            self.pre_mod_chain.appendleft(pre_modifier)

        if post_modifier is not None:
            self.post_mod_chain.appendleft(post_modifier)

    class ReactiveData(Disposable):

        value: T

        observable: Observable

        def __init__(self,
                     init_value: T,
                     pre_modifier: Callable[[T], T],
                     post_modifier: Callable[[Observable], Observable]):
            self._value = pre_modifier(init_value)
            self._subject = BehaviorSubject(self._value)
            self._modifier = pre_modifier

            self.observable = post_modifier(self._subject)

            def update(value):
                self._value = value

            self._dispose_token = self.observable.subscribe(update, lambda x: print(x))

        @property
        def value(self):
            return self._value

        @value.setter
        def value(self, value):
            self._subject.on_next(self._modifier(value))

        def dispose(self) -> None:
            self._subject.on_completed()
            self._dispose_token.dispose()

    def _get_data(self, obj, init_value: T = None) -> ReactiveData:
        assert obj is not None

        if hasattr(obj, self.KEY):
            return getattr(obj, self.KEY)[self.name]
        elif init_value is not None:
            def compose(f, g):
                return lambda x, y: g(x, f(x, y))

            def identity(_, x):
                return x

            def build_chain(chain):
                return partial(reduce(compose, chain, identity), obj)

            pre_chain = build_chain(self.pre_mod_chain)
            post_chain = build_chain(self.post_mod_chain)

            # noinspection PyTypeChecker
            data = self.ReactiveData(init_value, pre_chain, post_chain)

            setattr(obj, self.KEY, {self.name: data})

            return data

        raise AttributeError("The property has not been properly initialized.")

    def __get__(self, obj, obj_type=None) -> T:
        if obj is None:
            return self

        return self._get_data(obj, self.init_value).value

    def __set__(self, obj, value: T) -> None:
        if obj is None:
            return None

        if self.read_only and self.init_value is not None:
            raise AttributeError("Cannot modify a read-only property.")

        self._get_data(obj, value).value = value
