from collections import deque
from functools import reduce, partial
from typing import TypeVar, Generic, Callable, Optional, Union, Deque, Any

from returns.functions import raise_exception
from returns.maybe import Maybe
from returns.result import safe, Failure, Success
from rx import Observable
from rx.core.typing import Disposable
from rx.subject import BehaviorSubject

from . import PreModifier, PostModifier
from . import utils

T = TypeVar("T")
U = TypeVar("U")


class ReactiveProperty(Generic[T]):
    KEY = "_ro_property"

    pre_mod_chain: Deque[PreModifier]

    post_mod_chain: Deque[PostModifier]

    def __init__(self,
                 init_value: Optional[T] = None,
                 read_only=False,
                 name: Optional[str] = None,
                 parent: Optional["ReactiveProperty[T]"] = None,
                 pre_modifier: Optional[PreModifier] = None,
                 post_modifier: Optional[PostModifier] = None):

        self.init_value = init_value

        if parent is None:
            self.name = Maybe.from_value(name).value_or(utils.infer_or_require_name(3, utils.get_assigned_name))

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

    class ReactiveData(Generic[U], Disposable):

        observable: Observable

        def __init__(self,
                     init_value: U,
                     pre_modifier: Callable[[U], U],
                     post_modifier: Callable[[Observable], Observable]):
            self._value = pre_modifier(init_value)
            self._subject = BehaviorSubject(self._value)
            self._modifier = pre_modifier

            self.observable = post_modifier(self._subject)

            def update(value):
                self._value = value

            self._dispose_token = self.observable.subscribe(update, lambda x: print(x))

        @property
        def value(self) -> U:
            return self._value

        @value.setter
        def value(self, value: U):
            self._subject.on_next(self._modifier(value))

        def dispose(self) -> None:
            self._subject.on_completed()
            self._dispose_token.dispose()

    def _get_data(self, obj, init_value: Optional[T] = None) -> ReactiveData[T]:
        assert obj is not None

        def initialize(container: Any, key: str, default: Callable[[], Any], _: Exception):
            if init_value is not None:
                value = default()
                if type(container) == dict:
                    container[key] = value
                else:
                    setattr(container, key, value)

                return Success(value)

            return Failure(AttributeError("The property has not been properly initialized."))

        init_container = partial(initialize, obj, self.KEY, lambda: {})

        def create_data():
            def compose(f, g):
                return lambda x, y: g(x, f(x, y))

            def identity(_, x):
                return x

            # FIXME Annotating the following method will crash PyCharm's type checker (See PY-43455).
            # The signature should be 'def build_chain(chain: Deque[Callable[[Any, U], U]]) -> Callable[[U], U]'.
            def build_chain(chain):
                return partial(reduce(compose, chain, identity), obj)

            pre_chain = build_chain(self.pre_mod_chain)  # type: ignore
            post_chain = build_chain(self.post_mod_chain)  # type: ignore

            # noinspection PyTypeChecker
            return self.ReactiveData(init_value, pre_chain, post_chain)

        def init_data(v: Any):
            return partial(initialize, v, self.name, create_data)

        return safe(getattr)(obj, self.KEY) \
            .rescue(init_container) \
            .bind(lambda v: safe(lambda: v[self.name])().rescue(init_data(v))) \
            .fix(raise_exception) \
            .unwrap()

    def __get__(self, obj, obj_type=None) -> Union[T, "ReactiveProperty[T]"]:
        if obj is None:
            return self

        return self._get_data(obj, self.init_value).value

    def __set__(self, obj, value: T) -> None:
        if obj is None:
            return None

        if self.read_only and self.init_value is not None:
            raise AttributeError("Cannot modify a read-only property.")

        self._get_data(obj, value).value = value
