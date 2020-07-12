import dis
from itertools import dropwhile, takewhile

from types import FrameType
from typing import Optional, Iterable


def get_assigned_name(frame: FrameType) -> Optional[str]:
    try:
        stack = get_instructions(frame)

        stack = dropwhile(lambda i: i.opname.startswith("CALL_"), stack)
        stack = takewhile(lambda i: i.opname == "STORE_NAME", stack)

        inst = next(stack)

        return inst.argval if inst is not None else None
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
