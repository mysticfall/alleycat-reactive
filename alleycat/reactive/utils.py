import dis
import inspect
from itertools import dropwhile, takewhile
from types import FrameType
from typing import Iterable, Tuple, Any, TypeVar, Callable

from returns.maybe import Maybe, Nothing
from returns.pipeline import flow

T = TypeVar("T")


def get_current_frame(depth: int) -> Maybe[FrameType]:
    def move_up(frame: Maybe[FrameType]) -> Maybe[FrameType]:
        return frame.bind(lambda f: Maybe.from_value(f.f_back))

    return flow(Maybe.from_value(inspect.currentframe()), *[move_up for _ in range(depth)])


def get_assigned_name(frame: FrameType) -> Maybe[str]:
    try:
        inst = flow(
            dis.get_instructions(frame.f_code),
            lambda s: dropwhile(lambda i: i.offset != frame.f_lasti, s),
            lambda s: dropwhile(lambda i: i.opname.startswith("CALL_"), s),
            lambda s: takewhile(lambda i: i.opname == "STORE_NAME", s),
            lambda s: next(s))

        return Maybe.from_value(inst).map(lambda i: str(i.argval))
    except StopIteration:
        pass

    return Nothing


def get_property_reference(frame: FrameType) -> Maybe[Tuple[Any, str]]:
    try:
        stack = flow(
            dis.get_instructions(frame.f_code),
            lambda s: dropwhile(lambda i: not i.opname.startswith("CALL_"), s),
            lambda s: dropwhile(lambda i: not i.opname.startswith("CALL_"), s),
            lambda s: dropwhile(lambda i: i.opname.startswith("CALL_"), s),
            lambda s: dropwhile(lambda i: i.opname != "LOAD_FAST", s))

        variable = Maybe.from_value(next(stack)).map(lambda v: str(v.argval))

        stack = takewhile(lambda i: i.opname == "LOAD_ATTR", stack)

        attr = Maybe.from_value(next(stack)).map(lambda a: str(a.argval))

        return variable.bind(lambda v: attr.map(lambda a: (frame.f_locals.get(v), a)))
    except StopIteration:
        pass

    return Nothing


def get_object_to_extend(frame: FrameType) -> Maybe[Tuple[Any, str]]:
    try:
        stack = flow(
            dis.get_instructions(frame.f_code),
            lambda s: dropwhile(lambda i: not i.opname.startswith("SETUP_ANNOTATIONS"), s),
            lambda s: dropwhile(lambda i: not i.opname.startswith("LOAD_NAME") or i.argval != "extend", s),
            lambda s: dropwhile(lambda i: i.argval == "extend", s))

        variable = Maybe \
            .from_value(next(takewhile(lambda i: i.opname == "LOAD_NAME", stack))) \
            .map(lambda v: str(v.argval))

        attr = Maybe.from_value(next(takewhile(lambda i: i.opname == "LOAD_ATTR", stack))) \
            .map(lambda v: str(v.argval))

        return variable.bind(lambda v: attr.map(lambda a: (frame.f_globals.get(v), a)))
    except StopIteration:
        pass

    return Nothing


def find_or_require_name(depth: int, extractor: Callable[[FrameType], Maybe[T]]) -> T:
    value = get_current_frame(depth).bind(extractor).value_or(None)

    if value is None:
        raise ValueError("Argument 'name' is required when the platform does not provide bytecode instructions.")

    return value


def get_instructions(frame: FrameType) -> Iterable[dis.Instruction]:
    try:
        return dropwhile(lambda i: i.offset != frame.f_lasti, dis.get_instructions(frame.f_code))
    except StopIteration:
        return []


def dump_instructions(frame: FrameType) -> None:
    for ins in iter(dis.get_instructions(frame.f_code)):
        print(ins)
