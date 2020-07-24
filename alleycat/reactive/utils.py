import dis
import inspect
from dis import Instruction
from itertools import dropwhile, takewhile
from types import FrameType
from typing import Tuple, Any, TypeVar, Callable, List, Iterator

from returns.maybe import Maybe, Nothing
from returns.pipeline import flow

T = TypeVar("T")


def get_current_frame(depth: int = 1) -> Maybe[FrameType]:
    if depth < 0:
        raise ValueError("Argument 'depth' must be zero or a positive integer.")

    def move_up(frame: Maybe[FrameType]) -> Maybe[FrameType]:
        return frame.bind(lambda f: Maybe.from_value(f.f_back))

    return flow(Maybe.from_value(inspect.currentframe()), *[move_up for _ in range(depth)])  # type:ignore


def get_assigned_name(frame: FrameType) -> Maybe[str]:
    if frame is None:
        raise ValueError("Argument 'frame' is required.")

    try:
        inst: Instruction = flow(
            dis.get_instructions(frame.f_code),
            lambda s: dropwhile(lambda i: i.offset != frame.f_lasti, s),
            lambda s: dropwhile(lambda i: i.opname != "STORE_NAME", s),
            next)

        return Maybe.from_value(inst).map(lambda i: str(i.argval))
    except StopIteration:
        pass

    return Nothing


def get_property_reference(frame: FrameType) -> Maybe[Tuple[Any, str]]:
    if frame is None:
        raise ValueError("Argument 'frame' is required.")

    try:
        stack: List[Instruction] = flow(
            dis.get_instructions(frame.f_code),
            lambda s: takewhile(lambda i: i.offset != frame.f_lasti, s),
            lambda s: list(s)[-2:])

        variable = Maybe.from_value(stack[0]).map(lambda v: str(v.argval))
        attr = Maybe.from_value(stack[1]).map(lambda a: str(a.argval))

        return variable.bind(lambda v: attr.map(lambda a: (frame.f_locals.get(v), a)))
    except StopIteration:
        pass

    return Nothing


def infer_or_require_name(extractor: Callable[[FrameType], Maybe[T]], depth: int = 1) -> Callable[[], T]:
    if extractor is None:
        raise ValueError("Argument 'extractor' is required.")

    if depth < 0:
        raise ValueError("Argument 'depth' must be zero or a positive integer.")

    def process():
        value = get_current_frame(depth + 1).bind(extractor).value_or(None)

        if value is None:
            raise ValueError("Argument 'name' is required when the platform does not provide bytecode instructions.")

        return value

    return process


def get_instructions(frame: FrameType) -> Iterator[dis.Instruction]:
    if frame is None:
        raise ValueError("Argument 'frame' is required.")

    try:
        return dropwhile(lambda i: i.offset != frame.f_lasti, dis.get_instructions(frame.f_code))
    except StopIteration:
        return iter([])
