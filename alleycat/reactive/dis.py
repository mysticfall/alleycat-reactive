import dis
from itertools import dropwhile, takewhile

from types import FrameType
from typing import Optional, Iterable, Tuple


def get_assigned_name(frame: FrameType) -> Optional[str]:
    try:
        stack = dis.get_instructions(frame.f_code)

        stack = dropwhile(lambda i: i.offset != frame.f_lasti, dis.get_instructions(frame.f_code))
        stack = dropwhile(lambda i: i.opname.startswith("CALL_"), stack)
        stack = takewhile(lambda i: i.opname == "STORE_NAME", stack)

        inst = next(stack)

        return inst.argval if inst is not None else None
    except StopIteration:
        pass

    return None


def get_property_reference(frame: FrameType) -> Optional[Tuple[any, str]]:
    try:
        stack = dis.get_instructions(frame.f_code)

        stack = dropwhile(lambda i: not i.opname.startswith("CALL_"), stack)
        stack = dropwhile(lambda i: i.opname.startswith("CALL_"), stack)
        stack = dropwhile(lambda i: i.opname != "LOAD_FAST", stack)

        variable = next(stack)

        stack = takewhile(lambda i: i.opname == "LOAD_ATTR", stack)

        attr = next(stack)

        if variable is None or attr is None:
            return None

        obj = frame.f_locals.get(variable.argval)

        return (obj, attr.argval) if obj is not None else None
    except StopIteration:
        pass

    return None


def get_object_to_extend(frame: FrameType) -> Optional[Tuple[any, str]]:
    try:
        stack = dis.get_instructions(frame.f_code)

        stack = dropwhile(lambda i: not i.opname.startswith("SETUP_ANNOTATIONS"), stack)
        stack = dropwhile(lambda i: not i.opname.startswith("LOAD_NAME") or i.argval != "extend", stack)
        stack = dropwhile(lambda i: i.argval == "extend", stack)

        variable = next(takewhile(lambda i: i.opname == "LOAD_NAME", stack))
        attr = next(takewhile(lambda i: i.opname == "LOAD_ATTR", stack))

        if variable is None or attr is None:
            return None

        obj = frame.f_globals.get(variable.argval)

        return (obj, attr.argval) if obj is not None else None
    except StopIteration:
        pass

    return None


def get_instructions(frame: FrameType) -> Iterable[dis.Instruction]:
    try:
        return dropwhile(lambda i: i.offset != frame.f_lasti, dis.get_instructions(frame.f_code))
    except StopIteration:
        return []


def dump_instructions(frame: FrameType) -> None:
    for ins in iter(dis.get_instructions(frame.f_code)):
        print(ins)
