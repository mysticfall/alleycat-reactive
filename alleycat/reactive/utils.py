import dis
import inspect
from dis import Instruction
from itertools import dropwhile, takewhile
from types import FrameType
from typing import Tuple, Any, TypeVar, Iterator, Iterable

from returns.maybe import Maybe, Nothing, Some
from returns.pipeline import flow

T = TypeVar("T")


def get_current_frame(depth: int = 1) -> Maybe[FrameType]:
    if depth < 0:
        raise ValueError("Argument 'depth' must be zero or a positive integer.")

    def move_up(frame: Maybe[FrameType]) -> Maybe[FrameType]:
        return frame.bind(lambda f: Maybe.from_value(f.f_back))

    return flow(Maybe.from_value(inspect.currentframe()), *[move_up for _ in range(depth)])  # type:ignore


def get_property_reference(frame: FrameType) -> Maybe[Tuple[Any, str]]:
    if frame is None:
        raise ValueError("Argument 'frame' is required.")

    def collect(inst: Iterable[Instruction]):
        for i in inst:
            if i.opname == "LOAD_FAST" or i.opname == "LOAD_DEREF":
                yield i
                return
            yield i

    def unwrap(obj: Any, segments: Iterator[str]) -> Maybe[Any]:
        result: Maybe[Any]

        try:
            key = next(segments)

            if type(obj) == dict:
                result = unwrap(obj[key], segments)
            else:
                result = unwrap(getattr(obj, key), segments)
        except (AttributeError, KeyError):
            result = Nothing
        except StopIteration:
            result = Some(obj)

        return result

    try:
        *path, attr = flow(
            dis.get_instructions(frame.f_code),
            lambda s: takewhile(lambda i: i.offset != frame.f_lasti, s),
            lambda s: reversed(list(s)),
            lambda s: list(collect(s)),
            lambda s: reversed(s),
            lambda s: map(lambda i: str(i.argval), s))

        return unwrap(frame.f_locals, iter(path)).map(lambda obj: (obj, attr))
    except (StopIteration, ValueError):
        pass

    return Nothing


def is_invoked_from_observe(frame: FrameType) -> bool:
    if frame is None:
        raise ValueError("Argument 'frame' is required.")

    try:
        result = flow(
            dis.get_instructions(frame.f_code),
            lambda s: takewhile(lambda i: i.offset != frame.f_lasti, s),
            lambda s: reversed(list(s)),
            lambda s: dropwhile(lambda i: i.opname == "LOAD_FAST", s),
            lambda s: next(s),
            lambda s: s.opname == "LOAD_METHOD" and s.argval == "observe")

        return result
    except (StopIteration, ValueError):
        pass

    return False


def get_instructions(frame: FrameType) -> Iterator[dis.Instruction]:
    if frame is None:
        raise ValueError("Argument 'frame' is required.")

    try:
        return dropwhile(lambda i: i.offset != frame.f_lasti, dis.get_instructions(frame.f_code))
    except StopIteration:
        return iter([])
