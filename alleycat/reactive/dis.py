import dis
from itertools import dropwhile, takewhile
from types import FrameType
from typing import Iterable, Tuple

from returns.maybe import Maybe, Nothing
from returns.pipeline import flow


def get_assigned_name(frame: FrameType) -> Maybe[str]:
    try:
        inst = flow(
            dis.get_instructions(frame.f_code),
            lambda s: dropwhile(lambda i: i.offset != frame.f_lasti, s),
            lambda s: dropwhile(lambda i: i.opname.startswith("CALL_"), s),
            lambda s: takewhile(lambda i: i.opname == "STORE_NAME", s),
            lambda s: next(s))

        return Maybe.from_value(inst).map(lambda i: i.argval)
    except StopIteration:
        pass

    return Nothing


def get_property_reference(frame: FrameType) -> Maybe[Tuple[any, str]]:
    try:
        stack = flow(
            dis.get_instructions(frame.f_code),
            lambda s: dropwhile(lambda i: not i.opname.startswith("CALL_"), s),
            lambda s: dropwhile(lambda i: not i.opname.startswith("CALL_"), s),
            lambda s: dropwhile(lambda i: i.opname.startswith("CALL_"), s),
            lambda s: dropwhile(lambda i: i.opname != "LOAD_FAST", s))

        variable = Maybe.from_value(next(stack)).map(lambda v: v.argval)

        stack = takewhile(lambda i: i.opname == "LOAD_ATTR", stack)

        attr = Maybe.from_value(next(stack)).map(lambda a: a.argval)

        return variable.bind(lambda v: attr.map(lambda a: (frame.f_locals.get(v), a)))
    except StopIteration:
        pass

    return Nothing


def get_object_to_extend(frame: FrameType) -> Maybe[Tuple[any, str]]:
    try:
        stack = flow(
            dis.get_instructions(frame.f_code),
            lambda s: dropwhile(lambda i: not i.opname.startswith("SETUP_ANNOTATIONS"), s),
            lambda s: dropwhile(lambda i: not i.opname.startswith("LOAD_NAME") or i.argval != "extend", s),
            lambda s: dropwhile(lambda i: i.argval == "extend", s))

        variable = Maybe \
            .from_value(next(takewhile(lambda i: i.opname == "LOAD_NAME", stack))) \
            .map(lambda v: v.argval)

        attr = Maybe.from_value(next(takewhile(lambda i: i.opname == "LOAD_ATTR", stack))) \
            .map(lambda v: v.argval)

        return variable.bind(lambda v: attr.map(lambda a: (frame.f_globals.get(v), a)))
    except StopIteration:
        pass

    return Nothing


def get_instructions(frame: FrameType) -> Iterable[dis.Instruction]:
    try:
        return dropwhile(lambda i: i.offset != frame.f_lasti, dis.get_instructions(frame.f_code))
    except StopIteration:
        return []


def dump_instructions(frame: FrameType) -> None:
    for ins in iter(dis.get_instructions(frame.f_code)):
        print(ins)
